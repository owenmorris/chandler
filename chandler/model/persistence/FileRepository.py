
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import os, os.path

from datetime import datetime

from model.util.UUID import UUID
from model.persistence.Repository import Repository, RepositoryError
from model.item.ItemRef import RefDict, TransientRefDict


class FileRepository(Repository):
    """A basic one-shot XML files based repository.

    This simple repository implementation saves all items in separate XML
    item files in a given directory. It can then load them back to restore
    the same exact item hierarchy."""

    def create(self, verbose=False):

        if not self.isOpen():
            super(FileRepository, self).create(verbose)
            self._status |= Repository.OPEN

    def open(self, verbose=False, create=False):

        if not self.isOpen():
            super(FileRepository, self).open(verbose)
            self._status |= self.OPEN
            self._load()

    def close(self):

        if self.isOpen():
            self._status &= ~self.OPEN

    def _load(self):
        'Load items from the directory the repository was initialized with.'

        loading = None
        
        try:
            loading = self.setLoading()
            if os.path.isdir(self.dbHome):
                contents = file(os.path.join(self.dbHome, 'contents.lst'), 'r')
            
                for dir in contents.readlines():
                    self._loadItems(dir[:-1])
        finally:
            if loading is not None:
                self.setLoading(loading)

    def _loadItems(self, dir):

        hooks = []

        contents = file(os.path.join(self.dbHome, dir, 'contents.lst'), 'r')
        for uuid in contents.readlines():
            self._loadItemFile(os.path.join(self.dbHome, dir,
                                            uuid[:-1] + '.item'),
                               verbose=self.verbose, afterLoadHooks=hooks)
        contents.close()

        for hook in hooks:
            hook()

    def _loadItem(self, uuid):
        return None

    def _loadRoot(self, name):
        return None

    def _loadChild(self, parent, name):
        return None

    def purge(self):
        'Purge the repository directory tree of all item files that do not correspond to currently existing items in the repository.'
        
        if os.path.exists(self.dbHome):
            def purge(arg, path, names):
                for item in names:
                    if item.endswith('.item'):
                        uuid = UUID(item[:-5])
                        if not self._registry.has_key(uuid):
                            os.remove(os.path.join(path, item))
            os.path.walk(self.dbHome, purge, None)

    def commit(self, purge=False):
        '''Save all items into the directory this repository was created with.

        After save is complete a contents.lst file contains the UUIDs of all
        items that were saved to their own uuid.item file.'''

        if not self.isOpen():
            raise DBError, "Repository is not open"

        if not os.path.exists(self.dbHome):
            os.mkdir(self.dbHome)
        elif not os.path.isdir(self.dbHome):
            raise ValueError, "%s exists but is not a directory" %(self.dbHome)

        before = datetime.now()
        count = 0

        contents = file(os.path.join(self.dbHome, 'contents.lst'), 'w')
        hasSchema = self._roots.has_key('Schema')

        if hasSchema:
            count += self._saveItems(self.getRoot('Schema'))
            contents.write('Schema')
            contents.write('\n')
        
        for root in self._roots.itervalues():
            name = root.getItemName()
            if name != 'Schema':
                count += self._saveItems(root)
                contents.write(name)
                contents.write('\n')
                
        contents.close()

        after = datetime.now()
        print 'committed %d items in %s' %(count, after - before)
        
        if purge:
            self.purge()

    def _saveItems(self, root, withSchema=False):

        def commit(item, repository, contents, **args):

            count = 0
            if item.isDirty():
                repository._saveItem(item, **args)
                count += 1
                item.setDirty(False)

            contents.write(item.getUUID().str16())
            contents.write('\n')
                
            for child in item:
                count += commit(child, repository, contents, **args)

            return count

        name = root.getItemName()
        dir = os.path.join(self.dbHome, name)

        if not os.path.exists(dir):
            os.mkdir(dir)
        elif not os.path.isdir(dir):
            raise ValueError, "%s exists but is not a directory" %(dir)

        rootContents = file(os.path.join(dir, 'contents.lst'), 'w')
        count = commit(root, self, rootContents, verbose = self.verbose)
        rootContents.close()

        return count

    def _saveItem(self, item, **args):

        if args.get('verbose'):
            print item.getItemPath()
            
        uuid = item.getUUID().str16()
        filename = os.path.join(self.dbHome, item.getRoot().getItemName(),
                                uuid + '.item')
        out = file(filename, 'w')
        generator = xml.sax.saxutils.XMLGenerator(out, 'utf-8')

        generator.startDocument()
        item._saveItem(generator)
        generator.endDocument()

        out.write('\n')
        out.close()

    def createRefDict(self, item, name, otherName, persist):

        if persist:
            return FileRefDict(item, name, otherName)
        else:
            return TransientRefDict(item, name, otherName)
    
    def addTransaction(self, item):

        if not self.isOpen():
            raise RepositoryError, 'Repository is not open'

        return not self.isLoading()
    

class FileRefDict(RefDict):
    pass
