
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path

from datetime import datetime

from repository.util.UUID import UUID
from repository.util.SAX import XMLGenerator
from repository.persistence.Repository import Repository, RepositoryError
from repository.persistence.Repository import RepositoryView
from repository.item.ItemRef import RefDict, TransientRefDict


class FileRepository(Repository):
    """A basic one-shot XML files based repository.

    This simple repository implementation saves all items in separate XML
    item files in a given directory. It can then load them back to restore
    the same exact item hierarchy."""

    def create(self):

        if not self.isOpen():
            super(FileRepository, self).create()
            self._status |= Repository.OPEN

    def open(self, create=False):

        if not self.isOpen():
            super(FileRepository, self).open()
            self._status |= self.OPEN
            self.view._load()

    def close(self):

        if self.isOpen():
            self._status &= ~self.OPEN

    def commit(self, purge=False):

        super(FileRepository, self).commit(purge)
        if purge:
            self.view.purge()

    def _createView(self):

        return FileRepositoryView(self)


class FileRepositoryView(RepositoryView):

    def createRefDict(self, item, name, otherName, persist):

        if persist:
            return FileRefDict(item, name, otherName)
        else:
            return TransientRefDict(item, name, otherName)
    
    def _load(self):
        'Load items from the directory the repository was initialized with.'

        loading = None
        dbHome = self.repository.dbHome
        
        try:
            loading = self.setLoading()
            if os.path.isdir(dbHome):
                contents = file(os.path.join(dbHome, 'contents.lst'), 'r')
            
                for dir in contents.readlines():
                    self._loadItems(dir[:-1])
        finally:
            if loading is not None:
                self.setLoading(loading)

    def _loadItems(self, dir):

        hooks = []
        dbHome = self.repository.dbHome
        
        contents = file(os.path.join(dbHome, dir, 'contents.lst'), 'r')
        for uuid in contents.readlines():
            self._loadItemsFile(os.path.join(dbHome, dir,
                                             uuid[:-1] + '.item'),
                                afterLoadHooks=hooks)
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
        
        dbHome = self.repository.dbHome

        if os.path.exists(dbHome):
            def purge(arg, path, names):
                for item in names:
                    if item.endswith('.item'):
                        uuid = UUID(item[:-5])
                        if not self._registry.has_key(uuid):
                            os.remove(os.path.join(path, item))
            os.path.walk(dbHome, purge, None)

    def commit(self):
        """Save all items into the directory this repository was created with.

        After save is complete a contents.lst file contains the UUIDs of all
        items that were saved to their own uuid.item file."""

        dbHome = self.repository.dbHome

        if not os.path.exists(dbHome):
            os.mkdir(dbHome)
        elif not os.path.isdir(dbHome):
            raise ValueError, "%s exists but is not a directory" %(dbHome)

        before = datetime.now()
        count = 0

        contents = file(os.path.join(dbHome, 'contents.lst'), 'w')
        hasSchema = self._roots.has_key('Schema')

        if hasSchema:
            count += self._saveItems(self.getRoot('Schema'))
            contents.write('Schema')
            contents.write('\n')
        
        for root in self._roots.itervalues():
            name = root.itsName
            if name != 'Schema':
                count += self._saveItems(root)
                contents.write(name)
                contents.write('\n')
                
        contents.close()

        after = datetime.now()
        self.logger.info('committed %d items in %s', count, after - before)
        
    def _saveItems(self, root, withSchema=False):

        def commit(item, view, contents, **args):

            count = 0
            if item.isDirty():
                view._saveItem(item, **args)
                count += 1
                item.setDirty(0)

            contents.write(item.itsUUID.str16())
            contents.write('\n')
                
            for child in item:
                count += commit(child, view, contents, **args)

            return count

        name = root.itsName
        dir = os.path.join(self.repository.dbHome, name)

        if not os.path.exists(dir):
            os.mkdir(dir)
        elif not os.path.isdir(dir):
            raise ValueError, "%s exists but is not a directory" %(dir)

        rootContents = file(os.path.join(dir, 'contents.lst'), 'w')
        count = commit(root, self, rootContents)
        rootContents.close()

        return count

    def _saveItem(self, item, **args):

        self.logger.debug(item.itsPath)
            
        uuid = item.itsUUID.str16()
        filename = os.path.join(self.repository.dbHome,
                                item.itsRoot.itsName,
                                uuid + '.item')
        out = file(filename, 'w')
        generator = XMLGenerator(out, 'utf-8')

        generator.startDocument()
        item._saveItem(generator, 0L)
        generator.endDocument()

        out.write('\n')
        out.close()


class FileRefDict(RefDict):
    pass
