
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from model.item.ItemRef import RefDict
from MetaKind import MetaKind


class AttrDef(Item):

    kind = MetaKind({ 'Required': { 'Required': False,
                                    'Cardinality': 'single',
                                    'Default': False },
                      'Cardinality': { 'Required': False,
                                       'Cardinality': 'single',
                                       'Default': 'single' },
                      'Type': { 'Required': False,
                                'Cardinality': 'single',
                                'OtherName': 'TypeFor' },
                      'Default': { 'Required': False,
                                   'Cardinality': 'single' },
                      'OtherName': { 'Required': False,
                                     'Cardinality': 'single' },
                      'Kinds': { 'Required': False,
                                 'Cardinality': 'dict',
                                 'OtherName': 'AttrDefs' } })

    def refName(self, name):

        if name == 'AttrDefs':
            return self._name

        return super(AttrDef, self).refName(name)
