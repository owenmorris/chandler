
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import UUIDext

from new import classobj

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
        self._status |= Item.SCHEMA | Item.PINNED

        self._initialValues = None
        self._initialReferences = None

    def _fillItem(self, name, parent, kind, **kwds):

        super(Kind, self)._fillItem(name, parent, kind, **kwds)
        self.__init()

    def newItem(self, name, parent):
        """
        Create an item of this kind.

        The python class instantiated is taken from the Kind's classes
        attribute if it is set. The Item class is used otherwise.
        """
        
        return self.getItemClass()(name, parent, self)
            
    def getItemClass(self):
        """
        Return the class used to create items of this Kind.

        By default, the L{Item<repository.item.Item.Item>} class is returned.
        """

        return self.getAttributeValue('classes').get('python', Item)

    def check(self, recursive=False):

        result = super(Kind, self).check(recursive)
        
        if not self.getAttributeValue('superKinds', default=None,
                                      _attrDict = self._references):
            self.itsView.logger.warn('No superKinds for %s', self.itsPath)
            result = False

        return result
        
    def resolve(self, name):

        child = self.getItemChild(name)
        if child:
            return child._uuid
        
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

    def getOtherName(self, name, **kwds):

        otherName = self.getAttributeValue('otherNames', default={},
                                           _attrDict=self._values).get(name)

        if otherName is None:
            attribute = self.getAttribute(name)
            if attribute is not None:
                otherName = attribute.getAspect('otherName')

            if otherName is None:
                if 'default' in kwds:
                    return kwds['default']
                raise TypeError, 'Undefined otherName for attribute %s on kind %s' %(name, self.itsPath)

        return otherName

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

        attributes = self.getAttributeValue('attributes', default=None)
        if attributes is not None:

            if not globalOnly:
                for attribute in self.iterChildren():
                    if attribute._uuid in attributes:
                        yield (attribute._name, attribute)

            if not localOnly:
                for attribute in attributes:
                    if attribute.itsParent is not self:
                        yield (attributes._get(attribute._uuid)._alias,
                               attribute)

        if inherited:
            inheritedAttributes = self.inheritedAttributes
            for superKind in self._getSuperKinds():
                for name, attribute in superKind.iterAttributes():
                    if not attribute._uuid in inheritedAttributes:
                        inheritedAttributes.append(attribute, alias=name)
            for uuid, link in inheritedAttributes._iteritems():
                name = link._alias
                if not self.resolve(name):
                    yield (name, link._value.other(self))

    def _inheritAttribute(self, name):

        if self.hasValue('notFoundAttributes', name):
            return None

        cache = True
        for superKind in self._getSuperKinds():
            if superKind is not None:
                attribute = superKind.getAttribute(name)
                if attribute is not None:
                    # during core schema loading _kind can be None
                    if attribute._kind is not None:
                        self.addValue('inheritedAttributes',
                                      attribute, alias=name)
                    return attribute
            else:
                cache = False
                    
        if cache:
            self.addValue('notFoundAttributes', name)

        return None

    def _getSuperKinds(self):

        superKinds = self.getAttributeValue('superKinds', default=None,
                                            _attrDict=self._references)
        if not superKinds:
            self.itsView.logger.warn('No superKinds for %s', self.itsPath)
            return [ self.getItemKind() ]

        return superKinds

    def getItemKind(self):

        return self._kind.itsParent['Item']

    def mixin(self, superKinds):

        duplicates = {}
        for superKind in superKinds:
            if superKind._uuid in duplicates:
                raise ValueError, 'Kind %s is duplicated' %(superKind.itsPath)
            else:
                duplicates[superKind._uuid] = superKind
                
        hash = UUIDext.combine(0, self._uuid._hash)
        for superKind in superKinds:
            hash = UUIDext.combine(hash, superKind._uuid._hash)
        if hash < 0:
            hash = ~hash
        name = "mixin_%08x" %(hash)
        parent = self.getItemKind().itsParent['Mixins']

        kind = parent.getItemChild(name)
        if kind is None:
            kind = MixinKind(name, parent, self._kind)

            kind.addValue('superKinds', self)
            kind.superKinds.extend(superKinds)
            kind.addValue('mixins', self._uuid)
            kind.mixins.extend([sk._uuid for sk in superKinds])

            kind._createItemClass()
            
        return kind
        
    def isMixin(self):

        return False

    def isAlias(self):

        return False

    def isKindOf(self, superKind):

        if self is superKind:
            return True

        superKinds = self._getSuperKinds()

        if superKinds:
            for kind in superKinds:
                if kind is superKind:
                    return True

            for kind in superKinds:
                if kind.isKindOf(superKind):
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
                    otherName = self.getOtherName(name, default=None)
                    if otherName is None:
                        self._initialValues[name] = value
                    else:
                        self._initialReferences[name] = value

        for name, value in self._initialValues.iteritems():
            if name not in values:
                if isinstance(value, PersistentCollection):
                    value = value._copy(item, name, value._companion)
                elif isinstance(value, ItemValue):
                    value = value._copy(item, name)

                values[name] = value

        for name, value in self._initialReferences.iteritems():
            if name not in references:
                if value is None:
                    value = NoneRef
                elif isinstance(value, Item):
                    value = ItemRef(item, name, value, self.getOtherName(name))
                elif isinstance(value, PersistentCollection):
                    refDict = item._refDict(name, self.getOtherName(name))
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
            return self.itsView[value.itsUUID].isItemOf(self)

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

    def check(self, recursive=False):
        return super(Kind, self).check(recursive)


class MixinKind(Kind):

    def _fillItem(self, name, parent, kind, **kwds):

        super(MixinKind, self)._fillItem(name, parent, kind, **kwds)
        self._createItemClass()

    def isMixin(self):
        return True

    def _createItemClass(self):

        duplicates = {}
        superClasses = []
        
        for superKind in self._getSuperKinds():
            c = superKind.getItemClass()
            if c is not Item and c.__name__ not in duplicates:
                superClasses.append(c)
                duplicates[c.__name__] = c

        count = len(superClasses)

        if count == 0:
            c = None
        elif count == 1:
            c = superClasses[0]
        else:
            c = classobj(self._name, tuple(superClasses), {})

        if c is not None:
            self.classes = { 'python': c }
            self._values._setFlag('classes', self._values.TRANSIENT)

        return c
