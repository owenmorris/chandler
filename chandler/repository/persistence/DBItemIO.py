#   Copyright (c) 2005-2007 Open Source Applications Foundation
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


from chandlerdb.persistence.c import DBLockDeadlockError, Record
from chandlerdb.util.c import Nil, Empty, UUID, _hash, isuuid
from chandlerdb.item.c import CItem, isitemref, ItemRef, CValues
from chandlerdb.schema.c import CAttribute
from chandlerdb.item import Indexable
from repository.item.Sets import AbstractSet
from repository.item.Values import Values, References
from repository.item.ItemIO import \
    ItemWriter, ItemReader, ItemPurger, ValueReader
from repository.item.PersistentCollections \
     import PersistentList, PersistentDict, PersistentSet
from repository.item.RefCollections import RefDict
from repository.schema.TypeHandler import TypeHandler
from repository.persistence.DBRefs import DBStandAloneRefList
from repository.persistence.RepositoryError import \
        LoadError, LoadValueError, SaveValueError
    

class DBItemWriter(ItemWriter):

    def __init__(self, store, view):

        super(DBItemWriter, self).__init__()

        self.store = store
        self.valueBuffer = []
        self.dataBuffer = []
        self.toindex = view.isBackgroundIndexed()

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
        size += self.store._items.saveItem(item.itsUUID, version,
                                           self.uKind, prevKind,
                                           item._status & CItem.SAVEMASK,
                                           self.uParent, self.name,
                                           self.moduleName, self.className,
                                           self.values,
                                           item._values._getDirties(),
                                           item._references._getDirties())

        return size

    def writeValue(self, record, item, version, value, withSchema, attrType):

        flags = DBItemWriter.SINGLE | DBItemWriter.VALUE
        attrType = self._type(record, flags, item, value, True,
                              withSchema, attrType)
        return attrType.writeValue(self, record, item, version,
                                   value, withSchema)

    def writeList(self, record, item, version, value, withSchema, attrType):

        flags = DBItemWriter.LIST | DBItemWriter.VALUE
        attrType = self._type(record, flags, item, value, False,
                              withSchema, attrType)
        record += (Record.INT, len(value))
        size = 0
        for v in value:
            size += self.writeValue(record, item, version,
                                    v, withSchema, attrType)

        return size

    def writeSet(self, record, item, version, value, withSchema, attrType):

        flags = DBItemWriter.SET | DBItemWriter.VALUE
        attrType = self._type(record, flags, item, value, False,
                              withSchema, attrType)
        record += (Record.INT, len(value))
        size = 0
        for v in value:
            size += self.writeValue(record, item, version,
                                    v, withSchema, attrType)

        return size

    def writeDict(self, record, item, version, value, withSchema, attrType):

        flags = DBItemWriter.DICT | DBItemWriter.VALUE
        attrType = self._type(record, flags, item, value, False,
                              withSchema, attrType)
        record += (Record.INT, len(value))
        size = 0
        for k, v in value._iteritems():
            size += self.writeValue(record, item, version,
                                    k, False, None)
            size += self.writeValue(record, item, version,
                                    v, withSchema, attrType)

        return size

    def writeIndexes(self, record, item, version, value):

        if value._indexes:
            record += (Record.BYTE, len(value._indexes))
            return value._saveIndexes(self, record, version)
        else:
            record += (Record.BYTE, 0)

        return 0

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
            uuid = item.itsUUID
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
            attrCard = 'single'
            attrType = None
            if indexed is None:
                indexed = False
        else:
            c = attribute.c
            attrCard = c.cardinality
            attrType = attribute.type
            if indexed is None:
                indexed = c.indexed

        if indexed and self.toindex:
            flags |= CValues.TOINDEX
            item._status |= CItem.TOINDEX
            indexed = False

        record = Record(Record.UUID, attribute.itsUUID,
                        Record.BYTE, flags)

        valueRecord = Record()
        if withSchema:
            valueRecord += (Record.SYMBOL, name)

        try:
            if attrCard == 'single':
                self.writeValue(valueRecord, item, version,
                                value, withSchema, attrType)
            elif attrCard == 'list':
                self.writeList(valueRecord, item, version,
                               value, withSchema, attrType)
            elif attrCard == 'set':
                self.writeSet(valueRecord, item, version,
                              value, withSchema, attrType)
            elif attrCard == 'dict':
                self.writeDict(valueRecord, item, version,
                               value, withSchema, attrType)
        except DBLockDeadlockError:
            raise
        except Exception, e:
            raise SaveValueError, (item, name, e)

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

        record += (Record.RECORD, valueRecord)

        lobRecord = Record()
        for uuid in self.lobs:
            lobRecord += (Record.UUID, uuid)
        record += (Record.RECORD, lobRecord)

        indexRecord = Record()
        for uuid in self.indexes:
            indexRecord += (Record.UUID, uuid)
        record += (Record.RECORD, indexRecord)

        return self.store._values.c.saveValue(item.itsUUID, uValue, record)

    def indexValue(self, view, value, uItem, uAttr, uValue, version):

        self.store._index.indexValue(view._getIndexWriter(),
                                     value, uItem, uAttr, uValue, version)

    def indexReader(self, view, reader, uItem, uAttr, uValue, version):

        self.store._index.indexReader(view._getIndexWriter(),
                                      reader, uItem, uAttr, uValue, version)

    def _unchangedValue(self, item, name):

        try:
            self.values.append((name, self.oldValues[_hash(name)]))
        except KeyError:
            raise AssertionError, "unchanged value for '%s' not found" %(name)

        return 0

    def _type(self, record, flags, item, value, verify, withSchema, attrType):

        if attrType is None:
            if verify:
                attrType = TypeHandler.typeHandler(item.itsView, value)
                typeId = attrType.itsUUID
            else:
                typeId = None

        elif attrType.isAlias():
            if verify:
                aliasType = attrType.type(value)
                if aliasType is None:
                    raise TypeError, "%s does not alias type of value '%s' of type %s" %(attrType.itsPath, value, type(value))
                attrType = aliasType
                typeId = attrType.itsUUID
            else:
                typeId = None
            
        else:
            if verify and not attrType.recognizes(value):
                raise TypeError, "value '%s' of type %s is not recognized by type %s" %(value, type(value), attrType.itsPath)

            if withSchema:
                typeId = attrType.itsUUID
            else:
                typeId = None

        if (flags & DBItemWriter.SINGLE and
            attrType is not None and
            attrType.getFlags() & CAttribute.SIMPLE):
            flags |= DBItemWriter.SIMPLE
            record += (Record.BYTE, flags)
        elif typeId is None:
            record += (Record.BYTE, flags)
        else:
            flags |= DBItemWriter.TYPED
            record += (Record.BYTE, flags,
                       Record.UUID, typeId)

        return attrType

    def _ref(self, item, name, value, version, flags, withSchema, attribute):

        self.indexes = []
        uValue = UUID()
        self.values.append((name, uValue))
        size = 0

        record = Record(Record.UUID, attribute.itsUUID,
                        Record.BYTE, flags)

        refRecord = Record()
        if withSchema:
            refRecord += (Record.SYMBOL, name)

        if value is None:
            refRecord += (Record.BYTE, (DBItemWriter.NONE | DBItemWriter.REF |
                                        DBItemWriter.SINGLE))

        elif value is Empty:
            refRecord += (Record.BYTE, (DBItemWriter.NONE | DBItemWriter.REF |
                                        DBItemWriter.LIST))

        elif isuuid(value):
            if withSchema:
                raise AssertionError, 'withSchema is True'
            refRecord += (Record.BYTE, DBItemWriter.SINGLE | DBItemWriter.REF,
                          Record.UUID, value)

        elif isitemref(value):
            refRecord += (Record.BYTE, DBItemWriter.SINGLE | DBItemWriter.REF,
                          Record.UUID, value.itsUUID)

        elif value._isRefs():
            attrCard = attribute.c.cardinality
            if attrCard == 'list':
                flags = DBItemWriter.LIST | DBItemWriter.REF
                if withSchema:
                    flags |= DBItemWriter.TYPED
                refRecord += (Record.BYTE, flags,
                              Record.UUID, value.uuid)
                if withSchema:
                    refRecord += (Record.SYMBOL,
                                  item.itsKind.getOtherName(name, item))
                size += value._saveValues(version)

            elif attrCard == 'set':
                refRecord += (Record.BYTE, DBItemWriter.SET | DBItemWriter.REF,
                              Record.STRING, value.makeString(value))

            elif attrCard == 'dict':
                flags = DBItemWriter.DICT | DBItemWriter.REF
                if withSchema:
                    flags |= DBItemWriter.TYPED
                refRecord += (Record.BYTE, flags)
                if withSchema:
                    refRecord += (Record.SYMBOL,
                                  item.itsKind.getOtherName(name, item))
                refRecord += (Record.SHORT, len(value._dict))
                for key, refList in value._dict.iteritems():
                    refRecord += (Record.UUID_OR_SYMBOL, key,
                                  Record.UUID, refList.uuid)
                    if refList._isDirty():
                        size += refList._saveValues(version)

            else:
                raise NotImplementedError, attrCard

            if attrCard != 'dict':
                size += self.writeIndexes(refRecord, item, version, value)

        else:
            raise TypeError, value

        record += (Record.RECORD, refRecord,
                   Record.RECORD, Record())

        indexRecord = Record()
        for uuid in self.indexes:
            indexRecord += (Record.UUID, uuid)
        record += (Record.RECORD, indexRecord)

        size += self.store._values.c.saveValue(item.itsUUID, uValue, record)

        return size

    TYPED    = 0x01
    VALUE    = 0x02
    REF      = 0x04
    SET      = 0x08
    SINGLE   = 0x10
    LIST     = 0x20
    DICT     = 0x40
    NONE     = 0x80  # only used with REF
    SIMPLE   = 0x80  # only used with VALUE
    
    NOITEM = UUID('6d4df428-32a7-11d9-f701-000393db837c')


class DBValueReader(ValueReader):

    VALUE_TYPES = (Record.UUID, Record.BYTE, Record.RECORD)

    def __init__(self, store, uItem, status, version):

        self.store = store
        self.status = status
        self.version = version

        self.uItem = uItem
        self.name = None

    def readAttribute(self, view, uValue):

        store = self.store
        record = store._values.c.loadValue(self.uItem, uValue, (Record.UUID,))

        return record.data[0]

    def readValue(self, view, uValue, toIndex=False):

        store = self.store

        record = store._values.c.loadValue(self.uItem, uValue,
                                           DBValueReader.VALUE_TYPES)
        uAttr, vFlags, data = record.data

        if toIndex and not (vFlags & CValues.TOINDEX):
            return uAttr, Nil

        withSchema = (self.status & CItem.WITHSCHEMA) != 0

        if withSchema:
            attribute = None
            offset, name = 1, data[0]
        else:
            attribute = view[uAttr]
            offset, name = 0, attribute.itsName

        flags = data[offset]

        if flags & DBItemWriter.VALUE:
            if flags & DBItemWriter.SIMPLE:
                value = data[offset + 1]
            else:
                offset, value = self._value(offset, data, None, withSchema,
                                            attribute, view, name, [])
            return uAttr, value

        elif flags & DBItemWriter.REF:
            if flags & DBItemWriter.NONE:
                return uAttr, None

            elif flags & DBItemWriter.SINGLE:
                return uAttr, data[offset + 1]

            elif flags & DBItemWriter.LIST:
                return uAttr, DBStandAloneRefList(view, data[offset + 1],
                                                  self.version)

            elif flags & DBItemWriter.SET:
                value = AbstractSet.makeValue(data[offset + 1])
                value._setView(view)
                return uAttr, value

            elif flags & DBItemWriter.DICT:
                if withSchema:
                    offset += 2
                else:
                    offset += 1

                value = {}
                count = data[offset]
                offset += 1
                for i in xrange(count):
                    key, uuid = data[offset:offset+2]
                    offset += 2
                    value[key] = DBStandAloneRefList(view, uuid, self.version)
                return uAttr, value

            else:
                raise ValueError, flags

        else:
            raise ValueError, flags

    def hasTrueValue(self, view, uValue):

        store = self.store

        record = store._values.c.loadValue(self.uItem, uValue,
                                           DBValueReader.VALUE_TYPES)
        uAttr, vFlags, data = record.data

        withSchema = (self.status & CItem.WITHSCHEMA) != 0

        if withSchema:
            attribute = None
            offset, name = 1, data[0]
        else:
            attribute = view[uAttr]
            offset, name = 0, attribute.itsName

        flags = data[offset]

        if flags & DBItemWriter.VALUE:
            if flags & DBItemWriter.SIMPLE:
                value = data[offset + 1]
            else:
                offset, value = self._value(offset, data, None, withSchema,
                                            attribute, view, name, [])
            return not not value

        elif flags & DBItemWriter.REF:
            if flags & DBItemWriter.NONE:
                return False

            elif flags & DBItemWriter.SINGLE:
                return True

            elif flags & DBItemWriter.LIST:
                uuid = data[offset + 1]
                ref = self.store._refs.loadRef(view, uuid, self.version, uuid,
                                               True)
                return ref[2] > 0

            elif flags & DBItemWriter.SET:
                value = AbstractSet.makeValue(data[offset + 1])
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

        flags = data[offset]

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

        flags = data[offset]
        offset += 1
        
        if flags & DBItemWriter.NONE:
            if flags & DBItemWriter.LIST:
                return offset, Empty
            else:
                return offset, None

        elif flags & DBItemWriter.SINGLE:
            return offset+1, ItemRef(data[offset], view)

        elif flags & DBItemWriter.LIST:
            uuid = data[offset]
            offset += 1
            if withSchema:
                otherName = data[offset]
                offset += 1
            else:
                otherName = kind.getOtherName(name, None)
            value = view._createRefList(None, name, otherName, None,
                                        False, False, uuid)
            offset = self._readIndexes(offset, data, value, afterLoadHooks)

            return offset, value

        elif flags & DBItemWriter.SET:
            value = AbstractSet.makeValue(data[offset])
            value._setView(view)
            offset = self._readIndexes(offset + 1, data, value, afterLoadHooks)

            return offset, value

        elif flags & DBItemWriter.DICT:
            if withSchema:
                otherName = data[offset]
                offset += 1
            else:
                otherName = kind.getOtherName(name, None)

            value = RefDict(None, name, otherName)
            count = data[offset]
            offset += 1

            for i in xrange(count):
                key, uuid = data[offset:offset+2]
                offset += 2
                value._dict[key] = view._createRefList(None, name, otherName,
                                                       key, False, False, uuid)

            return offset, value

        else:
            raise LoadValueError, (self.name or self.uItem, name,
                                   "invalid cardinality: 0x%x" %(flags))

    def _type(self, offset, data, attrType, view, name):

        if data[offset] & DBItemWriter.TYPED:
            typeId = data[offset+1]
            try:
                return offset+2, view[typeId]
            except KeyError:
                raise LoadValueError, (self.name or self.uItem, name,
                                       "type not found: %s" %(typeId))

        return offset+1, attrType

    def _readValue(self, offset, data, withSchema, attrType, view, name,
                   afterLoadHooks):

        if data[offset] & DBItemWriter.SIMPLE:
            return offset+2, data[offset+1]

        offset, attrType = self._type(offset, data, attrType, view, name)
        if attrType is None:
            raise LoadValueError, (self.name or self.uItem, name,
                                   "value type is None")
        
        return attrType.readValue(self, offset, data, withSchema, view, name,
                                  afterLoadHooks)

    def _readList(self, offset, data, withSchema, attrType, view, name,
                  afterLoadHooks):

        offset, attrType = self._type(offset, data, attrType, view, name)
        count = data[offset]
        offset += 1

        value = PersistentList()
        for i in xrange(count):
            offset, v = self._readValue(offset, data, withSchema, attrType,
                                        view, name, afterLoadHooks)
            value._sequence.append(v)

        return offset, value

    def _readSet(self, offset, data, withSchema, attrType, view, name,
                 afterLoadHooks):

        offset, attrType = self._type(offset, data, attrType, view, name)
        count = data[offset]
        offset += 1

        value = PersistentSet()
        for i in xrange(count):
            offset, v = self._readValue(offset, data, withSchema, attrType,
                                        view, name, afterLoadHooks)
            value._set.add(v)

        return offset, value

    def _readDict(self, offset, data, withSchema, attrType, view, name,
                  afterLoadHooks):

        offset, attrType = self._type(offset, data, attrType, view, name)
        count = data[offset]
        offset += 1

        value = PersistentDict()
        for i in xrange(count):
            offset, k = self._readValue(offset, data, False, None,
                                        view, name, afterLoadHooks)
            offset, v = self._readValue(offset, data, withSchema, attrType,
                                        view, name, afterLoadHooks)
            value._mapping[k] = v

        return offset, value

    def _readIndexes(self, offset, data, value, afterLoadHooks):

        count = data[offset]
        offset += 1

        if count > 0:
            for i in xrange(count):
                offset = value._loadIndex(self, offset, data)
            afterLoadHooks.append(value._restoreIndexes)

        return offset


class DBItemReader(ItemReader, DBValueReader):

    def __init__(self, store, uItem, version, item):

        self.store = store
        self.uItem = uItem
        self.version = version

        (self.uKind, self.status, self.uParent, values, x,
         self.name, self.moduleName, self.className) = item.data

        self.uValues = tuple([uValue for uValue in values.data
                              if isuuid(uValue)])

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
        withSchema = (status & CItem.WITHSCHEMA) != 0
        isContainer = (status & CItem.CONTAINER) != 0

        status &= (CItem.CORESCHEMA | CItem.WITHSCHEMA | CItem.P_WATCHED |
                   CItem.SYSMONITOR | CItem.IDXMONITOR)
        watchers = view._watchers
        if watchers and self.uItem in watchers:
            status |= CItem.T_WATCHED

        kind = self._kind(self.uKind, withSchema, view, afterLoadHooks)
        parent = self._parent(self.uParent, withSchema, view, afterLoadHooks)
        cls = self._class(self.moduleName, self.className, withSchema, kind,
                          view, afterLoadHooks)

        values = Values()
        references = References()

        self._values(values, references, self.uValues, kind,
                     withSchema, view, afterLoadHooks)

        instance = view._instanceRegistry.pop(self.uItem, None)
        if instance is not None:
            if cls is not type(instance):
                instance.__class__ = cls
            item = self.item = instance
            status |= item._status & (item.PINNED | item.DEFERRED)
        else:
            item = self.item = cls.__new__(cls)

        if kind is not None:
            afterLoadHooks.append(lambda view: kind._setupClass(cls))

        if hasattr(cls, 'onItemLoad'):
            afterLoadHooks.append(item.onItemLoad)

        item._fillItem(self.name, parent, kind, self.uItem, view,
                       values, references, status, self.version,
                       afterLoadHooks, False)

        if isContainer:
            item._children = view._createChildren(item, False)

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

        item = self.item
        if item._kind is None:
            try:
                kind = view[self.uKind]
            except KeyError:
                raise LoadError, (self.name or self.uItem,
                                  "kind not found: %s" %(uuid))
            else:
                item._kind = kind
                cls = type(item)
                if not kind._setupClass(cls):
                    # run _setupClass again after load completes
                    # because of recursive load error
                    view._hooks.append(lambda view: kind._setupClass(cls))
                # give ItemValue instances another chance to cache schema info
                item.itsValues._setItem(item)
                item.itsRefs._setItem(item)

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

        records = self.store._values.c.loadValues(self.uItem, uValues,
                                                  DBValueReader.VALUE_TYPES)
        for record in records.itervalues():
            uAttr, vFlags, data = record.data

            if withSchema:
                attribute = None
                offset, name = 1, data[0]
            else:
                try:
                    attribute = view[uAttr]
                except KeyError:
                    raise LoadError, (self.name or self.uItem,
                                      "attribute not found: %s" %(uAttr))
                else:
                    offset, name = 0, attribute.itsName

            flags = data[offset]

            if flags & DBItemWriter.VALUE:
                if flags & DBItemWriter.SIMPLE:
                    offset, value = offset+2, data[offset + 1]
                else:
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
                vFlags &= CValues.SAVEMASK
                if vFlags:
                    d._setFlags(name, vFlags)

            if offset != len(data):
                raise ValueError, (name, 'short read')


class DBItemPurger(ItemPurger):

    VALUE_TYPES = DBValueReader.VALUE_TYPES + (Record.RECORD, Record.RECORD)

    def __init__(self, txn, store):

        self.store = store
        self.done = set()

    def purgeDocuments(self, txn, counter, uItem, version,
                       indexSearcher, indexReader, toVersion=None):

        self.store._index.purgeDocuments(txn, counter,
                                         indexSearcher, indexReader,
                                         uItem, toVersion)

    def purgeItems(self, txn, counter, items, toVersion=None):

        for uItem, version, status, values in items:
            self.purgeItem(txn, counter, uItem, version, status, values,
                           toVersion)

    def purgeItem(self, txn, counter,
                  uItem, version, status, values, toVersion=None):

        counter.current = (uItem, version)
        withSchema = (status & CItem.WITHSCHEMA) != 0
        store = self.store
        done = self.done

        record = DBItemPurger.VALUE_TYPES

        for uValue in values:
            if uValue in done:
                continue

            record = store._values.c.loadValue(uItem, uValue, record)
            if record is None:
                done.add(uValue)
                record = DBItemPurger.VALUE_TYPES
                continue

            uAttr, vFlags, data, lobs, indexes = record.data

            offset = 1 if withSchema else 0
            flags = data[offset]
            offset += 1

            if flags & DBItemWriter.REF:
                if flags & DBItemWriter.NONE:
                    pass
                elif flags & DBItemWriter.LIST:
                    uuid = data[offset]
                    if uuid not in done:
                        store._refs.purgeRefs(txn, counter, uuid, toVersion)
                        done.add(uuid)
                elif flags & DBItemWriter.DICT:
                    if withSchema:
                        offset += 1
                    size = data[offset]
                    offset += 1
                    for i in xrange(size):
                        uuid = data[offset + 1]
                        offset += 2
                        if uuid not in done:
                            store._refs.purgeRefs(txn, counter, uuid, toVersion)
                            done.add(uuid)

            for uuid in lobs:
                if uuid not in done:
                    store._lobs.purgeLob(txn, counter, uuid, toVersion)
                    done.add(uuid)
            for uuid in indexes:
                if uuid not in done:
                    store._indexes.purgeIndex(txn, counter, uuid, toVersion)
                    done.add(uuid)

            if toVersion is None:
                store._values.purgeValue(txn, counter, uItem, uValue)
            done.add(uValue)

        if toVersion is None:
            store._items.purgeItem(txn, counter, uItem, version)


class DBItemUndo(object):

    VALUE_TYPES = DBValueReader.VALUE_TYPES + (Record.RECORD, Record.RECORD)

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

    def undoItem(self, txn, indexReader, indexSearcher):
        
        store = self.repository.store
        _items = store._items
        _values = store._values
        _refs = store._refs
        _lobs = store._lobs
        _indexes = store._indexes

        withSchema = (self.status & CItem.WITHSCHEMA) != 0
        isNew = (self.status & CItem.NEW) != 0
        uItem = self.uItem
        version = self.version

        record = DBItemPurger.VALUE_TYPES

        status, uValues = _items.findValues(None, version, uItem,
                                            self.hashes, True)

        for uValue in uValues:
            if uValue is not None:
                record = _values.c.loadValue(uItem, uValue, record)
                uAttr, vFlags, data, lobs, indexes = record.data
                        
                if withSchema:
                    offset = 1
                else:
                    offset = 0

                flags = data[offset]
                offset += 1

                if flags & DBItemWriter.VALUE:
                    if isNew:
                        for uLob in lobs:
                            _lobs.purgeLob(txn, uLob)
                    for uIndex in indexes:
                        _indexes.undoIndex(txn, uIndex, version)
            
                elif flags & DBItemWriter.REF:
                    if flags & DBItemWriter.LIST:
                        uRefs = data[offset]
                        _refs.undoRefs(txn, uRefs, version)
                    elif flags & DBItemWriter.DICT:
                        if withSchema:
                            offset += 1
                        count = data[offset]
                        offset  += 1
                        for i in xrange(count):
                            uRefs = data[offset + 1]
                            offset += 2
                            _refs.undoRefs(txn, uRefs, version)
                    if flags & (DBItemWriter.LIST | DBItemWriter.SET):
                        for uIndex in indexes:
                            _indexes.undoIndex(txn, uIndex, version)
    
                _values.purgeValue(txn, None, uItem, uValue)
        
        _refs.undoRefs(txn, uItem, version) # children
        store._index.undoDocuments(indexSearcher, indexReader, uItem, version)

        _items.purgeItem(txn, None, uItem, version)
