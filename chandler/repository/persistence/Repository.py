
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path, xml.sax

from model.util.UUID import UUID
from model.util.Path import Path
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

    def create(self, verbose=False):

        self._init(verbose)
        
    def open(self, verbose=False, create=False):

        self._init(verbose)
        
    def _init(self, verbose):

        self._roots = {}
        self._registry = {}
        self._stubs = []
        self._status = 0
        self.verbose = verbose
        
    def close(self, purge=False):
        raise NotImplementedError, "Repository.close"

    def commit(self, purge=False):
        raise NotImplementedError, "Repository.commit"
    
    def createRefDict(self, item, name, otherName):
        raise NotImplementedError, "Repository.createRefDict"
    
    def addTransaction(self, item):
        raise NotImplementedError, "Repository.addTransaction"
    
    def isOpen(self):

        return (self._status & Repository.OPEN) != 0

    def isLoading(self):

        return (self._status & Repository.LOADING) != 0

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

        del self._registry[item.getUUID()]

    def _loadItem(self, uuid):
        raise NotImplementedError, "Repository._loadItem"

    def _loadRoot(self, name):
        raise NotImplementedError, "Repository._loadRoot"

    def _loadChild(self, parent, name):
        raise NotImplementedError, "Repository._loadChild"

    def _saveItem(self, item, **args):
        raise NotImplementedError, "Repository._saveItem"

    def _addStub(self, stub):

        self._stubs.append(stub)

    def getItemPath(self, path):
        'Return the path of the repository relative to its item, always //.'
        
        path.set('//')

        return path

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

    def _findKind(self, spec, withSchema):

        return self.find(spec)

    def find(self, spec, _index=0, load=True):
        '''Find an item as specified or return None if not found.
        
        Spec can be a Path, a UUID or a string in which case it gets coerced
        into one of the former. If spec is a path, the search is done relative
        to the first name element in the path, a root in the repository.'''
        
        if isinstance(spec, Path):
            l = len(spec)

            if l == 0:
                return None

            if spec[_index] == '//':
                _index += 1

            if _index >= l:
                return None

            root = self.getRoot(spec[_index], load)
            if root is not None:
                if _index == l - 1:
                    return root
                return root.find(spec, _index + 1, load)

            return None

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
                return self.find(Path(spec), 0, load)

        return None

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
            for root in self._roots.itervalues():
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
        
    def _loadItemFile(self, path, parent=None, verbose=False,
                      afterLoadHooks=None):

        if verbose:
            print path
            
        handler = ItemsHandler(self, parent or self, afterLoadHooks)
        xml.sax.parse(path, handler)

        return handler.item

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

    def purge(self):
        raise NotImplementedError, "Repository.purge"

    def check(self):

        for item in self:
            item.check()


    ROOT_ID = UUID('3631147e-e58d-11d7-d3c2-000393db837c')
    
    OPEN    = 0x1
    LOADING = 0x2


class Store(object):

    def open(self):
        raise NotImplementedError, "Store.open"

    def close(self):
        raise NotImplementedError, "Store.close"

    def loadItem(self, uuid):
        raise NotImplementedError, "Store.loadItem"
    
    def loadChild(self, parent, name):
        raise NotImplementedError, "Store.loadChild"

    def loadChildren(self, parent):
        raise NotImplementedError, "Store.loadChildren"

    def parseXML(self, xml, handler):
        raise NotImplementedError, "Store.parseXML"


class OnDemandRepository(Repository):

    def __init__(self, dbHome):
        
        super(OnDemandRepository, self).__init__(dbHome)
        self._hooks = None

    def _setLoading(self):

        loading = self._status & self.LOADING
        if not loading:
            self._status |= self.LOADING

        return loading

    def _resetLoading(self, loading):

        if not loading:
            self._status &= ~self.LOADING

            if self._hooks is not None:
                for hook in self._hooks:
                    hook()
                self._hooks = None

    def _loadItem(self, uuid):

        xml = self._store.loadItem(uuid)

        if xml is not None:
            if self.verbose:
                print "loading item %s" %(uuid)

            try:
                loading = self._setLoading()
                if not loading:
                    self._hooks = []

                item = self._loadItemXML(xml, self._store,
                                         afterLoadHooks = self._hooks)
                if self.verbose:
                    print "loaded item %s" %(item.getItemPath())

                return item
            finally:
                self._resetLoading(loading)

        return None

    def _loadRoot(self, name, verbose=False):

        return self._loadChild(None, name)

    def _loadChild(self, parent, name):

        if parent is not None and parent is not self:
            uuid = parent.getUUID()
        else:
            uuid = Repository.ROOT_ID

        xml = self._store.loadChild(uuid, name)

        if xml is not None:
            if self.verbose:
                if parent is not None and parent is not self:
                    print "loading child %s into %s" %(name,
                                                       parent.getItemPath())
                else:
                    print "loading root %s" %(name)

            try:
                loading = self._setLoading()
                if not loading:
                    self._hooks = []

                return self._loadItemXML(xml, self._store,
                                         afterLoadHooks = self._hooks)

            finally:
                self._resetLoading(loading)

        return None

    def _findKind(self, spec, withSchema):

        if withSchema:
            return self.find(spec, load=False)

        # when crossing the schema boundary, reset loading status so that
        # hooks get called before resuming regular loading
        
        try:
            hooks = self._hooks
            loading = self._status & self.LOADING
            self._status &= ~self.LOADING
            
            return self.find(spec)
        finally:
            self._hooks = hooks
            self._status |= loading
