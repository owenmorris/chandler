
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import libxml2, threading, heapq, logging

from repository.util.UUID import UUID
from repository.util.Path import Path
from repository.persistence.RepositoryError import RepositoryError
from repository.item.Item import Item
from repository.item.ItemHandler import ItemHandler, ItemsHandler
from repository.item.ItemRef import ItemStub, DanglingRefError
from repository.persistence.PackHandler import PackHandler


class RepositoryView(object):
    """
    This class implements the cache for loaded items. Changes to items in a
    view are not written into persistent storage until the view is
    committed. A view will not see changes in the repository made by other
    views until the view is refreshed during a L{commit}.
    """
    
    def __init__(self, repository, name):
        """
        Initializes a repository view.

        This contructor should not be invoked directly but the
        L{createView<repository.persistence.Repository.Repository.createView>}
        method should be used instead so that the appropriate view
        implementation for the repository be used.
        """

        super(RepositoryView, self).__init__()

        if not repository.isOpen():
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
        """

        return self.repository.setCurrentView(self)

    def _isRepository(self):

        return False

    def _isItem(self):

        return False

    def _createRefDict(self, item, name, otherName, persist, readOnly):

        raise NotImplementedError, "%s._createRefDict" %(type(self))
    
    def _getLobType(self):

        raise NotImplementedError, "%s._getLobType" %(type(self))

    def openView(self):
        """
        Open this repository view.

        A view is created open, calling this method is only necessary when
        re-opening a closed view.
        """

        self._roots = {}
        self._registry = {}
        self._deletedRegistry = {}
        self._childrenRegistry = {}
        self._stubs = []
        self._status = RepositoryView.OPEN
        
        self.repository.store.attachView(self)

    def closeView(self):
        """
        Close this repository view.

        All items in the view are marked stale. The item cache is flushed.
        A closed view cannot be used until is re-opened with L{openView}.
        """

        if not self._status & RepositoryView.OPEN:
            raise RepositoryError, "RepositoryView is not open"

        if self.repository._threaded.view is self:
            del self.repository._threaded.view
        
        for item in self._registry.itervalues():
            item._setStale()

        self._registry.clear()
        self._roots.clear()
        self._deletedRegistry.clear()
        self._childrenRegistry.clear()
        del self._stubs[:]
        self._status &= ~RepositoryView.OPEN

        self.repository.store.detachView(self)

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

    def isStale(self):

        return False
        
    def isLoading(self):
        """
        Tell whether this view is in the process of loading items.

        @return: boolean
        """

        return (self._status & RepositoryView.LOADING) != 0

    def _setLoading(self, loading=True):

        if self.repository.view is not self:
            raise RepositoryError, "In thread %s the current view is %s, not %s" %(threading.currentThread(), self.repository.view, self)

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

        For example: L{find} calls this method when passed a path with the
        callable being the simple lambda body:

            - C{lambda parent, name, child, **kwds: child}

        A C{load} keyword can be used to prevent loading of items by setting
        it to C{False}. Items are loaded as needed by default.

        @param path: an item path
        @type path: a L{Path<repository.util.Path.Path>} instance
        @param callable: a function, method, or lambda body
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

        root = self.getRoot(path[_index], kwds.get('load', True))
        root = callable(self, path[_index], root, **kwds)
        if root is not None:
            if _index == l - 1:
                return root
            return root.walk(path, callable, _index + 1, **kwds)

        return None

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
                    L{UUID<repository.util.UUID.UUID>} 
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
                        return self._loadDoc(load)
                    else:
                        return None

        if isinstance(spec, Path):
            return self.walk(spec, lambda parent, name, child, **kwds: child,
                             load=load)

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

        return self.walk(path, lambda parent, name, child, **kwds: child,
                         load=load)

    def findUUID(self, uuid, load=True):
        """
        Find an item by UUID.

        See L{find} for more information.

        @param uuid: a UUID
        @type uuid: L{UUID<repository.util.UUID.UUID>} or a uuid string
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

        if isinstance(uuid, str) or isinstance(uuid, unicode):
            uuid = UUID(uuid)
        elif not isinstance(uuid, UUID):
            raise TypeError, '%s is not UUID or string' %(type(uuid))

        return self.find(uuid, load)

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

        @param uuid: a L{UUID<repository.util.UUID.UUID>} instance
        @param name: a string or C{None}
        @return: an L{ACL<repository.item.Access.ACL>} instance or C{None}
        """

        return self.repository.store.loadACL(self.version, uuid, name)

    def loadPack(self, path, parent=None):
        """
        Load items from the pack definition file at path.

        This is mostly a bootstrap feature.

        @param path: the path to the packfile to load
        @type path: a string
        @param parent: the item to load the items in the pack under
        @type parent: an item
        """

        packs = self.getRoot('Packs')
        if not packs:
            packs = Item('Packs', self, None)

        handler = PackHandler(path, parent, self)
        libxml2.SAXParseFile(handler, path, 0)
        if handler.errorOccurred():
            raise handler.saxError()

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
            for root in self.getRoots():
                self.dir(root, path)
        else:
            if path is None:
                path = item.itsPath
            else:
                path.append(item.itsName)
            print path
            for child in item:
                self.dir(child, path)
            path.pop()

    def _resolveStubs(self):

        i = 0
        for ref in self._stubs[:]:
            if isinstance(ref._other, ItemStub):
                try:
                    other = ref.getOther()
                except DanglingRefError:
                    if self.isDebug():
                        self.logger.debug("%s -> %s is missing",
                                          ref, ref._other)
                    i += 1
                    continue

            self._stubs.pop(i)
        
    def _loadItemsFile(self, path, parent=None, afterLoadHooks=None):

        self.logger.debug("Loading item file: %s", path)
            
        handler = ItemsHandler(self, parent or self, afterLoadHooks)
        libxml2.SAXParseFile(handler, path, 0)
        if handler.errorOccurred():
            raise handler.saxError()

        return handler.items

    def _loadItemString(self, string, parent=None, afterLoadHooks=None):

        if self.isDebug():
            index = string.find('uuid="')
            if index > -1:
                self.logger.debug('loading item %s', string[index+6:index+28])
            else:
                self.logger.debug('loading item %s', string)
            
        handler = ItemHandler(self, parent or self, afterLoadHooks)
        ctx = libxml2.createPushParser(handler, string, len(string), "item")
        ctx.parseChunk('', 0, 1)
        if handler.errorOccurred():
            raise handler.saxError()

        return handler.item

    def _loadItemDoc(self, doc, parser, parent=None, afterLoadHooks=None,
                     instance=None):

        if self.isDebug():
            string = self.repository.store.getDocContent(doc)
            index = string.find('uuid="')
            if index > -1:
                self.logger.debug('loading item %s', string[index+6:index+28])
            else:
                self.logger.debug('loading item %s', string)
            
        handler = ItemHandler(self, parent or self, afterLoadHooks, instance)
        parser.parseDoc(doc, handler)

        return handler.item

    def check(self):
        """
        Runs repository consistency checks on this view.

        All items of the repository are loaded into this view and checked
        for consistency with their schema definition. See
        L{Item.check<repository.item.Item.Item.check>} for more details.
        """

        result = True
        for root in self.getRoots():
            check = root.check(True)
            result = result and check

        return result

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

        return self.getRoot(name, load) is not None

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

        try:
            return self._roots[name]
        except KeyError:
            return self._loadRoot(name)

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
        Iterate over the roots of this repository in this view.
        """

        return self.iterChildren()
    
    def iterChildren(self, load=True):
        """
        Iterate over the roots of this repository in this view.
        """

        return self.getRoots(load).__iter__()

    def getRoots(self, load=True):
        """
        Get all roots in the repository from this view.

        A repository root is defined as an item whose parent is this view.

        @param load: if load is C{False}, only return the loaded roots.
        @type load: boolean
        """
        
        return self._roots.values()

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

    def _addItem(self, item, previous=None, next=None):

        name = item.itsName

        if name in self._roots:
            raise ValueError, "A root named '%s' exists already" %(name)

        self._roots[name] = item

        return item

    def _removeItem(self, item):

        del self._roots[item.itsName]

    def _unloadChild(self, name):

        del self._roots[name]

    def _registerItem(self, item):

        uuid = item.itsUUID

        old = self._registry.get(uuid)
        if old and old is not item:
            raise ValueError, 're-registering %s with different object' %(item)
        
        self._registry[uuid] = item

    def _registerChildren(self, uuid, children):

        self._childrenRegistry[uuid] = children

    def _unregisterItem(self, item):

        uuid = item.itsUUID
        del self._registry[uuid]
        if item.isDeleting():
            self._deletedRegistry[uuid] = uuid

    def commit(self):
        """
        Commit all the changes made to items in this view.

        Committing a view causes the following to happen, in this order:
        
            1. Version conflicts are detected. If an item in this view was
               changed in another view and it committed its changes first,
               there is a chance that these changes would conflict with the
               ones about to be committed by this view. A
               C{VersionConflictError} is raised in that situation.
            2. All changes made to items in this view are saved to
               persistent storage.
            3. Change and history notifications are dispatched after the
               persistent store transaction was successfully committed.
            4. This view is refreshed to the latest version in persistent
               store. Pointers to items that changed in other views that are
               also in this view are marked C{STALE} unless they're pinned
               in memory in which case they're refreshed in place.
            5. If the view's cache has reached a threshhold item count - at
               the moment 10,000 - the least-used items are removed from
               cache and pointers to them are marked C{STALE} such that the
               size of the cache drops below 90% of this threshhold.
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

    def queryItems(self, query, load=True):
        """
        Query this view for items using an XPath query.

        @param query: an xpath expression
        @type query: a string
        @param load: if C{False} only return loaded items
        @type load: boolean
        """
        
        raise NotImplementedError, "%s.queryItems" %(type(self))

    def searchItems(self, query, load=True):
        """
        Search this view for items using an Lucene full text query.

        @param query: an lucene query
        @type query: a string
        @param load: if C{False} only return loaded items
        @type load: boolean
        """

        raise NotImplementedError, "%s.searchItems" %(type(self))

    def _loadItem(self, uuid):
        raise NotImplementedError, "%s._loadItem" %(type(self))

    def _loadRoot(self, name):
        raise NotImplementedError, "%s._loadRoot" %(type(self))

    def _loadChild(self, parent, name):
        raise NotImplementedError, "%s._loadChild" %(type(self))

    def _newItems(self):
        raise NotImplementedError, "%s._newItems" %(type(self))

    def _addStub(self, stub):

        if not self.isLoading():
            self._stubs.append(stub)

    def __getUUID(self):

        return self.repository.itsUUID

    def __getName(self):

        return self.name

    def getLogger(self):

        return self.repository.logger

    def isDebug(self):

        return self.repository.logger.getEffectiveLevel() <= logging.DEBUG

    itsUUID = property(__getUUID)
    itsName = property(__getName)
    itsPath = property(_getPath)
    itsParent = None
    
    logger = property(getLogger)
    debug = property(isDebug)
    store = property(_getStore)

    OPEN = 0x1
    LOADING = 0x2
    

class OnDemandRepositoryView(RepositoryView):

    def __init__(self, repository, name):
        
        super(OnDemandRepositoryView, self).__init__(repository, name)

        self.version = repository.store.getVersion()
        self._hooks = None
        self._notRoots = {}
        
    def _loadDoc(self, doc, instance=None):

        try:
            loading = self.isLoading()
            if not loading:
                self._setLoading(True)
                self._hooks = []

            exception = None

            item = self._loadItemDoc(doc, self.repository.store,
                                     afterLoadHooks = self._hooks,
                                     instance=instance)

            if item is None:
                self.logger.error("Item didn't load properly, xml parsing didn't balance: %s", self.repository.store.getDocContent(doc))
                raise ValueError, "item didn't load, see log for more info"
                                  
            uuid = item._uuid
            if uuid in self._childrenRegistry:
                if '_children' in item.__dict__:
                    first = item._children._firstKey
                    last = item._children._lastKey
                else:
                    first = last = None
                children = self._childrenRegistry[uuid]
                del self._childrenRegistry[uuid]
                item._children = children
                children._firstKey = first
                children._lastKey = last
                children._setItem(item)

            if self.isDebug():
                self.logger.debug("loaded version %d of %s",
                                  item._version, item.itsPath)

        except:
            if not loading:
                self._setLoading(False)
                self._hooks = None
            raise
        
        else:
            if not loading:
                try:
                    if self._hooks:
                        for hook in self._hooks:
                            hook()
                finally:
                    self._hooks = None
                    self._setLoading(False)

        return item

    def _loadItem(self, uuid, instance=None):

        if not uuid in self._deletedRegistry:
            doc = self.repository.store.loadItem(self.version, uuid)

            if doc is not None:
                self.logger.debug("loading item %s", uuid)
                return self._loadDoc(doc, instance)

        return None

    def _loadRoot(self, name):

        return self._loadChild(None, name)

    def getRoots(self, load=True):
        'Return a list of the roots in the repository.'

        if load:
            for uuid in self.repository.store.readNames(self.version,
                                                        self.itsUUID):
                self.find(uuid)
            
        return super(OnDemandRepositoryView, self).getRoots(load)

    def _loadChild(self, parent, name):

        if parent is not None and parent is not self:
            uuid = parent.itsUUID
        else:
            uuid = self.itsUUID

        store = self.repository.store
        doc = store.loadChild(self.version, uuid, name)
                
        if doc is not None:
            uuid = store.getDocUUID(doc)

            if (not self._deletedRegistry or
                not uuid in self._deletedRegistry):
                if self.isDebug():
                    if parent is not None and parent is not self:
                        self.logger.debug("loading child %s of %s",
                                          name, parent.itsPath)
                    else:
                        self.logger.debug("loading root %s", name)
                    
                return self._loadDoc(doc)

        return None

    def _findKind(self, spec, withSchema):

        if withSchema:
            return self.find(spec, load=False)

        # when crossing the schema boundary, reset loading status so that
        # hooks get called before resuming regular loading

        hooks = None
        
        try:
            hooks = self._hooks
            loading = self._setLoading(False)
            
            return self.find(spec)
        finally:
            self._hooks = hooks
            self._setLoading(loading)

    def _addItem(self, item, previous=None, next=None):

        super(OnDemandRepositoryView, self)._addItem(item, previous, next)

        name = item.itsName
        if name in self._notRoots:
            del self._notRoots[name]

        item.setPinned(True)

        return item

    def _removeItem(self, item):

        super(OnDemandRepositoryView, self)._removeItem(item)

        name = item.itsName
        self._notRoots[name] = name

        item.setPinned(False)
        
    def getRoot(self, name, load=True):

        if not name in self._notRoots:
            return super(OnDemandRepositoryView, self).getRoot(name, load)

        return None

    def prune(self, size):

        registry = self._registry

        if len(registry) > size * 1.1:
            heap = [ (item._lastAccess, item._uuid)
                     for item in registry.itervalues()
                     if not item._status & item.PINNED ]
            heapq.heapify(heap)
            count = len(heap) - int(size * 0.9)
            self.logger.info('pruning %d items', count)
            for i in xrange(count):
                registry[heapq.heappop(heap)[1]]._unloadItem()
