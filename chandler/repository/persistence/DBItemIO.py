
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from struct import pack, unpack
from cStringIO import StringIO

from chandlerdb.util.uuid import UUID, _hash
from chandlerdb.item.item import Nil
from repository.item.Item import Item
from repository.item.Values import Values, References, ItemValue
from repository.item.ItemIO import ItemWriter, ItemReader
from repository.item.PersistentCollections \
     import PersistentCollection, PersistentList, PersistentDict, PersistentSet
from repository.schema.TypeHandler import TypeHandler
from repository.persistence.RepositoryError \
     import LoadError, LoadValueError, MergeError
from repository.persistence.DBContainer import HashTuple


class DBItemWriter(ItemWriter):

    def __init__(self, store):

        super(DBItemWriter, self).__init__()

        self.store = store
        self.valueBuffer = StringIO()
        self.dataBuffer = StringIO()

    def writeItem(self, item, version):

        self.values = []

        if not (item.isNew() or item._version == 0):
            self.oldValues = self.store._items.getItemValues(item._version,
                                                             item._uuid)
        else:
            self.oldValues = None

        super(DBItemWriter, self).writeItem(item, version)
        self.store._items.saveItem(self.valueBuffer,
                                   item._uuid, version,
                                   self.uKind, item._status & Item.SAVEMASK,
                                   self.uParent, self.name,
                                   self.moduleName, self.className,
                                   self.values,
                                   item._values._getDirties(),
                                   item._references._getDirties())

        return 0

    def writeString(self, buffer, value):

        if isinstance(value, unicode):
            value = value.encode('utf-8')
            buffer.write(pack('>i', len(value)))
        else:
            buffer.write(pack('>i', -len(value)))
            
        buffer.write(value)

    def writeSymbol(self, buffer, value):

        if isinstance(value, unicode):
            value = value.encode('ascii')

        buffer.write(pack('>H', len(value)))
        buffer.write(value)

    def writeBoolean(self, buffer, value):

        if value:
            buffer.write('\1')
        else:
            buffer.write('\0')

    def writeInteger(self, buffer, value):

        buffer.write(pack('>i', value))

    def writeLong(self, buffer, value):
        
        buffer.write(pack('>q', value))
        
    def writeFloat(self, buffer, value):

        buffer.write(pack('>d', value))

    def writeUUID(self, buffer, value):

        buffer.write(value._uuid)

    def writeValue(self, buffer, item, value, withSchema, attrType):

        flags = DBItemWriter.SINGLE | DBItemWriter.VALUE
        attrType = self._type(buffer, flags, item, value, True,
                              withSchema, attrType)
        attrType.writeValue(self, buffer, item, value, withSchema)

    def writeList(self, buffer, item, value, withSchema, attrType):

        flags = DBItemWriter.LIST | DBItemWriter.VALUE
        attrType = self._type(buffer, flags, item, value, False,
                              withSchema, attrType)
        buffer.write(pack('>I', len(value)))
        for v in value:
            self.writeValue(buffer, item, v, withSchema, attrType)

    def writeSet(self, buffer, item, value, withSchema, attrType):

        flags = DBItemWriter.SET | DBItemWriter.VALUE
        attrType = self._type(buffer, flags, item, value, False,
                              withSchema, attrType)
        buffer.write(pack('>I', len(value)))
        for v in value:
            self.writeValue(buffer, item, v, withSchema, attrType)

    def writeDict(self, buffer, item, value, withSchema, attrType):

        flags = DBItemWriter.DICT | DBItemWriter.VALUE
        attrType = self._type(buffer, flags, item, value, False,
                              withSchema, attrType)
        buffer.write(pack('>I', len(value)))
        for k, v in value._iteritems():
            self.writeValue(buffer, item, k, False, None)
            self.writeValue(buffer, item, v, withSchema, attrType)

    def _kind(self, kind):

        if kind is None:
            self.uKind = DBItemWriter.KINDLESS
        else:
            self.uKind = kind._uuid

    def _parent(self, parent, isContainer):

        self.uParent = parent.itsUUID

    def _name(self, name):

        self.name = name

    def _className(self, moduleName, className):

        self.moduleName = moduleName
        self.className = className

    def _children(self, item, version, all):

        if item._children is not None:
            item._children._saveValues(version)

    def _acls(self, item, version, all):

        if item._status & Item.ADIRTY:
            store = self.store
            uuid = item._uuid
            for name, acl in item._acls.iteritems():
                store.saveACL(version, uuid, name, acl)

    def _values(self, item, version, withSchema, all):

        item._values._writeValues(self, version, withSchema, all)

    def _references(self, item, version, withSchema, all):

        item._references._writeValues(self, version, withSchema, all)

    def _value(self, item, name, value, version, flags, withSchema, attribute):

        uValue = UUID()
        self.values.append((name, uValue))

        if attribute is None:
            uAttr = DBItemWriter.KINDLESS
            attrCard = 'single'
            attrType = None
        else:
            uAttr = attribute._uuid
            attrCard = attribute.getAspect('cardinality', 'single')
            attrType = attribute.getAspect('type', None)
            
        buffer = self.dataBuffer
        buffer.truncate(0)
        buffer.seek(0)

        buffer.write(pack('>I', flags))
        if withSchema:
            self.writeSymbol(buffer, name)

        if attrCard == 'single':
            self.writeValue(buffer, item, value, withSchema, attrType)
        elif attrCard == 'list':
            self.writeList(buffer, item, value, withSchema, attrType)
        elif attrCard == 'set':
            self.writeSet(buffer, item, value, withSchema, attrType)
        elif attrCard == 'dict':
            self.writeDict(buffer, item, value, withSchema, attrType)

        self.store._values.saveValue(self.store.txn, item._uuid, version,
                                     uAttr, uValue, buffer.getvalue())

    def _unchangedValue(self, item, name):

        try:
            self.values.append((name, self.oldValues[_hash(name)]))
        except KeyError:
            raise AssertionError, "unchanged value for '%s' not found" %(name)

    def _type(self, buffer, flags, item, value, verify, withSchema, attrType):

        if attrType is not None and attrType.isAlias():
            if verify:
                aliasType = attrType.type(value)
                if aliasType is None:
                    raise TypeError, "%s does not alias type of value '%s' of type %s" %(attrType.itsPath, value, type(value))
                attrType = aliasType
                typeId = attrType._uuid
            else:
                typeId = None
            
        elif attrType is None:
            if verify:
                attrType = TypeHandler.typeHandler(item.itsView, value)
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
            buffer.write(chr(flags))
        else:
            flags |= DBItemWriter.TYPED
            buffer.write(chr(flags))
            buffer.write(typeId._uuid)

        return attrType

    def _ref(self, item, name, value, version, flags, withSchema, attribute):

        uValue = UUID()
        self.values.append((name, uValue))

        buffer = self.dataBuffer
        buffer.truncate(0)
        buffer.seek(0)

        buffer.write(pack('>I', flags))
        if withSchema:
            self.writeSymbol(buffer, name)

        if value is None:
            buffer.write(chr(DBItemWriter.NONE | DBItemWriter.REF))

        elif value._isUUID():
            if withSchema:
                raise AssertionError, 'withSchema is True'
            buffer.write(chr(DBItemWriter.SINGLE | DBItemWriter.REF))
            buffer.write(value._uuid)

        elif value._isItem():
            buffer.write(chr(DBItemWriter.SINGLE | DBItemWriter.REF))
            buffer.write(value._uuid._uuid)

        elif value._isRefList():
            flags = DBItemWriter.LIST | DBItemWriter.REF
            if withSchema:
                flags |= DBItemWriter.TYPED
            buffer.write(chr(flags))
            buffer.write(value.uuid._uuid)
            if withSchema:
                self.writeSymbol(buffer,
                                 item._kind.getOtherName(name, attribute._uuid))
            value._saveValues(version)
            if value._indexes:
                buffer.write(pack('>H', len(value._indexes)))
                for name, index in value._indexes.iteritems():
                    self.writeSymbol(buffer, name)
                    self.writeSymbol(buffer, index.getIndexType())
                    index._writeValue(self, buffer)
                    index._saveValues(version)
            else:
                buffer.write('\0\0')

        self.store._values.saveValue(self.store.txn, item._uuid, version,
                                     attribute._uuid, uValue, buffer.getvalue())

    TYPED    = 0x01
    VALUE    = 0x02
    REF      = 0x04
    SET      = 0x08
    SINGLE   = 0x10
    LIST     = 0x20
    DICT     = 0x40
    NONE     = 0x80
    
    KINDLESS = UUID('6d4df428-32a7-11d9-f701-000393db837c')


class DBItemReader(ItemReader):

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
        withSchema = (status & Item.CORESCHEMA) != 0
        isContainer = (status & Item.CONTAINER) != 0

        status &= Item.CORESCHEMA
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
                raise LoadError, (self.name or self.uItem,
                                  'Class changed from %s to %s' %(type(instance), cls))
            item = self.item = instance
            status |= item._status & item.PINNED
        else:
            item = self.item = cls.__new__(cls)

        item._fillItem(self.name, parent, kind,
                       uuid=self.uItem,
                       values=values,
                       references=references,
                       afterLoadHooks=afterLoadHooks,
                       version=self.version,
                       status=status,
                       update=False)

        if isContainer:
            item._children = view._createChildren(item, False)
            
        values._setItem(item)
        references._setItem(item)

        for name, value in values.iteritems():
            if isinstance(value, PersistentCollection):
                if withSchema:
                    # mixed collections not supported in core schema
                    companion = None
                else:
                    companion = kind.getAttribute(name).getAspect('companion',
                                                                  None)
                value._setOwner((item, name, companion))
            elif isinstance(value, ItemValue):
                value._setItem(item, name)

        if kind is not None:
            afterLoadHooks.append(lambda view: kind._setupClass(cls))

        if hasattr(cls, 'onItemLoad'):
            afterLoadHooks.append(item.onItemLoad)

        return item

    def readString(self, offset, data):
        offset, len = offset+4, unpack('>i', data[offset:offset+4])[0]
        if len >= 0:
            return offset+len, unicode(data[offset:offset+len], 'utf-8')
        else:
            return offset-len, data[offset:offset-len]

    def readSymbol(self, offset, data):
        offset, len, = offset+2, unpack('>H', data[offset:offset+2])[0]
        return offset+len, data[offset:offset+len]

    def readBoolean(self, offset, data):
        return offset+1, data[offset]=='\1'

    def readInteger(self, offset, data):
        return offset+4, unpack('>i', data[offset:offset+4])[0]

    def readLong(self, offset, data):
        return offset+8, unpack('>q', data[offset:offset+8])[0]
        
    def readFloat(self, offset, data):
        return offset+8, unpack('>d', data[offset:offset+8])[0]

    def readUUID(self, offset, data):
        return offset+16, UUID(data[offset:offset+16])

    def getUUID(self):
        return self.uItem

    def getVersion(self):
        return self.version

    def isDeleted(self):
        return (self.status & Item.DELETED) != 0

    def _kind(self, uuid, withSchema, view, afterLoadHooks):

        if uuid == DBItemWriter.KINDLESS:
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
            kind = view.find(self.uKind)
            if kind is None:
                raise LoadError, (self.name or self.uItem,
                                  "kind not found: %s" %(uuid))
            else:
                self.item._kind = kind

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
            parent = view.find(self.uParent)
            if parent is None:
                raise LoadError, (self.name or self.uItem,
                                  "parent not found: %s" %(self.uParent))
            else:
                self.item.move(parent)

    def _values(self, values, references, uValues, kind,
                withSchema, view, afterLoadHooks):

        store = self.store
        
        for uuid in uValues:
            attrId, data = store._values.loadValue(store.txn, uuid)
            valueFlags, = unpack('>I', data[0:4])
            if withSchema:
                attribute = None
                offset, name = self.readSymbol(4, data)
            else:
                attribute = view.find(attrId)
                if attribute is None:
                    raise LoadError, (self.name or self.uItem,
                                      "attribute not found: %s" %(attrId))
                offset, name = 4, attribute._name

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
                if valueFlags != 0:
                    d._setFlags(name, valueFlags)

    def _value(self, offset, data, kind, withSchema, attribute, view, name,
               afterLoadHooks):

        if withSchema:
            attrType = None
        else:
            attrType = attribute.getAspect('type', None)

        flags = ord(data[offset])

        if flags & DBItemWriter.SINGLE:
            return self.readValue(offset, data, withSchema, attrType,
                                  view, name)
        elif flags & DBItemWriter.LIST:
            return self.readList(offset, data, withSchema, attrType,
                                 view, name)
        elif flags & DBItemWriter.SET:
            return self.readSet(offset, data, withSchema, attrType,
                                view, name)
        elif flags & DBItemWriter.DICT:
            return self.readDict(offset, data, withSchema, attrType,
                                 view, name)
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
                otherName = kind.getOtherName(name, attribute._uuid)
            value = view._createRefList(None, name, otherName,
                                        True, False, False, uuid)
            count, = unpack('>H', data[offset:offset+2])
            offset += 2
            if count > 0:
                for i in xrange(count):
                    offset, indexName = self.readSymbol(offset, data)
                    offset, indexType = self.readSymbol(offset, data)
                    index = value.addIndex(indexName, indexType, loading=True)
                    offset = index._readValue(self, offset, data)

                afterLoadHooks.append(value._restoreIndexes)

            return offset, value

        else:
            raise LoadValueError, (self.name or self.uItem, name,
                                   "invalid cardinality: 0x%x" %(flags))

    def _type(self, offset, data, attrType, view, name):

        if ord(data[offset]) & DBItemWriter.TYPED:
            typeId = UUID(data[offset+1:offset+17])
            attrType = view.find(typeId)
            if attrType is None:
                raise LoadValueError, (self.name or self.uItem, name,
                                       "type not found: %s" %(typeId))

            return offset+17, attrType

        return offset+1, attrType

    def readValue(self, offset, data, withSchema, attrType, view, name):

        offset, attrType = self._type(offset, data, attrType, view, name)
        if attrType is None:
            raise LoadValueError, (self.name or self.uItem, name,
                                   "value type is None")
        
        return attrType.readValue(self, offset, data, withSchema, view, name)

    def readList(self, offset, data, withSchema, attrType, view, name):

        offset, attrType = self._type(offset, data, attrType, view, name)
        count, = unpack('>I', data[offset:offset+4])
        offset += 4

        value = PersistentList((None, None, None))
        for i in xrange(count):
            offset, v = self.readValue(offset, data, withSchema, attrType,
                                       view, name)
            value.append(v, False)

        return offset, value

    def readSet(self, offset, data, withSchema, attrType, view, name):

        offset, attrType = self._type(offset, data, attrType, view, name)
        count, = unpack('>I', data[offset:offset+4])
        offset += 4

        value = PersistentSet((None, None, None))
        for i in xrange(count):
            offset, v = self.readValue(offset, data, withSchema, attrType,
                                       view, name)
            value.add(v, False)

        return offset, value

    def readDict(self, offset, data, withSchema, attrType, view, name):

        offset, attrType = self._type(offset, data, attrType, view, name)
        count, = unpack('>I', data[offset:offset+4])
        offset += 4

        value = PersistentDict((None, None, None))
        for i in xrange(count):
            offset, k = self.readValue(offset, data, False, None,
                                       view, name)
            offset, v = self.readValue(offset, data, withSchema, attrType,
                                       view, name)
            value.__setitem__(k, v, False)

        return offset, value


class DBItemMergeReader(DBItemReader):

    def __init__(self, store, item, dirties, mergeFn, *args):

        super(DBItemMergeReader, self).__init__(store, item._uuid, *args)

        self.item = item
        self.dirties = dirties
        self.mergeFn = mergeFn

    def readItem(self, view, afterLoadHooks):

        status = self.status
        withSchema = (status & Item.CORESCHEMA) != 0
        kind = self._kind(self.uKind, withSchema, view, afterLoadHooks)

        self._values(self.item._values._prepareMerge(),
                     self.item._references._prepareMerge(),
                     self.uValues, kind, withSchema, view, afterLoadHooks)


class DBItemVMergeReader(DBItemMergeReader):

    def _value(self, offset, data, kind, withSchema, attribute, view, name,
               afterLoadHooks):

        value = Nil
        if name in self.dirties:
            offset, value = super(DBItemVMergeReader, self)._value(offset, data, kind, withSchema, attribute, view, name, afterLoadHooks)
            originalValues = self.item._values
            if originalValues._isDirty(name):
                originalValue = originalValues.get(name, Nil)
                if value == originalValue:
                    value = Nil
                elif self.mergeFn is not None:
                    value = self.mergeFn(MergeError.VALUE,
                                         self.item, name, value)
                else:
                    self._e_1_overlap(MergeError.VALUE, self.item, name)

        return offset, value
    
    def _ref(self, offset, data, kind, withSchema, attribute, view, name,
             afterLoadHooks):

        if name not in self.dirties:
            return offset, Nil

        flags = ord(data[offset])
        offset += 1

        if flags & DBItemWriter.LIST:
            return offset, Nil

        if flags & DBItemWriter.NONE:
            itemRef = None
        elif flags & DBItemWriter.SINGLE:
            offset, itemRef = self.readUUID(offset, data)
        else:
            raise LoadValueError, (self.name or self.uItem, name,
                                   "invalid cardinality: 0x%x" %(flags))

        origItem = self.item
        origRef = origItem._references.get(name, None)

        if self.item._references._isDirty(name):
            if origRef is not None:
                if origRef._isUUID():
                    if origRef == itemRef:
                        return offset, Nil
                    origRef = origItem._references._getRef(name, origRef)

                elif origRef._uuid == itemRef:
                    return offset, Nil

                self._e_2_overlap(MergeError.REF, self.item, name)

            elif itemRef is None:
                return offset, Nil

        if origRef is not None:
            if not (origRef._isItem() and origRef._uuid == itemRef or
                    origRef._isUUID() and origRef == itemRef):
                if origRef._isUUID():
                    origRef = origItem._references._getRef(name, origRef)
                origItem._references._unloadValue(name, origRef,
                                                  kind.getOtherName(name))

        return offset, itemRef

    def _e_1_overlap(self, code, item, name):
        
        raise MergeError, ('values', item, 'merging values failed because no mergeFn callback was passed to refresh(), overlapping attribute: %s' %(name), code)

    def _e_2_overlap(self, code, item, name):

        raise MergeError, ('values', item, 'merging refs is not yet implement\
ed, overlapping attribute: %s' %(name), MergeError.BUG)


class DBItemRMergeReader(DBItemMergeReader):

    def __init__(self, store, item, dirties, oldVersion, *args):

        super(DBItemRMergeReader, self).__init__(store, item, dirties,
                                                 None, *args)

        self.merged = []
        self.oldVersion = oldVersion
        self.oldDirties = item._references._getDirties()

    def readItem(self, view, afterLoadHooks):

        super(DBItemRMergeReader, self).readItem(view, afterLoadHooks)

        if self.merged:
            self.dirties = HashTuple(filter(lambda h: h not in self.merged,
                                            self.dirties))
        self.item._references._dirties = self.dirties

    def _value(self, offset, data, kind, withSchema, attribute, view, name,
               afterLoadHooks):

        return offset, Nil
    
    def _ref(self, offset, data, kind, withSchema, attribute, view, name,
             afterLoadHooks):

        if name in self.dirties:
            flags = ord(data[offset])

            if flags & DBItemWriter.LIST:
                if name in self.oldDirties:
                    value = self.item._references.get(name, None)
                    if value is not None and value._isRefList():
                        value._mergeChanges(self.oldVersion, self.version)
                        self.merged.append(self.dirties.hash(name))

                        return offset, Nil

                else:
                    offset, value = super(DBItemRMergeReader, self)._ref(offset, data, kind, withSchema, attribute, view, name, afterLoadHooks)
                    value._setItem(self.item)
    
                    return offset, value

        return offset, Nil
