
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import os.path
import os

from model.util.UUID import UUID
from model.util.Path import Path
from model.item.Item import Item
from model.item.Item import ItemHandler
from model.persistence.PackHandler import PackHandler


class Repository(object):
    """An abstract item repository.

    The repository has direct access to its roots by name and to all its
    items by UUID. It can be used as an iterator over all its items."""

    def create(self):

        self._init()
        
    def open(self, verbose=False):

        self._init()
        
    def _init(self):

        self._roots = {}
        self._registry = {}
        self._unresolvedRefs = []
        self._orphans = []
        
    def close(self, purge=False, verbose=False):
        raise NotImplementedError, "Repository.close"

    def isOpen(self):
        raise NotImplementedError, "Repository.isOpen"

    def save(self, purge=False, verbose=False):
        raise NotImplementedError, "Repository.save"
    
    def createRefDict(self, item, name, otherName, ordered=False):
        raise NotImplementedError, "Repository.createRefDict"
    
    def addTransaction(self, item):
        raise NotImplementedError, "Repository.addTransaction"
    
    def __iter__(self):

        return self._registry.itervalues()

    def _addItem(self, item):

        try:
            name = item.getName()
            current = self._roots[name]
        except KeyError:
            pass
        else:
            current.delete()

        self._roots[name] = item

        return item

    def _removeItem(self, item):

        del self._roots[item.getName()]

    def _registerItem(self, item):

        self._registry[item.getUUID()] = item

    def _unregisterItem(self, item):

        del self._registry[item.getUUID()]

    def _addOrphan(self, parentRef, item):

        self._registerItem(item)
        self._orphans.append((parentRef, item))

    def getPath(self, path):
        'Return the path of the repository relative to its item, always //.'
        
        path.set('//')

        return path

    def getRoot(self, name):
        'Return the root as named or None if not found.'
        
        return self._roots.get(name)

    def find(self, spec, _index=0):
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

            root = self._roots.get(spec[_index])
            if root is not None:
                if _index == l - 1:
                    return root
                return root.find(spec, _index + 1)

            return None

        elif isinstance(spec, UUID):
            try:
                return self._registry[spec]
            except KeyError:
                return None

        elif isinstance(spec, str) or isinstance(spec, unicode):
            if (spec[0] != '/' and
                (len(spec) == 36 and spec[8] == '-' or len(spec) == 22)):
                return self.find(UUID(spec))
            else:
                return self.find(Path(spec))

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
            path.append(item.getName())
            print path
            for child in item:
                self.dir(child, path)
            path.pop()
        
    def _appendRef(self, item, name, other, otherName, otherCard, itemRef,
                   refDict):

        self._unresolvedRefs.append((item, name, other, otherName, otherCard,
                                     itemRef, refDict))

    def resolveRefs(self, verbose=True):

        i = 0
        for ref in self._unresolvedRefs[:]:
            if ref[5]._other is None:
                other = ref[0].find(ref[2])
                if other is None:
                    if verbose:
                        print "%s -> %s is missing" %(ref[0], ref[2])
                    i += 1
                    continue

                ref[5].attach(ref[6], ref[0], ref[1], other, ref[3], ref[4])
                    
            self._unresolvedRefs.pop(i)

    def resolveOrphans(self):

        orphans = []
        for orphan in self._orphans:
            parent = self.find(orphan[0])
            if parent is None:
                print 'Warning: parent not found:', orphan[0]
                orphans.append(orphan)
            else:
                orphan[1].move(parent, loading=True)

        self._orphans = orphans

    def _loadItemFile(self, path, parent=None, verbose=False,
                      afterLoadHooks=None, loading=False):

        if verbose:
            print path
            
        handler = ItemHandler(self, parent or self, afterLoadHooks, loading)
        xml.sax.parse(path, handler)

        return handler.item

    def _loadItemString(self, string, parent=None, verbose=False,
                        afterLoadHooks=None, loading=False):

        if verbose:
            print string[51:73]
            
        handler = ItemHandler(self, parent or self, afterLoadHooks, loading)
        xml.sax.parseString(string, handler)

        return handler.item

    def purge(self):
        raise NotImplementedError, "Repository.purge"

    def saveItem(self, item, **args):
        raise NotImplementedError, "Repository.saveItem"
