
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import chandlerdb.util.uuid
import repository.util.Path
import repository.util.SingleRef
import repository.util.URL
import repository.item.Sets as Sets

from new import classobj
from struct import pack
from datetime import datetime, date, time, timedelta
from PyICU import ICUtzinfo

from chandlerdb.schema.descriptor import CDescriptor
from chandlerdb.util.uuid import _hash, _combine
from chandlerdb.item.item import Nil
from repository.item.Item import Item
from repository.item.PersistentCollections import \
     PersistentList, PersistentDict, PersistentTuple, PersistentSet
from repository.item.ItemHandler import ValueHandler
from repository.item.Query import KindQuery
from repository.schema.Kind import Kind
from repository.schema.TypeHandler import TypeHandler
from repository.util.ClassLoader import ClassLoader


class TypeKind(Kind):

    def onItemLoad(self, view):

        try:
            TypeHandler.typeHandlers[view][None] = self
        except KeyError:
            TypeHandler.typeHandlers[view] = { None: self }

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

    def onViewClose(self, view):

        TypeHandler.clear(view)

    def findTypes(self, value):
        """Return a list of types recognizing value.

        The list is sorted by order of 'relevance', a very subjective concept
        that is specific to the category of matching types.
        For example, Integer < Long < Float or String < Symbol."""

        matches = [i for i in KindQuery().run([self]) if i.recognizes(value)]
        if matches:
            matches.sort(lambda x, y: x._compareTypes(y))

        return matches


class Type(Item):

    def __init__(self, name, parent, kind):

        super(Type, self).__init__(name, parent, kind)
        self._status |= Item.SCHEMA | Item.PINNED
        
    def _fillItem(self, name, parent, kind, **kwds):

        super(Type, self)._fillItem(name, parent, kind, **kwds)
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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):
        raise NotImplementedError, "%s._writeValue" %(type(self))

    def readValue(self, itemReader, offset, data, withSchema, view, name):
        raise NotImplementedError, "%s._readValue" %(type(self))

    def hashValue(self, value):
        return _hash(self.makeString(value))

    NoneString = "__NONE__"


class String(Type):

    def onItemLoad(self, view):

        super(String, self).onItemLoad(view)
        self._registerTypeHandler(str, view)

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

    def makeString(self, value):

        return value

    def recognizes(self, value):

        return type(value) in (unicode, str)

    def typeXML(self, value, generator, withSchema):

        generator.cdataSection(value)

    def _compareTypes(self, other):

        return -1

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        return itemWriter.writeString(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name):
        
        return itemReader.readString(offset, data)

    def hashValue(self, value):
        
        if type(value) is unicode:
            value = value.encode('utf-8')

        return _hash(value)


class Symbol(Type):

    def getImplementationType(self):

        return str

    def handlerName(self):

        return 'str'

    def makeValue(self, data):

        if type(data) is unicode:
            return data.encode('utf-8')

        return str(data)

    def _compareTypes(self, other):

        return 1

    def recognizes(self, value):

        if type(value) not in (str, unicode):
            return False
        
        for char in value:
            if not (char == '_' or
                    char >= '0' and char <= '9' or
                    char >= 'A' and char <= 'Z' or
                    char >= 'a' and char <= 'z'):
                return False

        return True

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        return itemWriter.writeSymbol(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name):
        
        return itemReader.readSymbol(offset, data)


class Integer(Type):

    def getImplementationType(self):
        return int
    
    def handlerName(self):
        return 'int'

    def makeValue(self, data):
        return int(data)

    def _compareTypes(self, other):
        return -1

    def writeValue(self, itemWriter, buffer, item, value, withSchema):
        return itemWriter.writeInteger(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name):
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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):
        return itemWriter.writeLong(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name):
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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):
        return itemWriter.writeFloat(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name):
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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        size = itemWriter.writeFloat(buffer, value.real)
        size += itemWriter.writeFloat(buffer, value.imag)

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name):

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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        return itemWriter.writeBoolean(buffer, value)

    def readValue(self, itemReader, offset, data, withSchema, view, name):

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

        return chandlerdb.util.uuid.UUID(data)

    def makeString(self, value):

        if value is None:
            return Type.NoneString
        
        return value.str64()
    
    def recognizes(self, value):

        return value is None or type(value) is chandlerdb.util.uuid.UUID

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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        if value is None:
            buffer.write('\0')
            return 1
        else:
            buffer.write('\1')
            buffer.write(value._uuid)
            return 17

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        if data[offset] == '\0':
            return offset+1, None
        
        return offset+17, chandlerdb.util.uuid.UUID(data[offset+1:offset+17])

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
        
        uuid = chandlerdb.util.uuid.UUID(data)
        return repository.util.SingleRef.SingleRef(uuid)

    def makeString(self, value):

        if value is None:
            return Type.NoneString
        
        return str(value)
    
    def recognizes(self, value):

        return (value is None or
                type(value) is repository.util.SingleRef.SingleRef or
                isinstance(value, Item))

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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        if value is None:
            buffer.write('\0')
            return 1
        else:
            buffer.write('\1')
            buffer.write(value._uuid._uuid)
            return 17

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        if data[offset] == '\0':
            return offset+1, None
        
        uuid = chandlerdb.util.uuid.UUID(data[offset+1:offset+17])
        return offset+17, repository.util.SingleRef.SingleRef(uuid)

    def getFlags(self):

        return CDescriptor.PROCESS

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

        return repository.util.Path.Path(data)

    def makeString(self, value):

        if value is None:
            return Type.NoneString
        
        return str(value)
    
    def recognizes(self, value):

        return value is None or type(value) is repository.util.Path.Path

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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        if value is None:
            buffer.write('\0')
            size = 1
        else:
            buffer.write('\1')
            size = 1 + itemWriter.writeString(buffer, str(value))

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        if data[offset] == '\0':
            return offset+1, None
        
        offset, string = itemReader.readString(offset+1, data)
        return offset, repository.util.Path.Path(string)

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

        return repository.util.URL.URL(data)

    def makeString(self, value):

        if value is None:
            return Type.NoneString
        
        return str(value)
    
    def recognizes(self, value):

        return value is None or type(value) is repository.util.URL.URL

    def _compareTypes(self, other):

        return -1

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        if value is None:
            buffer.write('\0')
            size = 1
        else:
            buffer.write('\1')
            size = 1 + itemWriter.writeString(buffer, str(value))

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        if data[offset] == '\0':
            return offset+1, None
        
        offset, string = itemReader.readString(offset+1, data)
        return offset, repository.util.URL.URL(string)

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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):
        buffer.write('\0')
        return 1

    def readValue(self, itemReader, offset, data, withSchema, view, name):
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
        return ClassLoader.loadClass(data)

    def makeString(self, value):
        return '.'.join((value.__module__, value.__name__))

    def writeValue(self, itemWriter, buffer, item, value, withSchema):
        return itemWriter.writeString(buffer, self.makeString(value))

    def readValue(self, itemReader, offset, data, withSchema, view, name):
        offset, string = itemReader.readString(offset, data)
        return offset, ClassLoader.loadClass(string)

    def hashValue(self, value):
        return _combine(_hash(str(self.itsPath)), _hash(self.makeString(value)))
        

class Enumeration(Type):

    def getImplementationType(self):
        return type(self)

    def handlerName(self):
        return 'str'
    
    def makeValue(self, data):
        return data

    def makeString(self, value):
        return value

    def recognizes(self, value):

        try:
            return self.getAttributeValue('values', _attrDict=self._values).index(value) >= 0
        except ValueError:
            return False

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        if withSchema:
            return itemWriter.writeString(buffer, value)
        else:
            return itemWriter.writeInteger(buffer, self.getAttributeValue('values', _attrDict=self._values).index(value))

    def readValue(self, itemReader, offset, data, withSchema, view, name):
        
        if withSchema:
            return itemReader.readString(offset, data)
        else:
            offset, integer = itemReader.readInteger(offset, data)
            return offset, self.getAttributeValue('values', _attrDict=self._values)[integer]

    def hashValue(self, value):
        return _combine(_hash(str(self.itsPath)), _hash(self.makeString(value)))


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

        fields = self.getAttributeValue('fields', self._values, None, None)
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
            typeHandler = itemHandler.repository[chandlerdb.util.uuid.UUID(attrs['typeid'])]
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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

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
                size += itemWriter.writeValue(buffer, item, fieldValue,
                                              withSchema, fieldType)

        size += itemWriter.writeSymbol(buffer, '')

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        fields = self.getAttributeValue('fields', self._values, None, None)
        value = self.getImplementationType()()

        while True:
            offset, fieldName = itemReader.readSymbol(offset, data)
            if fieldName != '':
                fieldType = fields[fieldName].get('type', None)
                offset, fieldValue = itemReader.readValue(offset, data,
                                                          withSchema, fieldType,
                                                          view, name)
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

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        fields = self.getAttributeValue('fields', self._values, None, None)

        flds = {}
        while True:
            offset, fieldName = itemReader.readSymbol(offset, data)
            if fieldName != '':
                fieldType = fields[fieldName].get('type', None)
                offset, fieldValue = itemReader.readValue(offset, data,
                                                          withSchema, fieldType,
                                                          view, name)
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
    

class DateTime(DateStruct):

    nvformat = "%d-%02d-%02d %d:%d:%d.%06d"
    tzformat = "%d-%02d-%02d %d:%d:%d.%06d %s"

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


class Time(DateStruct):

    nvformat = "%d:%d:%d.%06d"
    tzformat = "%d:%d:%d.%06d %s"

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

        return value is None or type(value) is ICUtzinfo

    def _compareTypes(self, other):

        return 0

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        if value is None:
            buffer.write('\0')
            size = 1
        else:
            buffer.write('\1')
            size = 1 + itemWriter.writeString(buffer, str(value))

        return size

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        if data[offset] == '\0':
            return offset+1, None
        
        offset, string = itemReader.readString(offset+1, data)
        return offset, ICUtzinfo.getInstance(string)

    def hashValue(self, value):

        if value is None:
            return 0

        return _hash(str(value))


class Collection(Type):

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

    def getFlags(self):
        return CDescriptor.DICT

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

        return PersistentDict((None, None, None))

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        return itemWriter.writeDict(buffer, item, value, withSchema, None)

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        return itemReader.readDict(offset, data, withSchema, None, view, name)

    def hashValue(self, value):
        
        view = self.itsView
        hash = _hash(str(self.itsPath))
        for k, v in value.iteritems():
            hash = _combine(hash, TypeHandler.hashValue(view, k))
            hash = _combine(hash, TypeHandler.hashValue(view, v))

        return hash


class List(Collection):

    def getFlags(self):
        return CDescriptor.LIST
    
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

        return PersistentList((None, None, None))

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        return itemWriter.writeList(buffer, item, value, withSchema, None)

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        return itemReader.readList(offset, data, withSchema, None, view, name)


class Tuple(Collection):

    def getFlags(self):
        return CDescriptor.LIST

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
            def append(self, value, setDirty=True):
                super(_tuple, self).append(value)

        return _tuple()

    def getParsedValue(self, itemHandler, data):

        values = super(Tuple, self).getParsedValue(itemHandler, data)
        return PersistentTuple((None, None, None), values, False)

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        return itemWriter.writeList(buffer, item, value, withSchema, None)

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        offset, value = itemReader.readList(offset, data, withSchema,
                                            None, view, name)
        return offset, PersistentTuple((None, None, None), value, False)


class Set(Collection):

    def getFlags(self):
        return CDescriptor.SET

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

        return PersistentSet((None, None, None))

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        return itemWriter.writeSet(buffer, item, value, withSchema, None)

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        return itemReader.readSet(offset, data, withSchema, None, view, name)


class AbstractSet(Type):

    def getImplementationType(self):

        return Sets.AbstractSet

    def handlerName(self):

        return 'set'

    def makeValue(self, data):

        return Sets.AbstractSet.makeValue(data)

    def makeString(self, value):

        return Sets.AbtractSet.makeString(value)
    
    def recognizes(self, value):

        return isinstance(value, Sets.AbstractSet)

    def _compareTypes(self, other):

        return 0

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        string = Sets.AbstractSet.makeString(value)
        return itemWriter.writeString(buffer, string)

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        offset, string = itemReader.readString(offset, data)
        return offset, Sets.AbstractSet.makeValue(string)

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
                  encryption=None, key=None, indexed=False, replace=False):

        if data and not encoding and type(data) is unicode:
            encoding = 'utf-8'

        lob = self.getImplementationType()(self.itsView,
                                           encoding, mimetype, indexed)

        if data:
            if encoding:
                out = lob.getWriter(compression, encryption, key,
                                    False, replace)
            else:
                out = lob.getOutputStream(compression, encryption, key)
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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        return value._writeValue(itemWriter, buffer, withSchema)

    def readValue(self, itemReader, offset, data, withSchema, view, name):

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
