
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

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
