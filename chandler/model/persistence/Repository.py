
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import os.path
import os
import sys
import re

from model.util.UUID import UUID
from model.util.Path import Path
from model.item.Item import Item
from model.item.Item import ItemHandler


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
            if len(spec) == 36 and spec[8] == '-' or len(spec) == 22:
                return self.find(UUID(spec))
            else:
                return self.find(Path(spec))

        return None

    def load(self):
        'Load items from the directory the repository was initialized with.'
        
        if os.path.isdir(self._dir):
            contents = file(os.path.join(self._dir, 'contents.lst'), 'r')
            
            for dir in contents.readlines():
                self._loadRoot(dir[:-1])

    def _loadRoot(self, dir):

        cover = Repository.stub(self)

        contents = file(os.path.join(self._dir, dir, 'contents.lst'), 'r')
        for uuid in contents.readlines():
            self._loadItem(os.path.join(self._dir, dir, uuid[:-1] + '.item'),
                           cover)
        contents.close()
        
        for item in cover:
            if hasattr(item, '_parentRef'):
                item.move(self.find(item._parentRef))
                del item._parentRef

        cover._resolveKinds()
        
    def _loadItem(self, path, cover, parent=None):

        handler = ItemHandler(cover, parent or self)
        xml.sax.parse(path, handler)

        return handler.item

    def loadPack(self, path, parent=None, verbose=False):
        'Load items from the pack definition file at path.'

        cover = Repository.stub(self)
        xml.sax.parse(path, PackHandler(path, parent, cover, verbose))

    def purge(self):
        'Purge the repository directory tree of all item files that do not correspond to currently existing items in the repository.'
        
        if os.path.exists(self._dir):
            def purge(arg, path, names):
                for item in names:
                    if item.endswith('.item'):
                        uuid = UUID(item[:-5])
                        if not self._registry.has_key(uuid):
                            os.remove(os.path.join(path, item))
            os.path.walk(self._dir, purge, None)

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
        
    def save(self, encoding='iso-8859-1', purge=False, verbose=False):
        '''Save all items into the directory the repository was created with.

        After save is complete a contents.lst file contains the UUIDs of all
        items that were saved to their own uuid.item file.'''

        if not os.path.exists(self._dir):
            os.mkdir(self._dir)
        elif not os.path.isdir(self._dir):
            raise ValueError, self._dir + " exists but is not a directory"

        contents = file(os.path.join(self._dir, 'contents.lst'), 'w')
        hasSchema = self._roots.has_key('Schema')

        if hasSchema:
            self._saveRoot(self.getRoot('Schema'), encoding, True, verbose)
            contents.write('Schema')
            contents.write('\n')
        
        for root in self._roots.itervalues():
            name = root.getName()
            if name != 'Schema':
                self._saveRoot(root, encoding, not hasSchema, verbose)
                contents.write(name)
                contents.write('\n')
                
        contents.close()

        if purge:
            self.purge()

    def _saveRoot(self, root, encoding='iso-8859-1',
                  withSchema=False, verbose=False):

        name = root.getName()
        dir = os.path.join(self._dir, name)

        if not os.path.exists(dir):
            os.mkdir(dir)
        elif not os.path.isdir(dir):
            raise ValueError, dir + " exists but is not a directory"

        rootContents = file(os.path.join(dir, 'contents.lst'), 'w')
        root.save(self, contents=rootContents,
                  encoding = encoding, withSchema = withSchema,
                  verbose = verbose)
        rootContents.close()

    def saveItem(self, item, **args):

        if args.get('verbose'):
            print item.getPath()
            
        uuid = str(item.getUUID())
        filename = os.path.join(self._dir, item.getRoot().getName(),
                                uuid + '.item')
        out = file(filename, 'w')
        generator = xml.sax.saxutils.XMLGenerator(out, args.get('encoding',
                                                                'iso-8859-1'))

        generator.startDocument()
        item.toXML(generator, args.get('withSchema', False))
        generator.endDocument()

        args['contents'].write(uuid)
        args['contents'].write('\n')

        out.write('\n')
        out.close()


    class stub(object):

        def __init__(self, repository):
            super(Repository.stub, self).__init__()
            self.repository = repository
            self.registry = []
            self.kindRefs = []
            self.itemRefs = []

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

        def _resolveKinds(self):

            for item in self.kindRefs:
                ref = item._kindRef
                del item._kindRef
                item._kind = item.find(ref)

        def _resolveRefs(self, verbose=True):

            i = 0
            for ref in self.itemRefs[:]:
                if ref[3]._other is None:
                    other = ref[0].find(ref[1])
                    if other is None:
                        if verbose:
                            print ref, ref[1], "is missing"
                            i += 1
                            continue

                    ref[3]._attach(ref[0], other, ref[2])
                    
                self.itemRefs.pop(i)

        def find(self, spec):
            return self.repository.find(spec)

        def loadPack(self, path, parent=None, verbose=False):
            return self.repository.loadPack(path, parent, verbose)


class PackHandler(xml.sax.ContentHandler):
    'A SAX ContentHandler implementation responsible for loading packs.'

    def __init__(self, path, parent, cover, verbose):

        self.path = path
        self.cwd = [ os.path.dirname(path) ]
        self.parent = [ parent ]
        self.cover = cover
        self.verbose = verbose

    def startDocument(self):

        self.tagMethods = []
        self.tagAttrs = []

    def endDocument(self):

        self.cover._resolveKinds()
        self.cover._resolveRefs(True)
        
    def startElement(self, tag, attrs):

        self.data = ''
        method = getattr(PackHandler, tag + 'Start', None)
        if method is not None:
            method(self, attrs)
            
        self.tagMethods.append(getattr(PackHandler, tag + 'End', None))
        self.tagAttrs.append(attrs)

    def characters(self, data):

        self.data += data

    def endElement(self, tag):

        method = self.tagMethods.pop()
        attrs = self.tagAttrs.pop()

        if method is not None:
            method(self, attrs)

    def packStart(self, attrs):

        if attrs.has_key('cwd'):
            self.cwd[-1] = os.path.join(self.cwd[-1], attrs['cwd'])

        if attrs.has_key('file'):
            if not self.cover.find(Path('//', 'Packs', attrs['name'])):
                self.cover.loadPack(os.path.join(self.cwd[-1], attrs['file']),
                                    self.parent[-1],
                                    self.verbose)

        else:
            self.name = attrs['name']

            packs = self.cover.find('Packs')
            if not packs:
                packs = Item('Packs', self.cover.repository, None)

            Item(self.name, packs, None).setAttribute('File', self.path)

    def cwdStart(self, attrs):

        self.cwd.append(os.path.join(self.cwd[-1], attrs['path']))

    def cwdEnd(self, attrs):

        self.cwd.pop()

    def itemStart(self, attrs):

        parent = None
        
        if attrs.has_key('path'):
            parent = self.cover.find(Path(attrs['path']))
        elif attrs.has_key('uuid'):
            parent = self.cover.find(UUID(attrs['uuid']))
        elif attrs.has_key('file'):
            parent = self.loadItem(os.path.join(self.cwd[-1], attrs['file']),
                                   self.parent[-1])
        elif attrs.has_key('files'):
            pattern = '^' + attrs['files'] + '$'
            pattern = pattern.replace('.', '\\.').replace('*', '.*')
            exp = re.compile(pattern)

            for file in os.listdir(self.cwd[-1]):
                if exp.match(file):
                    parent = self.loadItem(os.path.join(self.cwd[-1], file),
                                           self.parent[-1])
            
        self.parent.append(parent)

        if attrs.has_key('cwd'):
            self.cwd.append(os.path.join(self.cwd[-1], attrs['cwd']))

    def itemEnd(self, attrs):

        self.parent.pop()

        if attrs.has_key('cwd'):
            self.cwd.pop()

        if len(self.parent) == 1:
            self.cover._resolveRefs()

    def loadItem(self, file, parent):

        if self.verbose:
            print file
            
        return self.cover._loadItem(file, parent)
