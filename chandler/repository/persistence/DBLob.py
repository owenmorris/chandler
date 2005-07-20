
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.item.Values import Values, ItemValue
from repository.util.Lob import Lob
from chandlerdb.util.uuid import UUID
from repository.util.Streams import ConcatenatedInputStream, NullInputStream


class DBLob(Lob, ItemValue):

    def __init__(self, view, *args, **kwds):

        Lob.__init__(self, *args, **kwds)
        ItemValue.__init__(self)
        
        self._uuid = None
        self._view = view
        self._version = 0

    def getUUID(self):

        if self._uuid is None:
            self._uuid = UUID()

        return self._uuid

    def getVersion(self):

        return self._version

    def _copy(self, item, attribute, key=None):

        return self.copy(item.itsView, key)

    def _writeData(self, uuid, store, db):

        if self._dirty or self._version == 0:
            if self._append:
                out = db.appendFile(store.lobName(uuid, self._version))
            else:
                self._version += 1
                out = db.createFile(store.lobName(uuid, self._version))
            size = 32

            out.write(self._data)
            size += len(self._data)

            out.close()
            self._data = ''

            item, attribute = self._getOwner()
            indexed = (not item.getAttributeAspect(attribute, 'indexed',
                                                   False, None, False) and
                       self._indexed)

            if indexed:
                reader = self.getPlainTextReader(replace=True)
                store._index.indexReader(self._view._getIndexWriter(),
                                         reader, item.itsUUID, attribute,
                                         self.getVersion())
                reader.close()
            
            self._dirty = False
            return size

        return 0

    def _writeValue(self, itemWriter, buffer, withSchema):

        uuid = self.getUUID()
        store = self._view.repository.store
        size = self._writeData(uuid, store, store._lobs)

        itemWriter.writeUUID(buffer, uuid)
        itemWriter.writeInteger(buffer, self._version)
        itemWriter.writeString(buffer, self.mimetype)
        itemWriter.writeBoolean(buffer, self._indexed)

        if self.encoding:
            itemWriter.writeString(buffer, self.encoding)
        else:
            itemWriter.writeString(buffer, '')

        if self._compression:
            itemWriter.writeSymbol(buffer, self._compression)
        else:
            itemWriter.writeSymbol(buffer, '')

        if self._encryption:
            itemWriter.writeSymbol(buffer, self._encryption)
        else:
            itemWriter.writeSymbol(buffer, '')

        return size

    def _readValue(self, itemReader, offset, data, withSchema):

        offset, self._uuid = itemReader.readUUID(offset, data)
        offset, self._version = itemReader.readInteger(offset, data)
        offset, self.mimetype = itemReader.readString(offset, data)
        offset, self._indexed = itemReader.readBoolean(offset, data)

        offset, encoding = itemReader.readString(offset, data)
        self.encoding = encoding or None
        offset, _compression = itemReader.readSymbol(offset, data)
        self._compression = _compression or None
        offset, _encryption = itemReader.readSymbol(offset, data)
        self._encryption = _encryption or None

        return offset, self

    def _xmlValue(self, generator):

        attrs = {}
        attrs['version'] = str(self._version)
        attrs['mimetype'] = self.mimetype

        if self.encoding:
            attrs['encoding'] = self.encoding
        if self._compression:
            attrs['compression'] = self._compression
        if self._encryption:
            attrs['encryption'] = self._encryption
        if self._indexed:
            attrs['indexed'] = 'True'
        
        generator.startElement('lob', attrs)
        generator.characters('expanding lob content not implemented')
        generator.endElement('lob')

    def load(self, data, attrs):

        super(DBLob, self).load(data, attrs)

        if attrs.get('type', 'text') != 'text':
            self._uuid = UUID(data)

    def _setData(self, data):

        super(DBLob, self)._setData(data)
        self._setDirty()

    def getOutputStream(self, compression=None, encryption=None, key=None,
                        append=False):

        if self._isReadOnly():
            raise TypeError, 'Value for %s on %s is read-only' %(self._getAttribute(), self._getItem())

        return super(DBLob, self).getOutputStream(compression, encryption,
                                                  key, append)

    def _getInputStream(self):

        if self._data:
            dataIn = super(DBLob, self)._getInputStream()
        else:
            dataIn = None

        store = self._view.repository.store
        lobs = store._lobs
        key = store.lobName(self.getUUID(), self._version)
        
        if dataIn is not None:
            if self._append:
                if lobs.fileExists(key):
                    return ConcatenatedInputStream(lobs.openFile(key), dataIn)
                else:
                    return dataIn
            else:
                return dataIn
        elif lobs.fileExists(key):
            return lobs.openFile(key)
        else:
            return NullInputStream()
