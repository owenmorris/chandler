
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

    def newItem(self, name, parent):
        '''Create an item of this kind.

        The class instantiated is taken from the Kind's Class attribute if it
        is set. The Item class is used otherwise.'''
        
        return self.getAttribute('Class')(name, parent, self)
        
    def getAttrDef(self, name, inherit=False):

        attrDef = self.getValue('AttrDefs', name, _attrDict=self._references)
        if attrDef is None:
            attrDef = self.getValue('InheritedAttrDefs', name,
                                    _attrDict=self._references)
            if attrDef is None:
                return self.inheritAttrDef(name)

        return attrDef

    def inheritAttrDef(self, name):

        if self.hasAttribute('SuperKind'):
            if self.hasValue('NotFoundAttrDefs', name):
                return None

            cache = True
            for superKind in self.SuperKind:
                if superKind is not None:
                    attrDef = superKind.getAttrDef(name, True)
                    if attrDef is not None:
                        self.attach('InheritedAttrDefs', attrDef)
                        return attrDef
                else:
                    cache = False
                    
            if cache and not self.hasValue('NotFoundAttrDefs', name):
                self.addValue('NotFoundAttrDefs', name)

        return None

    def _saveRefs(self, generator, withSchema):

        for attr in self._references.items():
            if self.getAttrAspect(attr[0], 'Persist', True):
                attr[1]._xmlValue(attr[0], self, '\n  ',
                                  generator, withSchema)


class KindKind(Kind):

    def getAttrDef(self, name, inherit=False):

        attrDef = super(KindKind, self).getAttrDef(name, inherit)
        if attrDef is None:
            attrDef = self.Class.kind.getAttrDef(name, inherit)

        return attrDef
    

Kind.kind = MetaKind(Kind, { 'SuperKind': { 'Required': False,
                                            'Cardinality': 'list',
                                            'OtherName': 'SubKind' },
                             'SubKind': { 'Required': False,
                                          'Cardinality': 'dict',
                                          'OtherName': 'SuperKind' },
                             'Items': { 'Required': False,
                                        'Cardinality': 'dict',
                                        'OtherName': 'Kind' },
                             'Kind': { 'Required': False,
                                       'Cardinality': 'single',
                                       'Persist': False,
                                       'OtherName': 'Items' },
                             'AttrDefs': { 'Required': True,
                                           'Cardinality': 'dict',
                                           'OtherName': 'Kinds' },
                             'InheritedAttrDefs': { 'Required': False,
                                                    'Cardinality': 'dict',
                                                    'OtherName': 'InheritingKinds' },
                             'NotFoundAttrDefs': { 'Required': True,
                                                   'Cardinality': 'list',
                                                   'Persist': False },
                             'Class': { 'Required': False,
                                        'Cardinality': 'single',
                                        'Default': None } })

Item.kind = MetaKind(Kind, { 'Kind': { 'Required': False,
                                       'Cardinality': 'single',
                                       'Persist': False,
                                       'OtherName': 'Items' } })
