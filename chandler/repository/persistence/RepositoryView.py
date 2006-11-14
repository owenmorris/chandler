#   Copyright (c) 2004-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import logging, heapq, sys, gc, threading, os, time

from Queue import Queue
from itertools import izip

from chandlerdb.util.c import UUID, isuuid, Nil, Default, CLinkedMap
from chandlerdb.item.c import CItem
from chandlerdb.persistence.c import CView

from repository.util.Path import Path
from repository.util.Lob import Lob
from repository.util.ClassLoader import ClassLoader
from repository.persistence.RepositoryError import *
from repository.item.Item import Item, MissingClass
from repository.item.Children import Children
from repository.item.Indexes import NumericIndex
from repository.item.RefCollections import RefList


class RepositoryView(CView):
    """
    This class implements the cache for loaded items. Changes to items in a
    view are not written into persistent storage until the view is
    committed. A view will not see changes in the repository made by other
    views until the view is refreshed, for example before a L{commit}.
    """
    
    # 0.5.0: first tracked core schema version
    # 0.5.1: added indexes to abstract sets
    # 0.5.2: renamed 'persist' aspect to 'persisted', added 'indexed' aspect
    # 0.5.3: new monitor implementation
    # 0.5.4: BString and UString types renamed to Bytes and Text
    # 0.5.5: added //Schema/Core/Type.types to get rid of type kind query
    # 0.5.6: added support for Kind extents
    # 0.5.7: added support for Kind inheritedSuperKinds cache
    # 0.5.8: added complete attribute cache
    # 0.5.9: removed repository.query.Query and Query kind
    # 0.5.10: added Importable type
    # 0.5.11: removed inheritedAttributes transient cache
    # 0.6.1: watcherDispatch layout changed
    # 0.6.2: added 'notify' aspect
    # 0.6.3: added Collection 'export' cloud with 'subscribers' endpoint
    # 0.6.4: changed format of some indexes to accept one or more attributes
    # 0.6.5: changed format of abstract sets to store an optional id
    # 0.6.6: added support for MethodFilteredSet
    # 0.6.7: watchers reworked to use RefDict
    # 0.6.8: removed support for persistent collection queue subscriptions
    # 0.6.9: added 'afterChange' attribute aspect
    # 0.6.10: added new enumeration type: ConstantEnumeration
    # 0.6.11: removed Kind inheritedSuperKinds transient cache
    # 0.6.12: removed 'persisted' aspect
    # 0.6.13: added 'literal' endpoint include policy
    # 0.6.14: added support for 'init' monitor op
    # 0.6.15: added IndexMonitor class
    # 0.6.16: added support for python's decimal.Decimal type
    
    CORE_SCHEMA_VERSION = 0x00061000

    def __init__(self, repository, name, version, deferDelete=Default):
        """
        Initializes a repository view.

        This contructor should not be invoked directly but the
        L{createView<repository.persistence.Repository.Repository.createView>}
        method should be used instead so that the appropriate view
        implementation for the repository be used.
        """

        if not name:
            name = threading.currentThread().getName()

        if repository is not None and not repository.isOpen():
            raise RepositoryError, "Repository is not open"

        super(RepositoryView, self).__init__(repository, name,
                                             RepositoryView.itsUUID)
        self.openView(version, deferDelete)
        
    def setCurrentView(self):
        """
        Make this view the current view for the current thread.

        The repository gets the current view from the current thread. This
        method should be used to select this view as the current one for the
        current thread.

        @return: the view that was current for the thread before this call.
        """

        return self.repository.setCurrentView(self)

    def _isNullView(self):

        return False

    def _createRefList(self, item, name, otherName, dictKey, 
                       readOnly, new, uuid):

        raise NotImplementedError, "%s._createRefList" %(type(self))
    
    def _createChildren(self, parent, new):

        raise NotImplementedError, "%s._createChildren" %(type(self))
    
    def _getLobType(self):

        raise NotImplementedError, "%s._getLobType" %(type(self))

    def createLob(self, data, *args, **kwds):

        return self['Schema']['Core']['Lob'].makeValue(data, *args, **kwds)

    def openView(self, version=None, deferDelete=Default):
        """
        Open this repository view.

        A view is created open, calling this method is only necessary when
        re-opening a closed view.
        """

        repository = self.repository

        if version is None:
            if repository is not None:
                version = repository.store.getVersion()
            else:
                version = 0

        self._notifications = Queue()

        self._version = long(version)
        self._roots = self._createChildren(self, version == 0)
        self._registry = {}
        self._deletedRegistry = {}
        self._instanceRegistry = {}
        self._loadingRegistry = set()
        self._status = ((self._status & RepositoryView.VERIFY) |
                        RepositoryView.OPEN)

        if deferDelete is Default:
            deferDelete = repository._deferDelete
        self._deferDelete = deferDelete
        if self._deferDelete:
            self.deferDelete()

        self.classLoader = ClassLoader(Item, MissingClass)

        if repository is not None:
            if repository.isRefCounted():
                self._status |= RepositoryView.REFCOUNTED
            repository.store.attachView(self)
            repository._openViews.append(self)

        self._loadSchema()

    def _loadSchema(self):

        schema = self.findPath('Packs/Schema')

        if schema is None:
            import repository
            path = os.path.join(os.path.dirname(repository.__file__),
                                'packs', 'schema.pack')
            schema = self.loadPack(path)
            schema.version = RepositoryView.CORE_SCHEMA_VERSION

        return schema

    def __nonzero__(self):

        return True

    def _setChildren(self, children):

        self._roots = children

    def setDirty(self, dirty):

        if dirty:
            if not self._status & RepositoryView.LOADING:
                self._status |= CItem.CDIRTY
        else:
            self._status &= ~CItem.CDIRTY

    def isDirty(self):

        return self._status & CItem.CDIRTY != 0

    def isDirtyAgain(self):
        """
        Tell if changes were made since last time L{mapChanges} was called.
        """

        return self._status & CItem.FDIRTY != 0

    def closeView(self):
        """
        Close this repository view.

        All items in the view are marked stale. The item cache is flushed.
        A closed view cannot be used until is re-opened with L{openView}.
        """

        if not self._status & RepositoryView.OPEN:
            raise RepositoryError, "RepositoryView is not open"

        repository = self.repository
        if repository is not None:
            if getattr(repository._threaded, 'view', None) is self:
                del repository._threaded.view
            repository._openViews.remove(self)

        self.flushNotifications()
        self._clear()

        if repository is not None:
            repository.store.detachView(self)

        self._status &= ~RepositoryView.OPEN

    def _clear(self):

        if self._registry:
            for item in self._registry.values():
                if hasattr(type(item), 'onViewClear'):
                    item.onViewClear(self)
                item._unloadItem(False, self, False)
            del item

        self._registry.clear()
        self._roots.clear()
        self._deletedRegistry.clear()
        self._instanceRegistry.clear()
        self._loadingRegistry.clear()

        if self._monitors:
            self._monitors.clear()
        if self._watchers:
            self._watchers.clear()

        # clear other caches that may have been added upstream
        self.__dict__.clear()
        gc.collect()

    def prune(self, size):
        """
        Remove least-used items from the view's item cache.

        If there are C{size + 10%} items in the view's cache, the least-used
        items are removed from cache such that the cache size decreases to
        C{size - 10%} items.

        Pinned items and schema items are never removed from cache.
        
        @param size: the threshhold value
        @type size: integer
        """

        pass

    def walk(self, path, callable, _index=0, **kwds):
        """
        Walk a path and invoke a callable along the way.

        The callable's arguments need to be defined as C{parent},
        C{childName}, C{child} and C{**kwds}.
        The callable is passed C{None} for the C{child} argument if C{path}
        doesn't correspond to an existing item.
        The callable's return value is used to recursively continue walking
        when it is not C{None}.
        The callable may be C{None} in which case it is equivalent to:

            - C{lambda parent, name, child, **kwds: child}

        A C{load} keyword can be used to prevent loading of items by setting
        it to C{False}. Items are loaded as needed by default.

        @param path: an item path
        @type path: a L{Path<repository.util.Path.Path>} instance
        @param callable: a function, method, lambda body, or None
        @type callable: a python callable
        @param kwds: optional keywords passed to the callable
        @return: the item the walk finished on or C{None}
        """

        l = len(path)
        if l == 0:
            return None

        if path[_index] == '//':
            _index += 1

        if _index >= l:
            return None

        name = path[_index]
        if isinstance(name, UUID):
            root = self.findUUID(name, kwds.get('load', True))
            if root is not None and root.itsParent is not self:
                root = None
        else:
            root = self.getRoot(name, kwds.get('load', True))
        
        if callable is not None:
            root = callable(self, path[_index], root, **kwds)
        if root is not None:
            if _index == l - 1:
                return root
            return root.walk(path, callable, _index + 1, **kwds)

        return None

    def _fwalk(self, path, load=True):

        if not isinstance(path, Path):
            raise TypeError, '%s is not Path or UUID' %(type(path))

        item = self
        for name in path:

            if name == '//':
                item = self
            elif name == '/':
                item = item.itsRoot
            elif name == '..':
                item = item.itsParent
            elif name == '.':
                pass
            elif isinstance(name, UUID):
                child = self.find(name, load)
                if child is None or child.itsParent is not item:
                    item = None
                else:
                    item = child
            else:
                item = item.getItemChild(name, load)

            if item is None:
                break

        return item

    def findPath(self, path, load=True):
        """
        Find an item by path.

        See L{find} for more information.

        @param path: a path
        @type path: L{Path<repository.util.Path.Path>} or a path string
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

        if isinstance(path, (str, unicode)):
            path = Path(path)
        elif not isinstance(path, Path):
            raise TypeError, '%s is not Path or string' %(type(path))

        return self._fwalk(path, load)

    def findUUID(self, uuid, load=True):
        """
        Find an item by UUID.

        See L{find} for more information.

        @param uuid: a UUID
        @type uuid: L{UUID<chandlerdb.util.c.UUID>} or a uuid string
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

        if isinstance(uuid, (str, unicode)):
            uuid = UUID(uuid)
        elif not isinstance(uuid, UUID):
            raise TypeError, '%s is not UUID or string' %(type(uuid))

        return self.find(uuid, load)

    def findValue(self, uItem, name, default=Default, version=None):
        """
        Find a value for an item attribute.

        If the item is already loaded, regular attribute value retrieval is
        used.

        If the item is not loaded, only the value for the named attribute is
        returned with the following limitations:

            - only local values are returned, schema-based inheritance is
              not used to return a non-local value.

            - item references and bi-directional ref collections are
              returned as UUIDs, they are not actually loaded.

        If the item does not exist or does not have a value for the given
        attribute an optional default value is returned or an exception is
        raised.

        To load multiple values for the same item, consider using
        L{findValues}.

        @param uItem: an item UUID
        @param name: an attribute name
        @param default: an optional default value to return if the item does
        not exist or does not have a local value for C{name}; an exception
        is raised if default is not specified and no value was found.
        @return: an attribute value or C{default}
        """

        if version is None:
            version = self.itsVersion

        if isuuid(uItem):
            item = self.find(uItem, False)
        else:
            item = uItem

        if item is not None and item.itsVersion <= version:
            return item.getAttributeValue(name, None, None, default, True)

        reader, uValue = self.repository.store.loadValue(self, version,
                                                         uItem, name)
        if reader is None:
            if uValue is Nil:
                if default is Default:
                    raise KeyError, uItem
                return default
            if uValue is Default:
                if default is Default:
                    raise AttributeError, (uItem, name)
                return default

        return reader.readValue(self, uValue)[1]

    def findValues(self, uItem, *pairs):
        """
        Find values for one or more attributes of an item.

        As with L{findValue}, if the item is already loaded, regular
        attribute value retrieval is used.

        If the item is not loaded, the values for the named attributes are
        returned, without loading the item, with the following limitations:

            - only local values are returned, schema-based inheritance is
              not used to return a non-local value.

            - item references and bi-directional ref collections are
              returned as UUIDs, they are not actually loaded.

        If the item does not exist or does not have a value for the given
        attribute a default value is returned.

        @param uItem: an item UUID
        @param pairs: one or more C{(name, default)} tuples for each
        attribute to retrieve a value for.
        @return: a tuple of attribute or default values, matching the order
        of the given C{(name, default)} pairs.
        """

        if isuuid(uItem):
            item = self.find(uItem, False)
        else:
            item = uItem

        if item is not None:
            return tuple([item.getAttributeValue(name, None, None,
                                                 default, True)
                          for name, default in pairs])

        names = (name for name, default in pairs)
        reader, uValues = self.repository.store.loadValues(self,
                                                           self.itsVersion,
                                                           uItem, names)
        if reader is None:
            return tuple([default for name, default in pairs])

        values = []
        for uValue, (name, default) in izip(uValues, pairs):
            if uValue is not None:
                values.append(reader.readValue(self, uValue)[1])
            else:
                values.append(default)

        return tuple(values)

    def hasValue(self, uItem, name):
        """
        Tell if an item has a local attribute value without loading it.

        As with L{findValue} and L{findValues}, if the item is already
        loaded, regular attribute retrieval is used.

        If the item is not loaded, the item record in the repository is
        checked for a value but it is not returned.

        @param uItem: an item UUID
        @param name: an attribute name
        @return: C{True} if a value was found, C{False} otherwise
        """

        item = self.find(uItem, False)
        if item is not None:
            return hasattr(item, name)

        return self.repository.store.hasValue(self, self.itsVersion,
                                              uItem, name)

    def hasTrueValue(self, uItem, name, version=None):
        """
        Find a value for an item attribute and check if it's 'True'.

        If the item is already loaded, regular attribute value retrieval is
        used.

        If the item is not loaded, only the value for the named attribute is
        returned with the following limitation:

            - only local values are tested, schema-based inheritance is
              not used to return a non-local value.

        If the item does not exist or does not have a value for the given
        attribute C{False} is returned.

        @param uItem: an item UUID
        @param name: an attribute name
        @return: C{True} or C{False}
        """

        if version is None:
            version = self.itsVersion

        item = self.find(uItem, False)
        if item is not None and item.itsVersion <= version:
            return item.hasTrueAttributeValue(name)

        reader, uValue = self.repository.store.loadValue(self, version,
                                                         uItem, name)
        if reader is None:
            return False

        return reader.hasTrueValue(self, uValue)

    def hasTrueValues(self, uItem, *names):
        """
        Find values for attributes of an item and check if they are 'True'.

        As with L{findValues}, if the item is already loaded, regular
        attribute value retrieval is used.

        If the item is not loaded, the values for the named attributes are
        checked, without loading the item, with the following limitations:

            - only local values are returned, schema-based inheritance is
              not used to return a non-local value.

        If the item does not exist or does not have a value for the given
        attribute False is returned.

        @param uItem: an item UUID
        @param names: one or more name for each attribute to check.
        @return: C{True} if all values are True, C{False} otherwise.
        """

        item = self.find(uItem, False)
        if item is not None:
            for name in names:
                if not item.hasTrueAttributeValue(name):
                    return False
            return True

        reader, uValues = self.repository.store.loadValues(self,
                                                           self.itsVersion,
                                                           uItem, names)
        if reader is None or None in uValues:
            return False

        for uValue in uValues:
            if not reader.hasTrueValue(self, uValue):
                return False

        return True

    def findMatch(self, view, matches=None):

        return view

    def _findKind(self, spec, withSchema):

        return self.find(spec)

    def getACL(self, uuid, name, default=None):
        """
        Get an Access Control List.

        ACLs are stored by C{(uuid, name)} tuples. C{name} can be C{None}.
        Therefore, each item in the repository may have an ACL, and each
        attribute value for each item in the repository may also have an
        ACL.

        By convention, the ACL for an item is stored with C{(item.itsUUID,
        None)} and the ACL for an attribute value on an item is stored with
        C{(item.itsUUID, attributeName)}.

        @param uuid: a L{UUID<chandlerdb.util.c.UUID>} instance
        @param name: a string or C{None}
        @param default: an optional default value to return when no ACL is
        found (by default C{None} is returned)
        @return: an L{ACL<repository.item.Access.ACL>} instance or C{None}
        """

        acl = self.repository.store.loadACL(self, self._version, uuid, name)
        if acl is None:
            return default

        return acl

    def loadPack(self, path, parent=None):
        """
        Load items from the pack definition file at path.

        This is mostly a bootstrap feature.

        @param path: the path to the packfile to load
        @type path: a string
        @param parent: the item to load the items in the pack under
        @type parent: an item
        @return: the loaded pack, an item of kind Pack
        """

        from repository.persistence.PackHandler import PackHandler

        handler = PackHandler(path, parent, self)

        try:
            verify = self._setVerify(False)
            handler.parseFile(path)
        finally:
            self._setVerify(verify)

        return handler.pack

    def dir(self, item=None, path=None):
        """
        Print out a listing of each item in the repository or under item.

        This is a debugging feature.

        @param item: the item to list children of, or C{None}
        @type item: an item
        @param path: the path to the item to list children of, or C{None}
        @type path: a L{Path<repository.util.Path.Path>} instance
        """
        
        if item is None:
            path = Path('//')
            for root in self.iterRoots():
                self.dir(root, path)
        else:
            if path is None:
                path = item.itsPath
            else:
                path.append(item._name or item._uuid)
            print path
            for child in item.iterChildren():
                self.dir(child, path)
            path.pop()

    def check(self, repair=False):
        """
        Runs repository consistency checks on this view.

        All items of the repository are loaded into this view and checked
        for consistency with their schema definition. See
        L{Item.check<repository.item.Item.Item.check>} for more details.
        """

        result = True
        for root in self.iterRoots():
            check = root.check(True, repair)
            result = result and check

        return result

    def hasRoots(self):
        """
        Tell whether this view has any roots.

        @return: C{True} or C{False}
        """

        return (self._roots is not None and
                self._roots._firstKey is not None)

    def hasRoot(self, name, load=True):
        """
        Tell whether the repository has a root by a given name.

        This view is searched for a root.

        @param name: the name of the root to be looked for
        @type name: a string
        @param load: controls whether to check only loaded roots if
        C{False} or all roots if C{True}, the default.
        @return: C{True} or C{False}
        """

        return (name is not None and
                self._roots.resolveAlias(name, load) is not None)

    def getRoot(self, name, load=True):
        """
        Get a root by a given name.

        This view is searched for a root.

        @param name: the name of the root to be looked for
        @type name: a string
        @param load: controls whether to check only loaded roots if
        C{False} or all roots if C{True}, the default.
        @return: a root item or C{None} if not found.
        """

        return self._roots.getByAlias(name, None, load)

    def getItemDisplayName(self):

        return self.name

    def getItemChild(self, name, load=True):

        return self.getRoot(name, load)

    def hasChildren(self):

        return self.hasRoots()

    def hasChild(self, name, load=True):

        return self.hasRoot(name, load)

    def __iter__(self):
        """
        (deprecated) Use L{iterRoots} instead.
        """

        raise DeprecationWarning, 'Use RepositoryView.iterRoots() instead'
    
    def iterChildren(self):
        """
        See L{iterRoots}
        """

        return self.iterRoots()
    
    def iterRoots(self, load=True):
        """
        Iterate over the roots of this repository in this view.
        """

        if not load:
            for child in self._roots._itervalues():
                yield child._value

        else:
            for child in self._roots:
                yield child

    def _getPath(self, path=None):

        if path is None:
            path = Path()
        path.set('//')

        return path

    def _getStore(self):

        return self.repository.store

    def _logItem(self, item):

        if not self.repository.isOpen():
            raise RepositoryError, 'Repository is not open'

        if item.itsView is not self:
            raise RepositoryError, 'Repository view is not owning item: %s' %(item.itsPath)

        return not self.isLoading()

    def dirtyItems(self):

        raise NotImplementedError, "%s.dirtyItems" %(type(self))

    def hasDirtyItems(self):

        raise NotImplementedError, "%s.hasDirtyItems" %(type(self))

    def _addItem(self, item):

        name = item.itsName
        if name is not None:
            key = self._roots.resolveAlias(name, not self.isLoading())
            if not (key is None or key == item.itsUUID):
                raise ValueError, "A root named '%s' exists already" %(name)

        self._roots._append(item)

        return item

    def _removeItem(self, item):

        del self._roots[item.itsUUID]

    def _unloadChild(self, child):

        self._roots._unloadChild(child)

    def _registerItem(self, item):

        uuid = item.itsUUID

        old = self._registry.get(uuid)
        if old is not None and old is not item:
            raise ValueError, '%s: re-registering %s with different object' %(self, item)
        
        self._registry[uuid] = item

    def _unregisterItem(self, item, reloadable):

        uuid = item.itsUUID
        del self._registry[uuid]

        if item.isDeleting():
            self._deletedRegistry[uuid] = item
        elif reloadable:
            self._instanceRegistry[uuid] = item

    def _reuseItemInstance(self, uuid):

        return self._instanceRegistry.pop(uuid, None)

    def refresh(self, mergeFn=None, version=None, notify=True):
        """
        Refresh this view to the changes made in other views.

        Refreshing a view causes the following to happen, in this order:
        
            1. Version conflicts are detected. If an item in this view was
               changed in another view and it committed its changes first,
               there is a chance that these changes would conflict with the
               ones about to be committed by this view. A
               C{VersionConflictError} is raised in that situation.
            2. The view is refreshed to the latest version in persistent
               store. Pointers to items that changed in other views that are
               also in this view are marked C{STALE} unless they're pinned
               in memory in which case they're refreshed in place.
            3. Change and history notifications from changes in other views
               are dispatched after the merges succeeded if C{notify} is
               C{True}, the default.
            4. If the view's cache has reached a threshhold item count - at
               the moment 10,000 - the least-used items are removed from
               cache and pointers to them are marked C{STALE} such that the
               size of the cache drops below 90% of this threshhold.
        """
        
        raise NotImplementedError, "%s.refresh" %(type(self))

    def commit(self, mergeFn=None, notify=True):
        """
        Commit all the changes made to items in this view.

        Committing a view causes the following to happen, in this order:
        
            1. L{refresh} is called.
            2. All changes made to items in the view are saved to
               persistent storage.
            3. Change and history notifications from the items committed
               are dispatched after the transactions commits if C{notify} is
               {True}, the default.
        """
        
        raise NotImplementedError, "%s.commit" %(type(self))

    def cancel(self):
        """
        Cancel all the changes made to items in this view.

        Cancelling a view causes the following to happen, in this order:
        
            1. All new items are unloaded.
            2. All deleted and changed items are refreshed to their original
               state and marked unchanged.
            3. If the view's cache has reached a threshhold item count - at
               the moment 10,000 - the least-used items are removed from
               cache and pointers to them are marked C{STALE} such that the
               size of the cache drops below 90% of this threshhold.
        """
        
        raise NotImplementedError, "%s.cancel" %(type(self))

    def queryItems(self, kind=None, attribute=None):
        """
        Query this view for items.

        @param kind: a kind item for a kind query
        @type kind: an item
        @param attribute: an attribute UUID for a value query
        @type attribute: a UUID
        """
        
        raise NotImplementedError, "%s.queryItems" %(type(self))

    def queryItemKeys(self, kind=None, attribute=None):
        """
        Query this view for item UUIDs.

        @param kind: a kind item for a kind query
        @type kind: an item
        @param attribute: an attribute UUID for a value query
        @type attribute: a UUID
        """
        
        raise NotImplementedError, "%s.queryItemKeys" %(type(self))

    def kindForKey(self, uuid):

        raise NotImplementedError, "%s.kindForKey" %(type(self))

    def searchItems(self, query, attribute=None, load=True):
        """
        Search this view for items using an Lucene full text query.

        @param query: a lucene query
        @type query: a string
        @param attribute: an attribute name to match against, C{None} by
        default to match against all attributes.
        @type attribute: a string
        @param load: if C{False} only return loaded items
        @type load: boolean
        """

        raise NotImplementedError, "%s.searchItems" %(type(self))

    def _loadItem(self, uuid):
        raise NotImplementedError, "%s._loadItem" %(type(self))

    def _loadRoot(self, name):
        raise NotImplementedError, "%s._loadRoot" %(type(self))

    def mapChanges(self, freshOnly=False):
        """
        Generate a change tuple for every item changed in this view.

        For each item that was changed in this view since it last committed
        a tuple is generated with the following elements:

            - the item

            - the item's current version

            - the item's current status bits

            - a list of changed literal attribute names

            - a list of changed references attribute names

        @param freshOnly: optionally limit tuple generation to
        items that were changed since last time this method was called or
        since the last commit, whichever came last; C{False} by default.
        @type freshOnly: boolean
        """

        raise NotImplementedError, "%s.mapChanges" %(type(self))
    
    def mapHistory(self, fromVersion=0, toVersion=0, history=None):
        """
        Generate a change tuple for every committed item change in other views.

        For each item that was changed and committed in another view a
        a tuple is generated with the following elements:

            - the UUID of the item

            - the item's committed version for the change

            - the item's Kind item

            - the item's committed status bits for the change

            - a list of changed literal attribute names

            - a list of changed references attribute names

            - None or the item's previous kind if it changed

        @param fromVersion: the version to start iterating changes from, the
        current version by default.
        @type fromVersion: integer
        @param toVersion: the version to continue iterating changes to, the
        latest committed version by default.
        @type toVersion: integer
        @param history: instead of querying the repository history between
        versions, use the history records in this list.
        @type history: iterable
        """

        raise NotImplementedError, "%s.mapHistory" %(type(self))

    def recordChangeNotifications(self):

        if not self._isRecording():
            self._changeNotifications = []
            self._status |= RepositoryView.RECORDING

    def playChangeNotifications(self):

        if self._isRecording():
            self._status &= ~RepositoryView.RECORDING
            for callable, args, kwds in self._changeNotifications:
                callable(*args, **kwds)
            self._changeNotifications = None

    def discardChangeNotifications(self):

        if self._isRecording():
            self._status &= ~RepositoryView.RECORDING
            self._changeNotifications = None

    def _commitMerge(self):

        if self._status & CItem.CMERGED:
            self._roots._commitMerge()

    def _revertMerge(self):

        if self._status & CItem.CMERGED:
            self._roots._revertMerge()

        self._status &= ~CItem.MERGED

    def getItemVersion(self, version, item):

        return self.repository.store.getItemVersion(self, version, item.itsUUID)

    def importItem(self, item):

        items = set()
        view = item.itsView
        if view is self or item.findMatch(self) is not None:
            return items

        replace = {}

        def filterItem(_item):
            if _item.findMatch(self, replace):
                return False

            if _item._isCopyExport():
                _item._copyExport(self, 'export', replace)
                return False

            return True

        item._collectItems(items, filterItem)
        if not (item in items or item._uuid in replace):
            if filterItem(item) is True:
                items.add(item)

        self._importValues(items, replace, view)
        self._importItems(items, replace, view)

        return items

    def _importValues(self, items, replace, view):

        sameType = type(self) is type(view)

        for item in items:
            kind = item._kind
            if not (kind is None or kind in items):
                uuid = kind._uuid
                localKind = replace.get(uuid)
                if localKind is None:
                    localKind = self.find(uuid)
                    if localKind is None:
                        raise ImportKindError, (kind, item)
                item._kind = localKind
                localKind._setupClass(type(item))

            try:
                item._status |= CItem.IMPORTING
                item._values._import(self)
                item._references._import(self, items, replace)
            finally:
                item._status &= ~CItem.IMPORTING
    
    def _importItems(self, items, replace, view):

        sameType = type(self) is type(view)

        def setRoot(root, _item):
            view._unregisterItem(_item, False)
            self._registerItem(_item)
            _item._root = root
            for child in _item.iterChildren():
                setRoot(root, child)

        for item in items:
            if hasattr(type(item), 'onItemImport'):
                item.onItemImport(self)
            if not sameType and item.hasChildren():
                children = self._createChildren(item, True)
                for child in item.iterChildren():
                    children._append(child)
                item._children = children
            parent = item.itsParent
            if not parent in items:
                localParent = parent.findMatch(self, replace)
                if localParent is None:
                    raise ImportParentError, (parent, item)
                if localParent is not parent:
                    if item.isNew():
                        parent._removeItem(item)
                    else:
                        parent._unloadChild(item)
                    root = localParent._addItem(item)
                    item._parent = localParent
                    setRoot(root, item)

    def queueNotification(self, item, op, change, name, other):

        self._notifications.put((item.itsUUID, op, change, name, other))

    def dispatchNotifications(self):

        count = 0
        queue = self._notifications

        while True:
            while not queue.empty():
                uItem, op, change, name, other = queue.get()
                count += 1

                watchers = self._watchers.get(uItem)
                if watchers:
                    watchers = watchers.get(self.SUBSCRIBERS)
                    if watchers:
                        try:
                            collection = self[uItem]
                        except KeyError:
                            continue
                        else:
                            for watcher in watchers:
                                watcher(op, change, collection, name, other)

            while self.isDirtyAgain():
                self._dispatchChanges(self.mapChanges(True))

            if queue.empty():
                break

        return count

    def flushNotifications(self):

        count = 0
        queue = self._notifications

        while not queue.empty():
            queue.get()
            count += 1

        return count

    def _dispatchHistory(self, history, refreshes, oldVersion, newVersion):

        raise NotImplementedError, "%s._dispatchHistory" %(type(self))

    def _dispatchChanges(self, changes):

        raise NotImplementedError, "%s._dispatchChanges" %(type(self))

    def _registerWatch(self, watchingItem, watchedItem, cls, key, *args):

        uWatching = watchingItem.itsUUID
        uWatched = watchedItem.itsUUID

        watchers = self._watchers.get(uWatched)
        if watchers is None:
            self._watchers[uWatched] = {key: [cls(self, uWatching, *args)]}
        else:
            watchers = watchers.get(key)
            if watchers is None:
                self._watchers[uWatched][key] = [cls(self, uWatching, *args)]
            else:
                for watcher in watchers:
                    if (watcher.watchingItem == uWatching and
                        type(watcher) is cls and watcher.compare(*args)):
                        return watcher
                watchers.append(cls(self, uWatching, *args))
                
        if cls is TransientWatchItem:
            watchedItem._status |= CItem.T_WATCHED

        return self._watchers[uWatched][key][-1]

    def _unregisterWatch(self, watchingItem, watchedItem, cls, key, *args):

        watchers = self._watchers
        uWatching = watchingItem.itsUUID
        uWatched = watchedItem.itsUUID

        if watchers:
            watchers = watchers.get(uWatched)
            if watchers:
                watchers = watchers.get(key)
                if watchers:
                    for watcher in watchers:
                        if (watcher.watchingItem == uWatching and
                            type(watcher) is cls and watcher.compare(*args)):
                            watchers.remove(watcher)
                    if not watchers:
                        del self._watchers[uWatched][key]
                        if not self._watchers[uWatched]:
                            del self._watchers[uWatched]
                        if cls is TransientWatchItem:
                            watchedItem._status &= ~CItem.T_WATCHED

    def _unregisterWatches(self, item):

        watchers = self._watchers
        if watchers:
            uItem = item.itsUUID
            watchers.pop(uItem, None)
            for uWatched, watcherDict in watchers.items():
                for key, watchers in watcherDict.items():
                    watchers = [watcher for watcher in watchers
                                if watcher.watchingItem != uItem]
                    if watchers:
                        watcherDict[key] = watchers
                    else:
                        del watcherDict[key]
                if not watcherDict:
                    del self._watchers[uWatched]

    def watchItem(self, watchingItem, watchedItem, methodName):
        return self._registerWatch(watchingItem, watchedItem,
                                   TransientWatchItem,
                                   watchedItem.itsUUID, methodName)

    def unwatchItem(self, watchingItem, watchedItem, methodName):
        self._unregisterWatch(watchingItem, watchedItem, TransientWatchItem,
                              watchedItem.itsUUID, methodName)

    def watchKind(self, watchingItem, kind, methodName):
        return self._registerWatch(watchingItem, kind.extent,
                                   TransientWatchKind,
                                   'extent', methodName)

    def unwatchKind(self, watchingItem, kind, methodName):
        self._unregisterWatch(watchingItem, kind.extent, TransientWatchKind,
                              'extent', methodName)

    def watchCollection(self, watchingItem, owner, attribute, methodName):
        return self._registerWatch(watchingItem, owner,
                                   TransientWatchCollection,
                                   attribute, methodName)

    def unwatchCollection(self, watchingItem, owner, attribute, methodName):
        self._unregisterWatch(watchingItem, owner, TransientWatchCollection,
                              attribute, methodName)

    def watchCollectionQueue(self, watchingItem, collection, methodName):
        return self._registerWatch(watchingItem, collection,
                                   TransientWatchCollection,
                                   RepositoryView.SUBSCRIBERS, methodName)

    def unwatchCollectionQueue(self, watchingItem, collection, methodName):
        self._unregisterWatch(watchingItem, collection,
                              TransientWatchCollection,
                              RepositoryView.SUBSCRIBERS, methodName)

    def printVersions(self, fromVersion=1, toVersion=0):

        for version, (then, viewSize, commitCount, name) in self.store.iterCommits(self, fromVersion, toVersion):
            if name == self.name:
                then = time.strftime("%d-%b-%y,%H:%M:%S", time.localtime(then))
                print "%6d: %s %4d %4d" %(version, then,
                                          viewSize, commitCount)

    def printItemVersions(self, item, fromVersion=1, toVersion=0):

        store = self.store
        for version, status in store.iterItemVersions(self, item.itsUUID, fromVersion, toVersion):
            then, viewSize, commitCount, name = store.getCommit(version)
            if name == self.name:
                then = time.strftime("%d-%b-%y,%H:%M:%S", time.localtime(then))
                print "%6d: %s %4d %4d 0x%08x" %(version, then,
                                                 viewSize, commitCount, status)

    itsUUID = UUID('3631147e-e58d-11d7-d3c2-000393db837c')
    SUBSCRIBERS = UUID('4dc81eae-1689-11db-a0ac-0016cbc90838')

    itsPath = property(_getPath)
    views = property(lambda self: self.repository.getOpenViews())


class OnDemandRepositoryView(RepositoryView):

    def __init__(self, repository, name, version, deferDelete=Default):

        if version is None:
            version = repository.store.getVersion()

        super(OnDemandRepositoryView, self).__init__(repository, name, version,
                                                     deferDelete)

    def openView(self, version=None, deferDelete=Default):

        self._exclusive = threading.RLock()
        self._hooks = []
        
        super(OnDemandRepositoryView, self).openView(version, deferDelete)

    def isNew(self):

        return self.itsVersion == 0

    def _acquireExclusive(self):

        return self._exclusive.acquire()

    def _releaseExclusive(self):

        return self._exclusive.release()

    def _setLoading(self, loading, runHooks=False):

        if not loading and self.isLoading() and runHooks:
            try:
                for hook in self._hooks:
                    hook(self)
            finally:
                self._hooks = []

        return super(OnDemandRepositoryView, self)._setLoading(loading)

    def _readItem(self, itemReader):

        release = False
        try:
            try:
                loading = self.isLoading()
                if not loading:
                    release = self._acquireExclusive()
                    self._setLoading(True)
                    self._hooks = []

                item = itemReader.readItem(self, self._hooks)
            except:
                if not loading:
                    self._setLoading(False, False)
                    self._hooks = []
                raise
        
            if not loading:
                self._setLoading(False, True)

            return item

        finally:
            if release:
                self._releaseExclusive()

    def _loadItem(self, uuid):

        if uuid in self._loadingRegistry:
            raise RecursiveLoadItemError, uuid

        if not uuid in self._deletedRegistry:
            itemReader = self.repository.store.loadItem(self, self.itsVersion,
                                                        uuid)

            if itemReader is not None:
                try:
                    self._loadingRegistry.add(uuid)
                    return self._readItem(itemReader)
                finally:
                    self._loadingRegistry.remove(uuid)

        return None

    def _findSchema(self, spec, withSchema):

        if withSchema:
            return self.find(spec, False)

        # when crossing the schema boundary, reset loading status so that
        # hooks get called before resuming regular loading

        try:
            hooks = self._hooks
            loading = self._setLoading(False)
            
            return self.find(spec)
        finally:
            self._hooks = hooks
            self._setLoading(loading)

    def _addItem(self, item):

        super(OnDemandRepositoryView, self)._addItem(item)

        item.setPinned(True)

        return item

    def _removeItem(self, item):

        super(OnDemandRepositoryView, self)._removeItem(item)

        item.setPinned(False)
        
    def prune(self, size):

        registry = self._registry
        
        if len(registry) > size * 1.1:
            gc.collect()
            heap = [(item._lastAccess, item.itsUUID)
                    for item in registry.itervalues()
                    if not item._status & (item.PINNED | item.DIRTY)]

            heapq.heapify(heap)

            count = len(heap) - int(size * 0.9)
            if count > 0:
                self.logger.info('pruning %d items', count)
                debug = self.isDebug()

                if self.isRefCounted():
                    for i in xrange(count):
                        item = registry[heapq.heappop(heap)[1]]
                        itemRefs = item._refCount()
                        pythonRefs = sys.getrefcount(item)
                        if pythonRefs - itemRefs <= 3:
                            item._unloadItem(False, self)
                        elif debug:
                            self.logger.debug('not pruning %s (refCount %d)',
                                              item._repr_(),
                                              pythonRefs - itemRefs)
                else:
                    for i in xrange(count):
                        registry[heapq.heappop(heap)[1]]._unloadItem(False, self)


class NullRepositoryView(RepositoryView):

    def __init__(self, verify=False):

        super(NullRepositoryView, self).__init__(None, "null view", 0, False)

        if verify:
            self._status |= RepositoryView.VERIFY

    def openView(self, version=None, deferDelete=Default):

        self._logger = logging.getLogger(__name__)
        super(NullRepositoryView, self).openView(version, False)

    def setCurrentView(self):

        raise AssertionError, "Null view cannot be made current"

    def refresh(self, mergeFn=None):
        
        raise AssertionError, "Null view cannot refresh"

    def commit(self, mergeFn=None):
        
        raise AssertionError, "Null view cannot commit"

    def cancel(self):
        
        raise AssertionError, "Null view cannot cancel"

    def _createRefList(self, item, name, otherName, dictKey, 
                       readOnly, new, uuid):

        return NullViewRefList(item, name, otherName, dictKey, readOnly)
    
    def _createChildren(self, parent, new):

        return Children(parent, new)

    def _createNumericIndex(self, **kwds):

        return NumericIndex(**kwds)
    
    def _getLobType(self):

        return NullViewLob

    def _findSchema(self, spec, withSchema):

        return self.find(spec, False)

    def _loadItem(self, uuid):

        return None

    def findValue(self, uItem, name, default=Default):

        if default is not Default:
            return getattr(self[uItem], name, default)

        return getattr(self[uItem], name)

    def setDirty(self, dirty):

        pass

    def isDirty(self):

        return False

    def isOpen(self):

        return (self._status & RepositoryView.OPEN) != 0

    def isNew(self):

        return False

    def isStale(self):

        return False

    def isRefCounted(self):

        return True
        
    def isLoading(self):

        return False

    def isDebug(self):

        return self._logger.getEffectiveLevel() <= logging.DEBUG

    def _isNullView(self):

        return True

    def _setLoading(self, loading, runHooks=False):

        raise AssertionError, "Null view cannot load items"

    def _getStore(self):

        return None

    def mapChanges(self, callable, freshOnly=False):

        pass

    def _logItem(self, item):

        return True

    def dirtyItems(self):

        return self._registry.itervalues()

    def hasDirtyItems(self):

        return len(self._registry) > 0

    def getLogger(self):

        return self._logger

    def getItemVersion(self, version, item):

        return item._version

    def queryItems(self, kind=None, attribute=None):

        if kind is not None:
            return (item for item in self._registry.itervalues()
                    if item._kind is kind)

        elif attribute is not None:
            raise NotImplementedError, 'attribute query'

        else:
            raise ValueError, 'one of kind or value must be set'

    def queryItemKeys(self, kind=None, attribute=None):

        if kind is not None:
            return (key for key, item in self._registry.iteritems()
                    if item._kind is kind)

        elif attribute is not None:
            raise NotImplementedError, 'attribute query'

        else:
            raise ValueError, 'one of kind or value must be set'

    def kindForKey(self, uuid):

        return self[uuid].itsKind

    logger = property(getLogger)
    itsUUID = UUID('17368718-a164-11d9-9351-000393db837c')


class NullViewLob(Lob):

    def __init__(self, view, *args, **kwds):

        super(NullViewLob, self).__init__(*args, **kwds)


class NullViewRefList(RefList):

    def __init__(self, item, name, otherName, dictKey, readOnly):

        super(NullViewRefList, self).__init__(item, name, otherName, dictKey,
                                              readOnly, CLinkedMap.NEW)

    def _setOwner(self, item, name):

        super(NullViewRefList, self)._setOwner(item, name)
        if item is not None:
            self.view = item.itsView

    def linkChanged(self, link, key):
        pass
    
    def _check(self, logger, item, name, repair):
        return True

    def _load(self, key):
        return False
    
    def _setDirty(self, noFireChanges=False):
        pass

    def iterkeys(self, excludeIndexes=False, firstKey=None, lastKey=None):
        return super(NullViewRefList, self).iterkeys(firstKey, lastKey)

    def _unloadRef(self, item):

        key = item.itsUUID
        self._flags |= CLinkedMap.LOAD

        if self.has_key(key, False):
            self._get(key, False).value = key


class TransientWatch(object):
    
    def __init__(self, view, watchingItem):

        self.view = view
        self.watchingItem = watchingItem


class TransientWatchCollection(TransientWatch):

    def __init__(self, view, watchingItem, methodName):

        super(TransientWatchCollection, self).__init__(view, watchingItem)
        self.methodName = methodName
        
    def __call__(self, op, change, owner, name, other):

        getattr(self.view[self.watchingItem],
                self.methodName)(op, owner, name, other)

    def compare(self, methodName):

        return self.methodName == methodName


class TransientWatchKind(TransientWatch):

    def __init__(self, view, watchingItem, methodName):

        super(TransientWatchKind, self).__init__(view, watchingItem)
        self.methodName = methodName
        
    def __call__(self, op, change, owner, name, other):

        if isuuid(owner):
            kind = self.view[owner].kind
        else:
            kind = owner.kind

        getattr(self.view[self.watchingItem], self.methodName)(op, kind, other)

    def compare(self, methodName):

        return self.methodName == methodName


class TransientWatchItem(TransientWatch):

    def __init__(self, view, watchingItem, methodName):

        super(TransientWatchItem, self).__init__(view, watchingItem)
        self.methodName = methodName
        
    def __call__(self, op, uItem, names):

        getattr(self.view[self.watchingItem], self.methodName)(op, uItem, names)

    def compare(self, methodName):

        return self.methodName == methodName
