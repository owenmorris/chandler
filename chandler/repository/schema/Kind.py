
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from new import classobj

from repository.item.Item import Item
from repository.item.Values import ItemValue
from repository.item.PersistentCollections import PersistentCollection
from repository.util.Path import Path
from chandlerdb.util.UUID import UUID, _uuid
from repository.util.SingleRef import SingleRef


class Kind(Item):

    def __init__(self, name, parent, kind):

        super(Kind, self).__init__(name, parent, kind)
        self.__init()

    def __init(self):

        # recursion avoidance
        self._values['notFoundAttributes'] = []
        refList = self._refList('inheritedAttributes',
                                'inheritingKinds', False)
        
        self._references['inheritedAttributes'] = refList
        self._status |= Item.SCHEMA | Item.PINNED

        self.__dict__['_initialValues'] = None
        self.__dict__['_initialReferences'] = None

    def _fillItem(self, name, parent, kind, **kwds):

        super(Kind, self)._fillItem(name, parent, kind, **kwds)
        if not kwds['update']:
            self.__init()

    def onItemLoad(self):

        # force-load attributes for schema bootstrapping
        if 'attributes' in self._references:
            for attribute in self.attributes:
                pass

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

        If this Kind has superKinds and C{self.classes['python']} is not set
        a composite class is generated and cached from the superKinds.

        The L{Item<repository.item.Item.Item>} class is returned by default.
        """

        try:
            return self._values['classes']['python']
        except KeyError:
            pass
        except TypeError:
            pass

        superClasses = []
        
        hash = _uuid.combine(0, self._uuid._hash)
        for superKind in self.superKinds:
            c = superKind.getItemClass()
            if c is not Item and c not in superClasses:
                superClasses.append(c)
                hash = _uuid.combine(hash, superKind._uuid._hash)

        count = len(superClasses)

        if count == 0:
            c = Item
        elif count == 1:
            c = superClasses[0]
        else:
            if hash < 0:
                hash = ~hash
            name = "class_%08x" %(hash)
            c = classobj(name, tuple(superClasses), {})

        self._values['classes'] = { 'python': c }
        self._values._setTransient('classes')

        return c

    def check(self, recursive=False):

        result = super(Kind, self).check(recursive)
        
        if not self.getAttributeValue('superKinds', default=None,
                                      _attrDict = self._references):
            if self is not self.getItemKind():
                self.itsView.logger.warn('No superKinds for %s', self.itsPath)
                result = False

        def checkClass(cls):
            if cls is not Item:
                if not (isinstance(cls, type) and issubclass(cls, Item)):
                    return cls
                for base in cls.__bases__:
                    if checkClass(base) is not None:
                        return base
            return None

        cls = checkClass(self.getItemClass())
        if cls is not None:
            self.itsView.logger.warn('Kind %s has an item class or superclass that is not a subclass of Item: %s %s', self.itsPath, cls, type(cls))
            result = False

        return result
        
    def resolve(self, name):

        child = self.getItemChild(name)
        if child:
            return child._uuid
        
        if self.hasAttributeValue('attributes', _attrDict=self._references):
            return self.attributes.resolveAlias(name)

        return None

    def getAttribute(self, name, noError=False):
        """
        Get an attribute definition item.

        The attribute is sought on the kind and on its superKinds in a left
        to right depth-first manner. If no attribute is found
        C{AttributeError} is raised.

        @param name: the name of the attribute sought
        @type name: a string
        @return: an L{Attribute<repository.schema.Attribute.Attribute>} item
        instance
        """

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

        if attribute is None and noError is False:
            raise AttributeError, "Kind %s has no definition for attribute '%s'" %(self.itsPath, name)

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
            otherName = self.getAttribute(name).getAspect('otherName')
            if otherName is None:
                if 'default' in kwds:
                    return kwds['default']
                raise TypeError, 'Undefined otherName for attribute %s on kind %s' %(name, self.itsPath)

        return otherName

    def iterAttributes(self, inherited=True,
                       localOnly=False, globalOnly=False):
        """
        Return a generator of C{(name, attribute, kind)} tuples for
        iterating over the Chandler attributes defined for and inherited by
        this kind. The C{kind} element is the kind the attribute was
        inherited from or this kind.

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
                        yield (attribute._name, attribute, self)

            if not localOnly:
                for attribute in attributes:
                    if attribute.itsParent is not self:
                        yield (attributes.getAlias(attribute), attribute, self)

        if inherited:
            inheritedAttributes = self.inheritedAttributes
            for superKind in self.superKinds:
                for name, attribute, k in superKind.iterAttributes():
                    if (attribute._uuid not in inheritedAttributes and
                        inheritedAttributes.resolveAlias(name) is None):
                        inheritedAttributes.append(attribute, alias=name)
            for uuid, link in inheritedAttributes._iteritems():
                name = link._alias
                if not self.resolve(name):
                    attribute = link._value
                    for kind in attribute.kinds:
                        if self.isKindOf(kind):
                            break
                    yield (name, attribute, kind)

    def _inheritAttribute(self, name):

        if self.hasValue('notFoundAttributes', name):
            return None

        cache = True
        for superKind in self.superKinds:
            if superKind is not None:
                attribute = superKind.getAttribute(name, True)
                if attribute is not None:
                    self.addValue('inheritedAttributes', attribute, alias=name)
                    return attribute
            else:
                cache = False
                    
        if cache:
            self.addValue('notFoundAttributes', name)

        return None

    def getItemKind(self):

        return self._kind.itsParent['Item']

    def mixin(self, superKinds):
        """
        Find or generate a mixin kind.

        The mixin kind is defined as the combination of this kind and the
        additional kind items specified with C{superKinds}.
        A new kind is generated if the corresponding mixin kind doesn't yet
        exist. The item class of the resulting mixin kind is a composite of
        the superKinds' item classes. See L{getItemClass} for more
        information.

        @param superKinds: the kind items added to this kind to form the mixin
        @type superKinds: list
        @return: a L{Kind<repository.schema.Kind.Kind>} instance
        """

        duplicates = {}
        for superKind in superKinds:
            if superKind._uuid in duplicates:
                raise ValueError, 'Kind %s is duplicated' %(superKind.itsPath)
            else:
                duplicates[superKind._uuid] = superKind
                
        hash = _uuid.combine(0, self._uuid._hash)
        for superKind in superKinds:
            hash = _uuid.combine(hash, superKind._uuid._hash)
        if hash < 0:
            hash = ~hash
        name = "mixin_%08x" %(hash)
        parent = self.getItemKind().itsParent['Mixins']

        kind = parent.getItemChild(name)
        if kind is None:
            kind = Kind(name, parent, self._kind)

            kind.addValue('superKinds', self)
            kind.superKinds.extend(superKinds)
            kind.addValue('mixins', self._uuid)
            kind.mixins.extend([sk._uuid for sk in superKinds])
            
        return kind
        
    def isMixin(self):

        return 'mixins' in self._values

    def isAlias(self):

        return False

    def isKindOf(self, superKind):

        if self is superKind:
            return True

        superKinds = self.superKinds

        if len(superKinds) > 0:
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
            for name, attribute, k in self.iterAttributes():
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
                    value = value._copy(item, name, value._companion,
                                        'copy', lambda x, other, z: other)
                elif isinstance(value, ItemValue):
                    value = value._copy(item, name)

                values[name] = value

        for name, value in self._initialReferences.iteritems():
            if name not in references:
                otherName = self.getOtherName(name)
                if isinstance(value, PersistentCollection):
                    refList = references[name] = item._refList(name, otherName)
                    for other in value.itervalues():
                        refList.append(other)
                else:
                    references._setValue(name, value, otherName)

    def flushCaches(self):
        """
        Flush the caches setup on this Kind and its subKinds.

        This method should be called when following properties have been
        changed:

            - the kind's item class, the value of C{self.classes['python']},
              see L{getItemClass} for more information

            - the kind's attributes list or some attributes' initial values

            - the kind's superKinds list

        The caches of the subKinds of this kind are flushed recursively.
        """

        self.inheritedAttributes.clear()
        del self.notFoundAttributes[:]
        self._initialValues = None
        self._initialReferences = None

        # clear auto-generated composite class
        if self._values._isTransient('classes'):
            self._values._clearTransient('classes')
            del self._values['classes']

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

    def getClouds(self, cloudAlias=None):
        """
        Get clouds for this kind, inheriting them if necessary.

        If there are no matching clouds, the matching clouds of the direct
        superKinds are returned, recursively.

        if C{cloudAlias} is not specified or C{None}, the first cloud of
        each cloud list traversed is returned.

        @return: a L{Cloud<repository.schema.Cloud.Cloud>} list, possibly empty
        """

        results = []
        clouds = self.getAttributeValue('clouds', default=None,
                                        _attrDict=self._references)

        if clouds is None or (cloudAlias is not None and
                              clouds.resolveAlias(cloudAlias) is None):
            for superKind in self.superKinds:
                results.extend(superKind.getClouds(cloudAlias))

        elif cloudAlias is not None:
            results.append(clouds.getByAlias(cloudAlias))

        elif len(clouds) > 0:
            results.append(clouds.first())

        return results


    NoneString = "__NONE__"
