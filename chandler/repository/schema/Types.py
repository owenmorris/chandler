
from model.item.Item import Item
from model.item.ItemRef import RefDict


class Type(Item):

    def __init__(self, name, parent, kind, **_kwds):

        super(Type, self).__init__(name, parent, kind, **_kwds)

        otherName = self._otherName('Type')
        self.setAttribute(otherName, RefDict(self, otherName))

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


class Enum(Type):

    def serialize(self, value):

        return str(self.Values.index(value))
    
    def unserialize(self, data):

        if data[0] >= '0' and data[0] <= '9':
            return self.Values[int(data)]

        return self.Values[self.Values.index(data)]
