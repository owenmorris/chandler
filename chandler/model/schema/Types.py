
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import mx.DateTime

from model.item.Item import Item
from model.item.Item import ItemHandler
from model.item.ItemRef import RefDict
from Kind import Kind


class Type(Item):

    def makeValue(cls, data):
        raise NotImplementedError, "Type.makeValue()"

    def makeString(cls, value):
        return str(value)

    def handlerName(cls):
        return "%s.%s" %(cls.__module__, cls.__name__)

    def typeXML(self, value, generator):

        fields = self.Fields
        if fields:
            generator.startElement('fields', {})
            for field in fields:
                self._fieldXML(value, field, generator)
            generator.endElement('fields')
        else:
            generator.characters(type(self).makeString(value))

    def _fieldXML(self, value, field, generator):

        fieldValue = getattr(value, field)
        attrs = { 'name': field,
                  'type': ItemHandler.typeName(fieldValue) }
        generator.startElement('field', attrs)
        generator.characters(type(self).makeString(fieldValue))
        generator.endElement('field')
          
    def unserialize(self, data):
        raise NotImplementedError, "Type.unserialize()"

    def getValue(self, itemHandler, data):
        return self.unserialize(data)

    def fieldsStart(self, itemHandler, attrs):
        itemHandler.fields = {}

    def fieldEnd(self, itemHandler, attrs):

        name = attrs['name']
        typeName = attrs['type']
        value = itemHandler.makeValue(typeName, itemHandler.data)

        itemHandler.fields[name] = value

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)
    handlerName = classmethod(handlerName)    


class String(Type):

    def makeValue(cls, data):
        return str(data)

    def unserialize(self, data):
        return String.makeValue(data)

    makeValue = classmethod(makeValue)


class Integer(Type):

    def makeValue(cls, data):
        return int(data)

    def unserialize(self, data):
        return Integer.makeValue(data)

    makeValue = classmethod(makeValue)


class Long(Type):

    def makeValue(cls, data):
        return long(data)

    def unserialize(self, data):
        return Long.makeValue(data)

    makeValue = classmethod(makeValue)


class Float(Type):

    def makeValue(cls, data):
        return float(data)

    def unserialize(self, data):
        return Float.makeValue(data)

    makeValue = classmethod(makeValue)

    
class Complex(Type):

    def makeValue(cls, data):
        return complex(data)

    def unserialize(self, data):
        return Complex.makeValue(data)

    makeValue = classmethod(makeValue)


class Bool(Type):

    def makeValue(cls, data):
        return data != 'False'

    def unserialize(self, data):
        return Bool.makeValue(data)

    makeValue = classmethod(makeValue)


class UUID(Type):

    def makeValue(cls, data):
        return model.util.UUID(data)

    def unserialize(self, data):
        return UUID.makeValue(data)

    makeValue = classmethod(makeValue)


class Path(Type):

    def makeValue(cls, data):
        return model.util.Path(data)

    def unserialize(self, data):
        return Path.makeValue(data)

    makeValue = classmethod(makeValue)


class Class(Type):

    def makeValue(cls, data):
        return cls.loadClass(data)

    def makeString(cls, value):
        return "%s.%s" %(value.__module__, value.__name__)

    def unserialize(self, data):
        return Class.makeValue(data)
        
    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)


class Enum(Type):

    def makeValue(cls, data):
        return data

    def makeString(cls, value):
        return value

    def typeXML(self, value, generator):

        try:
            number = self.Values.index(value)
        except ValueError:
            print value
            raise ValueError, "%d not in %s enum" %(value, self._name)
            
        generator.characters(str(number))
    
    def unserialize(self, data):

        if data[0] >= '0' and data[0] <= '9':
            return self.Values[int(data)]

        return self.Values[self.Values.index(data)]

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)


class DateTime(Type):

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


class DateTimeDelta(Type):

    defaults = { 'day': 0.0, 'hour': 0.0, 'minute': 0.0, 'second': 0.0 }

    def makeValue(cls, data):
        return mx.DateTime.DateTimeDeltaFrom(str(data))
        
    def unserialize(self, data):
        return DateTimeDelta.makeValue(data)

    def _fieldXML(self, value, field, generator):

        default = RelativeDateTime.defaults[field]
        fieldValue = getattr(value, field, default)
        if default != fieldValue:
            super(RelativeDateTime, self)._fieldXML(value, field, generator)
          
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


class RelativeDateTime(Type):

    defaults = { 'years': 0, 'months': 0, 'days': 0,
                 'year': None, 'month': None, 'day': None,
                 'hours': 0, 'minutes': 0, 'seconds': 0,
                 'hour': None, 'minute': None, 'second': None,
                 'weekday': None, 'weeks': 0 }

    def makeValue(cls, data):
        return mx.DateTime.RelativeDateTimeFrom(str(data))

    def unserialize(self, data):
        return RelativeDateTime.makeValue(data)

    def _fieldXML(self, value, field, generator):

        default = RelativeDateTime.defaults[field]
        fieldValue = getattr(value, field, default)
        if default != fieldValue:
            super(RelativeDateTime, self)._fieldXML(value, field, generator)
          
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
    

ItemHandler.typeHandlers[type] = Class
ItemHandler.typeHandlers[type(mx.DateTime.now())] = DateTime
ItemHandler.typeHandlers[type(mx.DateTime.DateTimeDelta(0))] = DateTimeDelta
ItemHandler.typeHandlers[type(mx.DateTime.RelativeDateTime())] = RelativeDateTime
