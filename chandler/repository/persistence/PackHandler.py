
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os.path
import re

from chandlerdb.util.UUID import UUID
from repository.util.Path import Path
from repository.util.SAX import ContentHandler
from repository.item.Item import Item


class PackHandler(ContentHandler):
    'A SAX ContentHandler implementation responsible for loading packs.'

    def __init__(self, path, parent, repository):

        ContentHandler.__init__(self)

        self.path = path
        self.cwd = [ os.path.dirname(path) ]
        self.parent = [ parent ]
        self.repository = repository
        self.hooks = [ None ]

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
            self.cwd[-1] = os.path.join(self.cwd[-1], attrs['cwd'])

        if attrs.has_key('file'):
            if not self.repository.find(Path('//', 'Packs', attrs['name'])):
                try:
                    self.repository.loadPack(os.path.join(self.cwd[-1],
                                                          attrs['file']),
                                             self.parent[-1])
                except Exception:
                    self.saveException()
                    return

        else:
            self.name = attrs['name']

            packs = self.repository.findPath('Packs')
            self.pack = Item(self.name, packs, None)

    def packEnd(self, attrs):

        if not attrs.has_key('file'):
            itemKind = self.repository.findPath('Schema/Core/Item')
            self.pack._kind = itemKind         #kludge
            self.pack.description = self.path

    def cwdStart(self, attrs):

        self.cwd.append(os.path.join(self.cwd[-1], attrs['path']))

    def cwdEnd(self, attrs):

        self.cwd.pop()

    def itemStart(self, attrs):

        parent = None

        if attrs.get('afterLoadHooks', 'False') == 'True':
            self.hooks.append([])
        
        if attrs.has_key('path'):
            parent = self.repository.find(Path(attrs['path']))
        elif attrs.has_key('uuid'):
            parent = self.repository.find(UUID(attrs['uuid']))
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
                    if self.errorOccurred():
                        return
            
        self.parent.append(parent)

        if attrs.has_key('cwd'):
            self.cwd.append(os.path.join(self.cwd[-1], attrs['cwd']))

    def itemEnd(self, attrs):

        item = self.parent.pop()

        if attrs.has_key('cwd'):
            self.cwd.pop()

        try:
            if attrs.get('afterLoadHooks', 'False') == 'True':
                for hook in self.hooks.pop():
                    hook()
        except Exception:
            self.saveException()
            return

    def loadItem(self, file, parent):

        try:
            items = self.repository._loadItemsFile(file, parent,
                                                   self.hooks[-1], True)

            for item in items:
                if item._status & item.NDIRTY == 0:
                    item._status |= item.NEW
                    item.setDirty(item.NDIRTY, None)

            return items[0]

        except Exception:
            self.saveException()
            return
