
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from model.item.ItemRef import RefDict
from MetaKind import MetaKind
from Kind import Kind


class Type(Item):

    kind = MetaKind(Kind, { 'TypeFor': { 'Required': False,
                                         'Cardinality': 'dict',
                                         'OtherName': 'Type' }})

    def makeValue(self, data):

        return self.unserialize(data)

    def typeName(self):

        raise NotImplementedError, "Type.typeName()"

    def serialize(self, value, withSchema=False):

        return str(value)
    
    def unserialize(self, data):

        raise NotImplementedError, "Type.unserialize()"


class String(Type):

    def typeName(self):
        return 'str'

    def unserialize(self, data):
        return str(data)


class Integer(Type):

    def typeName(self):
        return 'int'

    def unserialize(self, data):
        return int(data)


class Long(Type):

    def typeName(self):
        return 'long'

    def unserialize(self, data):
        return long(data)


class Float(Type):

    def typeName(self):
        return 'float'

    def unserialize(self, data):
        return float(data)

    
class Complex(Type):

    def typeName(self):
        return 'complex'

    def unserialize(self, data):
        return complex(data)


class Bool(Type):

    def typeName(self):
        return 'bool'

    def unserialize(self, data):
        return data != 'False'


class UUID(Type):

    def typeName(self):
        return 'uuid'

    def unserialize(self, data):
        return model.util.UUID(data)


class Path(Type):

    def typeName(self):
        return 'path'

    def unserialize(self, data):
        return model.util.Path(data)


class Class(Type):

    def typeName(self):

        return 'class'

    def serialize(self, value, withSchema=False):

        return "%s.%s" %(value.__module__, value.__name__)

    def unserialize(self, data):

        lastDot = data.rindex('.')
        module = data[:lastDot]
        name = data[lastDot+1:]
        
        return getattr(__import__(module, {}, {}, name), name)


class Enum(Type):

    kind = MetaKind(Kind, { 'TypeFor': { 'Required': False,
                                         'Cardinality': 'dict',
                                         'OtherName': 'Type' },
                            'Values': { 'Cardinality': 'list' } })

    def typeName(self):

        return 'str'

    def serialize(self, value, withSchema=False):

        number = self.Values.index(value)
        
        if withSchema:
            return value
        else:
            return str(number)
    
    def unserialize(self, data):

        if data[0] >= '0' and data[0] <= '9':
            return self.Values[int(data)]

        return self.Values.index(data) and data
