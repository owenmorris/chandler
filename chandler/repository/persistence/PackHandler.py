
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, re

from chandlerdb.util.c import UUID
from repository.util.Path import Path
from repository.util.SAX import ContentHandler
from repository.item.Item import Item
from repository.item.ItemHandler import ItemsHandler


class PackHandler(ContentHandler):
    'A SAX ContentHandler implementation responsible for loading packs.'

    def __init__(self, path, parent, view):

        ContentHandler.__init__(self)

        self.path = path
        self.cwd = [os.path.dirname(path)]
        self.parent = [parent]
        self.view = view
        self.hooks = []

        # the xml parser may return unicode for non-ascii paths or names
        # which need to be encoded to utf8
        self.fsenc = 'utf8'

        packs = view.getRoot('Packs')
        if packs is None:
            packs = Item('Packs', view, None)
        self.packs = packs

    def startDocument(self):

        self.tagAttrs = []

    def startElement(self, tag, attrs):

        if not self.errorOccurred():
            self.data = ''
            method = getattr(PackHandler, tag + 'Start', None)
            if method is not None:
                method(self, attrs)

            self.tagAttrs.append(attrs)

    def characters(self, data):

        self.data += data

    def endElement(self, tag):

        if not self.errorOccurred():
            attrs = self.tagAttrs.pop()

            method = getattr(PackHandler, tag + 'End', None)
            if method is not None:
                method(self, attrs)

    def packStart(self, attrs):

        if attrs.has_key('cwd'):
            cwd = attrs['cwd']
            if isinstance(cwd, unicode):
                cwd = cwd.encode(self.fsenc)

            self.cwd[-1] = os.path.join(self.cwd[-1], cwd)

        if attrs.has_key('file'):
            if not self.view.find(Path('//', 'Packs', attrs['name'])):
                try:
                    file = attrs['file']
                    if isinstance(file, unicode):
                        file = file.encode(self.fsenc)

                    self.view.loadPack(os.path.join(self.cwd[-1], file),
                                       self.parent[-1])
                except:
                    self.saveException()
                    return

        else:
            self.name = attrs['name']
            self.pack = Item(self.name, self.packs, None)
            self.hooks.append([])

    def packEnd(self, attrs):

        if not attrs.has_key('file'):
            packKind = self.view.findPath('Schema/Core/Pack')
            self.pack.itsKind = packKind
            self.pack.path = self.path
            for hook in self.hooks.pop():
                hook(self.view)

    def cwdStart(self, attrs):

        path = attrs['path']
        if isinstance(path, unicode):
            path = path.encode(self.fsenc)

        self.cwd.append(os.path.join(self.cwd[-1], path))

    def cwdEnd(self, attrs):

        self.cwd.pop()

    def itemStart(self, attrs):

        parent = None

        if attrs.get('afterLoadHooks', 'False') == 'True':
            self.hooks.append([])

        if attrs.has_key('path'):
            parent = self.view.find(Path(attrs['path']))
        elif attrs.has_key('uuid'):
            parent = self.view.find(UUID(attrs['uuid']))
        elif attrs.has_key('file'):
            file = attrs['file']
            if isinstance(file, unicode):
                file = file.encode(self.fsenc)

            parent = self.loadItem(os.path.join(self.cwd[-1], file),
                                   self.parent[-1])

        elif attrs.has_key('files'):
            files = attrs['files']
            if isinstance(files, unicode):
                files = files.encode(self.fsenc)

            pattern = '^' + files + '$'
            pattern = pattern.replace('.', '\\.').replace('*', '.*')
            exp = re.compile(pattern)

            for file in os.listdir(self.cwd[-1]):
                if exp.match(file):
                    parent = self.loadItem(os.path.join(self.cwd[-1], file),
                                           self.parent[-1])
                    if self.errorOccurred():
                        return

        self.parent.append(parent)

        if attrs.has_key('cwd'):
            cwd = attrs['cwd']
            if isinstance(cwd, unicode):
                cwd = cwd.encode(self.fsenc)

            self.cwd.append(os.path.join(self.cwd[-1], cwd))

    def itemEnd(self, attrs):

        item = self.parent.pop()

        if attrs.has_key('cwd'):
            self.cwd.pop()

        try:
            if attrs.get('afterLoadHooks', 'False') == 'True':
                for hook in self.hooks.pop():
                    hook(self.view)
        except:
            self.saveException()
            return

    def loadItem(self, file, parent):

        try:
            view = self.view
            view.logger.debug("Loading item file: %s", file)
            
            handler = ItemsHandler(view, parent or view, self.hooks[-1], True)
            handler.parseFile(file)

            for item in handler.items:
                if item._status & item.NDIRTY == 0:
                    item._status |= item.NEW
                    item.setDirty(item.NDIRTY, None)

            return handler.items[0]

        except:
            self.saveException()
            return
