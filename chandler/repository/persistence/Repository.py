
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
from model.persistence.PackHandler import PackHandler


class Repository(object):
    """An abstract item repository.

    The repository has direct access to its roots by name and to all its
    items by UUID. It can be used as an iterator over all its items."""

    def __init__(self):
        
        super(Repository, self).__init__()

        self._roots = {}
        self._registry = {}
        self._unresolvedRefs = []

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

        cover = Repository.stub(self)
        xml.sax.parse(path, PackHandler(path, parent, cover, verbose))

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
        
    def _appendRef(self, item, name, other, otherName, otherCard, itemRef):

        self._unresolvedRefs.append((item, name, other, otherName, otherCard,
                                     itemRef))

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

                ref[5]._attach(ref[0], ref[1], other, ref[3], ref[4])
                    
            self._unresolvedRefs.pop(i)


    def load(self, verbose=False):
        raise NotImplementedError, "Repository.load"

    def _loadRoot(self, dir, verbose=False):
        raise NotImplementedError, "Repository._loadRoot"

    def _loadItem(self, path, cover,
                  parent=None, verbose=False, afterLoadHooks=None):
        raise NotImplementedError, "Repository._loadItem"

    def purge(self):
        raise NotImplementedError, "Repository.purge"

    def save(self, encoding='iso-8859-1', purge=False, verbose=False):
        raise NotImplementedError, "Repository.save"

    def _saveRoot(self, root, encoding='iso-8859-1',
                  withSchema=False, verbose=False):
        raise NotImplementedError, "Repository._saveRoot"

    def saveItem(self, item, **args):
        raise NotImplementedError, "Repository.saveItem"


    class stub(object):

        def __init__(self, repository):
            super(Repository.stub, self).__init__()
            self.repository = repository
            self.registry = []

        def __iter__(self):
            return self.registry.__iter__()

        def _addItem(self, item):
            return item
            
        def _removeItem(self, item):
            pass

        def _registerItem(self, item):
            self.registry.append(item)
            self.repository._registerItem(item)

        def _unregisterItem(self, item):
            pass

        def _loadItem(self, path, parent):
            return self.repository._loadItem(path, self, parent)

        def _appendRef(self, item, name, other, otherName, otherCard, itemRef):
            self.repository._appendRef(item, name, other, otherName, otherCard,
                                       itemRef)

        def resolveRefs(self, verbose=False):
            self.repository.resolveRefs(verbose)

        def find(self, spec):
            return self.repository.find(spec)

        def loadPack(self, path, parent=None, verbose=False):
            return self.repository.loadPack(path, parent, verbose)
