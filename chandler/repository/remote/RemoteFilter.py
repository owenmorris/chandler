
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import cStringIO

from repository.util.SAX import XMLFilter, XMLGenerator
from chandlerdb.util.UUID import UUID
from repository.util.Streams import StringReader
from repository.util.Streams import BZ2OutputStream, ZlibOutputStream


class RemoteFilter(XMLFilter):

    def __init__(self, store, versionId, force=False):

        XMLFilter.__init__(self, None)

        self.store = store
        self.versionId = versionId
        self.force = force
        
        self._attrs = []
        self._isOn = False
        self._isSkipping = False
        
        self._txnStatus = 0
        self._lock = None
        self._buffer = cStringIO.StringIO()
        self._refBuffer = cStringIO.StringIO()
        self._keyBuffer = None
        self._document = None
        self._indexWriter = None
        self._count = 0
        
    def output(self):

        return self._isOn

    def getDocument(self):

        class doc(object):
            def __init__(self, xml):
                self._xml = xml
            def getContent(self):
                return self._xml
            
        return doc(self._document)

    def startElement(self, tag, attrs):

        if not self.errorOccurred():
            self.data = ''
            method = getattr(self, tag + 'Start', None)
            if method is not None:
                try:
                    method(attrs)
                except Exception:
                    self.saveException()
            self._attrs.append(attrs)

        XMLFilter.startElement(self, tag, attrs)

    def characters(self, data):

        self.data += data
        XMLFilter.characters(self, data)

    def cdataBlock(self, data):

        self.data += data
        XMLFilter.cdataBlock(self, data)

    def endElement(self, tag):

        if not self.errorOccurred():
            attrs = self._attrs.pop()
            method = getattr(self, tag + 'End', None)
            if method is not None:
                try:
                    method(attrs)
                except Exception:
                    self.saveException()
        else:
            if self._indexWriter is not None:
                self._indexWriter.close()
                self._indexWriter = None
            self.store.abortTransaction(self._txnStatus)
            self._txnStatus = 0
            if self._lock:
                self._lock = self.store.releaseLock(self._lock)

        XMLFilter.endElement(self, tag)

    def itemsStart(self, attrs):

        if attrs is not None and 'versionId' in attrs:
            versionId = UUID(attrs['versionId'])
            if versionId != self.versionId:
                raise ValueError, "remote version ids don't match"

        self._txnStatus = self.store.startTransaction()
        self._lock = self.store.acquireLock()

    def itemsEnd(self, attrs):

        if self._indexWriter is not None:
            self.store._index.optimizeIndex(self._indexWriter)
            self._indexWriter.close()
            self._indexWriter = None
            
        self.store.commitTransaction(self._txnStatus)
        self._txnStatus = 0
        if self._lock:
            self._lock = self.store.releaseLock(self._lock)

    def containerEnd(self, attrs):

        if not self._isSkipping:
            self.itemParent = UUID(self.data)

    def nameEnd(self, attrs):

        self.itemName = self.data

    def itemStart(self, attrs):

        self.itemUUID = UUID(attrs['uuid'])
        self.itemVersion = long(attrs['version'])

        version = self.store._items.getItemVersion(self.itemVersion,
                                                   self.itemUUID)
        if not self.force and version == self.itemVersion:
            self._isSkipping = True
            self._isOn = False

        else:
            self._buffer.truncate(0)
            self._buffer.seek(0)
            self.generator = XMLGenerator(self._buffer)
            self.generator.startDocument()
            self._isOn = True

    def itemEnd(self, attrs):

        if not self._isSkipping:
            self.generator.endElement('item')
            self.generator.endDocument()
            self.generator = None
            self._isOn = False

            xml = self._buffer.getvalue()
            if self._document is None:
                self._document = xml

            self._count += 1
            self.store.saveItem(xml, self.itemUUID, self.itemVersion,
                                (self.itemParent, self.itemName), None, 0)

        else:
            self._isSkipping = False

    def attributeStart(self, attrs):

        if not self._isSkipping:
            self.attributeName = attrs['name']

    def refStart(self, attrs):

        if self._isSkipping:
            return 

        if attrs and 'first' in attrs:
            self._isOn = False

            self._refsUUID = UUID(attrs['uuid'])
            self._keyBuffer = self.store._refs.prepareKey(self.itemUUID,
                                                          self._refsUUID)
            self._ref = None
            self._previous = None
            self._alias = None

    def refEnd(self, attrs):

        if self._isSkipping:
            return
        
        if attrs and 'first' in attrs:
            generator = self.generator

            if self._ref is not None:
                self.store._refs.saveRef(self._keyBuffer, self._refBuffer,
                                         self.itemVersion, self._ref,
                                         self._ref, self._previous,
                                         None, self._alias)
                if self._alias is not None:
                    self.store.writeName(self.itemVersion, self._refsUUID,
                                         self._alias, self._ref)
                    
            uuid = attrs['uuid']
            del attrs['uuid']

            generator.startElement('ref', attrs)
            generator.startElement('db', None)
            generator.characters(uuid)
            generator.endElement('db')
            self._isOn = True

            self._keyBuffer.close()
            self._keyBuffer = None

        elif not self._isOn:
            uuid = UUID(self.data)

            if self._ref is not None:
                self.store._refs.saveRef(self._keyBuffer, self._refBuffer,
                                         self.itemVersion, self._ref,
                                         self._ref, self._previous,
                                         uuid, self._alias)
                if self._alias is not None:
                    self.store.writeName(self.itemVersion, self._refsUUID,
                                         self._alias, self._ref)

            self._previous = self._ref
            self._ref = uuid

            if attrs:
                self._alias = attrs.get('alias', None)
            else:
                self._alias = None

    def textStart(self, attrs):

        if not self._isSkipping:
            self._isOn = False

    def textEnd(self, attrs):

        if self._isSkipping:
            return
        
        uuid = UUID(attrs['uuid'])
        version = long(attrs['version'])
        encoding = attrs['encoding']
        compression = attrs.get('compression', None)
        store = self.store

        if encoding != 'utf-8':
            unicodeText = self.data.decode('utf-8')
            text = unicodeText.encode(encoding)
        else:
            unicodeText = None
            text = self.data

        out = store._text.createFile(store.lobName(uuid, version))
        if compression == 'bz2':
            out = BZ2OutputStream(out)
        elif compression == 'zlib':
            out = ZlibOutputStream(out)
        out.write(text)
        out.close()

        if attrs['indexed'] == 'True':
            if self._indexWriter is None:
                self._indexWriter = store._index.getIndexWriter()
            if unicodeText is None:
                unicodeText = text.decode(encoding)
            store._index.indexDocument(self._indexWriter,
                                       StringReader(unicodeText),
                                       uuid, self.itemUUID, self.attributeName,
                                       version)

        uuid = attrs['uuid']
        del attrs['uuid']
        attrs['type'] = 'uuid'

        self.generator.startElement('text', attrs)
        self.generator.characters(uuid)
        self._isOn = True
