
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from model.item.ItemRef import RefDict


class Kind(Item):

    def __init__(self, name, parent, kind, **_kwds):

        super(Kind, self).__init__(name, parent, kind, **_kwds)

        # recursion avoidance
        self._values['NotFoundAttributes'] = []

    def newItem(self, name, parent):
        """Create an item of this kind.

        The python class instantiated is taken from the Kind's Classes
        attribute if it is set. The Item class is used otherwise."""
        
        return self.getItemClass()(name, parent, self)

    def getItemClass(self):

        return self.getAttributeValue('Classes')['python']
        
    def getAttribute(self, name):

        attribute = self.getValue('Attributes', name,
                                  _attrDict=self._references)
        if attribute is None:
            attribute = self.getValue('InheritedAttributes', name,
                                      _attrDict=self._references)
            if attribute is None:
                return self.inheritAttribute(name)

        return attribute

    def hasAttribute(self, name):

        if self.hasValue('Attributes', name, _attrDict=self._references):
            return True
        
        if self.hasValue('InheritedAttributes', name,
                         _attrDict=self._references):
            return True
        
        return self.inheritAttribute(name) is not None

    def inheritAttribute(self, name):

        if self.hasValue('NotFoundAttributes', name):
            return None
        
        inheritingKinds = self._getInheritingKinds()
        if inheritingKinds is not None:
            cache = True
            for inheritingKind in inheritingKinds:
                if inheritingKind is not None:
                    attribute = inheritingKind.getAttribute(name)
                    if attribute is not None:
                        self.attach('InheritedAttributes', attribute)
                        return attribute
                else:
                    cache = False
                    
            if cache:
                self.addValue('NotFoundAttributes', name)

        return None

    def _getInheritingKinds(self):

        if self.hasAttributeValue('SuperKinds'):
            return self.SuperKinds

        return self._kind._getInheritingKinds()

    def _saveRefs(self, generator, withSchema):

        for attr in self._references.items():
            if self.getAttributeAspect(attr[0], 'Persist', True):
                attr[1]._saveValue(attr[0], self, generator, withSchema)


class KindKind(Kind):

    def __init__(self, name, parent, kind, **_kwds):

        super(KindKind, self).__init__(name, parent, self, **_kwds)


class ItemKind(Kind):

    def _getInheritingKinds(self):

        return None


class SchemaRoot(Item):

    def __init__(self, name, parent, kind, **_kwds):

        super(SchemaRoot, self).__init__(name, parent, kind, **_kwds)

        afterLoadHooks = _kwds.get('_afterLoadHooks', None)
        if afterLoadHooks is not None:
            afterLoadHooks.append(self.afterLoadHook)

    def afterLoadHook(self):

        def apply(item):

            assert not item._values.get('NotFoundAttributes', []), item

            for child in item:
                apply(child)

        apply(self)
