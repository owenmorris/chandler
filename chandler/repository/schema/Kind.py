
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.item.Item import Item
from repository.item.ItemRef import RefDict
from repository.util.Path import Path
from repository.util.UUID import UUID
from repository.util.SingleRef import SingleRef


class Kind(Item):

    def __init__(self, name, parent, kind):

        super(Kind, self).__init__(name, parent, kind)

        # recursion avoidance
        self._values['notFoundAttributes'] = []
        refDict = self._refDict('inheritedAttributes',
                                'inheritingKinds', False)
        self._references['inheritedAttributes'] = refDict
        self._status |= Item.SCHEMA

        # will allow schema items to live anywhere
        self._status |= Item.SCHEMA

    def _fillItem(self, name, parent, kind, **kwds):

        super(Kind, self)._fillItem(name, parent, kind, **kwds)

        # recursion avoidance
        self._values['notFoundAttributes'] = []
        refDict = self._refDict('inheritedAttributes',
                                'inheritingKinds', False)
        self._references['inheritedAttributes'] = refDict
        self._status |= Item.SCHEMA

        # will allow schema items to live anywhere
        self._status |= Item.SCHEMA

    def newItem(self, name, parent):
        """Create an item of this kind.

        The python class instantiated is taken from the Kind's classes
        attribute if it is set. The Item class is used otherwise."""
        
        item = self.getItemClass()(name, parent, self)
        if self._kind is self:
            superKind = self._kind.getItemParent().getItemChild('Item')
            item.addValue('superKinds', superKind)

        return item
            
    def getItemClass(self):
        """Return the class used to create items of this Kind.

        By default, the Item class is returned."""

        return self.getAttributeValue('classes').get('python', Item)

    def resolve(self, name):

        child = self.getItemChild(name)
        if child:
            return child.getUUID()
        
        if self.hasAttributeValue('attributes', _attrDict=self._references):
            return self.attributes.resolveAlias(name)

        return None

    def getAttribute(self, name):

        uuid = self.resolve(name)
        if uuid is not None:
            attribute = self.getValue('attributes', uuid,
                                      _attrDict=self._references)
        else:
            attribute = None
            
        if attribute is None:
            uuid = self.inheritedAttributes.resolveAlias(name)
            if uuid is not None:
                attribute = self.getValue('inheritedAttributes', uuid,
                                          _attrDict=self._references)
            else:
                attribute = self._inheritAttribute(name)

        return attribute

    def hasAttribute(self, name):

        uuid = self.resolve(name)
        if uuid is not None:
            if self.hasValue('attributes', uuid, _attrDict=self._references):
                return True
        elif self.inheritedAttributes.resolveAlias(name):
            return True
        else:
            return self._inheritAttribute(name) is not None

    def _inheritAttribute(self, name):

        if self.hasValue('notFoundAttributes', name):
            return None

        inheritingKinds = self._getInheritingKinds()
        if inheritingKinds is not None:
            cache = True
            for inheritingKind in inheritingKinds:
                if inheritingKind is not None:
                    attribute = inheritingKind.getAttribute(name)
                    if attribute is not None:
                        self.addValue('inheritedAttributes', attribute,
                                      alias=name)
                        return attribute
                else:
                    cache = False
                    
            if cache:
                self.addValue('notFoundAttributes', name)

        return None

    def _getInheritingKinds(self):

        if self.hasAttributeValue('superKinds'):
            return self.superKinds

        raise ValueError, 'No superKind for %s' %(self.getItemPath())

    def _xmlRefs(self, generator, withSchema, version, mode):

        for attr in self._references.items():
            if self.getAttributeAspect(attr[0], 'persist', default=True):
                attr[1]._xmlValue(attr[0], self, generator, withSchema,
                                  version, mode)

    def isAlias(self):

        return False

    def isSubKindOf(self, superKind):

        superKinds = self.getAttributeValue('superKinds',
                                            _attrDict=self._references,
                                            default=[])

        if superKinds:
            for kind in superKinds:
                if kind is superKind:
                    return True

            for kind in superKinds:
                if kind.isSubKindOf(superKind):
                    return True

        return False


    # begin typeness of Kind as SingleRef
    
    def isValueReady(self, itemHandler):
        return True

    def startValue(self, itemHandler):
        pass

    def getParsedValue(self, itemHandler, data):
        return self.makeValue(data)
    
    def makeValue(self, data):

        if data == Kind.NoneString:
            return None
        
        return SingleRef(UUID(data))

    def makeString(self, data):

        if data is None:
            return Kind.NoneString
        
        return SingleRef(UUID(data))

    def typeXML(self, value, generator, withSchema):

        if value is None:
            data = Kind.NoneString
        else:
            data = value.getUUID().str64()
            
        generator.characters(data)

    def handlerName(self):

        return 'ref'
    
    def recognizes(self, value):

        if value is None:
            return True

        if isinstance(value, SingleRef):
            return self.getRepository()[value.getUUID()].isItemOf(self)

        if isinstance(value, Item):
            return value.isItemOf(self)
    
        return False

    # end typeness of Kind as SingleRef

    NoneString = "__NONE__"


class ItemKind(Kind):

    def _getInheritingKinds(self):

        return None


class SchemaRoot(Item):
    pass
