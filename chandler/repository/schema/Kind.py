
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from model.item.ItemRef import RefDict
from MetaKind import MetaKind


class Kind(Item):

    def getAttrDef(self, name):

        return self.AttrDefs.get(name)


class KindKind(Kind):

    def getAttrDef(self, name):

        attrDef = super(KindKind, self).getAttrDef(name)
        if attrDef is None:
            attrDef = self.Class.kind.getAttrDef(name)

        return attrDef
    

Kind.kind = MetaKind(Kind, { 'SuperKind': { 'Required': False,
                                            'Cardinality': 'dict',
                                            'OtherName': 'SubKind' },
                             'SubKind': { 'Required': False,
                                          'Cardinality': 'dict',
                                          'OtherName': 'SuperKind' },
                             'AttrDefs': { 'Required': True,
                                           'Cardinality': 'dict',
                                           'OtherName': 'Kinds' },
                             'Class': { 'Required': False,
                                        'Cardinality': 'single' } })
