
__revision__  = ""
__date__      = ""
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import os.path
import os
import sys

from model.util.UUID import UUID
from model.util.Path import Path
from Item import ItemHandler
from Container import Container


class Repository(object):
    '''A basic one-shot XML files based repository.

    This simple repository implementation saves all items in separate XML
    item files in a given directory. It can then load them back to restore
    the same exact item hierarchy.
    The repository has direct access to its roots by name and to all its
    items by UUID. It can be used as an iterator over all its items.'''

    def __init__(self, dir):
        'Construct a Repository giving it a directory pathname'
        
        super(Repository, self).__init__()

        self._dir = dir
        self._roots = {}
        self._registry = {}

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

    def find(self, spec):
        '''Find an item as specified or return None if not found.
        
        Spec can be a Path, a UUID or a string in which case it gets coerced
        into one of the former. If spec is a path, the search is done relative
        to the first name element in the path, a root in the repository.'''
        
        if isinstance(spec, Path):
            l = len(spec)

            if l == 0:
                return None

            if spec[0] == '//':
                index = 1
            else:
                index = 0

            if index >= l:
                return None

            root = self._roots.get(spec[index])
            if root is not None:
                return root.find(spec, index + 1)

            return None

        elif isinstance(spec, UUID):
            try:
                return self._registry[spec]
            except KeyError:
                return None

        elif isinstance(spec, str):
            if spec.find('/') >= 0:
                return self.find(Path(spec))
            elif len(spec) == 36 and spec[8] == '-' or len(spec) == 22:
                return self.find(UUID(spec))

        return None

    def load(self):
        'Load items from the directory the repository was initialized with.'
        
        class stub(object):

            def __init__(self, repository):
                super(stub, self).__init__()
                self.repository = repository

            def _addItem(self, item):
                return item
            
            def _removeItem(self, item):
                pass

            def _registerItem(self, item):
                self.repository._registerItem(item)

            def _unregisterItem(self, item):
                pass

            def find(self, spec):
                return self.repository.find(spec)

        cover = stub(self)

        if os.path.isdir(self._dir):
            contents = file(os.path.join(self._dir, 'contents.lst'), 'r')
            
            for uuid in contents.readlines():
                xml.sax.parse(os.path.join(self._dir, uuid[:-1] + '.item'),
                              ItemHandler(cover))

            for item in self:
                if hasattr(item, '_parentRef'):
                    parent = self.find(item._parentRef)
                    del item._parentRef
                else:
                    parent = self

                item.move(parent)

    def purge(self):
        'Purge the repository directory of all item files that do not correspond to currently existing items in the repository.'
        
        if os.path.exists(self._dir):
            for item in os.listdir(self._dir):
                if item.endswith('.item'):
                    uuid = UUID(item[:-5])
                    if not self._registry.has_key(uuid):
                        os.remove(os.path.join(self._dir, item))

    def dir(self, item=None, path=None):
        'Print out a listing of each item in the repository or under item.'
        
        if item is None:
            path = Path('//')
            for root in self._roots.itervalues():
                self.dir(root, path)
        else:
            path.append(item.getName())
            print path
            if isinstance(item, Container):
                for child in item:
                    self.dir(child, path)
            path.pop()
        
    def save(self, encoding='iso-8859-1'):
        '''Save all items into the directory the repository was created with.

        After save is complete a contents.lst file contains the UUIDs of all
        items that were saved to their own uuid.item file.'''

        if not os.path.exists(self._dir):
            os.mkdir(self._dir)
        elif not os.path.isdir(self._dir):
            raise ValueError, self._dir + " exists but is not a directory"

        for item in self:
            filename = str(item.getUUID()) + '.item'
            out = file(os.path.join(self._dir, filename), 'w')
            generator = xml.sax.saxutils.XMLGenerator(out, encoding)

            generator.startDocument()
            item.save(generator)
            generator.endDocument()

            out.write('\n')
            out.close()

        contents = file(os.path.join(self._dir, 'contents.lst'), 'w')

        for uuid in self._registry.iterkeys():
            contents.write(str(uuid))
            contents.write('\n')
            
        contents.close()
