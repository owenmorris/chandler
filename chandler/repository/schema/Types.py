
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import mx.DateTime
import repository.util.UUID
import repository.util.Path
import repository.item.PersistentCollections

from repository.item.Item import Item
from repository.item.ItemHandler import ItemHandler
from repository.item.ItemRef import RefDict
from repository.item.PersistentCollections import PersistentList
from repository.item.PersistentCollections import PersistentDict
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

        matches = [item for item in self.getItemParent() if item.isItemOf(self) and item.recognizes(value)]
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
        implementationType = self.getImplementationType()
        if implementationType is not None:
            typeHandlers = ItemHandler.typeHandlers[self.getRepository()]
            typeHandlers[self.getImplementationType()] = self._uuid

    def getImplementationType(self):
        return self.implementationTypes['python']

    def handlerName(cls):
        return None

    def makeValue(cls, data):
        raise NotImplementedError, "Type.makeValue()"

    def makeString(cls, value):
        return str(value)

    def recognizes(self, value):
        return type(value) is self.getImplementationType()

    # override this to compare types of the same category, like
    # Integer, Long and Float or String and Symbol
    # in order of 'relevance' for findTypes
    def _compareTypes(self, other):
        return 0

    def isAlias(self):
        return False

    def typeXML(self, value, generator, withSchema):
        generator.characters(type(self).makeString(value))

    def unserialize(self, data):
        raise NotImplementedError, "Type.unserialize()"

    def startValue(self, itemHandler):
        pass

    def isValueReady(self, itemHandler):
        return True

    def getValue(self, itemHandler, data):
        return self.unserialize(data)

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)
    handlerName = classmethod(handlerName)


class String(Type):

    def getImplementationType(self):
        return unicode

    def handlerName(cls):
        return 'unicode'

    def makeValue(cls, data):
        return unicode(data)

    def makeString(cls, value):
        return unicode(value)

    def recognizes(self, value):
        return type(value) is unicode or type(value) is str

    def unserialize(self, data):
        return String.makeValue(data)

    def _compareTypes(self, other):
        return -1

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)
    handlerName = classmethod(handlerName)


class Symbol(Type):

    def getImplementationType(self):
        return str

    def handlerName(cls):
        return 'str'

    def makeValue(cls, data):
        return str(data)

    def unserialize(self, data):
        return Symbol.makeValue(data)

    def _compareTypes(self, other):
        return 1
    
    makeValue = classmethod(makeValue)
    handlerName = classmethod(handlerName)


class Integer(Type):

    def getImplementationType(self):
        return int
    
    def handlerName(cls):
        return 'int'

    def makeValue(cls, data):
        return int(data)

    def unserialize(self, data):
        return Integer.makeValue(data)

    def _compareTypes(self, other):
        return -1

    makeValue = classmethod(makeValue)
    handlerName = classmethod(handlerName)


class Long(Type):

    def getImplementationType(self):
        return long
    
    def handlerName(cls):
        return 'long'

    def makeValue(cls, data):
        return long(data)

    def unserialize(self, data):
        return Long.makeValue(data)

    def recognizes(self, value):
        return type(value) is long or type(value) is int

    def _compareTypes(self, other):
        if other._name == 'Integer':
            return 1
        if other._name == 'Float':
            return -1
        return 0

    makeValue = classmethod(makeValue)
    handlerName = classmethod(handlerName)


class Float(Type):

    def getImplementationType(self):
        return float
    
    def handlerName(cls):
        return 'float'
    
    def makeValue(cls, data):
        return float(data)

    def unserialize(self, data):
        return Float.makeValue(data)

    def recognizes(self, value):
        return (type(value) is float or
                type(value) is long or type(value) is int)

    def _compareTypes(self, other):
        return 1

    makeValue = classmethod(makeValue)
    handlerName = classmethod(handlerName)

    
class Complex(Type):

    def getImplementationType(self):
        return complex
    
    def handlerName(cls):
        return 'complex'

    def makeValue(cls, data):
        return complex(data)

    def unserialize(self, data):
        return Complex.makeValue(data)

    makeValue = classmethod(makeValue)
    handlerName = classmethod(handlerName)


class Boolean(Type):

    def getImplementationType(self):
        return bool
    
    def handlerName(cls):
        return 'bool'
    
    def makeValue(cls, data):
        return data != 'False'

    def unserialize(self, data):
        return Boolean.makeValue(data)

    makeValue = classmethod(makeValue)
    handlerName = classmethod(handlerName)


class UUID(Type):

    def handlerName(cls):
        return 'uuid'

    def makeValue(cls, data):
        return repository.util.UUID.UUID(data)

    def unserialize(self, data):
        return UUID.makeValue(data)

    def makeString(cls, value):
        return value.str64()

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)
    handlerName = classmethod(handlerName)


class SingleRef(Type):

    def handlerName(cls):
        return 'ref'
    
    def makeValue(cls, data):
        uuid = repository.util.UUID.UUID(data)
        return repository.item.PersistentCollections.SingleRef(uuid)

    def unserialize(self, data):
        return SingleRef.makeValue(data)

    makeValue = classmethod(makeValue)
    handlerName = classmethod(handlerName)


class Path(Type):

    def handlerName(cls):
        return 'path'

    def makeValue(cls, data):
        return repository.util.Path.Path(data)

    def unserialize(self, data):
        return Path.makeValue(data)

    makeValue = classmethod(makeValue)
    handlerName = classmethod(handlerName)


class NoneType(Type):

    def getImplementationType(self):
        return type(None)

    def handlerName(cls):
        return 'none'
    
    def makeValue(cls, data):
        return None

    def makeString(cls, value):
        return "None"

    def unserialize(self, data):
        return None
        
    def recognizes(self, value):
        return value is None

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)
    handlerName = classmethod(handlerName)


class Class(Type):

    def getImplementationType(self):
        return type

    def handlerName(cls):
        return 'class'
    
    def makeValue(cls, data):
        return ClassLoader.loadClass(data)

    def makeString(cls, value):
        return "%s.%s" %(value.__module__, value.__name__)

    def unserialize(self, data):
        return Class.makeValue(data)
        
    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)
    handlerName = classmethod(handlerName)


class Enumeration(Type):

    def getImplementationType(self):
        return type(self)

    def handlerName(cls):
        return 'str'
    
    def makeValue(cls, data):
        return data

    def makeString(cls, value):
        return value

    def recognizes(self, value):

        try:
            return self.values.index(value) >= 0
        except ValueError:
            return False

    def typeXML(self, value, generator, withSchema):

        try:
            number = self.values.index(value)
        except ValueError:
            raise ValueError, "%d not in %s enum" %(value, self._name)
            
        generator.characters(str(number))
    
    def unserialize(self, data):

        if data[0] >= '0' and data[0] <= '9':
            return self.values[int(data)]

        return data

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)
    handlerName = classmethod(handlerName)


class Struct(Type):

    def startValue(self, itemHandler):
        itemHandler.tagCounts.append(0)

    def isValueReady(self, itemHandler):
        return itemHandler.tagCounts[-1] == 0

    def typeXML(self, value, generator, withSchema):

        fields = self.getAttributeValue('fields', _attrDict=self._values,
                                        default=[])

        if fields:
            repository = self.getRepository()
            generator.startElement('fields', {})
            for field in fields:
                self._fieldXML(repository, value, field, generator)
            generator.endElement('fields')
        else:
            raise TypeError, 'Struct %s has no fields' %(self.getItemPath())
    
    def _fieldXML(self, repository, value, field, generator):

        fieldName = field['name']
        fieldValue = getattr(value, fieldName)

        attrs = { 'name': fieldName }
        typeHandler = ItemHandler.typeHandler(repository, fieldValue)

        typeName = typeHandler.handlerName()
        if typeName is not None:
            attrs['type'] = typeName
        else:
            attrs['typeid'] = typeHandler._uuid.str64()

        generator.startElement('field', attrs)
        generator.characters(ItemHandler.makeString(repository, fieldValue))
        generator.endElement('field')

    def fieldsStart(self, itemHandler, attrs):

        itemHandler.tagCounts[-1] += 1
        itemHandler.fields = {}

    def fieldsEnd(self, itemHandler, attrs):

        itemHandler.tagCounts[-1] -= 1

    def fieldEnd(self, itemHandler, attrs):

        name = attrs['name']

        if attrs.has_key('type'):
            value = itemHandler.makeValue(attrs['type'], itemHandler.data)
        else:
            typeHandler = itemHandler.repository[UUID(attrs['typeid'])]
            value = typeHandler.unserialize(itemHandler.data)

        itemHandler.fields[name] = value

    def getValue(self, itemHandler, data):

        implementationType = self.getImplementationType()
        fields = itemHandler.fields

        if fields is None:
            return implementationType(data)
        else:
            return implementationType(**fields)


class DateTime(Struct):

    def getImplementationType(self):
        return DateTime.implementationType

    def makeValue(cls, data):
        return mx.DateTime.ISO.ParseDateTime(data)
        
    def makeString(cls, value):
        return mx.DateTime.ISO.str(value)

    def unserialize(self, data):
        return DateTime.makeValue(data)

    def getValue(self, itemHandler, data):

        flds = itemHandler.fields
        if flds is None:
            return self.unserialize(data)
        else:
            itemHandler.fields = None
        
        return mx.DateTime.DateTime(flds['year'],
                                    flds['month'],
                                    flds['day'],
                                    flds['hour'],
                                    flds['minute'],
                                    flds['second'])

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)
    implementationType = type(mx.DateTime.now())


class DateTimeDelta(Struct):

    defaults = { 'day': 0.0, 'hour': 0.0, 'minute': 0.0, 'second': 0.0 }

    def getImplementationType(self):
        return DateTimeDelta.implementationType

    def makeValue(cls, data):
        return mx.DateTime.DateTimeDeltaFrom(str(data))
        
    def unserialize(self, data):
        return DateTimeDelta.makeValue(data)

    def _fieldXML(self, repository, value, field, generator):

        fieldName = field['name']
        default = DateTimeDelta.defaults[fieldName]
        fieldValue = getattr(value, fieldName, default)
        if default != fieldValue:
            super(DateTimeDelta, self)._fieldXML(repository, value, field,
                                                 generator)
          
    def getValue(self, itemHandler, data):

        flds = itemHandler.fields
        if flds is None:
            return self.unserialize(data)
        else:
            itemHandler.fields = None
        
        return mx.DateTime.DateTimeDeltaFrom(days=flds.get('day', 0.0),
                                             hours=flds.get('hour', 0.0),
                                             minutes=flds.get('minute', 0.0),
                                             seconds=flds.get('second', 0.0))

    makeValue = classmethod(makeValue)
    implementationType = type(mx.DateTime.DateTimeDelta(0))
    

class RelativeDateTime(Struct):

    defaults = { 'years': 0, 'months': 0, 'days': 0,
                 'year': None, 'month': None, 'day': None,
                 'hours': 0, 'minutes': 0, 'seconds': 0,
                 'hour': None, 'minute': None, 'second': None,
                 'weekday': None, 'weeks': 0 }

    def getImplementationType(self):
        return RelativeDateTime.implementationType

    def makeValue(cls, data):
        return mx.DateTime.RelativeDateTimeFrom(str(data))

    def unserialize(self, data):
        return RelativeDateTime.makeValue(data)

    def _fieldXML(self, repository, value, field, generator):

        fieldName = field['name']
        default = RelativeDateTime.defaults[fieldName]
        fieldValue = getattr(value, fieldName, default)
        if default != fieldValue:
            super(RelativeDateTime, self)._fieldXML(repository, value, field,
                                                    generator)
          
    def getValue(self, itemHandler, data):

        flds = itemHandler.fields
        if flds is None:
            return self.unserialize(data)
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

    makeValue = classmethod(makeValue)
    implementationType = type(mx.DateTime.RelativeDateTime())


class Collection(Type):

    def getValue(self, itemHandler, data):

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

    def handlerName(cls):

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

    def _empty(self):

        return PersistentDict(None, None)

    handlerName = classmethod(handlerName)


class List(Collection):

    def handlerName(cls):

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
    
    def _empty(self):

        return PersistentList(None, None)
    
    handlerName = classmethod(handlerName)
