
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import mx.DateTime
import repository.util.UUID
import repository.util.Path
import repository.util.SingleRef

from repository.item.Item import Item
from repository.item.ItemHandler import ItemHandler
from repository.item.ItemRef import RefDict
from repository.item.PersistentCollections import PersistentList
from repository.item.PersistentCollections import PersistentDict
from repository.item.Query import KindQuery
from repository.schema.Kind import Kind
from repository.util.ClassLoader import ClassLoader


class TypeKind(Kind):

    def _fillItem(self, name, parent, kind, **kwds):

        super(TypeKind, self)._fillItem(name, parent, kind, **kwds)

        typeHandlers = ItemHandler.typeHandlers[self.getRepository()]
        typeHandlers[None] = self._uuid

    def findTypes(self, value):
        """Return a list of types recognizing value.

        The list is sorted by order of 'relevance', a very subjective concept
        that is specific to the category of matching types.
        For example, Integer < Long < Float or String < Symbol."""

        query = KindQuery()
        matches = [i for i in query.run([self]) if i.recognizes(value)]
        if matches:
            matches.sort(lambda x, y: x._compareTypes(y))

        return matches


class Type(Item):

    def __init__(self, name, parent, kind):

        super(Type, self).__init__(name, parent, kind)
        self._status |= Item.SCHEMA
        
    def _fillItem(self, name, parent, kind, **kwds):

        super(Type, self)._fillItem(name, parent, kind, **kwds)

        self._status |= Item.SCHEMA
        self._registerTypeHandler(self.getImplementationType())

    def _registerTypeHandler(self, implementationType):
        
        if implementationType is not None:
            typeHandlers = ItemHandler.typeHandlers[self.getRepository()]
            if implementationType in typeHandlers:
                typeHandlers[implementationType].append(self._uuid)
            else:
                typeHandlers[implementationType] = [ self._uuid ]

    def getImplementationType(self):
        return self.implementationTypes['python']

    def handlerName(self):
        return None

    def makeValue(self, data):
        raise NotImplementedError, "Type.makeValue()"

    def makeString(self, value):
        return str(value)

    def recognizes(self, value):
        return type(value) is self.getImplementationType()

    def eval(self, value):
        return value

    # override this to compare types of the same category, like
    # Integer, Long and Float or String and Symbol
    # in order of 'relevance' for findTypes
    def _compareTypes(self, other):
        return 0

    def isAlias(self):
        return False

    def typeXML(self, value, generator, withSchema):
        generator.characters(self.makeString(value))

    def startValue(self, itemHandler):
        pass

    def isValueReady(self, itemHandler):
        return True

    def getParsedValue(self, itemHandler, data):
        return self.makeValue(data)

    NoneString = "__NONE__"


class String(Type):

    def _fillItem(self, name, parent, kind, **kwds):

        super(String, self)._fillItem(name, parent, kind, **kwds)
        self._registerTypeHandler(str)

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


class Symbol(Type):

    def getImplementationType(self):

        return str

    def handlerName(self):

        return 'str'

    def makeValue(self, data):

        return str(data)

    def _compareTypes(self, other):

        return 1

    def recognizes(self, value):

        if not (isinstance(value, str) or isinstance(value, unicode)):
            return False
        
        for char in value:
            if not (char == '_' or
                    char >= '0' and char <= '9' or
                    char >= 'A' and char <= 'Z' or
                    char >= 'a' and char <= 'z'):
                return False

        return True


class Integer(Type):

    def getImplementationType(self):
        return int
    
    def handlerName(self):
        return 'int'

    def makeValue(self, data):
        return int(data)

    def _compareTypes(self, other):
        return -1


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

    
class Complex(Type):

    def getImplementationType(self):
        return complex
    
    def handlerName(self):
        return 'complex'

    def makeValue(self, data):
        return complex(data[1:-1])


class Boolean(Type):

    def getImplementationType(self):
        return bool
    
    def handlerName(self):
        return 'bool'
    
    def makeValue(self, data):
        return data != 'False'


class UUID(Type):

    def handlerName(self):

        return 'uuid'

    def makeValue(self, data):

        if data == Type.NoneString:
            return None

        return repository.util.UUID.UUID(data)

    def makeString(self, value):

        if value is None:
            return Type.NoneString
        
        return value.str64()
    
    def recognizes(self, value):

        return value is None or type(value) is repository.util.UUID.UUID

    def eval(self, value):

        return self.getRepository()[value]

    def _compareTypes(self, other):

        if other._name == 'None':
            return 1
        elif self._name < other._name:
            return -1
        elif self._name > other._name:
            return 1

        return 0


class SingleRef(Type):

    def handlerName(self):

        return 'ref'
    
    def makeValue(self, data):

        if data == Type.NoneString:
            return None
        
        uuid = repository.util.UUID.UUID(data)
        return repository.util.SingleRef.SingleRef(uuid)

    def makeString(self, value):

        if value is None:
            return Type.NoneString
        
        return str(value)
    
    def recognizes(self, value):

        return (value is None or
                type(value) is repository.util.SingleRef.SingleRef)

    def eval(self, value):

        return self.getRepository()[value.itsUUID]

    def _compareTypes(self, other):

        if other._name == 'None':
            return 1
        elif self._name < other._name:
            return -1
        elif self._name > other._name:
            return 1

        return 0


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

        item = self.find(value)
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


class Class(Type):

    def getImplementationType(self):
        return type

    def handlerName(self):
        return 'class'
    
    def makeValue(self, data):
        return ClassLoader.loadClass(data)

    def makeString(self, value):
        return "%s.%s" %(value.__module__, value.__name__)
        

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
            return self.values.index(value) >= 0
        except ValueError:
            return False


class Struct(Type):

    def startValue(self, itemHandler):
        itemHandler.tagCounts.append(0)

    def isValueReady(self, itemHandler):
        return itemHandler.tagCounts[-1] == 0

    def typeXML(self, value, generator, withSchema):

        fields = self.getAttributeValue('fields', _attrDict=self._values,
                                        default={})

        if fields:
            repository = self.getRepository()
            generator.startElement('fields', {})
            for fieldName, field in fields.iteritems():
                self._fieldXML(repository, value, fieldName, field, generator)
            generator.endElement('fields')
        else:
            raise TypeError, 'Struct %s has no fields' %(self.itsPath)
    
    def _fieldXML(self, repository, value, fieldName, field, generator):

        fieldValue = getattr(value, fieldName, Item.Nil)

        if fieldValue is not Item.Nil:
            typeHandler = field.get('type', None)

            if typeHandler is None:
                typeHandler = ItemHandler.typeHandler(repository, fieldValue)

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
            typeHandler = itemHandler.repository[repository.util.UUID.UUID(attrs['typeid'])]
            value = typeHandler.makeValue(itemHandler.data)
        elif attrs.has_key('type'):
            value = itemHandler.makeValue(attrs['type'], itemHandler.data)
        else:
            value = itemHandler.data
            field = self.fields[name]
            typeHandler = field.get('type', None)
            if typeHandler is not None:
                value = typeHandler.makeValue(value)

        itemHandler.fields[name] = value

    def recognizes(self, value):

        if super(Struct, self).recognizes(value):
            for fieldName, field in self.fields.iteritems():
                typeHandler = field.get('type', None)
                if typeHandler is not None:
                    fieldValue = getattr(value, fieldName, Item.Nil)
                    if not (fieldValue is Item.Nil or
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
            fieldValue = getattr(value, fieldName, Item.Nil)
            if fieldValue is not Item.Nil:
                strings.append("%s:%s" %(fieldName, fieldValue))

        return ",".join(strings)
    

class DateTime(Struct):

    def getImplementationType(self):
        return DateTime.implementationType

    def makeValue(self, data):
        return mx.DateTime.ISO.ParseDateTime(data)
        
    def makeString(self, value):
        return mx.DateTime.ISO.str(value)

    def recognizes(self, value):
        return type(value) is self.getImplementationType()

    def getParsedValue(self, itemHandler, data):

        flds = itemHandler.fields
        if flds is None:
            return self.makeValue(data)
        else:
            itemHandler.fields = None
        
        return mx.DateTime.DateTime(flds['year'],
                                    flds['month'],
                                    flds['day'],
                                    flds['hour'],
                                    flds['minute'],
                                    flds['second'])

    implementationType = type(mx.DateTime.now())


class DateTimeDelta(Struct):

    defaults = { 'day': 0.0, 'hour': 0.0, 'minute': 0.0, 'second': 0.0 }

    def getImplementationType(self):
        return DateTimeDelta.implementationType

    def makeValue(self, data):
        return mx.DateTime.DateTimeDeltaFrom(str(data))
        
    def makeString(self, value):
        return str(value)

    def recognizes(self, value):
        return type(value) is self.getImplementationType()

    def _fieldXML(self, repository, value, fieldName, field, generator):

        default = DateTimeDelta.defaults[fieldName]
        fieldValue = getattr(value, fieldName, default)
        if default != fieldValue:
            super(DateTimeDelta, self)._fieldXML(repository, value,
                                                 fieldName, field, generator)
          
    def getParsedValue(self, itemHandler, data):

        flds = itemHandler.fields
        if flds is None:
            return self.makeValue(data)
        else:
            itemHandler.fields = None
        
        return mx.DateTime.DateTimeDeltaFrom(days=flds.get('day', 0.0),
                                             hours=flds.get('hour', 0.0),
                                             minutes=flds.get('minute', 0.0),
                                             seconds=flds.get('second', 0.0))

    implementationType = type(mx.DateTime.DateTimeDelta(0))
    

class RelativeDateTime(Struct):

    defaults = { 'years': 0, 'months': 0, 'days': 0,
                 'year': None, 'month': None, 'day': None,
                 'hours': 0, 'minutes': 0, 'seconds': 0,
                 'hour': None, 'minute': None, 'second': None,
                 'weekday': None, 'weeks': 0 }

    def getImplementationType(self):
        return RelativeDateTime.implementationType

    def makeValue(self, data):
        return mx.DateTime.RelativeDateTimeFrom(str(data))

    def makeString(self, value):
        return str(value)

    def recognizes(self, value):
        return type(value) is self.getImplementationType()

    def _fieldXML(self, repository, value, fieldName, field, generator):

        default = RelativeDateTime.defaults[fieldName]
        fieldValue = getattr(value, fieldName, default)
        if default != fieldValue:
            super(RelativeDateTime, self)._fieldXML(repository, value,
                                                    fieldName, field,
                                                    generator)
          
    def getParsedValue(self, itemHandler, data):

        flds = itemHandler.fields
        if flds is None:
            return self.makeValue(data)
        else:
            itemHandler.fields = None

        return mx.DateTime.RelativeDateTime(years=flds.get('years', 0),
                                            months=flds.get('months', 0),
                                            days=flds.get('days', 0),
                                            year=flds.get('year', None),
                                            month=flds.get('month', None),
                                            day=flds.get('day', None),
                                            hours=flds.get('hours', 0),
                                            minutes=flds.get('minutes', 0),
                                            seconds=flds.get('seconds', 0),
                                            hour=flds.get('hour', None),
                                            minute=flds.get('minute', None),
                                            second=flds.get('second', None),
                                            weekday=flds.get('weekday', None),
                                            weeks=flds.get('weeks', 0))

    implementationType = type(mx.DateTime.RelativeDateTime())


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


class Dictionary(Collection):

    def handlerName(self):

        return 'dict'

    def recognizes(self, value):

        return isinstance(value, dict)

    def typeXML(self, value, generator, withSchema):

        repository = self.getRepository()

        generator.startElement('values', {})
        for key, val in value._iteritems():
            ItemHandler.xmlValue(repository,
                                 key, val, 'value', None, 'single', None,
                                 generator, withSchema)
        generator.endElement('values')

    def makeValue(self, data):
        """Make a dict of string key/value pairs from comma separated pairs.

        The implementation is very cheap, using split, so spaces are part of
        the dict's elements and the strings cannot contain spaces or colons."""

        result = {}
        if data:
            for pair in data.split(','):
                key, value = pair.split(':')
                result[key] = value

        return result

    def makeString(self, value):

        return ",".join(["%s:%s" %(k, v) for k, v in value.iteritems()])

    def _empty(self):

        return PersistentDict(None, None, None)


class List(Collection):

    def handlerName(self):

        return 'list'

    def recognizes(self, value):

        return isinstance(value, list)

    def typeXML(self, value, generator, withSchema):

        repository = self.getRepository()

        generator.startElement('values', {})
        for val in value._itervalues():
            ItemHandler.xmlValue(repository,
                                 None, val, 'value', None, 'single', None,
                                 generator, withSchema)
        generator.endElement('values')

    def makeValue(self, data):
        """Make a list of strings from comma separated strings.

        The implementation is very cheap, using split, so spaces are part of
        the list's elements and the strings cannot contain spaces."""

        if data:
            return data.split(',')
        else:
            return []

    def makeString(self, value):

        return ",".join([str(v) for v in value])

    def _empty(self):

        return PersistentList(None, None, None)


class Lob(Type):

    def getParsedValue(self, itemHandler, data):

        value = itemHandler.value
        itemHandler.value = None
        itemHandler.tagCounts.pop()

        return value

    def startValue(self, itemHandler):

        itemHandler.tagCounts.append(0)
        itemHandler.value = self.getImplementationType()(self.getRepository())

    def isValueReady(self, itemHandler):

        return itemHandler.tagCounts[-1] == 0


class Text(Lob):

    def getImplementationType(self):

        return self.getRepository().getLobType('text')

    def makeValue(self, data,
                  encoding='utf-8', mimetype='text/plain', compression='bz2',
                  indexed=False):

        text = self.getImplementationType()(self.getRepository(),
                                            encoding, mimetype, indexed)
        if data:
            writer = text.getWriter(compression)
            writer.write(data)
            writer.close()

        return text
    
    def textStart(self, itemHandler, attrs):

        itemHandler.tagCounts[-1] += 1

    def textEnd(self, itemHandler, attrs):

        itemHandler.value._textEnd(itemHandler.data, attrs)
        itemHandler.tagCounts[-1] -= 1

    def typeXML(self, value, generator, withSchema):

        value._xmlValue(generator)

    def handlerName(self):

        return 'text'


class Binary(Lob):

    def getImplementationType(self):

        return self.getRepository().getLobType('binary')

    def makeValue(self, data, mimetype='text/plain', compression=None):

        binary = self.getImplementationType()(self.getRepository(), mimetype)
        if data:
            out = binary.getOutputStream(compression)
            out.write(data)
            out.close()

        return binary
    
    def binaryStart(self, itemHandler, attrs):

        itemHandler.tagCounts[-1] += 1

    def binaryEnd(self, itemHandler, attrs):

        itemHandler.value._binaryEnd(itemHandler.data, attrs)
        itemHandler.tagCounts[-1] -= 1

    def typeXML(self, value, generator, withSchema):

        value._xmlValue(generator)

    def handlerName(self):

        return 'binary'
