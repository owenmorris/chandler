
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from new import classobj

from repository.item.Item import Item
from repository.item.Values import ItemValue
from repository.item.PersistentCollections import PersistentCollection
from repository.item.ItemError import NoSuchAttributeError, SchemaError
from repository.persistence.RepositoryError import RecursiveLoadItemError
from repository.util.Path import Path
from chandlerdb.util.UUID import UUID, _uuid
from repository.util.SingleRef import SingleRef
from repository.item.Monitors import Monitors, Monitor

class Kind(Item):

    def __init__(self, name, parent, kind):

        super(Kind, self).__init__(name, parent, kind)

        self.monitorValue('attributes', set=True, _attrDict=self._references)
        self.monitorValue('superKinds', set=True, _attrDict=self._references)
        self.monitorAttributes = False
        self.__init()
        
    def __init(self):

        # recursion avoidance
        self._values['notFoundAttributes'] = []
        refList = self._refList('inheritedAttributes',
                                'inheritingKinds', False)
        self._references['inheritedAttributes'] = refList

        ofKind = self._refList('ofKind', 'kindOf', False)
        self._references['ofKind'] = ofKind

        self._status |= Item.SCHEMA | Item.PINNED

        self.__dict__['_initialValues'] = None
        self.__dict__['_initialReferences'] = None

    def _fillItem(self, name, parent, kind, **kwds):

        super(Kind, self)._fillItem(name, parent, kind, **kwds)
        if not kwds['update']:
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

            if self._values.get('defaultKind', False):
                try:
                    uuid = cls.__dict__['_defaultKind']
                except KeyError:
                    cls._defaultKind = self._uuid
                else:
                    if uuid != self._uuid:
                        if self.find(uuid) is not None:
                            raise SchemaError, ("Cannot set class %s.%s _defaultKind attribute to %s's UUID, it is already set to %s", self.itsPath, cls.__module__, cls.__name__, uuid)
                        else:
                            cls._defaultKind = self._uuid

            self.monitorAttributes = True
            self._setupDescriptors(cls)

        except RecursiveLoadItemError:
            kinds[uuid].remove(cls)
            classes[cls].remove(uuid)

    def _setupDescriptors(self, cls, sync=False):

        try:
            descriptors = Kind._descriptors[cls]
        except KeyError:
            descriptors = Kind._descriptors[cls] = {}

        if sync:
            attributes = self.getAttributeValue('attributes',
                                                _attrDict=self._references,
                                                default=[])
            for name, descriptor in descriptors.items():
                attr = descriptor.getAttribute(self)
                if not (attr is None or attr[0] in attributes):
                    if descriptor.unregisterAttribute(self):
                        delattr(cls, name)

        for name, attribute, k in self.iterAttributes():
            descriptor = cls.__dict__.get(name, None)
            if descriptor is None:
                descriptor = Descriptor(name)
                descriptors[name] = descriptor
                setattr(cls, name, descriptor)
                descriptor.registerAttribute(self, attribute)
            elif type(descriptor) is Descriptor:
                descriptor.registerAttribute(self, attribute)
            else:
                self.itsView.logger.warn("Not installing attribute descriptor for '%s' since it would shadow already existing descriptor: %s", name, descriptor)

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
        for superKind in self.getAttributeValue('superKinds',
                                                _attrDict=self._references):
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
        self._setupClass(c)

        return c

    def check(self, recursive=False):

        result = super(Kind, self).check(recursive)
        
        if not self.getAttributeValue('superKinds', default=None,
                                      _attrDict = self._references):
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
                attr = descriptor.getAttribute(self)
                if attr is not None:
                    clsDescriptor = cls.__dict__.get(name, None)
                    if clsDescriptor is not descriptor:
                        self.itsView.logger.warn("Descriptor for attribute '%s', %s, on class %s doesn't match descriptor on Kind %s, %s", name, clsDescriptor, cls, self.itsPath, descriptor)
                        result = False
                    attribute = self.getAttribute(name, True)
                    if attribute is None:
                        self.itsView.logger.warn("Descriptor for attribute '%s' on class %s doesn't correspond to an attribute on Kind %s", name, cls, self.itsPath)
                        result = False
                    else:
                        if attr[0] != attribute._uuid:
                            self.itsView.logger.warn("Descriptor for attribute '%s' on class %s doesn't correspond to the attribute of the same name on Kind %s", name, cls, self.itsPath)
                            result = False

        return result
        
    def resolve(self, name):

        child = self.getItemChild(name)
        if child:
            return child._uuid

        references = self._references
        if self.hasAttributeValue('attributes', _attrDict=references):
            return self.getAttributeValue('attributes', _attrDict=references).resolveAlias(name)

        return None

    def getAttribute(self, name, noError=False):
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

        refs = self._references
        child = self.getItemChild(name)

        if 'attributes' in refs:
            attrs = refs['attributes']
            if child is not None and child in attrs:
                return child
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
            references = self._references
            inheritedAttributes = self.getAttributeValue('inheritedAttributes',
                                                         _attrDict=references)
            for superKind in self.getAttributeValue('superKinds',
                                                    _attrDict=references):
                for name, attribute, k in superKind.iterAttributes():
                    if (attribute._uuid not in inheritedAttributes and
                        inheritedAttributes.resolveAlias(name) is None):
                        inheritedAttributes.append(attribute, alias=name)
            for uuid in inheritedAttributes.iterkeys():
                link = inheritedAttributes._get(uuid)
                name = link._alias
                if not self.resolve(name):
                    attribute = link.getValue(self)
                    for kind in attribute.getAttributeValue('kinds', _attrDict=attribute._references):
                        if self.isKindOf(kind):
                            break
                    yield (name, attribute, kind)

    def _inheritAttribute(self, name):

        if self.hasValue('notFoundAttributes', name):
            return None

        cache = True
        for superKind in self.getAttributeValue('superKinds',
                                                _attrDict=self._references):
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
            kind = self._kind.newItem(name, parent)

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

        return superKind in self._kindOf()

    def _kindOf(self):

        try:
            return self._references['kindOf']

        except KeyError:
            kindOf = self._refList('kindOf', 'ofKind', False)
            self._references['kindOf'] = kindOf
            for superKind in self.getAttributeValue('superKinds',
                                                    _attrDict=self._references):
                kindOf.append(superKind)
                kindOf.update(superKind._kindOf())

            return kindOf

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

        isNew = item.isNew()

        for name, value in self._initialValues.iteritems():
            if name not in values:
                if isinstance(value, PersistentCollection):
                    value = value._copy(item, name, value._companion,
                                        'copy', lambda x, other, z: other)
                elif isinstance(value, ItemValue):
                    value = value._copy(item, name)

                values[name] = value
                if not isNew:   # __setKind case
                    item.setDirty(Item.VDIRTY, name,
                                  attrDict=values, noMonitors=True)

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
                    item.setDirty(Item.RDIRTY, name,
                                  attrDict=references, noMonitors=True)

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

    def writeValue(self, itemWriter, buffer, item, value, withSchema):

        if value is None:
            buffer.write('\0')
        else:
            buffer.write('\1')
            buffer.write(value.itsUUID._uuid)

    def readValue(self, itemReader, offset, data, withSchema, view, name):

        if data[offset] == '\0':
            return offset+1, None
        
        return offset+17, SingleRef(UUID(data[offset+1:offset+17]))

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

    def getClouds(self, cloudAlias):
        """
        Get clouds for this kind, inheriting them if necessary.

        If there are no matching clouds, the matching clouds of the direct
        superKinds are returned, recursively.

        @return: a L{Cloud<repository.schema.Cloud.Cloud>} list, possibly empty
        """

        results = []
        clouds = self.getAttributeValue('clouds', default=None,
                                        _attrDict=self._references)

        if clouds is None or clouds.resolveAlias(cloudAlias) is None:
            for superKind in self.getAttributeValue('superKinds',
                                                    _attrDict=self._references):
                results.extend(superKind.getClouds(cloudAlias))

        else:
            results.append(clouds.getByAlias(cloudAlias))

        return results


    NoneString = "__NONE__"
    _classes = {}
    _kinds = {}
    _descriptors = {}
    

class Descriptor(object):

    def __init__(self, name):

        self.name = name
        self.attrs = {}

    def registerAttribute(self, kind, attribute):

        if 'otherName' in attribute._values:
            flags = Descriptor.REF
        elif 'redirectTo' in attribute._values:
            flags = Descriptor.REDIRECT
        else:
            flags = Descriptor.VALUE

        self.attrs[kind._uuid] = (attribute._uuid, flags)

    def unregisterAttribute(self, kind):

        del self.attrs[kind._uuid]
        return len(self.attrs) == 0

    def getAttribute(self, kind):

        return self.attrs.get(kind._uuid, None)

    def getName(self):

        return self.name

    def getAttrDict(self, obj, flags):

        if flags & Descriptor.VALUE:
            return obj._values
        elif flags & Descriptor.REF:
            return obj._references
        elif flags & Descriptor.REDIRECT:
            return None

        raise AssertionError, (self.name, flags)

    def __get__(self, obj, owner):

        if obj is None:
            raise AttributeError, self.name

        kind = obj._kind
        if kind is not None:
            try:
                attrID, flags = self.attrs[kind._uuid]
                attrDict = self.getAttrDict(obj, flags)
            except KeyError:
                pass
            else:
                return obj.getAttributeValue(self.name,
                                             _attrDict=attrDict,
                                             _attrID=attrID)

        try:
            return obj.__dict__[self.name]
        except KeyError:
            raise AttributeError, self.name
            
    def __set__(self, obj, value):

        if obj is None:
            raise AttributeError, self.name

        kind = obj._kind
        if kind is not None:
            try:
                attrID, flags = self.attrs[kind._uuid]
                attrDict = self.getAttrDict(obj, flags)
            except KeyError:
                pass
            else:
                return obj.setAttributeValue(self.name, value,
                                             _attrDict=attrDict,
                                             _attrID=attrID)
                
        obj.__dict__[self.name] = value

    def __delete__(self, obj):

        if obj is None:
            raise AttributeError, self.name

        kind = obj._kind
        if kind is not None:
            try:
                attrID, flags = self.attrs[kind._uuid]
                attrDict = self.getAttrDict(obj, flags)
            except KeyError:
                pass
            else:
                return obj.removeAttributeValue(self.name,
                                                _attrDict=attrDict,
                                                _attrID=attrID)

        try:
            del obj.__dict__[self.name]
        except KeyError:
            raise AttributeError, self.name

    VALUE    = 0x0001
    REF      = 0x0002
    REDIRECT = 0x0004


class SchemaMonitor(Monitor):

    def schemaChange(self, op, kind, attrName):

        if isinstance(kind, Kind) and kind.monitorAttributes:
            kind.flushCaches()
            logger = kind.itsView.logger
            for cls in Kind._kinds.get(kind._uuid, []):
                logger.warning('Change in %s caused syncing of attribute descriptors on class %s.%s for Kind %s', attrName, cls.__module__, cls.__name__, kind.itsPath)
                kind._setupDescriptors(cls, True)
