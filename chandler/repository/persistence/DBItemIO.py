#   Copyright (c) 2005-2006 Open Source Applications Foundation
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


from struct import pack, unpack

from chandlerdb.persistence.c import DBLockDeadlockError
from chandlerdb.util.c import Nil, Default, UUID, _hash, isuuid
from chandlerdb.item.c import isitem, CItem, CValues
from chandlerdb.item.ItemValue import Indexable
from repository.item.Sets import AbstractSet
from repository.item.Values import Values, References
from repository.item.ItemIO import \
    ItemWriter, ItemReader, ItemPurger, ValueReader
from repository.item.PersistentCollections \
     import PersistentCollection, PersistentList, PersistentDict, PersistentSet
from repository.item.RefCollections import RefDict
from repository.schema.TypeHandler import TypeHandler
from repository.persistence.RepositoryError import \
        LoadError, LoadValueError, MergeError, SaveValueError
    

class DBItemWriter(ItemWriter):

    def __init__(self, store):

        super(DBItemWriter, self).__init__()

        self.store = store
        self.valueBuffer = []
        self.dataBuffer = []

    def writeItem(self, item, version):

        self.values = []
        
        self.uParent = DBItemWriter.NOITEM

        if not ((item._status & (CItem.NEW | CItem.MERGED)) != 0 or
                item._version == 0):
            self.oldValues = self.store._items.getItemValues(item.itsVersion,
                                                             item.itsUUID)
            if self.oldValues is None:
                raise AssertionError, ("Record not found for %s, version %s" %(item._repr_(), item._version))
        else:
            self.oldValues = None

        if item._isKDirty() and not item.isNew():
            prevKind = item._pastKind or DBItemWriter.NOITEM
        else:
            prevKind = None

        size = super(DBItemWriter, self).writeItem(item, version)
        size += self.store._items.saveItem(self.valueBuffer,
                                           item.itsUUID, version,
                                           self.uKind, prevKind,
                                           item._status & CItem.SAVEMASK,
                                           self.uParent, self.name,
                                           self.moduleName, self.className,
                                           self.values,
                                           item._values._getDirties(),
                                           item._references._getDirties())

        return size

    def writeString(self, buffer, value):

        if isinstance(value, unicode):
            value = value.encode('utf-8')
            size = len(value)
            buffer.append(pack('>i', size + 1))
        else:
            size = len(value)
            buffer.append(pack('>i', -(size + 1)))
            
        buffer.append(value)

        return 4 + size

    def writeSymbol(self, buffer, value):

        if isinstance(value, unicode):
            value = value.encode('ascii')

        buffer.append(pack('>H', len(value)))
        buffer.append(value)

        return 2 + len(value)

    def writeBoolean(self, buffer, value):

        if value is None:
            buffer.append('\2')
        elif value:
            buffer.append('\1')
        else:
            buffer.append('\0')

        return 1

    def writeShort(self, buffer, value):

        buffer.append(pack('>h', value))
        return 2

    def writeInteger(self, buffer, value):

        buffer.append(pack('>i', value))
        return 4

    def writeLong(self, buffer, value):
        
        buffer.append(pack('>q', value))
        return 8
        
    def writeFloat(self, buffer, value):

        buffer.append(pack('>d', value))
        return 8

    def writeUUID(self, buffer, value):

        buffer.append(value._uuid)
        return 16

    def writeLob(self, buffer, value, indexed):

        self.lobs.append(value)
        size = self.writeUUID(buffer, value)
        size += self.writeBoolean(buffer, indexed)

        return size

    def writeIndex(self, buffer, value):

        self.indexes.append(value)
        return self.writeUUID(buffer, value)

    def writeValue(self, buffer, item, version, value, withSchema, attrType):

        flags = DBItemWriter.SINGLE | DBItemWriter.VALUE
        attrType = self._type(buffer, flags, item, value, True,
                              withSchema, attrType)
        return attrType.writeValue(self, buffer, item, version,
                                   value, withSchema)

    def writeList(self, buffer, item, version, value, withSchema, attrType):

        flags = DBItemWriter.LIST | DBItemWriter.VALUE
        attrType = self._type(buffer, flags, item, value, False,
                              withSchema, attrType)
        buffer.append(pack('>I', len(value)))
        size = 4
        for v in value:
            size += self.writeValue(buffer, item, version,
                                    v, withSchema, attrType)

        return size

    def writeSet(self, buffer, item, version, value, withSchema, attrType):

        flags = DBItemWriter.SET | DBItemWriter.VALUE
        attrType = self._type(buffer, flags, item, value, False,
                              withSchema, attrType)
        buffer.append(pack('>I', len(value)))
        size = 4
        for v in value:
            size += self.writeValue(buffer, item, version,
                                    v, withSchema, attrType)

        return size

    def writeDict(self, buffer, item, version, value, withSchema, attrType):

        flags = DBItemWriter.DICT | DBItemWriter.VALUE
        attrType = self._type(buffer, flags, item, value, False,
                              withSchema, attrType)
        buffer.append(pack('>I', len(value)))
        size = 4
        for k, v in value._iteritems():
            size += self.writeValue(buffer, item, version,
                                    k, False, None)
            size += self.writeValue(buffer, item, version,
                                    v, withSchema, attrType)

        return size

    def writeIndexes(self, buffer, item, version, value):

        if value._indexes:
            buffer.append(pack('>H', len(value._indexes)))
            size = 2 + value._saveIndexes(self, buffer, version)
        else:
            buffer.append('\0\0')
            size = 2

        return size

    def _kind(self, kind):

        if kind is None:
            self.uKind = DBItemWriter.NOITEM
        else:
            self.uKind = kind.itsUUID

        return 0

    def _parent(self, parent, isContainer):

        if parent is None:
            self.uParent = DBItemWriter.NOITEM
        else:
            self.uParent = parent.itsUUID

        return 0

    def _name(self, name):

        self.name = name
        return 0

    def _className(self, moduleName, className):

        self.moduleName = moduleName
        self.className = className

        return 0

    def _children(self, item, version, all):

        if item._children is not None:
            return item._children._saveValues(version)

        return 0

    def _acls(self, item, version, all):

        size = 0
        if item._status & CItem.ADIRTY:
            store = self.store
            uuid = item._uuid
            for name, acl in item._acls.iteritems():
                size += store.saveACL(version, uuid, name, acl)

        return size

    def _values(self, item, version, withSchema, all):

        return item._values._writeValues(self, version, withSchema, all)

    def _references(self, item, version, withSchema, all):

        return item._references._writeValues(self, version, withSchema, all)

    def _value(self, item, name, value, version, flags, withSchema, attribute):

        self.lobs = []
        self.indexes = []
        view = item.itsView

        uValue = UUID()
        self.values.append((name, uValue))

        if isinstance(value, Indexable):
            indexed = value.isIndexed()
            indexable = True
        else:
            indexed = None
            indexable = False

        if attribute is None:
            uAttr = DBItemWriter.NOITEM
            attrCard = 'single'
            attrType = None
            if indexed is None:
                indexed = False
        else:
            uAttr = attribute._uuid
            c = attribute.c
            attrCard = c.cardinality
            attrType = attribute.getAspect('type', None)
            if indexed is None:
                indexed = c.indexed
            
        buffer = self.dataBuffer
        del buffer[:]

        if indexed:
            if view.isBackgroundIndexed():
                flags |= CValues.TOINDEX
                item._status |= CItem.TOINDEX
                indexed = False
            else:
                flags |= CValues.INDEXED
        buffer.append(chr(flags))

        if withSchema:
            self.writeSymbol(buffer, name)

        try:
            if attrCard == 'single':
                self.writeValue(buffer, item, version,
                                value, withSchema, attrType)
            elif attrCard == 'list':
                self.writeList(buffer, item, version,
                               value, withSchema, attrType)
            elif attrCard == 'set':
                self.writeSet(buffer, item, version,
                              value, withSchema, attrType)
            elif attrCard == 'dict':
                self.writeDict(buffer, item, version,
                               value, withSchema, attrType)
        except DBLockDeadlockError:
            raise
        except Exception, e:
            raise # SaveValueError, (item, name, e)

        if indexed:
            if indexable:
                value.indexValue(view, item.itsUUID, attribute.itsUUID, uValue,
                                 version)
            elif attrCard == 'single':
                if attrType is None:
                    valueType = TypeHandler.typeHandler(view, value)
                elif attrType.isAlias():
                    valueType = attrType.type(value)
                else:
                    valueType = attrType
                self.indexValue(view, valueType.makeUnicode(value),
                                item.itsUUID, attribute.itsUUID, uValue,
                                version)
            else:
                raise NotImplementedError, (attrCard, "full text indexing")

        for uuid in self.lobs:
            self.writeUUID(buffer, uuid)
        for uuid in self.indexes:
            self.writeUUID(buffer, uuid)

        buffer.append(pack('>H', len(self.lobs)))
        buffer.append(pack('>H', len(self.indexes)))

        return self.store._values.c.saveValue(self.store.txn,
                                              uAttr, uValue, ''.join(buffer))

    def indexValue(self, view, value, uItem, uAttr, uValue, version):

        self.store._index.indexValue(view._getIndexWriter(),
                                     value, uItem, uAttr, uValue, version)

    def indexReader(self, view, reader, uItem, uAttr, uValue, version):

        self.store._index.indexReader(view._getIndexWriter(),
                                      reader, uitem, uAttr, uValue, version)

    def _unchangedValue(self, item, name):

        try:
            self.values.append((name, self.oldValues[_hash(name)]))
        except KeyError:
            raise AssertionError, "unchanged value for '%s' not found" %(name)

        return 0

    def _type(self, buffer, flags, item, value, verify, withSchema, attrType):

        if attrType is None:
            if verify:
                attrType = TypeHandler.typeHandler(item.itsView, value)
                typeId = attrType._uuid
            else:
                typeId = None

        elif attrType.isAlias():
            if verify:
                aliasType = attrType.type(value)
                if aliasType is None:
                    raise TypeError, "%s does not alias type of value '%s' of type %s" %(attrType.itsPath, value, type(value))
                attrType = aliasType
                typeId = attrType._uuid
            else:
                typeId = None
            
        else:
            if verify and not attrType.recognizes(value):
                raise TypeError, "value '%s' of type %s is not recognized by type %s" %(value, type(value), attrType.itsPath)

            if withSchema:
                typeId = attrType._uuid
            else:
                typeId = None

        if typeId is None:
            buffer.append(chr(flags))
        else:
            flags |= DBItemWriter.TYPED
            buffer.append(chr(flags))
            buffer.append(typeId._uuid)

        return attrType

    def _ref(self, item, name, value, version, flags, withSchema, attribute):

        uValue = UUID()
        self.values.append((name, uValue))
        size = 0

        buffer = self.dataBuffer
        del buffer[:]

        buffer.append(chr(flags))
        if withSchema:
            self.writeSymbol(buffer, name)

        if value is None:
            buffer.append(chr(DBItemWriter.NONE | DBItemWriter.REF))

        elif isuuid(value):
            if withSchema:
                raise AssertionError, 'withSchema is True'
            buffer.append(chr(DBItemWriter.SINGLE | DBItemWriter.REF))
            buffer.append(value._uuid)

        elif isitem(value):
            buffer.append(chr(DBItemWriter.SINGLE | DBItemWriter.REF))
            buffer.append(value.itsUUID._uuid)

        elif value._isRefs():
            attrCard = attribute.c.cardinality
            if attrCard == 'list':
                flags = DBItemWriter.LIST | DBItemWriter.REF
                if withSchema:
                    flags |= DBItemWriter.TYPED
                buffer.append(chr(flags))
                buffer.append(value.uuid._uuid)
                if withSchema:
                    self.writeSymbol(buffer, item.itsKind.getOtherName(name, item))
                size += value._saveValues(version)

            elif attrCard == 'set':
                flags = DBItemWriter.SET | DBItemWriter.REF
                buffer.append(chr(flags))
                self.writeString(buffer, value.makeString(value))

            elif attrCard == 'dict':
                flags = DBItemWriter.DICT | DBItemWriter.REF
                if withSchema:
                    flags |= DBItemWriter.TYPED
                buffer.append(chr(flags))
                if withSchema:
                    self.writeSymbol(buffer, item.itsKind.getOtherName(name, item))
                buffer.append(pack('>H', len(value._dict)))
                size = 2
                for key, refList in value._dict.iteritems():
                    if isuuid(key):
                        buffer.append('\0')
                        buffer.append(key._uuid)
                    else:
                        buffer.append('\1')
                        self.writeSymbol(buffer, key)
                    buffer.append(refList.uuid._uuid)
                    if refList._isDirty():
                        size += refList._saveValues(version)

            else:
                raise NotImplementedError, attrCard

            if attrCard != 'dict':
                self.indexes = []
                size += self.writeIndexes(buffer, item, version, value)
                for uuid in self.indexes:
                    self.writeUUID(buffer, uuid)
                buffer.append(pack('>H', len(self.indexes)))

        else:
            raise TypeError, value

        size += self.store._values.c.saveValue(self.store.txn,
                                               attribute.itsUUID, uValue,
                                               ''.join(buffer))

        return size

    TYPED    = 0x01
    VALUE    = 0x02
    REF      = 0x04
    SET      = 0x08
    SINGLE   = 0x10
    LIST     = 0x20
    DICT     = 0x40
    NONE     = 0x80
    
    NOITEM = UUID('6d4df428-32a7-11d9-f701-000393db837c')


class DBValueReader(ValueReader):

    def __init__(self, store, status, version):

        self.store = store
        self.status = status
        self.version = version

        self.uItem = None
        self.name = None

    def readValue(self, view, uValue, toIndex=False):

        store = self.store
        uAttr, vFlags, data = store._values.c.loadValue(store.txn, uValue)

        if toIndex and not (ord(vFlags) & CValues.TOINDEX):
            return uAttr, Nil

        withSchema = (self.status & CItem.CORESCHEMA) != 0

        if withSchema:
            attribute = None
            offset, name = self.readSymbol(0, data)
        else:
            attribute = view[uAttr]
            offset, name = 0, attribute.itsName

        flags = ord(data[offset])

        if flags & DBItemWriter.VALUE:
            offset, value = self._value(offset, data, None, withSchema,
                                        attribute, view, name, [])
            return uAttr, value

        elif flags & DBItemWriter.REF:
            if flags & DBItemWriter.NONE:
                return uAttr, None

            elif flags & DBItemWriter.SINGLE:
                offset, uuid = self.readUUID(offset + 1, data)
                return uAttr, uuid

            elif flags & DBItemWriter.LIST:
                offset, uuid = self.readUUID(offset + 1, data)
                return uAttr, uuid

            elif flags & DBItemWriter.SET:
                offset, value = self.readString(offset + 1, data)
                value = AbstractSet.makeValue(value)
                value._setView(view)
                return uAttr, value

            elif flags & DBItemWriter.DICT:
                if withSchema:
                    offset, otherName = self.readSymbol(offset, data)
                value = {}
                offset, count = self.readShort(offset + 1, data)
                for i in xrange(count):
                    t = data[offset]
                    if t == '\0':
                        offset, key = self.readUUID(offset + 1, data)
                    else:
                        offset, key = self.readSymbol(offset + 1, data)
                    offset, uuid = self.readUUID(offset, data)
                    value[key] = uuid
                return uAttr, value

            else:
                raise ValueError, flags

        else:
            raise ValueError, flags

    def hasTrueValue(self, view, uValue):

        store = self.store
        uAttr, vFlags, data = store._values.c.loadValue(store.txn, uValue)

        withSchema = (self.status & CItem.CORESCHEMA) != 0

        if withSchema:
            attribute = None
            offset, name = self.readSymbol(0, data)
        else:
            attribute = view[uAttr]
            offset, name = 0, attribute.itsName

        flags = ord(data[offset])

        if flags & DBItemWriter.VALUE:
            offset, value = self._value(offset, data, None, withSchema,
                                        attribute, view, name, [])
            return not not value

        elif flags & DBItemWriter.REF:
            if flags & DBItemWriter.NONE:
                return False

            elif flags & DBItemWriter.SINGLE:
                offset, uuid = self.readUUID(offset + 1, data)
                return True

            elif flags & DBItemWriter.LIST:
                offset, uuid = self.readUUID(offset + 1, data)
                ref = self.store._refs.loadRef(view, uuid, self.version, uuid)
                return ref[2] > 0

            elif flags & DBItemWriter.SET:
                offset, value = self.readString(offset + 1, data)
                value = AbstractSet.makeValue(value)
                value._setView(view)
                return not not value

            else:
                raise ValueError, flags

        else:
            raise ValueError, flags

    def _value(self, offset, data, kind, withSchema, attribute, view, name,
               afterLoadHooks):

        if withSchema:
            attrType = None
        else:
            attrType = attribute.getAspect('type', None)

        flags = ord(data[offset])

        if flags & DBItemWriter.SINGLE:
            return self._readValue(offset, data, withSchema, attrType,
                                   view, name, afterLoadHooks)
        elif flags & DBItemWriter.LIST:
            return self._readList(offset, data, withSchema, attrType,
                                  view, name, afterLoadHooks)
        elif flags & DBItemWriter.SET:
            return self._readSet(offset, data, withSchema, attrType,
                                 view, name, afterLoadHooks)
        elif flags & DBItemWriter.DICT:
            return self._readDict(offset, data, withSchema, attrType,
                                  view, name, afterLoadHooks)
        else:
            raise LoadValueError, (self.name or self.uItem, name,
                                   "invalid cardinality: 0x%x" %(flags))

    def _ref(self, offset, data, kind, withSchema, attribute, view, name,
             afterLoadHooks):

        flags = ord(data[offset])
        offset += 1
        
        if flags & DBItemWriter.NONE:
            return offset, None

        elif flags & DBItemWriter.SINGLE:
            return self.readUUID(offset, data)

        elif flags & DBItemWriter.LIST:
            offset, uuid = self.readUUID(offset, data)
            if withSchema:
                offset, otherName = self.readSymbol(offset, data)
            else:
                otherName = kind.getOtherName(name, None)
            value = view._createRefList(None, name, otherName, None,
                                        True, False, False, uuid)
            offset = self._readIndexes(offset, data, value, afterLoadHooks)

            return offset, value

        elif flags & DBItemWriter.SET:
            offset, string = self.readString(offset, data)
            value = AbstractSet.makeValue(string)
            value._setView(view)
            offset = self._readIndexes(offset, data, value, afterLoadHooks)

            return offset, value

        elif flags & DBItemWriter.DICT:
            if withSchema:
                offset, otherName = self.readSymbol(offset, data)
            else:
                otherName = kind.getOtherName(name, None)
            value = RefDict(None, name, otherName)
            offset, count = self.readShort(offset, data)
            for i in xrange(count):
                t = data[offset]
                if t == '\0':
                    offset, key = self.readUUID(offset + 1, data)
                else:
                    offset, key = self.readSymbol(offset + 1, data)
                offset, uuid = self.readUUID(offset, data)
                value._dict[key] = view._createRefList(None, name, otherName,
                                                       key, True, False, False,
                                                       uuid)

            return offset, value

        else:
            raise LoadValueError, (self.name or self.uItem, name,
                                   "invalid cardinality: 0x%x" %(flags))

    def _type(self, offset, data, attrType, view, name):

        if ord(data[offset]) & DBItemWriter.TYPED:
            typeId = UUID(data[offset+1:offset+17])
            try:
                return offset+17, view[typeId]
            except KeyError:
                raise LoadValueError, (self.name or self.uItem, name,
                                       "type not found: %s" %(typeId))

        return offset+1, attrType

    def _readValue(self, offset, data, withSchema, attrType, view, name,
                   afterLoadHooks):

        offset, attrType = self._type(offset, data, attrType, view, name)
        if attrType is None:
            raise LoadValueError, (self.name or self.uItem, name,
                                   "value type is None")
        
        return attrType.readValue(self, offset, data, withSchema, view, name,
                                  afterLoadHooks)

    def _readList(self, offset, data, withSchema, attrType, view, name,
                  afterLoadHooks):

        offset, attrType = self._type(offset, data, attrType, view, name)
        count, = unpack('>I', data[offset:offset+4])
        offset += 4

        value = PersistentList()
        for i in xrange(count):
            offset, v = self._readValue(offset, data, withSchema, attrType,
                                        view, name, afterLoadHooks)
            value.append(v, False, False)

        return offset, value

    def _readSet(self, offset, data, withSchema, attrType, view, name,
                 afterLoadHooks):

        offset, attrType = self._type(offset, data, attrType, view, name)
        count, = unpack('>I', data[offset:offset+4])
        offset += 4

        value = PersistentSet()
        for i in xrange(count):
            offset, v = self._readValue(offset, data, withSchema, attrType,
                                        view, name, afterLoadHooks)
            value.add(v, False, False)

        return offset, value

    def _readDict(self, offset, data, withSchema, attrType, view, name,
                  afterLoadHooks):

        offset, attrType = self._type(offset, data, attrType, view, name)
        count, = unpack('>I', data[offset:offset+4])
        offset += 4

        value = PersistentDict()
        for i in xrange(count):
            offset, k = self._readValue(offset, data, False, None,
                                        view, name, afterLoadHooks)
            offset, v = self._readValue(offset, data, withSchema, attrType,
                                        view, name, afterLoadHooks)
            value.__setitem__(k, v, False, False)

        return offset, value

    def _readIndexes(self, offset, data, value, afterLoadHooks):

        count, = unpack('>H', data[offset:offset+2])
        offset += 2

        if count > 0:
            for i in xrange(count):
                offset = value._loadIndex(self, offset, data)
            afterLoadHooks.append(value._restoreIndexes)

        return offset

    def readString(self, offset, data):

        offset, len = offset+4, unpack('>i', data[offset:offset+4])[0]
        if len >= 0:
            len -= 1
            return offset+len, unicode(data[offset:offset+len], 'utf-8')
        else:
            len += 1
            return offset-len, data[offset:offset-len]

    def readSymbol(self, offset, data):

        offset, len, = offset+2, unpack('>H', data[offset:offset+2])[0]
        return offset+len, data[offset:offset+len]

    def readBoolean(self, offset, data):

        value = data[offset]

        if value == '\0':
            value = False
        elif value == '\1':
            value = True
        else:
            value = None

        return offset+1, value

    def readShort(self, offset, data):
        return offset+2, unpack('>h', data[offset:offset+2])[0]

    def readInteger(self, offset, data):
        return offset+4, unpack('>i', data[offset:offset+4])[0]

    def readLong(self, offset, data):
        return offset+8, unpack('>q', data[offset:offset+8])[0]
        
    def readFloat(self, offset, data):
        return offset+8, unpack('>d', data[offset:offset+8])[0]

    def readUUID(self, offset, data):
        return offset+16, UUID(data[offset:offset+16])

    def readLob(self, offset, data):
        offset, uuid = self.readUUID(offset, data)
        offset, indexed = self.readBoolean(offset, data)
        return offset, uuid, indexed

    def readIndex(self, offset, data):
        return self.readUUID(offset, data)


class DBItemReader(ItemReader, DBValueReader):

    def __init__(self, store, uItem,
                 version, uKind, status, uParent,
                 name, moduleName, className, uValues):

        self.store = store
        self.uItem = uItem
        self.version = version
        self.uKind = uKind
        self.status = status
        self.uParent = uParent
        self.name = name
        self.moduleName = moduleName
        self.className = className
        self.uValues = uValues

    def __repr__(self):

        if self.name is not None:
            name = ' ' + self.name
        else:
            name = ''

        if self.className is not None:
            className = ' (%s)' %(self.className)
        else:
            className = ''
            
        return "<ItemReader%s:%s %s>" %(className, name, self.uItem.str16())

    def readItem(self, view, afterLoadHooks):

        status = self.status
        withSchema = (status & CItem.CORESCHEMA) != 0
        isContainer = (status & CItem.CONTAINER) != 0

        status &= (CItem.CORESCHEMA | CItem.P_WATCHED)
        watchers = view._watchers
        if watchers and self.uItem in watchers:
            status |= CItem.T_WATCHED

        kind = self._kind(self.uKind, withSchema, view, afterLoadHooks)
        parent = self._parent(self.uParent, withSchema, view, afterLoadHooks)
        cls = self._class(self.moduleName, self.className, withSchema, kind,
                          view, afterLoadHooks)

        values = Values(None)
        references = References(None)

        self._values(values, references, self.uValues, kind,
                     withSchema, view, afterLoadHooks)

        instance = view._reuseItemInstance(self.uItem)
        if instance is not None:
            if cls is not type(instance):
                instance.__class__ = cls
            item = self.item = instance
            status |= item._status & item.PINNED
        else:
            item = self.item = cls.__new__(cls)

        item._fillItem(self.name, parent, kind, self.uItem,
                       values, references, status, self.version,
                       afterLoadHooks, False)

        if isContainer:
            item._children = view._createChildren(item, False)

        if kind is not None:
            afterLoadHooks.append(lambda view: kind._setupClass(cls))

        if hasattr(cls, 'onItemLoad'):
            afterLoadHooks.append(item.onItemLoad)

        return item

    def getUUID(self):
        return self.uItem

    def getVersion(self):
        return self.version

    def isDeleted(self):
        return (self.status & CItem.DELETED) != 0

    def _kind(self, uuid, withSchema, view, afterLoadHooks):

        if uuid == DBItemWriter.NOITEM:
            return None
        
        kind = super(DBItemReader, self)._kind(uuid, withSchema,
                                               view, afterLoadHooks)
        if kind is None:
            if withSchema:
                afterLoadHooks.append(self._setKind)
            else:
                raise LoadError, (self.name or self.uItem,
                                  "kind not found: %s" %(uuid))

        return kind

    def _setKind(self, view):

        if self.item._kind is None:
            try:
                kind = view[self.uKind]
            except KeyError:
                raise LoadError, (self.name or self.uItem,
                                  "kind not found: %s" %(uuid))
            else:
                self.item._kind = kind
                cls = type(self.item)
                if not kind._setupClass(cls):
                    # run _setupClass again after load completes
                    # because of recursive load error
                    view._hooks.append(lambda view: kind._setupClass(cls))

    def _parent(self, uuid, withSchema, view, afterLoadHooks):

        if uuid == view.itsUUID:
            return view
        
        parent = super(DBItemReader, self)._parent(uuid, withSchema,
                                                   view, afterLoadHooks)
        if parent is None:
            afterLoadHooks.append(self._move)

        return parent

    def _move(self, view):

        if self.item._parent is None:
            try:
                parent = view[self.uParent]
            except KeyError:
                raise LoadError, (self.name or self.uItem,
                                  "parent not found: %s" %(self.uParent))
            else:
                self.item.move(parent)

    def _values(self, values, references, uValues, kind,
                withSchema, view, afterLoadHooks):

        store = self.store
        c = store._values.c
        txn = store.txn

        for uuid in uValues:
            attrId, vFlags, data = c.loadValue(txn, uuid)
            if withSchema:
                attribute = None
                offset, name = self.readSymbol(0, data)
            else:
                try:
                    attribute = view[attrId]
                except KeyError:
                    raise LoadError, (self.name or self.uItem,
                                      "attribute not found: %s" %(attrId))
                else:
                    offset, name = 0, attribute.itsName

            flags = ord(data[offset])

            if flags & DBItemWriter.VALUE:
                offset, value = self._value(offset, data, kind, withSchema,
                                            attribute, view, name,
                                            afterLoadHooks)
                d = values
            elif flags & DBItemWriter.REF:
                offset, value = self._ref(offset, data, kind, withSchema,
                                          attribute, view, name,
                                          afterLoadHooks)
                d = references
            else:
                raise LoadValueError, (self.name or self.uItem, name,
                                       "not value or ref: 0x%x" %(flags))

            if value is not Nil:
                d[name] = value
                if vFlags != '\0':
                    vFlags = ord(vFlags) & CValues.SAVEMASK
                    if vFlags:
                        d._setFlags(name, vFlags)


class DBItemPurger(ItemPurger):

    def __init__(self, txn, store, uItem, keepValues,
                 indexSearcher, indexReader, status):

        self.store = store
        self.uItem = uItem

        self.keep = set(keepValues)
        self.done = set()

        withSchema = (status & CItem.CORESCHEMA) != 0
        keepOne = (status & CItem.DELETED) == 0
        keepDocuments = set()

        for value in keepValues:
            uAttr, vFlags, data = store._values.c.loadValue(txn, value)

            if withSchema:
                offset = self.skipSymbol(0, data)
            else:
                offset = 0
                
            flags = ord(data[offset])
            offset += 1

            if flags & DBItemWriter.VALUE:
                for uuid in self.iterLobs(flags, data):
                    self.keep.add(uuid)
                if ord(vFlags) & CValues.INDEXED:   # full text indexed
                    keepDocuments.add(uAttr)

            elif flags & DBItemWriter.REF:
                if flags & DBItemWriter.LIST:
                    self.keep.add(UUID(data[offset:offset+16]))
                elif flags & DBItemWriter.DICT:
                    if withSchema:
                        offset = self.skipSymbol(offset, data)
                    offset, size = self.readShort(offset, data)
                    for i in xrange(size):
                        t = data[offset]
                        if t == '\0':
                            offset += 17
                        else:
                            offset = self.skipSymbol(offset + 1, data)
                        self.keep.add(UUID(data[offset:offset+16]))
                        offset += 16

            self.keep.update(self.iterIndexes(flags, data))

        self.itemCount = 0
        self.valueCount = self.lobCount = self.blockCount = self.indexCount = 0
        self.refCount, self.nameCount = \
            store._refs.purgeRefs(txn, uItem, keepOne)
        self.documentCount = \
            store._index.purgeDocuments(indexSearcher, indexReader,
                                        uItem, keepDocuments)

    def iterLobs(self, flags, data):

        if flags & DBItemWriter.VALUE:
            lobCount, indexCount = unpack('>HH', data[-4:])

            lobStart = -(lobCount * 16 + indexCount * 16) - 4
            for i in xrange(lobCount):
                uuid = UUID(data[lobStart:lobStart+16])
                lobStart += 16
                yield uuid

    def iterIndexes(self, flags, data):

        if flags & DBItemWriter.VALUE:
            indexCount, = unpack('>H', data[-2:])
            indexStart = -indexCount * 16 - 4
            for i in xrange(indexCount):
                yield UUID(data[indexStart:indexStart+16])
                indexStart += 16

        elif flags & DBItemWriter.REF:
            if flags & (DBItemWriter.LIST | DBItemWriter.SET):
                indexCount, = unpack('>H', data[-2:])
                indexStart = -indexCount * 16 - 2
                for i in xrange(indexCount):
                    yield UUID(data[indexStart:indexStart+16])
                    indexStart += 16

    def skipSymbol(self, offset, data):
        offset, len, = offset+2, unpack('>H', data[offset:offset+2])[0]
        return offset + len

    def readShort(self, offset, data):
        return offset+2, unpack('>h', data[offset:offset+2])[0]

    def purgeItem(self, txn, values, version, status):

        withSchema = (status & CItem.CORESCHEMA) != 0
        store = self.store
        keep = self.keep
        done = self.done

        for uValue in values:
            if not (uValue in keep or uValue in done):
                uAttr, vFlags, data = store._values.c.loadValue(txn, uValue)

                if withSchema:
                    offset = self.skipSymbol(0, data)
                else:
                    offset = 0

                flags = ord(data[offset])
                offset += 1

                if flags & DBItemWriter.VALUE:
                    for uuid in self.iterLobs(flags, data):
                        if not (uuid in keep or uuid in done):
                            count = store._lobs.purgeLob(txn, uuid)
                            self.lobCount += count[0]
                            self.blockCount += count[1]
                            done.add(uuid)
                    for uuid in self.iterIndexes(flags, data):
                        if uuid not in done:
                            self.indexCount += store._indexes.purgeIndex(txn, uuid, uuid in keep)
                            done.add(uuid)

                elif flags & DBItemWriter.REF:
                    uuid = UUID(data[offset:offset+16])
                    if flags & DBItemWriter.LIST:
                        if uuid not in done:
                            count = store._refs.purgeRefs(txn, uuid,
                                                          uuid in keep)
                            self.refCount += count[0]
                            self.nameCount += count[1]
                            done.add(uuid)
                    elif flags & DBItemWriter.DICT:
                        if withSchema:
                            offset = self.skipSymbol(offset, data)
                        offset, size = self.readShort(offset, data)
                        for i in xrange(size):
                            t = data[offset]
                            if t == '\0':
                                offset += 17
                            else:
                                offset = self.skipSymbol(offset + 1, data)
                            uuid = UUID(data[offset:offset+16])
                            offset += 16
                            if uuid not in done:
                                count = store._refs.purgeRefs(txn, uuid,
                                                              uuid in keep)
                                self.refCount += count[0]
                                self.nameCount += count[1]
                                done.add(uuid)
                    if flags & (DBItemWriter.LIST | DBItemWriter.SET):
                        for uuid in self.iterIndexes(flags, data):
                            if uuid not in done:
                                self.indexCount += store._indexes.purgeIndex(txn, uuid, uuid in keep)
                                done.add(uuid)

                self.valueCount += store._values.purgeValue(txn, uValue)
                done.add(uValue)

        self.itemCount += store._items.purgeItem(txn, self.uItem, version)


class DBItemUndo(object):

    def __init__(self, repository, uItem, version,
                 uKind, status, uParent, prevKind, dirties):

        self.repository = repository
        self.uItem = uItem
        self.version = version
        self.uKind = uKind
        self.status = status
        self.uParent = uParent

        if status & CItem.NEW:
            self.hashes = None
        else:
            self.hashes = list(dirties)

    def skipSymbol(self, offset, data):
        offset, len, = offset+2, unpack('>H', data[offset:offset+2])[0]
        return offset + len

    def readShort(self, offset, data):
        return offset+2, unpack('>h', data[offset:offset+2])[0]

    def iterLobs(self, flags, data):

        if flags & DBItemWriter.VALUE:
            lobCount, indexCount = unpack('>HH', data[-4:])

            lobStart = -(lobCount * 16 + indexCount * 16) - 4
            for i in xrange(lobCount):
                uuid = UUID(data[lobStart:lobStart+16])
                lobStart += 16
                yield uuid

    def iterIndexes(self, flags, data):

        if flags & DBItemWriter.VALUE:
            indexCount, = unpack('>H', data[-2:])
            indexStart = -indexCount * 16 - 4
            for i in xrange(indexCount):
                yield UUID(data[indexStart:indexStart+16])
                indexStart += 16

        elif flags & DBItemWriter.REF:
            if flags & (DBItemWriter.LIST | DBItemWriter.SET):
                indexCount, = unpack('>H', data[-2:])
                indexStart = -indexCount * 16 - 2
                for i in xrange(indexCount):
                    yield UUID(data[indexStart:indexStart+16])
                    indexStart += 16

    def undoItem(self, txn, indexReader, indexSearcher):
        
        store = self.repository.store
        items = store._items
        values = store._values
        refs = store._refs
        lobs = store._lobs
        indexes = store._indexes

        withSchema = (self.status & CItem.CORESCHEMA) != 0
        isNew = (self.status & CItem.NEW) != 0
        uItem = self.uItem
        version = self.version

        status, uValues = items.findValues(None, version, uItem,
                                           self.hashes, True)

        for uValue in uValues:
            uAttr, vFlags, data = values.c.loadValue(txn, uValue)
                        
            if withSchema:
                offset = self.skipSymbol(0, data)
            else:
                offset = 0

            flags = ord(data[offset])
            offset += 1

            if flags & DBItemWriter.VALUE:
                if isNew:
                    for uLob in self.iterLobs(flags, data):
                        lobs.purgeLob(txn, uLob)
                for uIndex in self.iterIndexes(flags, data):
                    indexes.undoIndex(txn, uIndex, version)
            
            elif flags & DBItemWriter.REF:
                if flags & DBItemWriter.LIST:
                    uRefs = UUID(data[offset:offset+16])
                    refs.undoRefs(txn, uRefs, version)
                elif flags & DBItemWriter.DICT:
                    if withSchema:
                        offset = self.skipSymbol(offset, data)
                    offset, count = self.readShort(offset, data)
                    for i in xrange(count):
                        t = data[offset]
                        if t == '\0':
                            offset += 17
                        else:
                            offset = self.skipSymbol(offset + 1, data)
                        uRefs = UUID(data[offset:offset+16])
                        offset += 16
                        refs.undoRefs(txn, uRefs, version)
                if flags & (DBItemWriter.LIST | DBItemWriter.SET):
                    for uIndex in self.iterIndexes(flags, data):
                        indexes.undoIndex(txn, uIndex, version)
    
            values.purgeValue(txn, uValue)
        
        refs.undoRefs(txn, uItem, version) # children
        store._index.undoDocuments(indexSearcher, indexReader, uItem, version)

        items.purgeItem(txn, uItem, version)
