
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

#        fields = self.Fields
#        if fields:
#            generator.startElement('fields', {})
#            for field in fields:
#                fieldValue = getattr(value, field)
#                attrs = { 'name': field,
#                          'type': ItemHandler.typeName(fieldValue) }
#                generator.startElement('field', attrs)
#                generator.characters(type(self).makeString(fieldValue))
#                generator.endElement('field')
#            generator.endElement('fields')
#
#        else:
#            generator.characters(type(self).makeString(value))
    
         generator.characters(type(self).makeString(value))
         
    def unserialize(self, data):
        raise NotImplementedError, "Type.unserialize()"

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

    makeValue = classmethod(makeValue)
    makeString = classmethod(makeString)


class DateTimeDelta(Type):

    def makeValue(cls, data):
        return mx.DateTime.DateTimeDeltaFrom(str(data))
        
    def unserialize(self, data):
        return DateTimeDelta.makeValue(data)

    makeValue = classmethod(makeValue)


class RelativeDateTime(Type):

    def makeValue(cls, data):
        return mx.DateTime.RelativeDateTimeFrom(str(data))

    def unserialize(self, data):
        return RelativeDateTime.makeValue(data)

    makeValue = classmethod(makeValue)
    

ItemHandler.typeHandlers[type] = Class
ItemHandler.typeHandlers[type(mx.DateTime.now())] = DateTime
ItemHandler.typeHandlers[type(mx.DateTime.DateTimeDelta(0))] = DateTimeDelta
ItemHandler.typeHandlers[type(mx.DateTime.RelativeDateTime())] = RelativeDateTime
