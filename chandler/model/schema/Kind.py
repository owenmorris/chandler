
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from model.item.ItemRef import RefDict
from MetaKind import MetaKind


class Kind(Item):

    def __init__(self, name, parent, kind, **_kwds):

        super(Kind, self).__init__(name, parent, kind, **_kwds)

        self._attributes['NotFoundAttrDefs'] = []  # recursion avoidance
        
    def getAttrDef(self, name):

        attrDef = self.getValue('AttrDefs', name)
        if attrDef is None:
            attrDef = self.getValue('InheritedAttrDefs', name)
            if attrDef is None:
                return self.inheritAttrDef(name)

        return attrDef

    def inheritAttrDef(self, name):

        if self.hasAttribute('SuperKind'):
            if self.hasValue('NotFoundAttrDefs', name):
                return None
        
            for superKind in self.SuperKind:
                attrDef = superKind.getAttrDef(name)
                if attrDef is not None:
                    self.attach('InheritedAttrDefs', attrDef)
                    return attrDef
                
            if not self.hasValue('NotFoundAttrDefs', name):
                self.addValue('NotFoundAttrDefs', name)

        return None


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
                             'NotFoundAttrDefs': { 'Required': True,
                                                   'Cardinality': 'list',
                                                   'Persist': False },
                             'Class': { 'Required': False,
                                        'Cardinality': 'single' } })
