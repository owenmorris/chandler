
from model.item.Item import Item
from model.item.ItemRef import RefDict


class AttrDef(Item):

    def __init__(self, name, parent, kind, **_kwds):

        super(AttrDef, self).__init__(name, parent, kind, **_kwds)

        otherName = self._otherName('AttrDefs')
        self.setAttribute(otherName, RefDict(self, otherName))

    def refName(self, name):

        return self._name

    def getType(self):

        return self.Type

    def isRequired(self):

        return self.Required

    def isSingle(self):

        return self.Cardinality == 'single'

    def getDefault(self):

        return self.Default
