
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from model.item.ItemRef import RefDict


class Kind(Item):

    def __init__(self, name, parent, kind, **_kwds):

        super(Kind, self).__init__(name, parent, kind, **_kwds)

        self._attributes['NotFoundAttrDefs'] = []  # recursion avoidance

    def newItem(self, name, parent):
        '''Create an item of this kind.

        The class instantiated is taken from the Kind's Class attribute if it
        is set. The Item class is used otherwise.'''
        
        return self.getAttribute('Class')(name, parent, self)
        
    def getAttrDef(self, name, inheriting=False):

        attrDef = self._getAttrDef(name, inheriting)
        if attrDef is None:
            attrDef = self.getValue('InheritedAttrDefs', name,
                                    _attrDict=self._references)
            if attrDef is None:
                return self.inheritAttrDef(name)

        return attrDef

    def _getAttrDef(self, name, inheriting):

        return self.getValue('AttrDefs', name, _attrDict=self._references)

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
                attr[1]._xmlValue(attr[0], self, '\n  ', generator, withSchema)


class KindKind(Kind):

    def __init__(self, name, parent, kind, **_kwds):

        super(KindKind, self).__init__(name, parent, kind, **_kwds)

        if kind is None:
            self._kind = self


class SchemaRoot(Item):

    def __init__(self, name, parent, kind, **_kwds):

        super(SchemaRoot, self).__init__(name, parent, kind, **_kwds)

        afterLoadHooks = _kwds.get('_afterLoadHooks', None)
        if afterLoadHooks is not None:
            afterLoadHooks.append(self.afterLoadHook)

    def afterLoadHook(self):

        def cacheKind(item):

            if item._kind is None and item.hasAttribute('Kind'):
                item._kind = item.Kind
            for child in item:
                cacheKind(child)

        cacheKind(self)
