
from model.item.Item import Item
from model.item.ItemRef import RefDict
from MetaKind import MetaKind


class Kind(Item):

    kind = MetaKind({ 'SuperKind': { 'Required': False,
                                    'Cardinality': 'dict',
                                    'OtherName': 'SubKind' },
                      'SubKind': { 'Required': False,
                                   'Cardinality': 'dict',
                                   'OtherName': 'SuperKind' },
                      'AttrDefs': { 'Required': True,
                                    'Cardinality': 'dict',
                                    'OtherName': 'Kinds' } })
    
    def getAttrDef(self, name):

        return self.AttrDefs.get(name)
