
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

    def getValue(self, itemHandler, data):
        return self.makeValue(data)

    handlerName = classmethod(handlerName)


class String(Type):

    def getImplementationType(self):
        return unicode

    def handlerName(cls):
        return 'unicode'

    def makeValue(self, data):
        return unicode(data)

    def makeString(self, value):
        return unicode(value)

    def recognizes(self, value):
        return type(value) is unicode or type(value) is str

    def _compareTypes(self, other):
        return -1

    handlerName = classmethod(handlerName)


class Symbol(Type):

    def getImplementationType(self):
        return str

    def handlerName(cls):
        return 'str'

    def makeValue(self, data):
        return str(data)

    def _compareTypes(self, other):
        return 1
    
    handlerName = classmethod(handlerName)


class Integer(Type):

    def getImplementationType(self):
        return int
    
    def handlerName(cls):
        return 'int'

    def makeValue(self, data):
        return int(data)

    def _compareTypes(self, other):
        return -1

    handlerName = classmethod(handlerName)


class Long(Type):

    def getImplementationType(self):
        return long
    
    def handlerName(cls):
        return 'long'

    def makeValue(self, data):
        return long(data)

    def recognizes(self, value):
        return type(value) is long or type(value) is int

    def _compareTypes(self, other):
        if other._name == 'Integer':
            return 1
        if other._name == 'Float':
            return -1
        return 0

    handlerName = classmethod(handlerName)


class Float(Type):

    def getImplementationType(self):
        return float
    
    def handlerName(cls):
        return 'float'
    
    def makeValue(self, data):
        return float(data)

    def recognizes(self, value):
        return (type(value) is float or
                type(value) is long or type(value) is int)

    def _compareTypes(self, other):
        return 1

    handlerName = classmethod(handlerName)

    
class Complex(Type):

    def getImplementationType(self):
        return complex
    
    def handlerName(cls):
        return 'complex'

    def makeValue(self, data):
        return complex(data)

    handlerName = classmethod(handlerName)


class Boolean(Type):

    def getImplementationType(self):
        return bool
    
    def handlerName(cls):
        return 'bool'
    
    def makeValue(self, data):
        return data != 'False'

    handlerName = classmethod(handlerName)


class UUID(Type):

    def handlerName(cls):
        return 'uuid'

    def makeValue(self, data):
        return repository.util.UUID.UUID(data)

    def makeString(self, value):
        return value.str64()

    handlerName = classmethod(handlerName)


class SingleRef(Type):

    def handlerName(cls):
        return 'ref'
    
    def makeValue(self, data):
        uuid = repository.util.UUID.UUID(data)
        return repository.item.PersistentCollections.SingleRef(uuid)

    def eval(self, value):
        return self.getRepository()[value]

    handlerName = classmethod(handlerName)


class Path(Type):

    def handlerName(cls):
        return 'path'

    def makeValue(self, data):
        return repository.util.Path.Path(data)

    def eval(self, value):
        item = self.find(value)
        if item is None:
            raise ValueError, 'Path %s evaluated to None' %(value)
        return item

    handlerName = classmethod(handlerName)


class NoneType(Type):

    def getImplementationType(self):
        return type(None)

    def handlerName(cls):
        return 'none'
    
    def makeValue(self, data):
        return None

    def makeString(self, value):
        return "None"

    def recognizes(self, value):
        return value is None

    handlerName = classmethod(handlerName)


class Class(Type):

    def getImplementationType(self):
        return type

    def handlerName(cls):
        return 'class'
    
    def makeValue(self, data):
        return ClassLoader.loadClass(data)

    def makeString(self, value):
        return "%s.%s" %(value.__module__, value.__name__)
        
    handlerName = classmethod(handlerName)


class Enumeration(Type):

    def getImplementationType(self):

        return type(self)

    def handlerName(cls):

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

    handlerName = classmethod(handlerName)


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
            raise TypeError, 'Struct %s has no fields' %(self.getItemPath())
    
    def _fieldXML(self, repository, value, fieldName, field, generator):

        fieldValue = getattr(value, fieldName)
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
                    if not typeHandler.recognizes(getattr(value, fieldName)):
                        return False
            return True

        return False

    def getValue(self, itemHandler, data):

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
            strings.append("%s:%s" %(fieldName, getattr(value, fieldName)))

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

    def getValue(self, itemHandler, data):

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
        
    def recognizes(self, value):
        return type(value) is self.getImplementationType()

    def _fieldXML(self, repository, value, fieldName, field, generator):

        default = DateTimeDelta.defaults[fieldName]
        fieldValue = getattr(value, fieldName, default)
        if default != fieldValue:
            super(DateTimeDelta, self)._fieldXML(repository, value,
                                                 fieldName, field, generator)
          
    def getValue(self, itemHandler, data):

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

    def recognizes(self, value):
        return type(value) is self.getImplementationType()

    def _fieldXML(self, repository, value, fieldName, field, generator):

        default = RelativeDateTime.defaults[fieldName]
        fieldValue = getattr(value, fieldName, default)
        if default != fieldValue:
            super(RelativeDateTime, self)._fieldXML(repository, value,
                                                    fieldName, field,
                                                    generator)
          
    def getValue(self, itemHandler, data):

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

    def makeValue(self, data):

        result = {}
        for pair in data.split(','):
            key, value = pair.split(':')
            result[key] = value

        return result

    def makeString(self, value):

        strings = []
        for k, v in self.value.iteritems():
            strings.append("%s:%s" %(k, v))

        return ",".join(strings)

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
    
    def makeValue(self, data):

        return data.split(',')

    def makeString(self, value):

        return ",".join([str(v) for v in value])

    def _empty(self):

        return PersistentList(None, None)
    
    handlerName = classmethod(handlerName)
