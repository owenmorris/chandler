
from model.item.Item import Item
from model.item.ItemRef import RefDict


class Kind(Item):

    def __init__(self, name, parent, kind, **_kwds):

        super(Kind, self).__init__(name, parent, kind, **_kwds)

        self.setAttribute('AttrDefs', RefDict(self, 'AttrDefs'))

    def getAttrDef(self, name):

        return self.AttrDefs[name]
