
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import os.path
import re

from model.util.UUID import UUID
from model.util.Path import Path
from model.item.Item import Item


class PackHandler(xml.sax.ContentHandler):
    'A SAX ContentHandler implementation responsible for loading packs.'

    def __init__(self, path, parent, repository, verbose):

        self.path = path
        self.cwd = [ os.path.dirname(path) ]
        self.parent = [ parent ]
        self.repository = repository
        self.verbose = verbose
        self.hooks = [ None ]

    def startDocument(self):

        self.tagAttrs = []

    def endDocument(self):

        self.repository._resolveStubs()

    def startElement(self, tag, attrs):

        self.data = ''
        method = getattr(PackHandler, tag + 'Start', None)
        if method is not None:
            method(self, attrs)
            
        self.tagAttrs.append(attrs)

    def characters(self, data):

        self.data += data

    def endElement(self, tag):

        attrs = self.tagAttrs.pop()

        method = getattr(PackHandler, tag + 'End', None)
        if method is not None:
            method(self, attrs)

    def packStart(self, attrs):

        if attrs.has_key('cwd'):
            self.cwd[-1] = os.path.join(self.cwd[-1], attrs['cwd'])

        if attrs.has_key('file'):
            if not self.repository.find(Path('//', 'Packs', attrs['name'])):
                self.repository.loadPack(os.path.join(self.cwd[-1],
                                                      attrs['file']),
                                         self.parent[-1], self.verbose)

        else:
            self.name = attrs['name']

            packs = self.repository.find('Packs')
            Item(self.name, packs, None).setAttributeValue('File', self.path)

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
            
        self.parent.append(parent)

        if attrs.has_key('cwd'):
            self.cwd.append(os.path.join(self.cwd[-1], attrs['cwd']))

    def itemEnd(self, attrs):

        item = self.parent.pop()

        if attrs.has_key('cwd'):
            self.cwd.pop()

        if attrs.get('afterLoadHooks', 'False') == 'True':
            for hook in self.hooks.pop():
                hook()

    def loadItem(self, file, parent):

        if self.verbose:
            print file
            
        return self.repository._loadItemFile(file, parent,
                                             afterLoadHooks=self.hooks[-1])
