#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


import re

from new import classobj
from struct import pack
from datetime import datetime, date, time, timedelta
from PyICU import ICUtzinfo, FloatingTZ

from chandlerdb.schema.c import CAttribute
from chandlerdb.util.c import _hash, _combine, Nil
from chandlerdb.item.c import isitem
from repository.item.Item import Item
from repository.item.PersistentCollections import \
     PersistentList, PersistentDict, PersistentTuple, PersistentSet
from repository.item.ItemHandler import ValueHandler
from repository.schema.Kind import Kind
from repository.schema.TypeHandler import TypeHandler

from chandlerdb.util.c import UUID as UUIDType
from chandlerdb.util.c import SingleRef as SingleRefType
from repository.util.Path import Path as PathType
from repository.util.URL import URL as URLType
from repository.item.Sets import AbstractSet as AbstractSetType


class TypeKind(Kind):

    def onItemLoad(self, view):

        try:
            TypeHandler.typeHandlers[view][None] = self
        except KeyError:
            TypeHandler.typeHandlers[view] = { None: self }

    def _collectTypes(self, view):  # run when loading core schema pack

        self.types = [item for item in view.dirtyItems()
                      if item.isItemOf(self)]

    def onItemCopy(self, view, orig):

        try:
            TypeHandler.typeHandlers[view][None] = self
        except KeyError:
            TypeHandler.typeHandlers[view] = { None: self }

    def onItemImport(self, view):

        if view is not self.itsView:
            try:
                del TypeHandler.typeHandlers[self.itsView][None]
            except KeyError:
                pass

            try:
                TypeHandler.typeHandlers[view][None] = self
            except KeyError:
                TypeHandler.typeHandlers[view] = { None: self }

    def onViewClear(self, view):

        TypeHandler.clear(view)

    def findTypes(self, value):
        """
        Return a list of types recognizing value.

        The list is sorted by order of 'relevance', a very subjective concept
        that is specific to the category of matching types.
        For example, Integer < Long < Float or String < Symbol.
        """

        matches = [type for type in self.types if type.recognizes(value)]
        if matches:
            matches.sort(lambda x, y: x._compareTypes(y))

        return matches


class Type(Item):

    def __init__(self, *args, **kw):

        super(Type, self).__init__(*args, **kw)

        self._status |= Item.SCHEMA | Item.PINNED
        TypeHandler.typeHandlers[self.itsView][None].types.append(self)
        
    def _fillItem(self, *args):

        super(Type, self)._fillItem(*args)
        self._status |= Item.SCHEMA | Item.PINNED

    def _registerTypeHandler(self, implementationType, view):

        if implementationType is not None:
            try:
                typeHandlers = TypeHandler.typeHandlers[view]
            except KeyError:
                typeHandlers = TypeHandler.typeHandlers[view] = {}

            if implementationType in typeHandlers:
                typeHandlers[implementationType].append(self)
            else:
                typeHandlers[implementationType] = [ self ]

    def _unregisterTypeHandler(self, implementationType, view):

        if implementationType is not None:
            try:
                TypeHandler.typeHandlers[view][implementationType].remove(self)
            except KeyError:
                return
            except ValueError:
                return

    def onItemLoad(self, view):
        self._registerTypeHandler(self.getImplementationType(), view)

    def onItemUnload(self, view, clean):
        self._unregisterTypeHandler(self.getImplementationType(), view)

    def onItemDelete(self, view, deferred):
        self._unregisterTypeHandler(self.getImplementationType(), view)

    def onItemCopy(self, view, orig):
        self._registerTypeHandler(self.getImplementationType(), view)

    def onItemImport(self, view):
        if view is not self.itsView:
            implementationType = self.getImplementationType()
            self._unregisterTypeHandler(implementationType, self.itsView)
            self._registerTypeHandler(implementationType, view)

    def getImplementationType(self):
        return self.getAttributeValue('implementationTypes',
                                      self._values)['python']

    def handlerName(self):
        return None

    def makeValue(self, data):
        raise NotImplementedError, "%s.makeValue()" %(type(self))

    def makeString(self, value):
        return str(value)

    def makeUnicode(self, value):
        return unicode(value)

    def recognizes(self, value):
        return type(value) is self.getImplementationType()

    def eval(self, value):
        return value

    def hashItem(self):
        """
        Compute a hash value from this type's schema.

        The hash value is computed from the type's path.

        @return: an integer
        """

        return _hash(str(self.itsPath))

    # override this to compare types of the same category, like
    # Integer, Long and Float or String and Symbol
    # in order of 'relevance' for findTypes
    def _compareTypes(self, other):
        return 0

    def isAlias(self):
        return False

    def getFlags(self):
        return 0

    def typeXML(self, value, generator, withSchema):
        generator.characters(self.makeString(value))

    def startValue(self, itemHandler):
        pass

    def isValueReady(self, itemHandler):
        return True

    def getParsedValue(self, itemHandler, data):
        return self.makeValue(data)

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):
        raise NotImplementedError, "%s._writeValue" %(type(self))

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        raise NotImplementedError, "%s._readValue" %(type(self))

    def hashValue(self, value):
        return _hash(self.makeString(value))

    NoneString = "__NONE__"


class StringType(Type):

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):
        return itemWriter.writeString(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        return itemReader.readString(offset, data)

    def typeXML(self, value, generator, withSchema):
        generator.cdataSection(value)

    def makeString(self, value):
        return value

    def _compareTypes(self, other):
        return -1


class String(StringType):

    def onItemLoad(self, view):

        super(String, self).onItemLoad(view)
        self._registerTypeHandler(str, view)

    def onItemUnload(self, view, clean):

        super(String, self).onItemUnload(view, clean)
        self._unregisterTypeHandler(str, view)

    def onItemDelete(self, view, deferred):

        super(String, self).onItemDelete(view, deferred)
        self._unregisterTypeHandler(str, view)

    def onItemCopy(self, view, orig):

        super(String, self).onItemCopy(view, orig)
        self._registerTypeHandler(str, view)

    def onItemImport(self, view):

        super(String, self).onItemImport(view)
        if view is not self.itsView:
            self._unregisterTypeHandler(str, self.itsView)
            self._registerTypeHandler(str, view)

    def getImplementationType(self):

        return unicode

    def handlerName(self):

        return 'unicode'

    def makeValue(self, data):

        if isinstance(data, unicode):
            return data

        return unicode(data, 'utf-8')

    def recognizes(self, value):

        return type(value) in (unicode, str)

    def hashValue(self, value):
        
        if type(value) is unicode:
            value = value.encode('utf-8')

        return _hash(value)


class BString(StringType):

    def recognizes(self, value):
        return type(value) is str

    def getImplementationType(self):
        return str

    def handlerName(self):
        return 'str'

    def hashValue(self, value):
        return _hash(value)

    def makeValue(self, data):
        return str(data)


class UString(StringType):

    def recognizes(self, value):
        t = type(value)
        return (t is unicode or
                t is str and len(value.decode('ascii', 'ignore')) == len(value))

    def getImplementationType(self):
        return unicode

    def handlerName(self):
        return 'unicode'

    def hashValue(self, value):
        return _hash(value.encode('utf-8'))

    def makeValue(self, data):
        return unicode(data)


class Symbol(BString):

    illegal = re.compile("[^_a-zA-Z0-9]")

    def _compareTypes(self, other):

        return 1

    def recognizes(self, value):

        if type(value) not in (str, unicode):
            return False

        return self.illegal.search(value) is None

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        return itemWriter.writeSymbol(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        
        return itemReader.readSymbol(offset, data)


class Importable(Symbol):

    illegal = re.compile("[^_.a-zA-Z0-9]")


class Integer(Type):

    def getImplementationType(self):
        return int
    
    def handlerName(self):
        return 'int'

    def makeValue(self, data):
        return int(data)

    def _compareTypes(self, other):
        return -1

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):
        return itemWriter.writeInteger(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        return itemReader.readInteger(offset, data)

    def hashValue(self, value):
        return _hash(pack('>l', value))


class Long(Type):

    def getImplementationType(self):
        return long
    
    def handlerName(self):
        return 'long'

    def makeValue(self, data):
        return long(data)

    def recognizes(self, value):
        return type(value) in (long, int)

    def _compareTypes(self, other):
        if other._name == 'Integer':
            return 1
        if other._name == 'Float':
            return -1
        return 0

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):
        return itemWriter.writeLong(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        return itemReader.readLong(offset, data)

    def hashValue(self, value):
        return _hash(pack('>q', value))


class Float(Type):

    def getImplementationType(self):
        return float
    
    def handlerName(self):
        return 'float'
    
    def makeValue(self, data):
        return float(data)

    def recognizes(self, value):
        return type(value) in (float, long, int)

    def _compareTypes(self, other):
        return 1

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):
        return itemWriter.writeFloat(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        return itemReader.readFloat(offset, data)

    def hashValue(self, value):
        return _hash(pack('>d', value))

    
class Complex(Type):

    def getImplementationType(self):
        return complex
    
    def handlerName(self):
        return 'complex'

    def makeValue(self, data):
        return complex(data[1:-1])

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        size = itemWriter.writeFloat(buffer, value.real)
        size += itemWriter.writeFloat(buffer, value.imag)

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        offset, real = itemReader.readFloat(offset, data)
        offset, imag = itemReader.readFloat(offset, data)

        return offset, complex(real, imag)

    def hashValue(self, value):

        return _combine(_hash(pack('>d', value.real)),
                        _hash(pack('>d', value.imag)))
        

class Boolean(Type):

    def getImplementationType(self):
        return bool
    
    def handlerName(self):
        return 'bool'
    
    def makeValue(self, data):

        if data in ('True', 'true'):
            return True
        elif data in ('False', 'false'):
            return False
        else:
            raise ValueError, "'%s' is not 'T|true' or 'F|false'" %(data)

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        return itemWriter.writeBoolean(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        return itemReader.readBoolean(offset, data)

    def hashValue(self, value):

        if value == True:
            return _hash('True')
        else:
            return _hash('False')


class UUID(Type):

    def handlerName(self):

        return 'uuid'

    def makeValue(self, data):

        if data == Type.NoneString:
            return None

        return UUIDType(data)

    def makeString(self, value):

        if value is None:
            return Type.NoneString
        
        return value.str64()
    
    def recognizes(self, value):

        return value is None or type(value) is UUIDType

    def eval(self, value):

        return self.itsView[value]

    def _compareTypes(self, other):

        if other._name == 'None':
            return 1
        elif self._name < other._name:
            return -1
        elif self._name > other._name:
            return 1

        return 0

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        if value is None:
            buffer.append('\0')
            return 1
        else:
            buffer.append('\1')
            buffer.append(value._uuid)
            return 17

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        if data[offset] == '\0':
            return offset+1, None
        
        return offset+17, UUIDType(data[offset+1:offset+17])

    def hashValue(self, value):

        if value is None:
            return 0

        return value._hash        


class SingleRef(Type):

    def handlerName(self):

        return 'ref'
    
    def makeValue(self, data):

        if data == Type.NoneString:
            return None
        
        uuid = UUIDType(data)
        return SingleRefType(uuid)

    def makeString(self, value):

        if value is None:
            return Type.NoneString
        
        return str(value)
    
    def recognizes(self, value):

        return (value is None or
                type(value) is SingleRefType or
                isitem(value))

    def eval(self, value):

        return self.itsView[value.itsUUID]

    def _compareTypes(self, other):

        if other._name == 'None':
            return 1
        elif self._name < other._name:
            return -1
        elif self._name > other._name:
            return 1

        return 0

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        if value is None:
            buffer.append('\0')
            return 1
        else:
            buffer.append('\1')
            buffer.append(value._uuid._uuid)
            return 17

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        if data[offset] == '\0':
            return offset+1, None
        
        uuid = UUIDType(data[offset+1:offset+17])
        return offset+17, SingleRefType(uuid)

    def getFlags(self):

        return CAttribute.PROCESS

    def hashValue(self, value):

        if value is None:
            return 0

        return _combine(_hash(str(self.itsPath)), value._uuid._hash)


class Path(Type):

    def handlerName(self):

        return 'path'

    def makeValue(self, data):

        if data == Type.NoneString:
            return None

        return PathType(data)

    def makeString(self, value):

        if value is None:
            return Type.NoneString
        
        return str(value)
    
    def recognizes(self, value):

        return value is None or type(value) is PathType

    def eval(self, value):

        item = self.findPath(value)
        if item is None:
            raise ValueError, 'Path %s evaluated to None' %(value)

        return item

    def _compareTypes(self, other):

        if other._name == 'None':
            return 1
        elif self._name < other._name:
            return -1
        elif self._name > other._name:
            return 1

        return 0

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        if value is None:
            buffer.append('\0')
            size = 1
        else:
            buffer.append('\1')
            size = 1 + itemWriter.writeString(buffer, str(value))

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        if data[offset] == '\0':
            return offset+1, None
        
        offset, string = itemReader.readString(offset+1, data)
        return offset, PathType(string)

    def hashValue(self, value):

        if value is None:
            return 0

        return _combine(_hash(str(self.itsPath)), _hash(str(value)))


class URL(Type):

    def handlerName(self):

        return 'url'

    def makeValue(self, data):

        if data == Type.NoneString:
            return None

        return URLType(data)

    def makeString(self, value):

        if value is None:
            return Type.NoneString
        
        return str(value)
    
    def recognizes(self, value):

        return value is None or type(value) is URLType

    def _compareTypes(self, other):

        return -1

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        if value is None:
            buffer.append('\0')
            size = 1
        else:
            buffer.append('\1')
            size = 1 + itemWriter.writeString(buffer, str(value))

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        if data[offset] == '\0':
            return offset+1, None
        
        offset, string = itemReader.readString(offset+1, data)
        return offset, URLType(string)

    def hashValue(self, value):

        if value is None:
            return 0

        return _combine(_hash(str(self.itsPath)), _hash(str(value)))


class NoneType(Type):

    def getImplementationType(self):
        return type(None)

    def handlerName(self):
        return 'none'
    
    def makeValue(self, data):
        return None

    def makeString(self, value):
        return Type.NoneString

    def recognizes(self, value):
        return value is None

    def _compareTypes(self, other):
        return -1

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):
        buffer.append('\0')
        return 1

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        if data[offset] != '\0':
            raise AssertionError, 'invalid byte for None'
        return offset+1, None

    def hashValue(self, value):
        return 0


class Class(Type):

    def getImplementationType(self):
        return type

    def recognizes(self, value):
        return isinstance(value, (type, classobj))

    def handlerName(self):
        return 'class'
    
    def makeValue(self, data):
        return self.itsView.classLoader.loadClass(data)

    def makeString(self, value):
        return '.'.join((value.__module__, value.__name__))

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):
        return itemWriter.writeString(buffer, self.makeString(value))

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        offset, string = itemReader.readString(offset, data)
        return offset, view.classLoader.loadClass(string)

    def hashValue(self, value):
        return _combine(_hash(str(self.itsPath)), _hash(self.makeString(value)))
        

class Enumeration(Type):

    def getImplementationType(self):
        return str

    def handlerName(self):
        return 'str'
    
    def makeValue(self, data):
        return data

    def makeString(self, value):
        return value

    def recognizes(self, value):
        return value in self.values

    # it is assumed that an enum is not having more than 256 values
    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        if withSchema:
            return itemWriter.writeString(buffer, value)
        else:
            buffer.append(chr(self.values.index(value)))
            return 1

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        
        if withSchema:
            return itemReader.readString(offset, data)

        return offset+1, self._values['values'][ord(data[offset])]

    def hashValue(self, value):
        return _combine(_hash(str(self.itsPath)), _hash(self.makeString(value)))


class EnumValue(object):

    def __init__(self, enumName, name, value):

        self.enumName = enumName
        self.name = name
        self.value = value

    def __repr__(self):

        return "%s.%s" %(self.enumName, self.name)

    def __str__(self):

        return self.name

    def __eq__(self, other):

        if isinstance(other, EnumValue):
            return self.value == other.value

        return self.value == other

    def __ne__(self, other):

        if isinstance(other, EnumValue):
            return self.value != other.value

        return self.value != other

    def __le__(self, other):

        if isinstance(other, EnumValue):
            return self.value <= other.value

        return self.value <= other

    def __lt__(self, other):

        if isinstance(other, EnumValue):
            return self.value < other.value

        return self.value < other

    def __ge__(self, other):

        if isinstance(other, EnumValue):
            return self.value >= other.value

        return self.value >= other

    def __gt__(self, other):

        if isinstance(other, EnumValue):
            return self.value > other.value

        return self.value > other


class ConstantEnumeration(Enumeration):

    def _fillItem(self, *args):
        super(ConstantEnumeration, self)._fillItem(*args)
        if 'values' in self._values:
            self._afterValuesChange('set', 'values')

    def getImplementationType(self):
        return EnumValue

    def handlerName(self):
        return 'str'
    
    def recognizes(self, value):
        return value in self.constants

    def makeValue(self, data):
        for value in self.constants:
            if data == str(value):
                return value
        raise ValueError, data

    def makeString(self, value):
        return str(value)

    # it is assumed that an enum is not having more than 256 values
    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        if withSchema:
            return itemWriter.writeString(buffer, str(value))
        else:
            buffer.append(chr(self.constants.index(value)))
            return 1

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        
        if withSchema:
            return self.makeValue(itemReader.readString(offset, data))

        return offset+1, self.constants[ord(data[offset])]

    def _afterValuesChange(self, op, name):

        if op == 'set':
            self.constants = [EnumValue(self.itsName, name, value)
                              for name, value in self._values['values']]
        elif op == 'remove':
            del self.constants


class Struct(Type):

    def getDefaultValue(self, fieldName):
        return Nil

    def getFieldValue(self, value, fieldName, default):
        return getattr(value, fieldName, default)

    def startValue(self, itemHandler):
        itemHandler.tagCounts.append(0)

    def isValueReady(self, itemHandler):
        return itemHandler.tagCounts[-1] == 0

    def typeXML(self, value, generator, withSchema):

        fields = getattr(self, 'fields', None)
        if fields:
            repository = self.itsView
            generator.startElement('fields', {})
            for fieldName, field in fields.iteritems():
                self._fieldXML(repository, value, fieldName, field, generator)
            generator.endElement('fields')
        else:
            raise TypeError, 'Struct %s has no fields' %(self.itsPath)
    
    def _fieldXML(self, repository, value, fieldName, field, generator):

        fieldValue = getattr(value, fieldName, Nil)

        if fieldValue is not Nil:
            typeHandler = field.get('type', None)

            if typeHandler is None:
                typeHandler = TypeHandler.typeHandler(repository, fieldValue)

            attrs = { 'name': fieldName, 'typeid': typeHandler._uuid.str64() }
            generator.startElement('field', attrs)
            generator.characters(typeHandler.makeString(fieldValue))
            generator.endElement('field')

    def fieldsStart(self, itemHandler, attrs):

        itemHandler.tagCounts[-1] += 1
        itemHandler.fields = {}

    def fieldsEnd(self, itemHandler, attrs):

        itemHandler.tagCounts[-1] -= 1

    def fieldEnd(self, itemHandler, attrs):

        name = attrs['name']

        if attrs.has_key('typeid'):
            typeHandler = itemHandler.repository[UUIDType(attrs['typeid'])]
            value = typeHandler.makeValue(itemHandler.data)
        elif attrs.has_key('typepath'):
            typeHandler = itemHandler.repository.findPath(attrs['typepath'])
            value = typeHandler.makeValue(itemHandler.data)
        elif attrs.has_key('type'):
            value = itemHandler.makeValue(attrs['type'], itemHandler.data)
        else:
            value = itemHandler.data
            field = self.getAttributeValue('fields', _attrDict=self._values)[name]
            typeHandler = field.get('type', None)
            if typeHandler is not None:
                try:
                    value = typeHandler.makeValue(value)
                except AttributeError:
                    raise AttributeError, (typeHandler, value, type(value))

        itemHandler.fields[name] = value

    def recognizes(self, value):

        if super(Struct, self).recognizes(value):
            for fieldName, field in self.fields.iteritems():
                typeHandler = field.get('type', None)
                if typeHandler is not None:
                    fieldValue = getattr(value, fieldName, Nil)
                    if not (fieldValue is Nil or
                            typeHandler.recognizes(fieldValue)):
                        return False
            return True

        return False

    def getParsedValue(self, itemHandler, data):

        fields = itemHandler.fields
        
        if fields is None:
            return self.makeValue(data)

        else:
            result = self.getImplementationType()()
            for fieldName, value in fields.iteritems():
                setattr(result, fieldName, value)

            return result

    def makeValue(self, data):

        result = self.getImplementationType()()
        if data:
            for pair in data.split(','):
                fieldName, value = pair.split(':')
                typeHandler = self.fields[fieldName].get('type', None)
                if typeHandler is not None:
                    value = typeHandler.makeValue(value)
                setattr(result, fieldName, value)

        return result

    def makeString(self, value):

        strings = []
        for fieldName, field in self.fields.iteritems():
            fieldValue = getattr(value, fieldName, Nil)
            if fieldValue is not Nil:
                strings.append("%s:%s" %(fieldName, fieldValue))

        return ",".join(strings)

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        size = 0

        fields = self.getAttributeValue('fields', self._values, None, None)
        if fields:
            for fieldName, field in fields.iteritems():
                default = self.getDefaultValue(fieldName) 
                fieldValue = self.getFieldValue(value, fieldName, default)
                if fieldValue == default:
                    continue
            
                fieldType = field.get('type', None)
                size += itemWriter.writeSymbol(buffer, fieldName)
                size += itemWriter.writeValue(buffer, item, version,
                                              fieldValue, withSchema, fieldType)

        size += itemWriter.writeSymbol(buffer, '')

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        fields = self.getAttributeValue('fields', self._values, None, None)
        value = self.getImplementationType()()

        while True:
            offset, fieldName = itemReader.readSymbol(offset, data)
            if fieldName != '':
                fieldType = fields[fieldName].get('type', None)
                offset, fieldValue = \
                    itemReader._readValue(offset, data,
                                          withSchema, fieldType,
                                          view, name, afterLoadHooks)
                setattr(value, fieldName, fieldValue)
            else:
                return offset, value

    def hashValue(self, value):

        view = self.itsView
        hash = _hash(str(self.itsPath))

        fields = self.getAttributeValue('fields', self._values, None, None)
        if fields:
            for fieldName, field in fields.iteritems():
                default = self.getDefaultValue(fieldName) 
                fieldValue = self.getFieldValue(value, fieldName, default)
                if fieldValue == default:
                    continue
            
                fieldType = field.get('type', None)
                hash = _combine(hash, _hash(fieldName))
                if fieldType is not None:
                    hash = _combine(hash, fieldType.hashValue(fieldValue))
                else:
                    hash = _combine(hash, TypeHandler.hashValue(view,
                                                                fieldValue))

        return hash


class DateStruct(Struct):

    def recognizes(self, value):
        return type(value) is self.getImplementationType()

    def getParsedValue(self, itemHandler, data):

        flds = itemHandler.fields
        if flds is None:
            return self.makeValue(data)
        else:
            itemHandler.fields = None
            return self._valueFromFields(flds)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        fields = self.getAttributeValue('fields', self._values, None, None)

        flds = {}
        while True:
            offset, fieldName = itemReader.readSymbol(offset, data)
            if fieldName != '':
                fieldType = fields[fieldName].get('type', None)
                offset, fieldValue = \
                    itemReader._readValue(offset, data,
                                          withSchema, fieldType,
                                          view, name, afterLoadHooks)
                flds[fieldName] = fieldValue
            else:
                break

        return offset, self._valueFromFields(flds)

    def parseSecond(self, second):

        values = second.split('.')
        count = len(values)
        
        if count < 1:
            raise ValueError, second

        ss = values[0]

        if count > 1:
            v1 = values[1]
            us = int(v1)
            for i in xrange(len(v1), 6):
                us *= 10
        else:
            us = 0

        return int(ss), us
    
    def writeTime(self, itemWriter, buffer, value):

        seconds = value.hour * 3600 + value.minute * 60 + value.second
        tzname = value.tzname()
        size = itemWriter.writeInteger(buffer, seconds)
        size += itemWriter.writeInteger(buffer, value.microsecond)

        if tzname is not None:
            buffer.append('\1')
            size += 1 + itemWriter.writeString(buffer, tzname)
        else:
            buffer.append('\0')
            size += 1

        return size

    def readTime(self, itemReader, offset, data):

        offset, seconds = itemReader.readInteger(offset, data)
        offset, microsecond = itemReader.readInteger(offset, data) 
        
        if data[offset] == '\1':
            offset, tzname = itemReader.readString(offset + 1, data)
            tz = ICUtzinfo.getInstance(tzname)
        else:
            offset += 1
            tz = None

        hour = seconds / 3600
        minute = (seconds % 3600) / 60
        second = seconds % 60

        return offset, time(hour, minute, second, microsecond, tz)


class DateTime(DateStruct):

    nvformat = "%d-%02d-%02d %d:%d:%d.%06d"
    tzformat = "%d-%02d-%02d %d:%d:%d.%06d %s"

    # bypass == optimization as it will return True with different timezones
    def getFlags(self):

        return CAttribute.PROCESS_SET

    def getImplementationType(self):

        return datetime

    def getFieldValue(self, value, fieldName, default):

        if fieldName == 'timezone':
            tz = value.tzinfo
            if tz is not None:
                return value.tzname()
            else:
                return default

        return super(DateTime, self).getFieldValue(value, fieldName, default)

    def makeString(self, value):
        
        if value.tzinfo is None:
            return DateTime.nvformat %(value.year, value.month, value.day,
                                       value.hour, value.minute, value.second,
                                       value.microsecond)
        else:
            return DateTime.tzformat %(value.year, value.month, value.day,
                                       value.hour, value.minute, value.second,
                                       value.microsecond, value.tzname())

    def makeValue(self, data):

        values = data.split(' ')
        count = len(values)

        if count < 2:
            raise ValueError, data

        if count >= 2:
            try:
                (yyyy, MM, dd) = values[0].split('-')
                (HH, mm, second) = values[1].split(':')
                tz = None
            except ValueError, e:
                e.args = (e.args[0], data)
                raise

        if count >= 3:
            tz = ICUtzinfo.getInstance(values[2])

        ss, us = self.parseSecond(second)

        return datetime(int(yyyy), int(MM), int(dd),
                        int(HH), int(mm), ss, us, tz)

    def _valueFromFields(self, flds):

        if 'timezone' in flds and flds['timezone'] is not None:
            tz = ICUtzinfo.getInstance(flds['timezone'])
        else:
            tz = None

        return datetime(flds['year'], flds['month'], flds['day'],
                        flds['hour'], flds['minute'], flds['second'],
                        flds['microsecond'], tz)

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        size = itemWriter.writeInteger(buffer, value.toordinal())
        size += self.writeTime(itemWriter, buffer, value)

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        offset, then = itemReader.readInteger(offset, data)
        offset, time = self.readTime(itemReader, offset, data)

        return offset, datetime.combine(date.fromordinal(then), time)


class DateTimeTZ(DateTime):

    def recognizes(self, value):
        return type(value) is datetime and value.tzinfo is not None

    def makeValue(self, data):

        values = data.split(' ')
        count = len(values)

        if count < 2:
            raise ValueError, data

        if count >= 2:
            try:
                (yyyy, MM, dd) = values[0].split('-')
                (HH, mm, second) = values[1].split(':')
            except ValueError, e:
                e.args = (e.args[0], data)
                raise

        if count >= 3:
            tz = ICUtzinfo.getInstance(values[2])
        else:
            tz = ICUtzinfo.floating

        ss, us = self.parseSecond(second)

        return datetime(int(yyyy), int(MM), int(dd),
                        int(HH), int(mm), ss, us, tz)


class Date(DateStruct):

    format = "%d-%02d-%02d"

    def getImplementationType(self):

        return date

    def makeString(self, value):
        
        return Date.format %(value.year, value.month, value.day),

    def makeValue(self, data):

        try:
            yyyy, MM, dd = data.split('-')
        except ValueError:
            raise ValueError, data

        return date(int(yyyy), int(MM), int(dd))

    def _valueFromFields(self, flds):

        return date(flds['year'], flds['month'], flds['day'])

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        return itemWriter.writeInteger(buffer, value.toordinal())

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        offset, then = itemReader.readInteger(offset, data)
        return offset, date.fromordinal(then)


class Time(DateStruct):

    nvformat = "%d:%d:%d.%06d"
    tzformat = "%d:%d:%d.%06d %s"

    # bypass == optimization as it will return True with different timezones
    def getFlags(self):

        return CAttribute.PROCESS_SET

    def getImplementationType(self):

        return time

    def getFieldValue(self, value, fieldName, default):

        if fieldName == 'timezone':
            tz = value.tzinfo
            if tz is not None:
                return value.tzname()
            else:
                return default

        return super(Time, self).getFieldValue(value, fieldName, default)

    def makeString(self, value):
        
        if value.tzinfo is None:
            return Time.nvformat %(value.hour, value.minute, value.second,
                                   value.microsecond)
        else:
            return Time.tzformat %(value.hour, value.minute, value.second,
                                   value.microsecond, value.tzname())

    def makeValue(self, data):

        values = data.split(' ')
        count = len(values)

        if count < 1:
            raise ValueError, data

        if count >= 1:
            (HH, mm, second) = values[0].split(':')
            tz = None

        if count >= 2:
            tz = ICUtzinfo.getInstance(values[1])

        ss, us = self.parseSecond(second)

        return time(int(HH), int(mm), ss, us, tz)

    def _valueFromFields(self, flds):

        if 'timezone' in flds:
            tz = ICUtzinfo.getInstance(flds['timezone'])
        else:
            tz = None

        return time(flds['hour'], flds['minute'], flds['second'],
                    flds['microsecond'], tz)

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        return self.writeTime(itemWriter, buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        return self.readTime(itemReader, offset, data)


class TimeTZ(Time):

    def recognizes(self, value):
        return type(value) is time and value.tzinfo is not None

    def makeValue(self, data):

        values = data.split(' ')
        count = len(values)

        if count < 1:
            raise ValueError, data

        if count >= 1:
            (HH, mm, second) = values[0].split(':')

        if count >= 2:
            tz = ICUtzinfo.getInstance(values[1])
        else:
            tz = ICUtzinfo.floating

        ss, us = self.parseSecond(second)

        return time(int(HH), int(mm), ss, us, tz)


class TimeDelta(DateStruct):

    defaults = { 'days': 0, 'seconds': 0, 'microseconds': 0 }
    format = "%d+%d.%06d"
    strFormat = "%d days, %d:%02d:%02d.%06d"

    def getDefaultValue(self, fieldName):
        return TimeDelta.defaults[fieldName]

    def getImplementationType(self):
        return timedelta

    def makeString(self, value):
        return TimeDelta.format %(value.days, value.seconds, value.microseconds)

    def makeValue(self, data):

        try:
            if ':' in data:
                values = data.split(' ')
                if len(values) >= 3:
                    dd = int(values[0])
                    time = values[2]
                else:
                    dd = 0
                    time = values[0]

                hh, mm, seconds = time.split(':')
                ss, us = self.parseSecond(seconds)

                return timedelta(days=dd, hours=int(hh), minutes=int(mm),
                                 seconds=ss, microseconds=us)

            dd, seconds = data.split('+')
            ss, us = self.parseSecond(seconds)

            return timedelta(int(dd), ss, us)
        
        except ValueError:
            raise ValueError, data

    def _fieldXML(self, repository, value, fieldName, field, generator):

        default = self.getDefaultValue(fieldName)
        fieldValue = self.getFieldValue(value, fieldName, default)
        if default != fieldValue:
            super(TimeDelta, self)._fieldXML(repository, value,
                                             fieldName, field, generator)

    def _valueFromFields(self, flds):

        return timedelta(flds.get('days', 0),
                         flds.get('seconds', 0),
                         flds.get('microseconds', 0))

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        size = itemWriter.writeInteger(buffer, value.days)
        size += itemWriter.writeInteger(buffer, value.seconds)
        size += itemWriter.writeInteger(buffer, value.microseconds)

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        
        offset, days = itemReader.readInteger(offset, data)
        offset, seconds = itemReader.readInteger(offset, data)
        offset, microseconds = itemReader.readInteger(offset, data)

        return offset, timedelta(days, seconds, microseconds)


class TimeZone(Type):

    def getImplementationType(self):

        return ICUtzinfo

    def handlerName(self):

        return 'tzinfo'

    def makeValue(self, data):

        if data == Type.NoneString:
            return None
        
        return ICUtzinfo.getInstance(data)

    def makeString(self, value):

        if value is None:
            return Type.NoneString
        
        return str(value)
    
    def recognizes(self, value):

        return value is None or type(value) in (ICUtzinfo, FloatingTZ)

    def _compareTypes(self, other):

        return 0

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        if value is None:
            buffer.append('\0')
            size = 1
        else:
            buffer.append('\1')
            size = 1 + itemWriter.writeString(buffer, str(value))

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        if data[offset] == '\0':
            return offset+1, None
        
        offset, string = itemReader.readString(offset+1, data)
        return offset, ICUtzinfo.getInstance(string)

    def hashValue(self, value):

        if value is None:
            return 0

        return _hash(str(value))


class Collection(Type):

    def getFlags(self):

        return CAttribute.PROCESS_SET

    def getParsedValue(self, itemHandler, data):

        itemHandler.tagCounts.pop()
        itemHandler.attributes.pop()
        return itemHandler.collections.pop()

    def startValue(self, itemHandler):

        itemHandler.tagCounts.append(0)
        itemHandler.attributes.append(None)
        itemHandler.collections.append(self._empty())

    def isValueReady(self, itemHandler):

        return itemHandler.tagCounts[-1] == 0

    def valuesStart(self, itemHandler, attrs):

        itemHandler.tagCounts[-1] += 1

    def valuesEnd(self, itemHandler, attrs):

        itemHandler.tagCounts[-1] -= 1

    def valueStart(self, itemHandler, attrs):

        itemHandler.tagCounts[-1] += 1
        itemHandler.valueStart(itemHandler, attrs)

    def valueEnd(self, itemHandler, attrs, **kwds):

        itemHandler.tagCounts[-1] -= 1
        itemHandler.valueEnd(itemHandler, attrs, **kwds)

    def hashValue(self, value):

        view = self.itsView
        hash = _hash(str(self.itsPath))
        for v in value:
            hash = _combine(hash, TypeHandler.hashValue(view, v))

        return hash


class Dictionary(Collection):

    def handlerName(self):
        return 'dict'

    def recognizes(self, value):
        return isinstance(value, dict)

    def typeXML(self, value, generator, withSchema):

        repository = self.itsView

        generator.startElement('values', {})
        for key, val in value._iteritems():
            ValueHandler.xmlValue(repository,
                                  key, val, 'value', None, 'single', None, {},
                                  generator, withSchema)
        generator.endElement('values')

    def makeString(self, value):

        return ",".join(["%s:%s" %(k, v) for k, v in value.iteritems()])

    def makeValue(self, data):
        """
        Make a dict of string key/value pairs from comma separated pairs.

        The implementation is very cheap, using split, so spaces are part of
        the dict's elements and the strings cannot contain spaces or colons.
        """

        result = {}
        if data:
            for pair in data.split(','):
                key, value = pair.split(':')
                result[key] = value

        return result

    def makeCollection(self, values):

        result = {}

        count = len(values)
        if count % 2:
            raise ValueError, 'keys/values list is not of even length'

        for i in xrange(0, count, 2):
            result[values[i]] = values[i + 1]

        return result

    def _empty(self):

        return PersistentDict()

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        return itemWriter.writeDict(buffer, item, version,
                                    value, withSchema, None)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        return itemReader._readDict(offset, data, withSchema, None, view, name,
                                    afterLoadHooks)

    def hashValue(self, value):
        
        view = self.itsView
        hash = _hash(str(self.itsPath))
        for k, v in value.iteritems():
            hash = _combine(hash, TypeHandler.hashValue(view, k))
            hash = _combine(hash, TypeHandler.hashValue(view, v))

        return hash


class List(Collection):

    def handlerName(self):
        return 'list'

    def recognizes(self, value):
        return isinstance(value, list)

    def typeXML(self, value, generator, withSchema):

        repository = self.itsView

        generator.startElement('values', {})
        for val in value._itervalues():
            ValueHandler.xmlValue(repository,
                                  None, val, 'value', None, 'single', None, {},
                                  generator, withSchema)
        generator.endElement('values')

    def makeString(self, value):

        return ",".join([str(v) for v in value])

    def makeValue(self, data):
        """
        Make a list of strings from comma separated strings.

        The implementation is very cheap, using split, so spaces are part of
        the list's elements and the strings cannot contain spaces.
        """

        if data:
            return data.split(',')
        else:
            return []

    def makeCollection(self, values):

        return list(values)

    def _empty(self):

        return PersistentList()

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        return itemWriter.writeList(buffer, item, version,
                                    value, withSchema, None)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        return itemReader._readList(offset, data, withSchema, None, view, name,
                                    afterLoadHooks)


class Tuple(Collection):

    def handlerName(self):
        return 'tuple'

    def recognizes(self, value):
        return isinstance(value, tuple)

    def typeXML(self, value, generator, withSchema):

        repository = self.itsView

        generator.startElement('values', {})
        for val in value:
            ValueHandler.xmlValue(repository,
                                  None, val, 'value', None, 'single', None, {},
                                  generator, withSchema)
        generator.endElement('values')

    def makeString(self, value):

        return ",".join([str(v) for v in value])

    def makeValue(self, data):
        """
        Make a tuple of strings from comma separated strings.

        The implementation is very cheap, using split, so spaces are part of
        the tuple's elements and the strings cannot contain spaces.
        """

        if data:
            return tuple(data.split(','))
        else:
            return ()

    def makeCollection(self, values):

        return tuple(values)

    def _empty(self):

        class _tuple(list):
            def append(self, value, setDirty=True, ignore=None):
                super(_tuple, self).append(value)

        return _tuple()

    def getParsedValue(self, itemHandler, data):

        values = super(Tuple, self).getParsedValue(itemHandler, data)
        return PersistentTuple(None, None, values, False)

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        return itemWriter.writeList(buffer, item, version,
                                    value, withSchema, None)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        offset, value = itemReader._readList(offset, data, withSchema,
                                             None, view, name, afterLoadHooks)
        return offset, PersistentTuple(None, None, value, False)


class Set(Collection):

    def handlerName(self):
        return 'set'

    def recognizes(self, value):
        return isinstance(value, set)

    def typeXML(self, value, generator, withSchema):

        repository = self.itsView

        generator.startElement('values', {})
        for val in value._itervalues():
            ValueHandler.xmlValue(repository,
                                  None, val, 'value', None, 'single', None, {},
                                  generator, withSchema)
        generator.endElement('values')

    def makeString(self, value):

        return ",".join([str(v) for v in value])

    def makeValue(self, data):
        """
        Make a set of strings from comma separated strings.

        The implementation is very cheap, using split, so spaces are part of
        the list's elements and the strings cannot contain spaces.
        """

        if data:
            return data.split(',')
        else:
            return []

    def makeCollection(self, values):

        return set(values)

    def _empty(self):

        return PersistentSet()

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        return itemWriter.writeSet(buffer, item, version,
                                   value, withSchema, None)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        return itemReader._readSet(offset, data, withSchema, None, view, name,
                                   afterLoadHooks)


class AbstractSet(Type):

    def getImplementationType(self):

        return AbstractSetType

    def handlerName(self):

        return 'set'

    def makeValue(self, data):

        return AbstractSetType.makeValue(data)

    def makeString(self, value):
        
        return AbstractSetType.makeString(value)
    
    def recognizes(self, value):

        return isinstance(value, AbstractSetType)

    def _compareTypes(self, other):

        return 0

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        string = AbstractSetType.makeString(value)
        size = itemWriter.writeString(buffer, string)
        size += itemWriter.writeIndexes(buffer, item, version, value)

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        offset, string = itemReader.readString(offset, data)
        value = AbstractSetType.makeValue(string)
        value._setView(view)

        offset = itemReader._readIndexes(offset, data, value, afterLoadHooks)

        return offset, value

    def hashValue(self, value):

        if value is None:
            return 0

        return _hash(repr(value))


class Lob(Type):

    def getImplementationType(self):

        return self.itsView._getLobType()

    def getParsedValue(self, itemHandler, data):

        value = itemHandler.value
        itemHandler.value = None
        itemHandler.tagCounts.pop()

        return value

    def makeValue(self, data,
                  encoding=None, mimetype='text/plain', compression='bz2',
                  encryption=None, key=None, iv=None,
                  indexed=None, replace=False):

        if data and not encoding and type(data) is unicode:
            encoding = 'utf-8'

        lob = self.getImplementationType()(self.itsView,
                                           encoding, mimetype, indexed)

        if data:
            if encoding:
                out = lob.getWriter(compression, encryption, key, iv,
                                    False, replace)
            else:
                out = lob.getOutputStream(compression, encryption, key, iv)
            out.write(data)
            out.close()

        return lob
    
    def startValue(self, itemHandler):

        itemHandler.tagCounts.append(0)
        itemHandler.value = self.getImplementationType()(self.itsView)

    def isValueReady(self, itemHandler):

        return itemHandler.tagCounts[-1] == 0

    def typeXML(self, value, generator, withSchema):

        value._xmlValue(generator)

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        return value._writeValue(itemWriter, buffer, version, withSchema)

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        value = self.getImplementationType()(self.itsView)
        return value._readValue(itemReader, offset, data, withSchema)

    def lobStart(self, itemHandler, attrs):

        itemHandler.tagCounts[-1] += 1

    def lobEnd(self, itemHandler, attrs):

        itemHandler.value.load(itemHandler.data, attrs)
        itemHandler.tagCounts[-1] -= 1

    def handlerName(self):

        return 'lob'

    def hashValue(self, value):

        # for now
        return 0
