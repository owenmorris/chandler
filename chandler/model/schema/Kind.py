
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from model.item.Item import Item
from model.item.ItemRef import RefDict
from model.util.Path import Path


class Kind(Item):

    def __init__(self, name, parent, kind):

        super(Kind, self).__init__(name, parent, kind)

        # recursion avoidance
        self._values['notFoundAttributes'] = []

    def _fillItem(self, name, parent, kind, **kwds):

        super(Kind, self)._fillItem(name, parent, kind, **kwds)

        # recursion avoidance
        self._values['notFoundAttributes'] = []

    def newItem(self, name, parent):
        """Create an item of this kind.

        The python class instantiated is taken from the Kind's classes
        attribute if it is set. The Item class is used otherwise."""
        
        return self.getItemClass()(name, parent, self)

    def getItemClass(self):
        """Return the class used to create items of this Kind.

        By default, the Item class is returned."""
        
        return self.getAttributeValue('classes').get('python', Item)
        
    def getAttribute(self, name):

        attribute = self.getValue('attributes', name,
                                  _attrDict=self._references)
        if attribute is None:
            attribute = self.getValue('inheritedAttributes', name,
                                      _attrDict=self._references)
            if attribute is None:
                return self.inheritAttribute(name)

        return attribute

    def hasAttribute(self, name):

        if self.hasValue('attributes', name, _attrDict=self._references):
            return True
        
        if self.hasValue('inheritedAttributes', name,
                         _attrDict=self._references):
            return True
        
        return self.inheritAttribute(name) is not None

    def inheritAttribute(self, name):

        if self.hasValue('notFoundAttributes', name):
            return None
        
        inheritingKinds = self._getInheritingKinds()
        if inheritingKinds is not None:
            cache = True
            for inheritingKind in inheritingKinds:
                if inheritingKind is not None:
                    attribute = inheritingKind.getAttribute(name)
                    if attribute is not None:
                        self.attach('inheritedAttributes', attribute)
                        return attribute
                else:
                    cache = False
                    
            if cache:
                self.addValue('notFoundAttributes', name)

        return None

    def _getInheritingKinds(self):

        if self.hasAttributeValue('superKinds'):
            return self.superKinds

#        return self._kind._getInheritingKinds()
        raise ValueError, 'No superKind for %s' %(self.getItemPath())

    def _saveRefs(self, generator, withSchema):

        for attr in self._references.items():
            if self.getAttributeAspect(attr[0], 'persist', True):
                attr[1]._saveValue(attr[0], self, generator, withSchema)

    def isAlias(self):
        return False

    def recognizes(self, value):
        raise NotImplementedError, "Kind.recognizes()"


class KindKind(Kind):

    def __init__(self, name, parent, kind):

        super(KindKind, self).__init__(name, parent, self)

    def _fillItem(self, name, parent, kind, **kwds):
    
        super(KindKind, self)._fillItem(name, parent, self, **kwds)


class ItemKind(Kind):

    def _getInheritingKinds(self):

        return None


class SchemaRoot(Item):

    def _fillItem(self, name, parent, kind, **kwds):

        super(SchemaRoot, self)._fillItem(name, parent, kind, **kwds)

        if kwds['afterLoadHooks'] is not None:
            kwds['afterLoadHooks'].append(self.afterLoadHook)

    def afterLoadHook(self):

        def apply(item):

            assert not item._values.get('notFoundAttributes', []), item

            for child in item:
                apply(child)

        apply(self)
