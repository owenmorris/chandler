
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from model.item.ItemRef import RefDict
from MetaKind import MetaKind


class Type(Item):

    kind = MetaKind({ 'TypeFor': { 'Required': False,
                                   'Cardinality': 'dict',
                                   'OtherName': 'Type' } })

    def serialize(self, value):

        return str(value)
    
    def unserialize(self, data):

        raise NotImplementedError, "Type.unserialize()"

    def refName(self, name):

        return self._name


class String(Type):

    def unserialize(self, data):
        return str(data)


class Integer(Type):

    def unserialize(self, data):
        return int(data)


class Long(Type):

    def unserialize(self, data):
        return long(data)


class Float(Type):

    def unserialize(self, data):
        return float(data)

    
class Complex(Type):

    def unserialize(self, data):
        return complex(data)


class Bool(Type):

    def unserialize(self, data):
        return data != 'False'


class UUID(Type):

    def unserialize(self, data):
        return model.util.UUID(data)


class Path(Type):

    def unserialize(self, data):
        return model.util.Path(data)


class Enum(Type):

    def serialize(self, value):

        return str(self.Values.index(value))
    
    def unserialize(self, data):

        if data[0] >= '0' and data[0] <= '9':
            return self.Values[int(data)]

        return self.Values[self.Values.index(data)]
