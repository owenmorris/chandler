
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.item.Values import Values, ItemValue
from repository.util.Lob import Text, Binary
from repository.util.UUID import UUID
from repository.util.Streams import ConcatenatedInputStream, NullInputStream


class XMLText(Text, ItemValue):

    def __init__(self, view, *args, **kwds):

        Text.__init__(self, *args, **kwds)
        ItemValue.__init__(self)
        
        self._uuid = None
        self._view = view
        self._version = 0

    def _copy(self, item, attribute):

        view = item.itsView
        copy = view._getLobType('text')(view, self.encoding,
                                        self.mimetype, self._indexed)

        inputStream = self.getInputStream()
        outputStream = copy.getOutputStream(self._compression)

        outputStream.write(inputStream.read())
        outputStream.close()
        inputStream.close()

        return copy

    def _xmlValue(self, generator):

        uuid = self.getUUID()
        
        if self._dirty or self._version == 0:
            store = self._view.repository.store
            if self._append:
                out = store._text.appendFile(store.lobName(uuid,
                                                           self._version))
            else:
                self._version += 1
                out = store._text.createFile(store.lobName(uuid,
                                                           self._version))
            out.write(self._data)
            out.close()
            self._data = ''

            if self._indexed:
                store._index.indexDocument(self._view._getIndexWriter(),
                                           self.getPlainTextReader(),
                                           uuid,
                                           self._getItem().itsUUID,
                                           self._getAttribute(),
                                           self.getVersion())
            self._dirty = False

        attrs = {}
        attrs['version'] = str(self._version)
        attrs['mimetype'] = self.mimetype
        attrs['encoding'] = self.encoding
        if self._compression:
            attrs['compression'] = self._compression
        attrs['type'] = 'uuid'
        if self._indexed:
            attrs['indexed'] = 'True'
        
        generator.startElement('text', attrs)
        generator.characters(uuid.str64())
        generator.endElement('text')

    def getUUID(self):

        if self._uuid is None:
            self._uuid = UUID()

        return self._uuid

    def getVersion(self):

        return self._version

    def load(self, data, attrs):

        self.mimetype = attrs.get('mimetype', 'text/plain')
        self._compression = attrs.get('compression', None)
        self._version = long(attrs.get('version', '0'))
        self._indexed = attrs.get('indexed', 'False') == 'True'

        if attrs.has_key('encoding'):
            self._encoding = attrs['encoding']

        if attrs.get('type', 'text') == 'text':
            writer = self.getWriter()
            writer.write(data)
            writer.close()
        else:
            self._uuid = UUID(data)

    def _setData(self, data):

        super(XMLText, self)._setData(data)
        self._setDirty()

    def getOutputStream(self, compression=None, append=False):

        if self._isReadOnly():
            raise TypeError, 'Value for %s on %s is read-only' %(self._getAttribute(), self._getItem())

        return Text.getOutputStream(self, compression, append)

    def _getInputStream(self):

        if self._data:
            dataIn = super(XMLText, self)._getInputStream()
        else:
            dataIn = None

        store = self._view.repository.store
        text = store._text
        key = store.lobName(self.getUUID(), self._version)
        
        if dataIn is not None:
            if self._append:
                if text.fileExists(key):
                    return ConcatenatedInputStream(text.openFile(key), dataIn)
                else:
                    return dataIn
            else:
                return dataIn
        elif text.fileExists(key):
            return text.openFile(key)
        else:
            return NullInputStream()
        

class XMLBinary(Binary, ItemValue):

    def __init__(self, view, *args, **kwds):

        Binary.__init__(self, *args, **kwds)
        ItemValue.__init__(self)

        self._uuid = None
        self._view = view
        self._version = 0
        
    def _copy(self, item, attribute):

        view = item.itsView
        copy = view._getLobType('binary')(view, self.mimetype, self._indexed)

        inputStream = self.getInputStream()
        outputStream = copy.getOutputStream(self._compression)

        outputStream.write(inputStream.read())
        outputStream.close()
        inputStream.close()

        return copy

    def _xmlValue(self, generator):

        uuid = self.getUUID()

        if self._dirty or self._version == 0:
            store = self._view.repository.store
            if self._append:
                out = store._binary.appendFile(store.lobName(uuid,
                                                             self._version))
            else:
                self._version += 1
                out = store._binary.createFile(store.lobName(uuid,
                                                             self._version))
            out.write(self._data)
            out.close()
            self._data = ''

            if self._indexed:
                store._index.indexDocument(self._view._getIndexWriter(),
                                           self.getPlainTextReader(),
                                           uuid,
                                           self._getItem().itsUUID,
                                           self._getAttribute(),
                                           self.getVersion())
            
            self._dirty = False

        attrs = {}
        attrs['version'] = str(self._version)
        attrs['mimetype'] = self.mimetype
        if self._compression:
            attrs['compression'] = self._compression
        attrs['type'] = 'uuid'
        
        generator.startElement('binary', attrs)
        generator.characters(uuid.str64())
        generator.endElement('binary')

    def getUUID(self):

        if self._uuid is None:
            self._uuid = UUID()

        return self._uuid

    def getVersion(self):

        return self._version

    def load(self, data, attrs):

        self.mimetype = attrs.get('mimetype', 'text/plain')
        self._compression = attrs.get('compression', None)
        self._version = long(attrs.get('version', '0'))

        if attrs.get('type', 'binary') == 'binary':
            writer = self.getWriter()
            writer.write(data)
            writer.close()
        else:
            self._uuid = UUID(data)

    def _setData(self, data):

        super(XMLBinary, self)._setData(data)
        self._setDirty()

    def getOutputStream(self, compression=None, append=False):

        if self._isReadOnly():
            raise TypeError, 'Value for %s on %s is read-only' %(self._getAttribute(), self._getItem())

        return Binary.getOutputStream(self, compression, append)

    def _getInputStream(self):

        if self._data:
            dataIn = super(XMLBinary, self)._getInputStream()
        else:
            dataIn = None

        store = self._view.repository.store
        binary = store._binary
        key = store.lobName(self.getUUID(), self._version)
        
        if dataIn is not None:
            if self._append:
                if binary.fileExists(key):
                    return ConcatenatedInputStream(binary.openFile(key),
                                                   dataIn)
                else:
                    return dataIn
            else:
                return dataIn
        elif binary.fileExists(key):
            return binary.openFile(key)
        else:
            return NullInputStream()
