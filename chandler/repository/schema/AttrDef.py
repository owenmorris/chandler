
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
                            'InheritingKinds': { 'Required': False,
                                                 'Cardinality': 'dict',
                                                 'OtherName': 'InheritedAttrDefs' },
                            'Kinds': { 'Required': False,
                                       'Cardinality': 'dict',
                                       'OtherName': 'AttrDefs' },
                            'Kind': { 'Required': False,
                                      'Cardinality': 'single',
                                      'OtherName': 'Items' } })

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

    def _saveRefs(self, generator, withSchema):

        for attr in self._references.items():
            if self.getAttrAspect(attr[0], 'Persist', True):
                attr[1]._xmlValue(attr[0], self, '\n  ',
                                  generator, withSchema)
