
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.item.Values import Values, ItemValue
from repository.util.Lob import Text, Binary
from chandlerdb.util.UUID import UUID
from repository.util.Streams import ConcatenatedInputStream, NullInputStream


class DBLob(object):

    def _writeData(self, uuid, store, db):

        if self._dirty or self._version == 0:
            if self._append:
                out = db.appendFile(store.lobName(uuid, self._version))
            else:
                self._version += 1
                out = db.createFile(store.lobName(uuid, self._version))
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


class DBText(Text, DBLob, ItemValue):

    def __init__(self, view, *args, **kwds):

        Text.__init__(self, *args, **kwds)
        ItemValue.__init__(self)
        
        self._uuid = None
        self._view = view
        self._version = 0

    def _copy(self, item, attribute, key=None):

        view = item.itsView
        copy = view._getLobType('text')(view, self.encoding,
                                        self.mimetype, self._indexed)

        inputStream = self.getInputStream(key)
        outputStream = copy.getOutputStream(self._compression, self._encryption,
                                            key)

        outputStream.write(inputStream.read())
        outputStream.close()
        inputStream.close()

        return copy

    def _writeValue(self, itemWriter, buffer, withSchema):

        uuid = self.getUUID()
        store = self._view.repository.store
        self._writeData(uuid, store, store._text)

        itemWriter.writeUUID(buffer, uuid)
        itemWriter.writeInteger(buffer, self._version)
        itemWriter.writeString(buffer, self.mimetype)
        itemWriter.writeString(buffer, self.encoding)
        itemWriter.writeBoolean(buffer, self._indexed)

        if self._compression:
            itemWriter.writeSymbol(buffer, self._compression)
        else:
            itemWriter.writeSymbol(buffer, '')

        if self._encryption:
            itemWriter.writeSymbol(buffer, self._encryption)
        else:
            itemWriter.writeSymbol(buffer, '')

    def _readValue(self, itemReader, offset, data, withSchema):

        offset, self._uuid = itemReader.readUUID(offset, data)
        offset, self._version = itemReader.readInteger(offset, data)
        offset, self.mimetype = itemReader.readString(offset, data)
        offset, self.encoding = itemReader.readString(offset, data)
        offset, self._indexed = itemReader.readBoolean(offset, data)
        offset, _compression = itemReader.readSymbol(offset, data)
        self._compression = _compression or None
        offset, _encryption = itemReader.readSymbol(offset, data)
        self._encryption = _encryption or None

        return offset, self

    def _xmlValue(self, generator):

        attrs = {}
        attrs['version'] = str(self._version)
        attrs['mimetype'] = self.mimetype
        attrs['encoding'] = self.encoding
        if self._compression:
            attrs['compression'] = self._compression
        if self._encryption:
            attrs['encryption'] = self._encryption
        if self._indexed:
            attrs['indexed'] = 'True'
        
        generator.startElement('text', attrs)
        generator.characters('expanding text content not implemented')
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
        self._encryption = attrs.get('encryption', None)
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

        super(DBText, self)._setData(data)
        self._setDirty()

    def getOutputStream(self, compression=None, encryption=None, key=None,
                        append=False):

        if self._isReadOnly():
            raise TypeError, 'Value for %s on %s is read-only' %(self._getAttribute(), self._getItem())

        return Text.getOutputStream(self, compression, encryption, key, append)

    def _getInputStream(self):

        if self._data:
            dataIn = super(DBText, self)._getInputStream()
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
        

class DBBinary(Binary, DBLob, ItemValue):

    def __init__(self, view, *args, **kwds):

        Binary.__init__(self, *args, **kwds)
        ItemValue.__init__(self)

        self._uuid = None
        self._view = view
        self._version = 0
        
    def _copy(self, item, attribute, key=None):

        view = item.itsView
        copy = view._getLobType('binary')(view, self.mimetype, self._indexed)

        inputStream = self.getInputStream(key)
        outputStream = copy.getOutputStream(self._compression, self._encryption,
                                            key)

        outputStream.write(inputStream.read())
        outputStream.close()
        inputStream.close()

        return copy

    def _writeValue(self, itemWriter, buffer, withSchema):

        uuid = self.getUUID()
        store = self._view.repository.store
        self._writeData(uuid, store, store._binary)

        itemWriter.writeUUID(buffer, uuid)
        itemWriter.writeInteger(buffer, self._version)
        itemWriter.writeString(buffer, self.mimetype)
        itemWriter.writeBoolean(buffer, self._indexed)

        if self._compression:
            itemWriter.writeSymbol(buffer, self._compression)
        else:
            itemWriter.writeSymbol(buffer, '')

        if self._encryption:
            itemWriter.writeSymbol(buffer, self._encryption)
        else:
            itemWriter.writeSymbol(buffer, '')

    def _readValue(self, itemReader, offset, data, withSchema):

        offset, self._uuid = itemReader.readUUID(offset, data)
        offset, self._version = itemReader.readInteger(offset, data)
        offset, self.mimetype = itemReader.readString(offset, data)
        offset, self._indexed = itemReader.readBoolean(offset, data)
        offset, _compression = itemReader.readSymbol(offset, data)
        self._compression = _compression or None
        offset, _encryption = itemReader.readSymbol(offset, data)
        self._encryption = _encryption or None

        return offset, self

    def _xmlValue(self, generator):

        attrs = {}
        attrs['version'] = str(self._version)
        attrs['mimetype'] = self.mimetype
        if self._compression:
            attrs['compression'] = self._compression
        if self._encryption:
            attrs['encryption'] = self._encryption
        
        generator.startElement('binary', attrs)
        generator.characters('expanding binary content not implemented')
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
        self._encryption = attrs.get('encryption', None)
        self._version = long(attrs.get('version', '0'))

        if attrs.get('type', 'binary') == 'binary':
            writer = self.getWriter()
            writer.write(data)
            writer.close()
        else:
            self._uuid = UUID(data)

    def _setData(self, data):

        super(DBBinary, self)._setData(data)
        self._setDirty()

    def getOutputStream(self, compression=None, encryption=None, key=None,
                        append=False):

        if self._isReadOnly():
            raise TypeError, 'Value for %s on %s is read-only' %(self._getAttribute(), self._getItem())

        return Binary.getOutputStream(self, compression, encryption, key,
                                      append)

    def _getInputStream(self):

        if self._data:
            dataIn = super(DBBinary, self)._getInputStream()
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
