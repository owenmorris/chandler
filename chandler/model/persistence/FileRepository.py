
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import os.path
import os

from model.util.UUID import UUID
from model.persistence.Repository import Repository
from model.item.ItemRef import RefDict


class FileRepository(Repository):
    """A basic one-shot XML files based repository.

    This simple repository implementation saves all items in separate XML
    item files in a given directory. It can then load them back to restore
    the same exact item hierarchy."""

    def __init__(self, dir):
        'Construct a FileRepository giving it a directory pathname'
        
        super(FileRepository, self).__init__()
        self._dir = dir
        self._isOpen = False

    def create(self):

        if not self._isOpen:
            super(FileRepository, self).create()
            self._isOpen = True

    def open(self, verbose=False):

        if not self._isOpen:
            super(FileRepository, self).open()
            self._load(verbose=verbose)
            self._isOpen = True

    def close(self):

        if self._isOpen:
            self._isOpen = False

    def isOpen(self):

        return self._isOpen

    def _load(self, verbose=False):
        'Load items from the directory the repository was initialized with.'
        
        if os.path.isdir(self._dir):
            contents = file(os.path.join(self._dir, 'contents.lst'), 'r')
            
            for dir in contents.readlines():
                self._loadRoot(dir[:-1], verbose=verbose)

    def _loadRoot(self, dir, verbose=False):

        hooks = []

        contents = file(os.path.join(self._dir, dir, 'contents.lst'), 'r')
        for uuid in contents.readlines():
            self._loadItemFile(os.path.join(self._dir, dir,
                                            uuid[:-1] + '.item'),
                               verbose=verbose, afterLoadHooks=hooks,
                               loading=True)
        contents.close()

        self.resolveOrphans()
        for hook in hooks:
            hook()

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

    def save(self, purge=False, verbose=False):
        '''Save all items into the directory this repository was created with.

        After save is complete a contents.lst file contains the UUIDs of all
        items that were saved to their own uuid.item file.'''

        if not os.path.exists(self._dir):
            os.mkdir(self._dir)
        elif not os.path.isdir(self._dir):
            raise ValueError, "%s exists but is not a directory" %(self._dir)

        contents = file(os.path.join(self._dir, 'contents.lst'), 'w')
        hasSchema = self._roots.has_key('Schema')

        if hasSchema:
            self._saveRoot(self.getRoot('Schema'), True, verbose)
            contents.write('Schema')
            contents.write('\n')
        
        for root in self._roots.itervalues():
            name = root.getName()
            if name != 'Schema':
                self._saveRoot(root, not hasSchema, verbose)
                contents.write(name)
                contents.write('\n')
                
        contents.close()

        if purge:
            self.purge()

    def _saveRoot(self, root, withSchema=False, verbose=False):

        def save(item, repository, **args):

            repository.saveItem(item, **args)
            for child in item:
                save(child, repository, **args)

        name = root.getName()
        dir = os.path.join(self._dir, name)

        if not os.path.exists(dir):
            os.mkdir(dir)
        elif not os.path.isdir(dir):
            raise ValueError, "%s exists but is not a directory" %(dir)

        rootContents = file(os.path.join(dir, 'contents.lst'), 'w')
        save(root, self, contents = rootContents, withSchema = withSchema,
             verbose = verbose)
        rootContents.close()

    def saveItem(self, item, **args):

        if args.get('verbose'):
            print item.getPath()
            
        uuid = str(item.getUUID())
        filename = os.path.join(self._dir, item.getRoot().getName(),
                                uuid + '.item')
        out = file(filename, 'w')
        generator = xml.sax.saxutils.XMLGenerator(out, 'utf-8')

        generator.startDocument()
        item.toXML(generator, args.get('withSchema', False))
        generator.endDocument()

        args['contents'].write(uuid)
        args['contents'].write('\n')

        out.write('\n')
        out.close()

    def createRefDict(self, item, name, otherName, ordered=False):

        return FileRefDict(item, name, otherName, ordered)
    
    def addTransaction(self, item):
        pass
    

class FileRefDict(RefDict):

    def _xmlValues(self, generator):

        for ref in self._iteritems():
            ref[1]._xmlValue(ref[0], self._item, generator)
