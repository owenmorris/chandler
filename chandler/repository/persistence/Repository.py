
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path, xml.sax, threading

from model.util.UUID import UUID
from model.util.Path import Path
from model.util.ThreadLocal import ThreadLocal
from model.item.Item import Item
from model.item.ItemHandler import ItemHandler, ItemsHandler
from model.item.ItemRef import ItemStub, DanglingRefError
from model.persistence.PackHandler import PackHandler


class RepositoryError(ValueError):
    "All repository related exceptions go here"
    

class Repository(object):
    """An abstract item repository.

    The repository has direct access to its roots by name and to all its
    items by UUID. It can be used as an iterator over all its items."""

    def __init__(self, dbHome):

        super(Repository, self).__init__()

        self.dbHome = dbHome
        self._status = 0
        self._threaded = ThreadLocal()

    def create(self, verbose=False):

        self._init(verbose)
        
    def open(self, verbose=False, create=False):

        self._init(verbose)
        
    def _init(self, verbose):

        self._status = 0
        self.verbose = verbose
        
    def _isRepository(self):

        return True
    
    def close(self, purge=False):

        raise NotImplementedError, "Repository.close"

    def commit(self, purge=False):

        if not self.isOpen():
            raise RepositoryError, "Repository is not open"

        self.view.commit()

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

        return self.view._registry.itervalues()

    def isOpen(self):

        return (self._status & Repository.OPEN) != 0

    def hasRoot(self, name, load=True):

        return self.getRoot(name, load) is not None

    def getRoot(self, name, load=True):

        return self.getRoot(self, name, load)

    def getRoots(self):

        return self.view.getRoots()

    def walk(self, path, callable, _index=0, **kwds):

        return self.view.walk(path, callable, _index, **kwds)

    def find(self, spec, _index=0, load=True):

        return self.view.find(spec, _index, load)

    def loadPack(self, path, parent=None, verbose=False):

        self.view.loadPack(path, parent, verbose)

    def dir(self, item=None, path=None):

        self.view.dir(item, path)

    def check(self):

        self.view.check()

    ROOT_ID = UUID('3631147e-e58d-11d7-d3c2-000393db837c')
    OPEN = 0x1
    view = property(_getView)


class RepositoryView(object):

    def __init__(self, repository):

        super(RepositoryView, self).__init__()

        self.repository = repository

        self._thread = threading.currentThread()
        self._roots = {}
        self._registry = {}
        self._deletedRegistry = {}
        self._stubs = []
        self._status = 0

    def _isRepository(self):
        return False

    def createRefDict(self, item, name, otherName, persist):
        raise NotImplementedError, "RepositoryView.createRefDict"
    
    def getVersion(self, uuid):
        raise NotImplementedError, "RepositoryView.getVersion"

    def isLoading(self):

        return (self._status & RepositoryView.LOADING) != 0
        
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
                    if load:
                        return self._loadItem(spec)

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

    def loadPack(self, path, parent=None, verbose=False):
        'Load items from the pack definition file at path.'

        packs = self.getRoot('Packs')
        if not packs:
            packs = Item('Packs', self, None)

        xml.sax.parse(path, PackHandler(path, parent, self, verbose))

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

    def _resolveStubs(self, verbose=True):

        i = 0
        for ref in self._stubs[:]:
            if isinstance(ref._other, ItemStub):
                try:
                    other = ref.getOther()
                except DanglingRefError:
                    if verbose:
                        print "%s -> %s is missing" %(ref, ref._other)
                    i += 1
                    continue

            self._stubs.pop(i)
        
    def _loadItemsFile(self, path, parent=None, verbose=False,
                       afterLoadHooks=None):

        if verbose:
            print path
            
        handler = ItemsHandler(self, parent or self, afterLoadHooks)
        xml.sax.parse(path, handler)

        return handler.items

    def _loadItemString(self, string, parent=None, verbose=False,
                        afterLoadHooks=None):

        if verbose:
            print string[51:73]
            
        handler = ItemHandler(self, parent or self, afterLoadHooks)
        xml.sax.parseString(string, handler)

        return handler.item

    def _loadItemXML(self, xml, parser, parent=None, verbose=False,
                     afterLoadHooks=None):

        if verbose:
            print string[51:73]
            
        handler = ItemHandler(self, parent or self, afterLoadHooks)
        parser.parseXML(xml, handler)

        return handler.item

    def check(self):

        def apply(item):

            item.check()
            for child in item:
                apply(child)

        for root in self.getRoots():
            apply(root)

    def hasRoot(self, name, load=True):

        return self.getRoot(name, load) is not None

    def getRoot(self, name, load=True):
        'Return the root as named or None if not found.'

        try:
            return self._roots[name]
        except KeyError:
            return self._loadRoot(name)

    def getRoots(self):
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

    def __iter__(self):

        return self._registry.itervalues()

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

    def _registerItem(self, item):

        self._registry[item.getUUID()] = item

    def _unregisterItem(self, item):

        uuid = item.getUUID()
        del self._registry[uuid]
        if item.isDeleting():
            self._deletedRegistry[uuid] = uuid

    def _loadItem(self, uuid):
        raise NotImplementedError, "Repository._loadItem"

    def _loadRoot(self, name):
        raise NotImplementedError, "Repository._loadRoot"

    def _loadChild(self, parent, name):
        raise NotImplementedError, "Repository._loadChild"

    def _addStub(self, stub):

        if not self.isLoading():
            self._stubs.append(stub)

    def _getRootID(self):

        return Repository.ROOT_ID

    ROOT_ID = property(_getRootID)
    LOADING = 0x1
    

class Store(object):

    def open(self):
        raise NotImplementedError, "Store.open"

    def close(self):
        raise NotImplementedError, "Store.close"

    def loadItem(self, view, uuid):
        raise NotImplementedError, "Store.loadItem"
    
    def loadChild(self, view, parent, name):
        raise NotImplementedError, "Store.loadChild"

    def loadroots(self, view):
        raise NotImplementedError, "Store.loadRoots"

    def parseXML(self, xml, handler):
        raise NotImplementedError, "Store.parseXML"

    def getUUID(self, xml):
        raise NotImplementedError, "Store.getUUID"


class OnDemandRepository(Repository):

    def _createView(self):

        return OnDemandRepositoryView(self)


class OnDemandRepositoryView(RepositoryView):

    def __init__(self, repository):
        
        super(OnDemandRepositoryView, self).__init__(repository)
        self._hooks = None

    def _loadXML(self, xml):

        try:
            loading = self.isLoading()
            if not loading:
                self.setLoading(True)
                self._hooks = []

            exception = None

            item = self._loadItemXML(xml, self.repository._store,
                                     afterLoadHooks = self._hooks)
            if self.repository.verbose:
                print "loaded item %s" %(item.getItemPath())

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
            xml = self.repository._store.loadItem(self, uuid)

            if xml is not None:
                if self.repository.verbose:
                    print "loading item %s" %(uuid)
                return self._loadXML(xml)

        return None

    def _loadRoot(self, name):

        return self._loadChild(None, name)

    def _loadChild(self, parent, name):

        if parent is not None and parent is not self:
            uuid = parent.getUUID()
        else:
            uuid = self.ROOT_ID

        store = self.repository._store
        xml = store.loadChild(self, uuid, name)
                
        if xml is not None:
            uuid = store.getUUID(xml)
            if (not self._deletedRegistry or
                not store.getUUID(xml) in self._deletedRegistry):
                if self.repository.verbose:
                    if parent is not None and parent is not self:
                        print "loading child %s of %s" %(name,
                                                         parent.getItemPath())
                    else:
                        print "loading root %s" %(name)
                return self._loadXML(xml)

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
