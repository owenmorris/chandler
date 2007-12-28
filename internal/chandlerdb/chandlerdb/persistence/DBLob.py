#   Copyright (c) 2004-2007 Open Source Applications Foundation
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


from chandlerdb.item.c import ItemValue
from chandlerdb.util.c import UUID
from chandlerdb.persistence.c import Record

from chandlerdb.util.Lob import Lob
from chandlerdb.util.Streams import ConcatenatedInputStream, NullInputStream


class DBLob(Lob, ItemValue):

    def __init__(self, view, *args, **kwds):

        Lob.__init__(self, *args, **kwds)
        ItemValue.__init__(self, view, None, None)
        self._uuid = None

    def _copy(self, item, attribute, copyPolicy, copyFn, key=None):

        return self.copy(item.itsView, key)

    def _clone(self, item, attribute):

        return self.copy(item.itsView, None)

    def _setDirty(self):

        super(DBLob, self)._setDirty()
        self._dirty = True

    def _writeData(self, version, db):

        if self._dirty:
            name = self._uuid._uuid
            if self._append:
                out = db.appendFile(name)
            else:
                out = db.createFile(name)
            size = 32

            out.write(self._data)
            size += len(self._data)

            out.close()
            self._data = ''
            self._dirty = False

            return size

        return 0

    def indexValue(self, view, uItem, uAttr, uValue, version):

        store = view.repository.store
        reader = self.getPlainTextReader(replace=True)
        store._index.indexReader(view._getIndexWriter(), reader,
                                 uItem, uAttr, uValue, version)
        reader.close()

    def _writeValue(self, itemWriter, record, version, withSchema):

        if self._uuid is None or not self._append:
            self._uuid = UUID()
            self._dirty = True

        store = self._view.repository.store
        size = self._writeData(version, store._lobs)

        itemWriter.lobs.append(self._uuid)
        record += (Record.UUID, self._uuid,
                   Record.BOOLEAN, self._indexed,
                   Record.SYMBOL, self.mimetype,
                   Record.SYMBOL, self.encoding,
                   Record.SYMBOL, self._compression,
                   Record.SYMBOL, self._encryption,
                   Record.SYMBOL, self._iv)

        return size

    def _readValue(self, itemReader, offset, data, withSchema):

        self._uuid, self._indexed = data[offset:offset+2]
        offset += 2

        (self.mimetype, self.encoding, self._compression,
         self._encryption, self._iv) = data[offset:offset+5]

        return offset+5, self

    def _xmlValue(self, generator):

        attrs = {}
        attrs['mimetype'] = self.mimetype

        if self.encoding:
            attrs['encoding'] = self.encoding
        if self._compression:
            attrs['compression'] = self._compression
        if self._encryption:
            attrs['encryption'] = self._encryption
        if self._iv:
            attrs['iv'] = self._iv.encode('hex')
        if self._indexed is not None:
            attrs['indexed'] = str(self._indexed)
        
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

    def getOutputStream(self, compression=None,
                        encryption=None, key=None, iv=None,
                        append=False):

        if self.isReadOnly():
            raise TypeError, 'Value for %s on %s is read-only' %(self.itsAttribute, self.itsItem)

        return super(DBLob, self).getOutputStream(compression, encryption,
                                                  key, iv, append)

    def _getInputStream(self):

        if self._data:
            dataIn = super(DBLob, self)._getInputStream()
        else:
            dataIn = None

        store = self._view.repository.store
        lobs = store._lobs

        if self._uuid is None:
            if dataIn is None:
                return NullInputStream()
            return dataIn
        
        key = self._uuid._uuid

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
