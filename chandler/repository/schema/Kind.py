
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from new import classobj

from chandlerdb.util.uuid import UUID, _hash, _combine
from chandlerdb.schema.descriptor import CDescriptor
from chandlerdb.item.item import Nil, Default
from chandlerdb.item.ItemError import NoSuchAttributeError, SchemaError

from repository.item.Item import Item
from repository.item.Monitors import Monitor
from repository.item.Values import ItemValue, Values, References
from repository.item.PersistentCollections import PersistentCollection
from repository.persistence.RepositoryError import RecursiveLoadItemError
from repository.util.Path import Path
from repository.util.SingleRef import SingleRef
from repository.schema.TypeHandler import TypeHandler
from repository.item.Query import KindQuery


class Kind(Item):

    def __init__(self, name, parent, kind):

        super(Kind, self).__init__(name, parent, kind)
        self.__init()
        
    def __init(self):

        self.monitorSchema = False

        # recursion avoidance
        self._values['notFoundAttributes'] = []
        refList = self._refList('inheritedAttributes', 'inheritingKinds', False)
        self._references['inheritedAttributes'] = refList

        ofKind = self._refList('ofKind', 'kindOf', False)
        self._references['ofKind'] = ofKind

        self._status |= Item.SCHEMA | Item.PINNED

        self.__dict__['_initialValues'] = None
        self.__dict__['_initialReferences'] = None

    def _fillItem(self, name, parent, kind, **kwds):

        super(Kind, self)._fillItem(name, parent, kind, **kwds)
        if not kwds.get('update'):
            self.__init()

    def onItemLoad(self, view):

        # force-load attributes for schema bootstrapping
        if 'attributes' in self._references:
            for attribute in self._references['attributes']:
                pass

    def _setupClass(self, cls):

        try:
            uuid = self._uuid
            classes = Kind._classes
            kinds = Kind._kinds

            try:
                kinds[uuid].add(cls)
            except KeyError:
                kinds[uuid] = set((cls,))

            try:
                if uuid in classes[cls]:
                    return
                classes[cls].add(uuid)
            except KeyError:
                classes[cls] = set((uuid,))

            self.monitorSchema = True
            self._setupDescriptors(cls)

        except RecursiveLoadItemError:
            kinds[uuid].remove(cls)
            classes[cls].remove(uuid)

    def _getDescriptors(self, cls):

        return Kind._descriptors.get(cls, {})

    def _setupDescriptors(self, cls, sync=None):

        try:
            descriptors = Kind._descriptors[cls]
        except KeyError:
            descriptors = Kind._descriptors[cls] = {}

        if sync is not None:
            if sync == 'attributes':
                attributes = self.getAttributeValue('attributes',
                                                    self._references, None, [])
            elif sync == 'superKinds':
                attributes = set(a._uuid for n, a, k in self.iterAttributes())
            else:
                raise AssertionError, sync
            
            for name, descriptor in descriptors.items():
                try:
                    attrId, flags = descriptor.getAttribute(self)
                except KeyError:
                    pass
                else:
                    if attrId not in attributes:
                        if descriptor.unregisterAttribute(self):
                            delattr(cls, name)

        for name, attribute, k in self.iterAttributes():
            descriptor = cls.__dict__.get(name, None)
            if descriptor is None:
                descriptor = CDescriptor(name)
                descriptors[name] = descriptor
                setattr(cls, name, descriptor)
                descriptor.registerAttribute(self, attribute)
            elif isinstance(descriptor, CDescriptor):
                descriptor.registerAttribute(self, attribute)
            else:
                self.itsView.logger.warn("Not installing attribute descriptor for '%s' since it would shadow already existing descriptor: %s", name, descriptor)

    def newItem(self, name=None, parent=None, cls=None, **values):
        """
        Create an new item of this kind.

        The python class instantiated is taken from the Kind's classes
        attribute if it is set. The Item class is used otherwise.

        The item's constructor is invoked.

        @param name: The name of the item. It must be unique among the names
        this item's siblings. C{name} may be C{None}.
        @type name: a string or C{None} to create an anonymous item.
        @param parent: The parent of this item. C{parent} is
        optional. When ommitted, the item is made a root of either the
        C{kind}'s view or of the global null view.
        @type parent: an item or the item's repository view
        @param cls: an optional python class to instantiate the item with,
        defaults to the class set on this kind.
        @type cls: a python new style class, that is, a type instance
        """

        if cls is None:
            cls = self.getItemClass()
        
        return cls(name, parent, self, **values)

    def instantiateItem(self, name, parent, uuid,
                        cls=None, version=0, withInitialValues=False):
        """
        Instantiate an existing item of this kind.

        This method is intended to help in instantiating an existing item,
        that is an item in this or another repository for which there
        already exists a UUID.

        The item's constructor is not invoked, the item's onItemLoad
        method is invoked if defined.

        @param name: The name of the item. It must be unique among the names
        this item's siblings. C{name} may be C{None}.
        @type name: a string or C{None} to create an anonymous item.
        @param parent: The parent of this item. All items require a parent
        unless they are a repository root in which case C{parent} is a
        repository view.
        @type parent: an item or the item's repository view
        @param uuid: The uuid for the item.
        @type uuid: L{UUID<chandlerdb.util.uuid.UUID>}
        @param cls: an optional python class to instantiate the item with,
        defaults to the class set on this kind.
        @type cls: a python new style class, that is, a type instance
        @param version: the optional version of this item instance, zero by
        default.
        @type version: integer
        @param withInitialValues: optionally set the initial values for
        attributes as specified in this Kind's attribute definitions.
        @type withInitialValues: boolean
        """

        if cls is None:
            cls = self.getItemClass()

        values = Values(None)
        references = References(None)

        item = cls.__new__(cls)
        item._fillItem(name, parent, self,
                       uuid=uuid, version=version,
                       values=values, references=references)

        values._setItem(item)
        references._setItem(item)
        self._setupClass(cls)

        if withInitialValues:
            self.getInitialValues(item, values, references)

        if hasattr(cls, 'onItemLoad'):
            item.onItemLoad(self.itsView)

        return item
            
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
        
        for superKind in self.getAttributeValue('superKinds', self._references):
            c = superKind.getItemClass()
            if c is not Item and c not in superClasses:
                superClasses.append(c)

        count = len(superClasses)

        if count == 0:
            c = Item
        elif count == 1:
            c = superClasses[0]
        else:
            hash = 0
            for c in superClasses:
                hash = _combine(hash, _hash('.'.join((c.__module__,
                                                      c.__name__))))
            if hash < 0:
                hash = ~hash
            name = "class_%08x" %(hash)
            c = classobj(name, tuple(superClasses), {})

        self._values['classes'] = { 'python': c }
        self._values._setTransient('classes')
        self._setupClass(c)

        return c

    def check(self, recursive=False):

        result = super(Kind, self).check(recursive)
        
        if not self.getAttributeValue('superKinds', self._references):
            if self is not self.getItemKind():
                self.itsView.logger.warn('No superKinds for %s', self.itsPath)
                result = False

        itemClass = self.getItemClass()
        result = self._checkClass(itemClass, True)

        classes = Kind._kinds.get(self._uuid)
        if classes is not None:
            for cls in classes:
                if cls is not itemClass:
                    result = self._checkClass(cls, False) and result

        attrs = self._references.get('attributes', None)
        if attrs:
            if attrs._aliases is None or len(attrs) != len(attrs._aliases):
                self.itsView.logger.warn("Attributes list aliases for %s doesn't attributes list", self.itsPath)
                result = False

        return result

    def _checkClass(self, cls, isItemClass):

        result = True

        def checkInheritance(cls):
            if cls is not Item:
                if not (isinstance(cls, type) and issubclass(cls, Item)):
                    return cls
                for base in cls.__bases__:
                    if checkInheritance(base) is not None:
                        return base
            return None

        problemCls = checkInheritance(cls)
        if problemCls is not None:
            self.itsView.logger.warn('Kind %s has an item class or superclass that is not a subclass of Item: %s %s', self.itsPath, problemCls, type(problemCls))
            result = False

        descriptors = Kind._descriptors.get(cls)
        if descriptors is None:
            if not isItemClass:
                self.itsView.logger.warn("No descriptors for class %s but Kind %s seems to think otherwise", cls, self.itsPath)
                result = False
        else:
            for name, descriptor in descriptors.iteritems():
                try:
                    attrId, flags = descriptor.getAttribute(self)
                except KeyError:
                    pass
                else:
                    clsDescriptor = cls.__dict__.get(name, None)
                    if clsDescriptor is not descriptor:
                        self.itsView.logger.warn("Descriptor for attribute '%s', %s, on class %s doesn't match descriptor on Kind %s, %s", name, clsDescriptor, cls, self.itsPath, descriptor)
                        result = False
                    attribute = self.getAttribute(name, True)
                    if attribute is None:
                        self.itsView.logger.warn("Descriptor for attribute '%s' on class %s doesn't correspond to an attribute on Kind %s", name, cls, self.itsPath)
                        result = False
                    else:
                        if attrId != attribute._uuid:
                            self.itsView.logger.warn("Descriptor for attribute '%s' on class %s doesn't correspond to the attribute of the same name on Kind %s", name, cls, self.itsPath)
                            result = False

        return result
        
    def getAttribute(self, name, noError=False, item=None):
        """
        Get an attribute definition item.

        The attribute is sought on the kind and on its superKinds in a left
        to right depth-first manner. If no attribute is found a subclass of
        C{AttributeError} is raised.

        @param name: the name of the attribute sought
        @type name: a string
        @return: an L{Attribute<repository.schema.Attribute.Attribute>} item
        instance
        """

        if item is not None:
            try:
                descriptor = Kind._descriptors[type(item)][name]
            except KeyError:
                pass
            else:
                try:
                    attrId, flags = descriptor.getAttribute(self)
                except KeyError:
                    pass
                else:
                    return self.itsView.find(attrId)

        refs = self._references
        attrs = refs.get('attributes', None)

        if attrs is not None:
            attribute = attrs.getByAlias(name)
        else:
            attribute = None
            
        if attribute is None:
            attribute = refs['inheritedAttributes'].getByAlias(name)

            if attribute is None:
                attribute = self._inheritAttribute(name)

                if attribute is None and noError is False:
                    raise NoSuchAttributeError, (self, name)

        return attribute

    def hasAttribute(self, name):

        attributes = self._references.get('attributes', None)
        if attributes is not None:
            uuid = attributes.resolveAlias(name)
        else:
            uuid = None

        if uuid is not None:
            return True
        elif self.inheritedAttributes.resolveAlias(name):
            return True
        else:
            return self._inheritAttribute(name) is not None

    def getOtherName(self, name, _attrID=None, item=None, default=Default):

        otherNames = self._values.get('otherNames', None)
        if otherNames is not None:
            otherName = otherNames[name]
        else:
            otherName = None

        if otherName is None:
            if _attrID is not None:
                attribute = self.find(_attrID)
            else:
                attribute = self.getAttribute(name, False, item)

            otherName = attribute._values.get('otherName', None)
            if otherName is None:
                if default is not Default:
                    return default
                raise TypeError, 'Undefined otherName for attribute %s on kind %s' %(name, self.itsPath)

        return otherName

    def iterAttributes(self, inherited=True,
                       localOnly=False, globalOnly=False):
        """
        Return a generator of C{(name, attribute, kind)} tuples for
        iterating over the Chandler attributes defined for and inherited by
        this kind. The C{kind} element is the kind the attribute was
        inherited from or this kind.

        The name of an attribute is defined to be the alias with which it was
        added into the kind's C{attributes} attribute. This alias name may
        of course be the same as the corresponding attribute's item name.

        @param inherited: if C{True}, iterate also over attributes that are
        inherited by this kind via its superKinds.
        @type inherited: boolean
        @param localOnly: if C{True}, only pairs for local attributes are
        returned. Local attributes are defined as direct children items
        of the kinds they're defined on and are not meant to be shared
        except through inheritance.
        @type localOnly: boolean
        @param globalOnly: if C{True}, only pairs for the global attributes
        are returned. Global attributes are not defined as direct children
        items and are intended to be shareable by multiple kinds.
        @type globalOnly: boolean
        """

        references = self._references
        attributes = references.get('attributes', None)

        if attributes is not None:

            if not globalOnly:
                for attribute in attributes:
                    if attribute.itsParent is self:
                        yield (attributes.getAlias(attribute), attribute, self)

            if not localOnly:
                for attribute in attributes:
                    if attribute.itsParent is not self:
                        yield (attributes.getAlias(attribute), attribute, self)

        if inherited:
            inheritedAttributes = self.getAttributeValue('inheritedAttributes',
                                                         references)
            for superKind in self.getAttributeValue('superKinds', references):
                for name, attribute, k in superKind.iterAttributes():
                    if (attribute._uuid not in inheritedAttributes and
                        inheritedAttributes.resolveAlias(name) is None):
                        inheritedAttributes.append(attribute, alias=name)
            for uuid in inheritedAttributes.iterkeys():
                link = inheritedAttributes._get(uuid)
                name = link._alias
                if (attributes is None or
                    attributes.resolveAlias(name) is None):
                    attribute = link.getValue(self)
                    for kind in attribute.getAttributeValue('kinds', attribute._references):
                        if self.isKindOf(kind):
                            break
                    yield (name, attribute, kind)

    def _inheritAttribute(self, name):

        if self.hasValue('notFoundAttributes', name):
            return None

        cache = True
        for superKind in self.getAttributeValue('superKinds', self._references):
            if superKind is not None:
                attribute = superKind.getAttribute(name, True)
                if attribute is not None:
                    self._references['inheritedAttributes'].append(attribute, alias=name)
                    return attribute
            else:
                cache = False
                    
        if cache:
            self._values['notFoundAttributes'].append(name)

        return None

    def iterItems(self, recursive=False):

        for item in KindQuery(recursive).run((self,)):
            yield item

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
                
        hash = self.hashItem()
        for superKind in superKinds:
            hash = _combine(hash, superKind.hashItem())
        if hash < 0:
            hash = ~hash
        name = "mixin_%08x" %(hash)
        parent = self.getItemKind().itsParent['Mixins']

        kind = parent.getItemChild(name)
        if kind is None:
            kind = self._kind.newItem(name, parent)

            kind.addValue('superKinds', self)
            kind.superKinds.extend(superKinds)
            kind.mixins = [sk.itsPath for sk in kind.superKinds]
            
        return kind
        
    def isMixin(self):

        return 'mixins' in self._values

    def isAlias(self):

        return False

    def isKindOf(self, superKind):

        if self is superKind:
            return True

        return superKind in self._kindOf()

    def _kindOf(self):

        try:
            return self._references['kindOf']

        except KeyError:
            kindOf = self._refList('kindOf', 'ofKind', False)
            self._references['kindOf'] = kindOf
            for superKind in self.getAttributeValue('superKinds',
                                                    self._references):
                kindOf.append(superKind)
                kindOf.update(superKind._kindOf())

            return kindOf

    def getInitialValues(self, item, values, references):

        # setup cache
        if self._initialValues is None:
            self._initialValues = {}
            self._initialReferences = {}
            for name, attribute, k in self.iterAttributes():
                value = attribute.getAspect('initialValue', Nil)
                if value is not Nil:
                    otherName = self.getOtherName(name, None, None, None)
                    if otherName is None:
                        self._initialValues[name] = value
                    else:
                        self._initialReferences[name] = value

        isNew = item.isNew()

        for name, value in self._initialValues.iteritems():
            if name not in values:
                if isinstance(value, PersistentCollection):
                    value = value._copy((item, name, value._owner[2]),
                                        'copy', lambda x, other, z: other)
                elif isinstance(value, ItemValue):
                    value = value._copy(item, name)

                values[name] = value
                if not isNew:   # __setKind case
                    item.setDirty(Item.VDIRTY, name, values, True)

        for name, value in self._initialReferences.iteritems():
            if name not in references:
                otherName = self.getOtherName(name)
                if isinstance(value, PersistentCollection):
                    refList = references[name] = item._refList(name, otherName)
                    for other in value.itervalues():
                        refList.append(other)
                else:
                    references._setValue(name, value, otherName)
                if not isNew:   # __setKind case
                    item.setDirty(Item.RDIRTY, name, references, True)

    def flushCaches(self, reason, silent=False):
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

        for subKind in self.getAttributeValue('subKinds', self._references,
                                              None, []):
            subKind.flushCaches(reason, silent)

        if reason is not None:
            logger = self.itsView.logger
            for cls in Kind._kinds.get(self._uuid, []):
                if not silent:
                    logger.warning('Change in %s caused syncing of attribute descriptors on class %s.%s for Kind %s', reason, cls.__module__, cls.__name__, self.itsPath)
                self._setupDescriptors(cls, reason)

        if 'schemaHash' in self._values:
            del self.schemaHash

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

    def writeValue(self, itemWriter, buffer, item, version, value, withSchema):

        if value is None:
            buffer.write('\0')
            return 1
        else:
            buffer.write('\1')
            buffer.write(value.itsUUID._uuid)
            return 17

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        if data[offset] == '\0':
            return offset+1, None
        
        return offset+17, SingleRef(UUID(data[offset+1:offset+17]))

    def hashValue(self, value):

        if value is None:
            return 0

        return TypeHandler.hashValue(self.itsView, SingleRef(value.itsUUID))

    def indexValue(self, itemWriter, item, name, version, value):

        pass

    def handlerName(self):

        return 'ref'
    
    def recognizes(self, value):

        if value is None:
            return True

        if isinstance(value, SingleRef):
            item = self.itsView.find(value.itsUUID)
            if item is not None:
                return item.isItemOf(self)
            return True

        if isinstance(value, Item):
            return value.isItemOf(self)
    
        return False

    def getFlags(self):

        return CDescriptor.KIND | CDescriptor.PROCESS

    # end typeness of Kind as SingleRef

    def getClouds(self, cloudAlias):
        """
        Get clouds for this kind, inheriting them if necessary.

        If there are no matching clouds, the matching clouds of the direct
        superKinds are returned, recursively.

        @return: a L{Cloud<repository.schema.Cloud.Cloud>} list, possibly empty
        """

        results = []
        clouds = self.getAttributeValue('clouds', self._references, None, None)

        if clouds is None or clouds.resolveAlias(cloudAlias) is None:
            for superKind in self.getAttributeValue('superKinds',
                                                    self._references):
                results.extend(superKind.getClouds(cloudAlias))

        else:
            results.append(clouds.getByAlias(cloudAlias))

        return results

    def _hashItem(self):

        hash = 0
        isMixin = self.isMixin()

        if not isMixin:
            hash = _combine(hash, _hash(str(self.itsPath)))

        for superKind in self.getAttributeValue('superKinds', self._references):
            hash = _combine(hash, superKind.hashItem())

        if not isMixin:
            attributes = list(self.iterAttributes(False))
            attributes.sort()
            for name, attribute, kind in attributes:
                hash = _combine(hash, _hash(name))
                hash = _combine(hash, attribute.hashItem())

        return hash

    def hashItem(self):
        """
        Compute a hash value from this kind's schema.

        The hash value is computed from the kind's path (unless it is a
        mixin kind), superKind and locally defined name - attribute item
        hashes.

        @return: an integer
        """

        if 'schemaHash' in self._values:
            return self.schemaHash

        self.schemaHash = hash = self._hashItem()
        return hash

    def onValueChanged(self, name):

        if name == 'attributeHash':
            if 'schemaHash' in self._values:
                del self.schemaHash

    def findMatch(self, view, matches=None):

        uuid = self._uuid

        if matches is not None:
            match = matches.get(uuid)
        else:
            match = None
            
        if match is None:
            match = view.find(uuid)
            if match is None:
                match = view.find(self.itsPath)
                if not (match is None or matches is None):
                    if not (self is match or
                            self.hashItem() == match.hashItem()):
                        raise SchemaError, ("kind matches are incompatible: %s %s", self.itsPath, match.itsPath)
                    matches[uuid] = match

        return match

    def _printItemBody(self, _level):

        print ' ' * (_level + 2), "attributes for this kind:"

        displayedAttrs = {}
        for (name, attr, k) in self.iterAttributes():
            displayedAttrs[name] = attr

        keys = displayedAttrs.keys()
        keys.sort()
        indent = ' ' * (_level + 4)
        for key in keys:
            print indent, key, displayedAttrs[key].itsPath

        super(Kind, self)._printItemBody(_level)


    NoneString = "__NONE__"
    _classes = {}
    _kinds = {}
    _descriptors = {}
    

class SchemaMonitor(Monitor):

    def schemaChange(self, op, kind, attrName):

        if isinstance(kind, Kind) and kind.monitorSchema:
            kind.flushCaches(attrName)
