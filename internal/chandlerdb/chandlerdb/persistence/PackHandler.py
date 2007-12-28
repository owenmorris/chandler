#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import os, re
from pkg_resources import resource_stream, resource_listdir

from chandlerdb.util.c import UUID
from chandlerdb.util.Path import Path
from chandlerdb.util.SAX import ContentHandler
from chandlerdb.item.Item import Item
from chandlerdb.item.ItemHandler import ItemsHandler


class PackHandler(ContentHandler):
    'A SAX ContentHandler implementation responsible for loading packs.'

    def __init__(self, path, parent, package, view):

        ContentHandler.__init__(self)

        self.path = path
        self.package = package
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
                                       self.parent[-1], self.package)
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

            if self.package is not None:
                if os.path.sep != '/':
                    path = self.cwd[-1].replace(os.path.sep, '/')
                else:
                    path = self.cwd[-1]
                files = resource_listdir(self.package, path)
            else:
                files = os.listdir(self.cwd[-1])

            for file in files:
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
            handler = ItemsHandler(view, parent or view, self.hooks[-1], True)

            if self.package is not None:
                if os.path.sep != '/':
                    file = file.replace(os.path.sep, '/')
                stream = resource_stream(self.package, file)
            else:
                stream = None

            handler.parseFile(file, stream)

            for item in handler.items:
                if item._status & item.NDIRTY == 0:
                    item._status |= item.NEW
                    item.setDirty(item.NDIRTY, None)

            return handler.items[0]

        except:
            self.saveException()
            return
