
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from model.item.ItemRef import RefDict
from MetaKind import MetaKind
from Kind import Kind

class AttrDef(Item):

    kind = MetaKind(Kind, { 'Required': { 'Required': False,
                                          'Cardinality': 'single',
                                          'Default': False },
                            'Cardinality': { 'Required': False,
                                             'Cardinality': 'single',
                                             'Default': 'single',
                                             'Values': ['single', 'list',
                                                        'dict'] },
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

        if name == 'AttrDefs' or name == 'InheritedAttrDefs':
            return self._name

        return super(AttrDef, self).refName(name)

    def hasAspect(self, name):

        return self.hasAttribute(name)

    def getAspect(self, name, default=None):

        if self.hasAttribute(name):
            return self.getAttribute(name)

        return default
