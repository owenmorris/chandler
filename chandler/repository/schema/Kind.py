
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.item.Item import Item
from repository.item.Values import ItemValue
from repository.item.ItemRef import ItemRef, RefDict, NoneRef
from repository.item.PersistentCollections import PersistentCollection
from repository.util.Path import Path
from repository.util.UUID import UUID
from repository.util.SingleRef import SingleRef


class Kind(Item):

    def __init__(self, name, parent, kind):

        super(Kind, self).__init__(name, parent, kind)
        self.__init()

    def __init(self):

        # recursion avoidance
        self._values['notFoundAttributes'] = []
        refDict = self._refDict('inheritedAttributes',
                                'inheritingKinds', False)
        self._references['inheritedAttributes'] = refDict
        self._status |= Item.SCHEMA

        # will allow schema items to live anywhere
        self._status |= Item.SCHEMA

        self._initialValues = None
        self._initialReferences = None

    def _fillItem(self, name, parent, kind, **kwds):

        super(Kind, self)._fillItem(name, parent, kind, **kwds)
        self.__init()

    def newItem(self, name, parent):
        """Create an item of this kind.

        The python class instantiated is taken from the Kind's classes
        attribute if it is set. The Item class is used otherwise."""
        
        item = self.getItemClass()(name, parent, self)
        if self._kind is self:
            superKind = self._kind.itsParent.getItemChild('Item')
            item.addValue('superKinds', superKind)

        return item
            
    def getItemClass(self):
        """Return the class used to create items of this Kind.

        By default, the Item class is returned."""

        return self.getAttributeValue('classes').get('python', Item)

    def resolve(self, name):

        child = self.getItemChild(name)
        if child:
            return child.itsUUID
        
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

    def iterAttributes(self, inherited=True,
                       localOnly=False, globalOnly=False):
        """
        Return a generator of C{(name, attribute)} pairs for iterating over the
        Chandler attributes defined for and inherited by this kind.

        @param inherited: if C{True}, iterate also over attributes that are
        inherited by this kind via its superKinds.
        @type inherited: boolean
        @param localOnly: if C{True}, only pairs for local attributes are
        returned. Local attributes are defined as direct children items
        of the kinds they're defined on and are not meant to be shared
        except through inheritance. The name of a local attribute is defined
        to be the name of its corresponding attribute item.
        @type localOnly: boolean
        @param globalOnly: if C{True}, only pairs for the global attributes
        are returned. Global attributes are not defined as direct children
        items and are intended to be shareable by multiple kinds. The name
        of a global attribute is defined to be the alias with which it was
        added into the kind's C{attributes} attribute. This alias name may
        of course be the same as the corresponding attribute's item name.
        @type globalOnly: boolean
        """

        if inherited:
            inheritedAttributes = self.inheritedAttributes
            for superKind in self._getSuperKinds():
                for name, attribute in superKind.iterAttributes(inherited,
                                                                localOnly,
                                                                globalOnly):
                    if not attribute.itsUUID in inheritedAttributes:
                        inheritedAttributes.append(attribute, alias=name)
                    yield (name, attribute)

        attributes = self.getAttributeValue('attributes', default=None)
        if attributes is not None:

            if not localOnly:
                aliases = attributes._aliases
                if aliases:
                    for (alias, uuid) in aliases.iteritems():
                        yield (alias, attributes[uuid])
    
            if not globalOnly:
                for attribute in self.iterChildren():
                    if attribute._uuid in attributes:
                        yield (attribute._name, attribute)

    def _inheritAttribute(self, name):

        if self.hasValue('notFoundAttributes', name):
            return None

        cache = True
        for superKind in self._getSuperKinds():
            if superKind is not None:
                attribute = superKind.getAttribute(name)
                if attribute is not None:
                    self.addValue('inheritedAttributes', attribute, alias=name)
                    return attribute
            else:
                cache = False
                    
        if cache:
            self.addValue('notFoundAttributes', name)

        return None

    def _getSuperKinds(self):

        try:
            return self.getAttributeValue('superKinds',
                                          _attrDict=self._references)
        except AttributeError:
            raise ValueError, 'No superKind for %s' %(self.itsPath)

    def _xmlRefs(self, generator, withSchema, version, mode):

        for attr in self._references.items():
            if self.getAttributeAspect(attr[0], 'persist', default=True):
                attr[1]._xmlValue(attr[0], self, generator, withSchema,
                                  version, mode)

    def isAlias(self):

        return False

    def isSubKindOf(self, superKind):

        superKinds = self._getSuperKinds()

        if superKinds:
            for kind in superKinds:
                if kind is superKind:
                    return True

            for kind in superKinds:
                if kind.isSubKindOf(superKind):
                    return True

        return False

    def getInitialValues(self, item, values, references):

        # setup cache
        if self._initialValues is None:
            self._initialValues = {}
            self._initialReferences = {}
            for name, attribute in self.iterAttributes():
                value = attribute.getAspect('initialValue', default=Item.Nil)
                if value is not Item.Nil:
                    otherName = attribute.getAspect('otherName')
                    if otherName is None:
                        self._initialValues[name] = value
                    else:
                        self._initialReferences[name] = value

        for name, value in self._initialValues.iteritems():
            if isinstance(value, PersistentCollection):
                value = value._copy(item, name, value._companion)
            elif isinstance(value, ItemValue):
                value = value._copy(item, name)

            values[name] = value

        for name, value in self._initialReferences.iteritems():
            if value is None:
                value = NoneRef
            elif isinstance(value, Item):
                value = ItemRef(item, name, value, item._otherName(name))
            elif isinstance(value, PersistentCollection):
                refDict = self._refDict(name, item._otherName(name))
                for other in value.itervalues():
                    refDict.append(other)
                value = refDict
            else:
                raise TypeError, value
            
            references[name] = value

    def flushCaches(self):

        self.inheritedAttributes.clear()
        del self.notFoundAttributes[:]
        self._initialValues = None
        self._initialReferences = None

        for subKind in self.getAttributeValue('subKinds',
                                              _attrDict=self._references,
                                              default=[]):
            subKind.flushCaches()

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
            data = value.itsUUID.str64()
            
        generator.characters(data)

    def handlerName(self):

        return 'ref'
    
    def recognizes(self, value):

        if value is None:
            return True

        if isinstance(value, SingleRef):
            return self.getRepository()[value.itsUUID].isItemOf(self)

        if isinstance(value, Item):
            return value.isItemOf(self)
    
        return False

    # end typeness of Kind as SingleRef

    def getClouds(self):

        clouds = self.getAttributeValue('clouds', default=None,
                                        _attrDict=self._references)

        if not clouds:
            for superKind in self._getSuperKinds():
                clouds = superKind.getClouds()
                if clouds:
                    break

        return clouds

    NoneString = "__NONE__"


class ItemKind(Kind):

    def _getSuperKinds(self):
        return []
