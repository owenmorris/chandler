
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys, os, os.path, threading, logging
import libxml2

from repository.util.UUID import UUID
from repository.util.Path import Path
from repository.util.ThreadLocal import ThreadLocal
from repository.item.Item import Item
from repository.item.ItemHandler import ItemHandler, ItemsHandler
from repository.item.ItemRef import ItemStub, DanglingRefError
from repository.persistence.PackHandler import PackHandler

from PyLucene import attachCurrentThread


class RepositoryError(ValueError):
    "All repository related exceptions go here"

class VersionConflictError(RepositoryError):
    "Another thread changed %s and saved those changes before this thread got a chance to do so. These changes conflict with this thread's changes, the item cannot be saved."

    def __str__(self):
        return self.__doc__ %(self.args[0].getItemPath())

    def getItem(self):
        return self.args[0]


class Repository(object):
    """An abstract item repository.

    The repository has direct access to its roots by name and to all its
    items by UUID. It can be used as an iterator over all its items."""

    def __init__(self, dbHome):

        super(Repository, self).__init__()

        self.dbHome = dbHome
        self._status = 0
        self._threaded = ThreadLocal()
        self._notifications = []

    def create(self):

        self._init()
        
    def open(self, create=False):

        self._init()

    def serverOpen(self):

        raise NotImplementedError, "Repository.serverOpen"

    def delete(self):
        
        raise NotImplementedError, "Repository.delete"

    def _init(self):

        self._status = 0
        self.logger = logging.getLogger('repository')

        if '-debug' in sys.argv:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        if '-stderr' in sys.argv or not self.logger.root.handlers:
            if not self.logger.handlers:
                self.logger.addHandler(logging.StreamHandler())
            
    def _isRepository(self):

        return True

    def _isItem(self):

        return False
    
    def close(self, purge=False):
        pass

    def closeView(self, purge=False):
        self.view.close()

    def commit(self, purge=False):

        if not self.isOpen():
            raise RepositoryError, "Repository is not open"

        self.view.commit()

    def cancel(self):

        if not self.isOpen():
            raise RepositoryError, "Repository is not open"

        self.view.cancel()

    def _createView(self):

        return RepositoryView(self)

    def _getView(self):

        try:
            return self._threaded.view

        except AttributeError:
            view = self._createView()
            self._threaded.view = view

            return view

    def __iter__(self):

        return self.iterChildren()
    
    def iterChildren(self, load=True):

        return self.view.iterChildren(load)

    def isOpen(self):

        return (self._status & Repository.OPEN) != 0

    def hasRoot(self, name, load=True):

        return self.getRoot(name, load) is not None

    def getRoot(self, name, load=True):

        return self.view.getRoot(name, load)

    def __getitem__(self, key):

        return self.view.__getitem__(key)

    def getRoots(self, load=True):

        return self.view.getRoots(load)

    def walk(self, path, callable, _index=0, **kwds):

        return self.view.walk(path, callable, _index, **kwds)

    def find(self, spec, _index=0, load=True):

        return self.view.find(spec, _index, load)

    def queryItems(self, query, load=True):

        return self.view.queryItems(query, load)

    def searchItems(self, query, load=True):

        return self.view.searchItems(query, load)

    def loadPack(self, path, parent=None):

        self.view.loadPack(path, parent)

    def dir(self, item=None, path=None):

        self.view.dir(item, path)

    def check(self):

        return self.view.check()

    def getUUID(self):

        return Repository.ROOT_ID

    def addNotificationCallback(self, fn):

        self._notifications.append(fn)

    def removeNotificationCallback(self, fn):

        try:
            return self._notifications.pop(self._notifications.index(fn))
        except ValueError:
            return None

    ROOT_ID = UUID('3631147e-e58d-11d7-d3c2-000393db837c')
    OPEN = 0x1
    view = property(_getView)


class RepositoryView(object):

    def __init__(self, repository):

        super(RepositoryView, self).__init__()

        if not repository.isOpen():
            raise RepositoryError, "Repository is not open"

        self.repository = repository

        self._thread = threading.currentThread()
        self._roots = {}
        self._registry = {}
        self._deletedRegistry = {}
        self._childrenRegistry = {}
        self._stubs = []
        self._status = RepositoryView.OPEN
        
        repository.store.attachView(self)

    def __str__(self):

        return "<%s for %s>" %(type(self).__name__, self._thread.getName())

    def _isRepository(self):

        return False

    def _isItem(self):

        return False

    def createRefDict(self, item, name, otherName, persist):

        raise NotImplementedError, "RepositoryView.createRefDict"
    
    def getTextType(self):

        raise NotImplementedError, "RepositoryView.getTextType"

    def closeView(self):

        self.close()

    def close(self):

        if not self._status & RepositoryView.OPEN:
            raise RepositoryError, "RepositoryView is not open"

        del self.repository._threaded.view
        
        for item in self._registry.itervalues():
            item._setStale()

        self._registry.clear()
        self._roots.clear()
        self._deletedRegistry.clear()
        self._childrenRegistry.clear()

        self._status &= ~RepositoryView.OPEN

        self.repository.store.detachView(self)

    def isOpen(self):

        return ((self._status & RepositoryView.OPEN) != 0 and
                self.repository.isOpen())

    def isLoading(self):

        return (self._status & RepositoryView.LOADING) != 0

    def isStale(self):

        return False
        
    def setLoading(self, loading=True):

        if self._thread is not threading.currentThread():
            raise RepositoryError, 'current thread is not owning thread'

        status = (self._status & RepositoryView.LOADING != 0)

        if loading:
            self._status |= RepositoryView.LOADING
        else:
            self._status &= ~RepositoryView.LOADING

        return status

    def walk(self, path, callable, _index=0, **kwds):

        if _index == 0 and not isinstance(path, Path):
            path = Path(path)

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

    def find(self, spec, _index=0, load=True):
        '''Find an item as specified or return None if not found.
        
        Spec can be a Path, a UUID or a string in which case it gets coerced
        into one of the former. If spec is a path, the search is done relative
        to the first name element in the path, a root in the repository.'''
        
        if isinstance(spec, Path):
            return self.walk(spec, lambda parent, name, child, **kwds: child,
                             load=load)

        elif isinstance(spec, UUID):
            if spec == self.ROOT_ID:
                return self
            else:
                try:
                    return self._registry[spec]
                except KeyError:
                    if load is True:
                        return self._loadItem(spec)
                    elif load and not spec in self._deletedRegistry:
                        return self._loadDoc(load)

        elif isinstance(spec, str) or isinstance(spec, unicode):
            if (spec[0] != '/' and
                (len(spec) == 36 and spec[8] == '-' or len(spec) == 22)):
                return self.find(UUID(spec), 0, load)
            else:
                return self.walk(Path(spec),
                                 lambda parent, name, child, **kwds: child,
                                 0, load=load)

        return None

    def _findKind(self, spec, withSchema):

        return self.find(spec)

    def loadPack(self, path, parent=None):
        'Load items from the pack definition file at path.'

        packs = self.getRoot('Packs')
        if not packs:
            packs = Item('Packs', self, None)

        libxml2.SAXParseFile(PackHandler(path, parent, self), path, 0)

    def dir(self, item=None, path=None):
        'Print out a listing of each item in the repository or under item.'
        
        if item is None:
            path = Path('//')
            for root in self.getRoots():
                self.dir(root, path)
        else:
            path.append(item.getItemName())
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

        self.logger.debug(path)
            
        handler = ItemsHandler(self, parent or self, afterLoadHooks)
        libxml2.SAXParseFile(handler, path, 0)

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

        return handler.item

    def _loadItemDoc(self, doc, parser, parent=None, afterLoadHooks=None):

        if self.isDebug():
            string = self.repository.store.getDocContent(doc)
            index = string.find('uuid="')
            if index > -1:
                self.logger.debug('loading item %s', string[index+6:index+28])
            else:
                self.logger.debug('loading item %s', string)
            
        handler = ItemHandler(self, parent or self, afterLoadHooks)
        parser.parseDoc(doc, handler)

        return handler.item

    def check(self):

        result = True
        for root in self.getRoots():
            check = root.check(True)
            result = result and check

        return result

    def hasRoot(self, name, load=True):

        return self.getRoot(name, load) is not None

    def getRoot(self, name, load=True):
        'Return the root as named or None if not found.'

        try:
            return self._roots[name]
        except KeyError:
            return self._loadRoot(name)

    def __getitem__(self, key):

        if isinstance(key, UUID):
            if key == self.ROOT_ID:
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

        return self.iterChildren()
    
    def iterChildren(self, load=True):

        return self.getRoots(load).__iter__()

    def getRoots(self, load=True):
        'Return a list of the roots in the repository.'

        return self._roots.values()

    def getItemPath(self, path=None):
        'Return the path of the repository relative to its item, always //.'

        if path is None:
            path = Path()
        path.set('//')

        return path

    def logItem(self, item):

        if not self.repository.isOpen():
            raise RepositoryError, 'Repository is not open'

        if item.getRepository() is not self.repository.view:
            raise RepositoryError, 'current thread is not owning item'

        return not self.isLoading()

    def _addItem(self, item, previous=None, next=None):

        try:
            name = item.getItemName()
            current = self._roots[name]
        except KeyError:
            pass
        else:
            current.delete()

        self._roots[name] = item

        return item

    def _removeItem(self, item):

        del self._roots[item.getItemName()]

    def _unloadChild(self, name):

        del self._roots[name]

    def _registerItem(self, item):

        uuid = item.getUUID()

        old = self._registry.get(uuid)
        if old and old is not item:
            raise ValueError, 're-registering %s with different object' %(item)
        
        self._registry[uuid] = item

    def _registerChildren(self, uuid, children):

        self._childrenRegistry[uuid] = children

    def _unregisterItem(self, item):

        uuid = item.getUUID()
        del self._registry[uuid]
        if item.isDeleting():
            self._deletedRegistry[uuid] = uuid

    def commit(self):
        raise NotImplementedError, "RepositoryView.commit"

    def cancel(self):
        raise NotImplementedError, "RepositoryView.cancel"

    def queryItems(self, query, load=True):
        raise NotImplementedError, "RepositoryView.queryItems"

    def searchItems(self, query, load=True):
        raise NotImplementedError, "RepositoryView.searchItems"

    def _loadItem(self, uuid):
        raise NotImplementedError, "RepositoryView._loadItem"

    def _loadRoot(self, name):
        raise NotImplementedError, "RepositoryView._loadRoot"

    def _loadChild(self, parent, name):
        raise NotImplementedError, "RepositoryView._loadChild"

    def _addStub(self, stub):

        if not self.isLoading():
            self._stubs.append(stub)

    def getUUID(self):

        return Repository.ROOT_ID

    def getLogger(self):

        return self.repository.logger

    def isDebug(self):

        return self.repository.logger.getEffectiveLevel() <= logging.DEBUG

    ROOT_ID = property(getUUID)
    logger = property(getLogger)
    debug = property(isDebug)

    OPEN = 0x1
    LOADING = 0x2
    

class Store(object):

    def __init__(self, repository):

        super(Store, self).__init__()
        self.repository = repository

    def open(self, create=False):
        raise NotImplementedError, "Store.open"

    def close(self):
        raise NotImplementedError, "Store.close"

    def getVersion(self):
        raise NotImplementedError, "Store.getVersion"

    def loadItem(self, version, uuid):
        raise NotImplementedError, "Store.loadItem"
    
    def loadChild(self, version, uuid, name):
        raise NotImplementedError, "Store.loadChild"

    def loadRoots(self, version):
        raise NotImplementedError, "Store.loadRoots"

    def loadRef(self, version, uItem, uuid, key):
        raise NotImplementedError, "Store.loadRef"

    def queryItems(self, version, query):
        raise NotImplementedError, "Store.queryItems"
    
    def searchItems(self, version, query):
        raise NotImplementedError, "Store.searchItems"
    
    def parseDoc(self, doc, handler):
        raise NotImplementedError, "Store.parseDoc"

    def getDocUUID(self, doc):
        raise NotImplementedError, "Store.getDocUUID"

    def getDocVersion(self, doc):
        raise NotImplementedError, "Store.getDocVersion"

    def getDocContent(self, doc):
        raise NotImplementedError, "Store.getDocContent"

    def attachView(self, view):
        pass

    def detachView(self, view):
        pass


class OnDemandRepository(Repository):

    def _createView(self):

        return OnDemandRepositoryView(self)


class OnDemandRepositoryView(RepositoryView):

    def __init__(self, repository):
        
        super(OnDemandRepositoryView, self).__init__(repository)

        self._hooks = None
        self.version = repository.store.getVersion()

    def _loadDoc(self, doc):

        try:
            loading = self.isLoading()
            if not loading:
                self.setLoading(True)
                self._hooks = []

            exception = None

            item = self._loadItemDoc(doc, self.repository.store,
                                     afterLoadHooks = self._hooks)

            if item is None:
                self.logger.error("Item didn't load properly, xml parsing didn't balance: %s", self.repository.store.getDocContent(doc))
                raise ValueError, "item didn't load, see log for more info"
                                  
            uuid = item._uuid
            if uuid in self._childrenRegistry:
                children = self._childrenRegistry[uuid]
                del self._childrenRegistry[uuid]
                item._children = children
                children._setItem(item)

            if self.isDebug():
                self.logger.debug("loaded version %d of %s",
                                  item._version, item.getItemPath())

        except:
            if not loading:
                self.setLoading(False)
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
                    self.setLoading(False)

        return item

    def _loadItem(self, uuid):

        if not uuid in self._deletedRegistry:
            doc = self.repository.store.loadItem(self.version, uuid)

            if doc is not None:
                self.logger.debug("loading item %s", uuid)
                return self._loadDoc(doc)

        return None

    def _loadRoot(self, name):

        return self._loadChild(None, name)

    def _loadChild(self, parent, name):

        if parent is not None and parent is not self:
            uuid = parent.getUUID()
        else:
            uuid = self.ROOT_ID

        store = self.repository.store
        doc = store.loadChild(self.version, uuid, name)
                
        if doc is not None:
            uuid = store.getDocUUID(doc)

            if (not self._deletedRegistry or
                not uuid in self._deletedRegistry):
                if self.isDebug():
                    if parent is not None and parent is not self:
                        self.logger.debug("loading child %s of %s",
                                          name, parent.getItemPath())
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
            loading = self.setLoading(False)
            
            return self.find(spec)
        finally:
            self._hooks = hooks
            self.setLoading(loading)


class RepositoryNotifications(dict):

    def __init__(self, repository):

        super(RepositoryNotifications, self).__init__()
        self.repository = repository

    def changed(self, uuid, reason, **kwds):

        value = self.get(uuid, Item.Nil)

        if value is not Item.Nil:
            value.append((reason, kwds))
        else:
            self[uuid] = [ (reason, kwds) ]

    def dispatchChanges(self):

        callbacks = self.repository._notifications
        if callbacks:
            for uuid, reasons in self.iteritems():
                (reason, kwds) = reasons.pop()
                for callback in callbacks:
                    callback(uuid, 'ItemChanged', reason, **kwds)
                for (reason, kwds) in reasons:
                    for callback in callbacks:
                        callback(uuid, 'CollectionChanged', reason, **kwds)

        self.clear()

    def history(self, uuid, reason, **kwds):

        self[uuid] = (reason, kwds)
    
    def dispatchHistory(self):

        callbacks = self.repository._notifications
        if callbacks:
            for uuid, (reason, kwds) in self.iteritems():
                for callback in callbacks:
                    callback(uuid, 'History', reason, **kwds)

        self.clear()


class RepositoryThread(threading.Thread):

    def __init__(self, repository, *args, **kwds):

        self.repository = repository
        super(RepositoryThread, self).__init__(*args, **kwds)

    def run(self):

        try:
            result = attachCurrentThread(super(RepositoryThread, self))
        finally:
            self.repository.closeView()

        return result
