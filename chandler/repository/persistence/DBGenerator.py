
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import libxml2

from struct import pack
from cStringIO import StringIO

from chandlerdb.util.UUID import UUID
from repository.util.SAX import XMLGenerator
from repository.item.Item import Item
from repository.persistence.Repository import Repository


class DBGenerator(XMLGenerator):

    def __init__(self, store, uItem, version, status, vDirties, rDirties):

        self.store = store
        self.uItem = uItem
        self.version = version
        self.status = status
        self.vDirties = vDirties
        self.rDirties = rDirties
        self._buffer = StringIO()
        self._valueBuffer = StringIO()
        
        super(DBGenerator, self).__init__(self._buffer, 'utf-8')

    def startDocument(self):

        self._getValue()

        self.uKind = DBGenerator.KINDLESS
        self.name = None
        self.className = None
        self.moduleName = None
        self.uParent = Repository.itsUUID
        self.container = False
        self.uAttr = None
        self.attrName = None
        self.values = []

    def endDocument(self):
        pass

    def startElement(self, tag, attrs):

        if tag in ('item', 'name', 'kind', 'parent'):
            pass

        elif tag == 'class':
            self.moduleName = attrs['module']

        elif tag in ('attribute', 'ref'):
            self.uAttr = UUID(attrs['id'])
            self.attrName = attrs['name']
            super(DBGenerator, self).startElement(tag, attrs)

        else:
            super(DBGenerator, self).startElement(tag, attrs)

    def endElement(self, tag):

        if tag == 'item':
            self.store._items.saveItem(self._valueBuffer,
                                       self.uItem, self.version,
                                       self.uKind, self.status,
                                       self.uParent, self.name,
                                       self.moduleName, self.className,
                                       self.values,
                                       self.vDirties, self.rDirties)

        elif tag == 'name':
            self.name = self._getValue()

        elif tag == 'kind':
            self.uKind = UUID(self._getValue())

        elif tag == 'parent':
            self.uParent = UUID(self._getValue())

        elif tag == 'class':
            self.className = self._getValue()

        elif tag in ('attribute', 'ref'):
            super(DBGenerator, self).endElement(tag)
            uValue = UUID()
            self.values.append((self.attrName, uValue))
            self.store._values.saveValue(self._valueBuffer,
                                         self.uItem, self.version,
                                         self.uAttr, uValue,
                                         self._getValue())
            self.uAttr = None
            self.attrName = None

        else:
            super(DBGenerator, self).endElement(tag)

    def _getValue(self):

        try:
            return self._buffer.getvalue()
        finally:
            self._buffer.truncate(0)
            self._buffer.seek(0)

    KINDLESS = UUID('6d4df428-32a7-11d9-f701-000393db837c')


class ItemDoc(object):

    def __init__(self, store, uItem, version,
                 uKind, status, uParent, name, moduleName, className, values):

        self.store = store
        self.uItem = uItem
        self.version = version
        self.uKind = uKind
        self.uParent = uParent
        self.name = name
        self.moduleName = moduleName
        self.className = className
        self.status = status
        self.values = values

    def __repr__(self):

        if self.name is not None:
            name = ' ' + self.name
        else:
            name = ''

        if self.className is not None:
            className = ' (%s)' %(self.className)
        else:
            className = ''
            
        return "<ItemDoc%s:%s %s>" %(className, name, self.uItem.str16())

    def getUUID(self):

        return self.uItem

    def getVersion(self):

        return self.version

    def isDeleted(self):

        return self.status & Item.DELETED != 0

    def getParentId(self):

        return self.uParent

    def parse(self, handler):

        ctx = libxml2.createPushParser(handler, '', 0, '')

        header = '<?xml version="1.0" encoding="utf-8"?>'
        ctx.parseChunk(header, len(header), False)
        ctx.parseChunk('<xml>', 5, False)

        attrs = { 'version': str(self.version),
                  'uuid': self.uItem.str64() }
        if self.status & Item.CORESCHEMA:
            attrs['withSchema'] = 'True'
        handler.startElement('item', attrs)

        if self.name is not None:
            handler.startElement('name', {})
            handler.characters(self.name)
            handler.endElement('name')

        if self.className is not None:
            handler.startElement('class', { 'module': self.moduleName })
            handler.characters(self.className)
            handler.endElement('class')

        if self.uKind != DBGenerator.KINDLESS:
            handler.startElement('kind', { 'type': 'uuid' })
            handler.characters(self.uKind.str64())
            handler.endElement('kind')

        attrs = { 'type': 'uuid' }
        if self.status & Item.CONTAINER:
            attrs['container'] = 'True'
        handler.startElement('parent', attrs)
        handler.characters(self.uParent.str64())
        handler.endElement('parent')

        for uValue in self.values:
            value = self.store._values.loadValue(uValue)
            ctx.parseChunk(value, len(value), False)
            if handler.errorOccurred():
                raise handler.saxError()

        handler.endElement('item')
        ctx.parseChunk('</xml>', 6, True)

        if handler.errorOccurred():
            raise handler.saxError()
