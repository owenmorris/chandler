
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import logging, heapq, sys, gc, threading, os

from chandlerdb.util.uuid import UUID
from chandlerdb.item.item import CItem
from repository.util.Path import Path
from repository.util.ThreadSemaphore import ThreadSemaphore
from repository.util.Lob import Lob
from repository.persistence.RepositoryError import *
from repository.item.Children import Children
from repository.item.Indexes import NumericIndex
from repository.item.RefCollections import TransientRefList


class RepositoryView(object):
    """
    This class implements the cache for loaded items. Changes to items in a
    view are not written into persistent storage until the view is
    committed. A view will not see changes in the repository made by other
    views until the view is refreshed during a L{commit}.
    """
    
    # 0.5.0: first tracked core schema version
    # 0.5.1: added indexes to abstract sets
    # 0.5.2: renamed 'persist' aspect to 'persisted', added 'indexed' aspect
    # 0.5.3: new monitor implementation
    
    CORE_SCHEMA_VERSION = 0x00050300

    def __init__(self, repository, name, version):
        """
        Initializes a repository view.

        This contructor should not be invoked directly but the
        L{createView<repository.persistence.Repository.Repository.createView>}
        method should be used instead so that the appropriate view
        implementation for the repository be used.
        """

        super(RepositoryView, self).__init__()

        if repository is not None and not repository.isOpen():
            raise RepositoryError, "Repository is not open"

        self.repository = repository
        self.name = name or threading.currentThread().getName()

        self.openView()
        
    def __repr__(self):

        return "<%s: %s>" %(type(self).__name__, self.name)

    def setCurrentView(self):
        """
        Make this view the current view for the current thread.

        The repository gets the current view from the current thread. This
        method should be used to select this view as the current one for the
        current thread.

        @return: the view that was current for the thread before this call.
        """

        return self.repository.setCurrentView(self)

    def _isRepository(self):

        return False

    def _isView(self):

        return True

    def _isItem(self):

        return False

    def _isNullView(self):

        return False

    def _createRefList(self, item, name, otherName,
                       persisted, readOnly, new, uuid):

        raise NotImplementedError, "%s._createRefList" %(type(self))
    
    def _createChildren(self, parent, new):

        raise NotImplementedError, "%s._createChildren" %(type(self))
    
    def _getLobType(self):

        raise NotImplementedError, "%s._getLobType" %(type(self))

    def openView(self):
        """
        Open this repository view.

        A view is created open, calling this method is only necessary when
        re-opening a closed view.
        """

        self._roots = self._createChildren(self, False)
        self._registry = {}
        self._deletedRegistry = {}
        self._instanceRegistry = {}
        self._loadingRegistry = set()
        self._status = RepositoryView.OPEN

        repository = self.repository
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

    def __len__(self):

        return len(self._registry)

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
            if repository._threaded.view is self:
                del repository._threaded.view
            repository._openViews.remove(self)

        self.clear()

        if repository is not None:
            repository.store.detachView(self)

    def clear(self):

        for item in self._registry.itervalues():
            if hasattr(type(item), 'onViewClear'):
                item.onViewClear(self)
            item._setStale()

        self._registry.clear()
        self._roots.clear()
        self._deletedRegistry.clear()
        self._instanceRegistry.clear()

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

    def isOpen(self):
        """
        Tell whether this view is open.

        If the repository owning this view is closed, this view is also
        considered closed.

        @return: boolean
        """

        return ((self._status & RepositoryView.OPEN) != 0 and
                self.repository.isOpen())

    def isNew(self):

        return False

    def isStale(self):

        return False

    def isRefCounted(self):

        return (self._status & RepositoryView.REFCOUNTED) != 0
        
    def isLoading(self):
        """
        Tell whether this view is in the process of loading items.

        @return: boolean
        """

        return (self._status & RepositoryView.LOADING) != 0

    def _setLoading(self, loading, runHooks=False):

        status = (self._status & RepositoryView.LOADING != 0)

        if loading:
            self._status |= RepositoryView.LOADING
        else:
            self._status &= ~RepositoryView.LOADING

        return status

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

    def find(self, spec, load=True):
        """
        Find an item.

        An item can be found by a path determined by its name and container
        or by a uuid generated for it at creation time. If C{spec} is a
        relative path, it is evaluated relative to C{self}.

        This method returns C{None} if the item is not found or if it is
        found but not yet loaded and C{load} was set to C{False}.

        See the L{findPath} and L{findUUID} methods for versions of this
        method that can also be called with a string.

        @param spec: a path or UUID
        @type spec: L{Path<repository.util.Path.Path>} or
                    L{UUID<chandlerdb.util.uuid.UUID>} 
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """
        
        if isinstance(spec, UUID):
            if spec == self.itsUUID:
                return self
            else:
                try:
                    return self._registry[spec]
                except KeyError:
                    if load is True:
                        return self._loadItem(spec)
                    elif load and not spec in self._deletedRegistry:
                        # in this case, load is an itemReader (queryItems)
                        return self._readItem(load)
                    else:
                        return None

        if isinstance(spec, Path):
            return self._fwalk(spec, load)

        raise TypeError, '%s is not Path or UUID' %(type(spec))

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

        if isinstance(path, str) or isinstance(path, unicode):
            path = Path(path)
        elif not isinstance(path, Path):
            raise TypeError, '%s is not Path or string' %(type(path))

        return self._fwalk(path, load)

    def findUUID(self, uuid, load=True):
        """
        Find an item by UUID.

        See L{find} for more information.

        @param uuid: a UUID
        @type uuid: L{UUID<chandlerdb.util.uuid.UUID>} or a uuid string
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

        if isinstance(uuid, str) or isinstance(uuid, unicode):
            uuid = UUID(uuid)
        elif not isinstance(uuid, UUID):
            raise TypeError, '%s is not UUID or string' %(type(uuid))

        return self.find(uuid, load)

    def findMatch(self, view, matches=None):

        return view
    
    def _findKind(self, spec, withSchema):

        return self.find(spec)

    def getACL(self, uuid, name):
        """
        Get an Access Control List.

        ACLs are stored by C{(uuid, name)} tuples. C{name} can be C{None}.
        Therefore, each item in the repository may have an ACL, and each
        attribute value for each item in the repository may also have an
        ACL.

        By convention, the ACL for an item is stored with C{(item.itsUUID,
        None)} and the ACL for an attribute value on an item is stored with
        C{(item.itsUUID, attributeName)}.

        @param uuid: a L{UUID<chandlerdb.util.uuid.UUID>} instance
        @param name: a string or C{None}
        @return: an L{ACL<repository.item.Access.ACL>} instance or C{None}
        """

        return self.repository.store.loadACL(self._version, uuid, name)

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
        handler.parseFile(path)

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

    def check(self):
        """
        Runs repository consistency checks on this view.

        All items of the repository are loaded into this view and checked
        for consistency with their schema definition. See
        L{Item.check<repository.item.Item.Item.check>} for more details.
        """

        result = True
        for root in self.iterRoots():
            check = root.check(True)
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

    def __getitem__(self, key):

        if isinstance(key, UUID):
            if key == self.itsUUID:
                return self
            else:
                try:
                    return self._registry[key]
                except KeyError:
                    item = self._loadItem(key)
                    if item is not None:
                        return item
                    raise

        if isinstance(key, str) or isinstance(key, unicode):
            root = self.getRoot(key)
            if root is not None:
                return root
            raise KeyError, key

        raise TypeError, key

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

    def _unsavedItems(self):

        raise NotImplementedError, "%s._unsavedItems" %(type(self))

    def _addItem(self, item, previous=None, next=None):

        name = item.itsName

        if (name is not None and
            self._roots.resolveAlias(name, not self.isLoading()) is not None):
            raise ValueError, "A root named '%s' exists already" %(name)

        self._roots.__setitem__(item._uuid, item, alias=name)

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

        try:
            instance = self._instanceRegistry[uuid]
            del self._instanceRegistry[uuid]
        except KeyError:
            instance = None

        return instance

    def refresh(self, mergeFn=None, version=None):
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
               are dispatched after the merges succeeded.
            4. If the view's cache has reached a threshhold item count - at
               the moment 10,000 - the least-used items are removed from
               cache and pointers to them are marked C{STALE} such that the
               size of the cache drops below 90% of this threshhold.
        """
        
        raise NotImplementedError, "%s.refresh" %(type(self))

    def commit(self, mergeFn=None):
        """
        Commit all the changes made to items in this view.

        Committing a view causes the following to happen, in this order:
        
            1. L{refresh} is called.
            2. All changes made to items in the view are saved to
               persistent storage.
            3. Change and history notifications from the items committed
               are dispatched after the transactions commits.
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

    def queryItems(self, kind=None, attribute=None, load=True):
        """
        Query this view for items.

        @param kind: a kind item for a kind query
        @type kind: an item
        @param attribute: an attribute UUID for a value query
        @type attribute: a UUID
        @param load: if C{False} only return loaded items
        @type load: boolean
        """
        
        raise NotImplementedError, "%s.queryItems" %(type(self))

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

    def __getUUID(self):

        return self.repository.itsUUID

    def __getName(self):

        return self.name

    def getLogger(self):

        return self.repository.logger

    def isDebug(self):

        return self.repository.logger.getEffectiveLevel() <= logging.DEBUG

    def getRepositoryView(self):

        return self

    def mapChanges(self, callable, freshOnly=False):
        """
        Invoke a callable for every item changed in this view.

        For each item that was changed in this view since it last committed
        a callable is invoked with the following arguments:

            - the item

            - the item's current version

            - the item's current status bits

            - a list of changed literal attribute names

            - a list of changed references attribute names

        The return value of C{callable} is not used.

        @param callable: the function or method to be invoked.
        @type callable: a python callable
        @param freshOnly: optionally limit invocation of C{callable} to
        items that were changed since last time this method was called or
        since the last commit, whichever came last; C{False} by default.
        @type freshOnly: boolean
        """

        raise NotImplementedError, "%s.mapChanges" %(type(self))
    
    def mapHistory(self, callable, fromVersion=0, toVersion=0):
        """
        Invoke a callable for every committed item change in other views.

        For each item in this view that was changed and committed in another
        view a callable is invoked with the following arguments:

            - the item as it is in this view

            - the item's committed version for the change

            - the item's committed status bits for the change

            - a list of changed literal attribute names

            - a list of changed references attribute names

        @param fromVersion: the version to start iterating changes from, the
        current version by default.
        @type fromVersion: integer
        @param fromVersion: the version to continue iterating changes to, the
        latest committed version by default.
        @type fromVersion: integer
        """

        raise NotImplementedError, "%s.mapHistory" %(type(self))
        
    def _commitMerge(self):

        if self._status & CItem.CMERGED:
            self._roots._commitMerge()

    def _revertMerge(self):

        if self._status & CItem.CMERGED:
            self._roots._revertMerge()

        self._status &= ~CItem.MERGED

    def getItemVersion(self, version, item):

        return self.repository.store.getItemVersion(version, item._uuid)

    def addNotificationCallback(self, fn):

        self.repository.addNotificationCallback(fn)

    def removeNotificationCallback(self, fn):

        return self.repository.removeNotificationCallback(fn)

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

    itsUUID = property(__getUUID)
    itsName = property(__getName)
    itsPath = property(_getPath)
    itsView = property(lambda self: self)
    itsVersion = property(lambda self: self._version,
                          lambda self, value: self.refresh(version=value))
    itsParent = None
    
    logger = property(getLogger)
    debug = property(isDebug)
    store = property(_getStore)
    views = property(lambda self: self.repository.getOpenViews())

    OPEN       = 0x0001
    REFCOUNTED = 0x0002
    LOADING    = 0x0004
    COMMITTING = 0x0008
    FDIRTY     = 0x0010
    
    # flags from CItem
    # CDIRTY   = 0x0200
    # merge flags


class OnDemandRepositoryView(RepositoryView):

    def __init__(self, repository, name, version):

        if version is not None:
            self._version = version
        else:
            self._version = repository.store.getVersion()

        self._exclusive = ThreadSemaphore()
        self._hooks = []
        
        super(OnDemandRepositoryView, self).__init__(repository, name, version)

    def isNew(self):

        return self._version == 0

    def _setLoading(self, loading, runHooks=False):

        if not loading and self.isLoading() and runHooks:
            try:
                for hook in self._hooks:
                    hook(self)
            finally:
                self._hooks = []

        return super(OnDemandRepositoryView, self)._setLoading(loading,
                                                               runHooks)
    def _readItem(self, itemReader):

        try:
            release = False
            loading = self.isLoading()
            debug = self.isDebug()
            if not loading:
                release = self._exclusive.acquire()
                self._setLoading(True)
                self._hooks = []

            exception = None

            if debug:
                self.logger.debug('loading item %s', itemReader.getUUID())

            item = itemReader.readItem(self, self._hooks)
            if debug:
                self.logger.debug("loaded version %d of %s",
                                  item._version, item.itsPath)

        except:
            if not loading:
                self._setLoading(False, False)
                self._hooks = []
            if release:
                self._exclusive.release()
            raise
        
        else:
            if not loading:
                self._setLoading(False, True)
            if release:
                self._exclusive.release()

        return item

    def _loadItem(self, uuid):

        if uuid in self._loadingRegistry:
            raise RecursiveLoadItemError, uuid

        if not uuid in self._deletedRegistry:
            itemReader = self.repository.store.loadItem(self._version, uuid)

            if itemReader is not None:
                try:
                    self._loadingRegistry.add(uuid)
                    self.logger.debug("loading item %s", uuid)
                    return self._readItem(itemReader)
                finally:
                    self._loadingRegistry.remove(uuid)

        return None

    def _findSchema(self, spec, withSchema):

        if withSchema:
            return self.find(spec, load=False)

        # when crossing the schema boundary, reset loading status so that
        # hooks get called before resuming regular loading

        try:
            hooks = self._hooks
            loading = self._setLoading(False)
            
            return self.find(spec)
        finally:
            self._hooks = hooks
            self._setLoading(loading)

    def _addItem(self, item, previous=None, next=None):

        super(OnDemandRepositoryView, self)._addItem(item, previous, next)

        item.setPinned(True)

        return item

    def _removeItem(self, item):

        super(OnDemandRepositoryView, self)._removeItem(item)

        item.setPinned(False)
        
    def prune(self, size):

        registry = self._registry
        
        if len(registry) > size * 1.1:
            gc.collect()
            heap = [(item._lastAccess, item._uuid)
                    for item in registry.itervalues()
                    if not item._status & (item.PINNED | item.DIRTY)]

            heapq.heapify(heap)

            count = len(heap) - int(size * 0.9)
            if count > 0:
                self.logger.info('pruning %d items', count)

                if self.isRefCounted():
                    for i in xrange(count):
                        item = registry[heapq.heappop(heap)[1]]
                        itemRefs = item._refCount()
                        pythonRefs = sys.getrefcount(item)
                        if pythonRefs - itemRefs <= 3:
                            item._unloadItem(False, self)
                        else:
                            self.logger.warn('not pruning %s (refCount %d)',
                                             item._repr_(),
                                             pythonRefs - itemRefs)
                else:
                    for i in xrange(count):
                        registry[heapq.heappop(heap)[1]]._unloadItem(False, self)


class NullRepositoryView(RepositoryView):

    def __init__(self):

        self._logger = logging.getLogger('repository')
        if not (self._logger.root.handlers or self._logger.handlers):
            self._logger.addHandler(logging.StreamHandler())
        
        super(NullRepositoryView, self).__init__(None, "null view", 0)

    def setCurrentView(self):

        raise AssertionError, "Null view cannot be made current"

    def refresh(self, mergeFn=None):
        
        raise AssertionError, "Null view cannot refresh"

    def commit(self, mergeFn=None):
        
        raise AssertionError, "Null view cannot commit"

    def cancel(self):
        
        raise AssertionError, "Null view cannot cancel"

    def _createRefList(self, item, name, otherName,
                       persisted, readOnly, new, uuid):

        return NullViewRefList(item, name, otherName, persisted, readOnly)
    
    def _createChildren(self, parent, new):

        return Children(parent, new)

    def _createNumericIndex(self, **kwds):

        return NumericIndex(**kwds)
    
    def _getLobType(self):

        return NullViewLob

    def _findSchema(self, spec, withSchema):

        return self.find(spec, load=False)

    def _loadItem(self, uuid):

        return None

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

    def _isNullView(self):

        return True

    def _setLoading(self, loading, runHooks=False):

        raise AssertionError, "Null view cannot load items"

    def _getStore(self):

        return None

    def _logItem(self, item):

        return True

    def _unsavedItems(self):

        return self._registry.itervalues()

    def getLogger(self):

        return self._logger

    def isDebug(self):

        return self._logger.getEffectiveLevel() <= logging.DEBUG

    def __getUUID(self):

        return self.itsUUID

    def getRepositoryView(self):

        return self

    def getItemVersion(self, version, item):

        return item._version

    def queryItems(self, kind=None, attribute=None, load=True):

        if kind is not None:
            return [item for item in self._registry.itervalues()
                    if item._kind is kind]

        elif attribute is not None:
            raise NotImplementedError, 'attribute query'

        else:
            raise ValueError, 'one of kind or value must be set'


    logger = property(getLogger)
    itsUUID = UUID('17368718-a164-11d9-9351-000393db837c')


class NullViewLob(Lob):

    def __init__(self, view, *args, **kwds):

        super(NullViewLob, self).__init__(*args, **kwds)


class NullViewRefList(TransientRefList):

    def __init__(self, item, name, otherName, persisted, readOnly):

        super(NullViewRefList, self).__init__(item, name, otherName, readOnly)
        self._transient = not persisted

    def _isTransient(self):

        return self._transient
