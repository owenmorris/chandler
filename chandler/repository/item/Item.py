
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import cStringIO

from repository.item.ItemRef import ItemRef, NoneRef, RefArgs
from repository.item.ItemRef import Values, References, RefDict
from repository.item.ItemHandler import ItemHandler
from repository.item.PersistentCollections import PersistentCollection
from repository.item.PersistentCollections import PersistentList
from repository.item.PersistentCollections import PersistentDict

from repository.util.SingleRef import SingleRef
from repository.util.UUID import UUID
from repository.util.Path import Path
from repository.util.LinkedMap import LinkedMap
from repository.util.SAX import XMLGenerator


class Item(object):
    'The root class for all items.'
    
    def __init__(self, name, parent, kind):
        """
        Construct an Item.

        @param name: The name of the item. It must be unique among the names
        this item's siblings. C{name} be C{None} in which case the base64
        string representation of this item's C{UUID} becomes its name.
        @type name: a string
        @param parent: The parent of this item. All items require a parent
        unless they are a repository root in which case the parent argument
        is the repository.
        @type parent: an item
        @param kind: The kind for this item. This kind has definitions for
        all the Chandler attributes that are to be used with this item.
        This parameter can be C{None} for Chandler attribute-less operation.
        Items have two sets of attributes: the regular implementation python
        attributes and the Chandler attributes. When an item is persisted
        only the Chandler attributes are saved.
        @type kind: an item
        """
        super(Item, self).__init__()

        self._status = Item.NEW
        self._version = 0L
        self._uuid = UUID()

        self._values = Values(self)
        self._references = References(self)
        
        self._name = name or self._uuid.str64()
        self._kind = None
        self._root = None

        self._setParent(parent)
        self._setKind(kind)

    def _fillItem(self, name, parent, kind, **kwds):

        self._uuid = kwds['uuid']
        self._name = name or self._uuid.str64()
        self._kind = None
        self._root = None
        self._status = 0
        self._version = kwds['version']

        kwds['values']._setItem(self)
        self._values = kwds['values']
        
        kwds['references']._setItem(self)
        self._references = kwds['references']

        self._setParent(parent, kwds.get('previous'), kwds.get('next'))
        self._setKind(kind)

    def __iter__(self):
        """
        Iterate over the children of this item.
        """

        return self.iterChildren()
    
    def __repr__(self):
        """
        The debugging string representation of an item.

        It follows the following format:

        C{<classname (optional status): name uuid>}

        where:
          - C{classname} is the name of the class implementing the item
          - C{optional status} is displayed when the item is stale or deleted
          - C{name} is the item's name
          - C{uuid} is the item's UUID
        """

        if self._status & Item.RAW:
            return super(Item, self).__repr__()

        if self._status & Item.DELETED:
            return "<%s (deleted): %s %s>" %(type(self).__name__, self._name,
                                             self._uuid.str16())
        if self._status & Item.STALE:
            return "<%s (stale): %s %s>" %(type(self).__name__, self._name,
                                           self._uuid.str16())
        
        return "<%s: %s %s>" %(type(self).__name__, self._name,
                               self._uuid.str16())

    def __getattr__(self, name):
        """
        This method is called by python when looking up a Chandler attribute.
        @param name: the name of the attribute being accessed.
        @type name: a string
        """

        return self.getAttributeValue(name)

    def __setattr__(self, name, value):
        """
        This method is called whenever an attribute's value is set.

        It resolves whether the attribute is a Chandler attribute or a regular
        python attribute and dispatches to the relevant methods.
        @param name: the name of the attribute being set.
        @type name: a string
        @param value: the value being set.
        @type value: anything
        """

        if name[0] != '_':
            if self._values.has_key(name):
                return self.setAttributeValue(name, value,
                                              _attrDict=self._values)
            elif self._references.has_key(name):
                return self.setAttributeValue(name, value,
                                              _attrDict=self._references)
            elif self._kind is not None and self._kind.hasAttribute(name):
                return self.setAttributeValue(name, value)

        return super(Item, self).__setattr__(name, value)

    def __delattr__(self, name):
        """
        This method is called whenever an attribute's value is removed.

        It resolves whether the attribute is a Chandler attribute or a regular
        python attribute and dispatches to the relevant methods.
        @param name: the name of the attribute being cleared.
        @type name: a string
        """

        if self._values.has_key(name):
            self.removeAttributeValue(name, _attrDict=self._values)
        elif self._references.has_key(name):
            self.removeAttributeValue(name, _attrDict=self._references)
        else:
            super(Item, self).__delattr__(name)

    def _otherName(self, name):

        otherName = None
        
        if self._kind is not None:
            attribute = self._kind.getAttribute(name)
            if attribute is not None:
                otherName = attribute.getAspect('otherName')

        if otherName is None:
            raise TypeError, 'Undefined other endpoint for %s.%s' %(self.getItemPath(), name)

        return otherName

    def hasAttributeAspect(self, name, aspect):

        if self._kind is not None:
            attribute = self._kind.getAttribute(name)
            if attribute is not None:
                return attribute.hasAspect(aspect)

        return False

    def getAttributeAspect(self, name, aspect, **kwds):

        if self._kind is not None:
            attribute = self._kind.getAttribute(name)
            if attribute is not None:
                return attribute.getAspect(aspect, **kwds)

        return kwds.get('default', None)

    def setAttributeValue(self, name, value=None, _attrDict=None):
        """Create and/or set a Chandler attribute.

        This method is only required when the Chandler attribute doesn't yet
        exist or when there is an ambiguity between a python and a Chandler
        attribute, a situation best avoided."""

        self.setDirty(attribute=name)

        isItem = isinstance(value, Item)
        isRef = not isItem and (isinstance(value, ItemRef) or
                                isinstance(value, RefDict))
        old = None

        if _attrDict is None:
            if self._values.has_key(name):
                _attrDict = self._values
            elif self._references.has_key(name):
                _attrDict = self._references
            elif self.getAttributeAspect(name, 'otherName', default=None):
                _attrDict = self._references
            else:
                _attrDict = self._values

        if _attrDict is self._references:
            if value is None:
                value = NoneRef
                isRef = True
            if name in _attrDict:
                old = _attrDict[name]

                if isinstance(old, ItemRef):
                    if isItem:
                        if old is not NoneRef:
                            # reattaching on original endpoint
                            old.reattach(self, name, old.other(self), value,
                                         self._otherName(name))
                            return value
                    elif isRef:
                        # reattaching on other endpoint,
                        # can't reuse ItemRef
                        old.detach(self, name, old.other(self),
                                   self._otherName(name))
                    else:
                        raise TypeError, type(value)

                elif isinstance(old, RefDict):
                    old.clear()

                else:
                    raise TypeError, type(old)

        if isItem:
            otherName = self.getAttributeAspect(name, 'otherName',
                                                default=None)
            card = self.getAttributeAspect(name, 'cardinality',
                                           default='single')

            if card != 'single':
                raise ValueError, 'cardinality %s of %s.%s requires collection' %(self, name, card)

            if otherName is None:
                self._values[name] = value = SingleRef(value.getUUID())

            else:
                value = ItemRef(self, name, value, otherName)
                self._references[name] = value

        elif isRef:
            self._references[name] = value

        elif isinstance(value, list):
            if _attrDict is self._references:
                if old is None:
                    self._references[name] = refDict = self._refDict(name)
                else:
                    assert isinstance(old, RefDict)
                    refDict = old
                refDict.extend(value)
                value = refDict
            else:
                companion = self.getAttributeAspect(name, 'companion',
                                                    default=None)
                value = PersistentList(self, name, companion, *value)
                self._values[name] = value

        elif isinstance(value, dict):
            if _attrDict is self._references:
                if old is None:
                    self._references[name] = refDict = self._refDict(name)
                else:
                    assert isinstance(old, RefDict)
                    refDict = old
                for item in value.itervalues():
                    refDict.append(item)
                value = refDict
            else:
                companion = self.getAttributeAspect(name, 'companion',
                                                    default=None)
                value = PersistentDict(self, name, companion, **value)
                self._values[name] = value
            
        elif isinstance(value, ItemValue):
            value._setItem(self, name)
            self._values[name] = value
            
        else:
            self._values[name] = value

        return value

    def getAttributeValue(self, name, _attrDict=None, **kwds):
        """Return the named Chandler attribute value.

        If the attribute is not set then attempt to inherit a value if the
        attribute's inheritFrom aspect is set, attempt to return the value
        of the optional 'default' keyword passed to this method, attempt to
        return the value of its defaultValue aspect if set, or finally raise 
        AttributeError. 
        Calling this method is only required when there is a name ambiguity
        between a python and a Chandler attribute, a situation best avoided."""

        if self._status & Item.STALE:
            raise ValueError, "item is stale: %s" %(self)

        try:
            if (_attrDict is self._values or
                _attrDict is None and name in self._values):
                value = self._values[name]
                if isinstance(value, SingleRef):
                    value = self.getRepository().find(value.getUUID())
                return value

            elif (_attrDict is self._references or
                  _attrDict is None and name in self._references):
                value = self._references[name]
                if isinstance(value, ItemRef):
                    return value.other(self)
                return value

        except KeyError:
            pass

        value = self.getAttributeAspect(name, 'initialValue', default=Item.Nil)
        if value is not Item.Nil:
            return self.setAttributeValue(name, value)

        inherit = self.getAttributeAspect(name, 'inheritFrom', default=None)
        if inherit is not None:
            value = self
            for attr in inherit.split('.'):
                value = value.getAttributeValue(attr)
            if isinstance(value, PersistentCollection):
                value.setReadOnly(True)
            return value

        elif kwds.has_key('default'):
            return kwds['default']

        value = self.getAttributeAspect(name, 'defaultValue', default=Item.Nil)
        if value is not Item.Nil:
            if isinstance(value, PersistentCollection):
                value.setReadOnly(True)
            return value

        raise AttributeError, "%s has no value for '%s'" %(self.getItemPath(),
                                                           name)

    def removeAttributeValue(self, name, _attrDict=None):
        "Remove a Chandler attribute's value."

        self.setDirty(attribute=name)

        if _attrDict is None:
            if self._values.has_key(name):
                _attrDict = self._values
            elif self._references.has_key(name):
                _attrDict = self._references

        if _attrDict is self._values:
            del _attrDict[name]
        elif _attrDict is self._references:
            value = _attrDict[name]

            if isinstance(value, ItemRef):
                value.detach(self, name,
                             value.other(self), self._otherName(name))
                del _attrDict[name]
            elif isinstance(value, RefDict):
                value.clear()
                del _attrDict[name]
            else:
                raise ValueError, value

    def hasChild(self, name, load=True):

        return (self.__dict__.has_key('_children') and
                self._children.has_key(name, load))

    def hasChildren(self):

        return (self.__dict__.has_key('_children') and
                self._children._firstKey is not None)

    def placeChild(self, child, after):
        """Place a child after another one in this item's children collection.

        To place a children in first position, pass None for after."""

        if not (child.getItemParent() is self):
            raise ValueError, '%s not a child of %s' %(child, self)
        if not (after is None or after.getItemParent() is self):
            raise ValueError, '%s not a child of %s' %(after, self)
        
        key = child.getItemName()
        if after is None:
            afterKey = None
        else:
            afterKey = after.getItemName()

        self._children.place(key, afterKey)

    def dir(self, recursive=True):
        'Print out a listing of each child under this item, recursively.'
        
        for child in self:
            print child.getItemPath()
            if recursive:
                child.dir(True)

    def iterChildren(self, load=True):

        if self._status & Item.STALE:
            raise ValueError, "item is stale: %s" %(self)

        if not load:
            if self.__dict__.has_key('_children'):
                for child in self._children._itervalues():
                    yield child._value

        elif self.__dict__.has_key('_children'):
            for child in self._children:
                yield child

    def iterAttributes(self, valuesOnly=False, referencesOnly=False):
        """Get a generator of (name, value) tuples for attributes of this item.

        By setting valuesOnly to True, no item references are returned.
        By setting referencesOnly to True, only references are returned."""

        if not referencesOnly:
            for attr in self._values.iteritems():
                yield attr

        if not valuesOnly:
            for ref in self._references.iteritems():
                if isinstance(ref[1], ItemRef):
                    yield (ref[0], ref[1].other(self))
                else:
                    yield ref

    def check(self, recursive=False):

        logger = self.getRepository().logger
        result = True

        def checkValue(name, value, attrType):

            if not attrType.recognizes(value):
                logger.error('Value %s of type %s in attribute %s on %s is not recognized by type %s', value, type(value), name, self.getItemPath(), attrType.getItemPath())

                return False

            return True

        def checkCardinality(name, value, cardType, attrCard):

            if not isinstance(value, cardType):
                logger.error('Value %s of type %s in attribute %s on %s is not an instance of type %s which is required for cardinality %s', value, type(value), name, self.getItemPath(), cardType, attrCard)

                return False

            return True

        for key, value in self._values.iteritems():
            attrType = self.getAttributeAspect(key, 'type', default=None)
            if attrType is not None:
                attrCard = self.getAttributeAspect(key, 'cardinality',
                                                   default='single')
                if attrCard == 'single':
                    check = checkValue(key, value, attrType)
                    result = result and check
                elif attrCard == 'list':
                    check = checkCardinality(key, value, list, 'list')
                    result = result and check
                    if check:
                        for v in value:
                            check = checkValue(key, v, attrType)
                            result = result and check
                elif attrCard == 'dict':
                    check = checkCardinality(key, value, dict, 'dict')
                    result = result and check
                    if check:
                        for v in value.itervalues():
                            check = checkValue(key, v, attrType)
                            result = result and check
        
        for key, value in self._references.iteritems():
            check = value.check(self, key)
            result = result and check

        if recursive:
            for child in self:
                check = child.check(True)
                result = result and check

        return result
        
    def getValue(self, attribute, key, default=None, _attrDict=None):
        'Get a value from a multi-valued attribute.'

        if _attrDict is None:
            value = (self._values.get(attribute, Item.Nil) or
                     self._references.get(attribute, Item.Nil))
        else:
            value = _attrDict.get(attribute, Item.Nil)
            
        if value is Item.Nil:
            return default

        if isinstance(value, dict):
            return value.get(key, default)

        if isinstance(value, list):
            if key < len(value):
                return value[key]
            else:
                return default

        raise TypeError, "%s is not multi-valued" %(attribute)

    def setValue(self, attribute, value, key=None, alias=None, _attrDict=None):
        """Set a value for a multi-valued attribute, for an optional key.

        When the cardinality of the attribute is 'list' and its type is a
        literals, key must be an integer.
        When the cardinality of the attribute is 'list' and its values are
        references, key may be an integer or the refName of the item value
        to set."""

        self.setDirty(attribute=attribute)

        if _attrDict is None:
            if self._values.has_key(attribute):
                _attrDict = self._values
            elif self._references.has_key(attribute):
                _attrDict = self._references
            elif self.getAttributeAspect(attribute, 'otherName', default=None):
                _attrDict = self._references
            else:
                _attrDict = self._values

        isItem = isinstance(value, Item)
        attrValue = _attrDict.get(attribute, Item.Nil)
            
        if attrValue is Item.Nil:
            card = self.getAttributeAspect(attribute, 'cardinality',
                                           default='single')

            if card == 'dict':
                if isItem and _attrDict is self._references:
                    attrValue = self._refDict(attribute)
                else:
                    companion = self.getAttributeAspect(attribute, 'companion',
                                                        default=None)
                    attrValue = PersistentDict(self, attribute, companion)
                    attrValue[key] = value
                    _attrDict[attribute] = attrValue
                    return attrValue

            elif card == 'list':
                if isItem and _attrDict is self._references:
                    attrValue = self._refDict(attribute)
                else:
                    companion = self.getAttributeAspect(attribute, 'companion',
                                                        default=None)
                    attrValue = PersistentList(self, attribute, companion,
                                               value)
                    _attrDict[attribute] = attrValue
                    return attrValue

            else:
                self.setAttributeValue(attribute, value, _attrDict)
                return value

            _attrDict[attribute] = attrValue

        if isItem:
            attrValue.__setitem__(value._refName(attribute),
                                  value, alias=alias)
        else:
            attrValue[key] = value

        return attrValue

    def addValue(self, attribute, value, key=None, alias=None, _attrDict=None):
        "Add a value for a multi-valued attribute for a given optional key."

        if _attrDict is None:
            if self._values.has_key(attribute):
                _attrDict = self._values
            elif self._references.has_key(attribute):
                _attrDict = self._references
            elif self.getAttributeAspect(attribute, 'otherName', default=None):
                _attrDict = self._references
            else:
                _attrDict = self._values

        isItem = isinstance(value, Item)
        attrValue = _attrDict.get(attribute, Item.Nil)

        if attrValue is Item.Nil:
            attrValue = self.getAttributeAspect(attribute, 'initialValue',
                                                default=Item.Nil)
            if attrValue is not Item.Nil:
                attrValue = self.setAttributeValue(attribute, attrValue)

        if attrValue is Item.Nil:
            self.setValue(attribute, value, key, alias, _attrDict)

        else:
            self.setDirty(attribute=attribute)

            if isinstance(attrValue, dict):
                if isItem and _attrDict is self._references:
                    attrValue.__setitem__(value._refName(attribute),
                                          value, alias=alias)
                else:
                    attrValue[key] = value
            elif isinstance(attrValue, list):
                attrValue.append(value)
            else:
                self.setAttributeValue(attribute, value, _attrDict)

    def hasKey(self, attribute, key):
        """Tell where a multi-valued attribute has a value for a given key.

        When the cardinality of the attribute is 'list' and its type is a
        literal, key must be an integer.
        When the cardinality of the attribute is 'list' and its values are
        references, key must be an integer or the refName of the item value
        to remove."""

        value = (self._values.get(attribute, Item.Nil) or
                 self._references.get(attribute, Item.Nil))

        if value is not Item.Nil:
            if isinstance(value, dict):
                return value.has_key(key)
            elif isinstance(value, list):
                return 0 <= key and key < len(value)
            elif value is not None:
                raise TypeError, "%s is not multi-valued" %(attribute)

        return False

    def hasValue(self, attribute, value, _attrDict=None):
        """Tell whether an attribute contains a given value.

        If the attribute is multi-valued the value argument is checked for
        appartenance in the attribute's value collection.
        If the attribute is single-valued the value argument is checked for
        equality with the attribute's value."""

        if _attrDict is not None:
            attrValue = _attrDict.get(attribute, Item.Nil)
        else:
            attrValue = (self._values.get(attribute, Item.Nil) or
                         self._references.get(attribute, Item.Nil))

        if attrValue is Item.Nil:
            return False

        if isinstance(attrValue, RefDict) or isinstance(attrValue, list):
            return value in attrValue

        elif isinstance(attrValue, dict):
            for v in attrValue.itervalues():
                if v == value:
                    return True

        else:
            return attrValue == value

        return False

    def removeValue(self, attribute, key=None, value=None, _attrDict=None):
        """Remove the value from a multi-valued attribute for a given key.

        When the cardinality of the attribute is 'list' and its type is a
        literal, key must be an integer and value None.
        When the cardinality of the attribute is 'dict' and its type is a
        literal, key must be an existing key and value is ignored.
        When the cardinality of the attribute is 'list' and its
        values are references, key is ignored and value must be the
        referenced item to remove from the collection."""

        if _attrDict is None:
            if self._values.has_key(attribute):
                _attrDict = self._values
            elif self._references.has_key(attribute):
                _attrDict = self._references
            elif self.getAttributeAspect(attribute, 'otherName', default=None):
                _attrDict = self._references
            else:
                _attrDict = self._values

        value = _attrDict.get(attribute, Item.Nil)
        if value is not Item.Nil:
            del value[key]
        else:
            raise KeyError, 'No value for attribute %s' %(attribute)

        self.setDirty(attribute=attribute)

    def _removeRef(self, name):

        del self._references[name]

    def hasAttributeValue(self, name, _attrDict=None):
        'Check for existence of a value for a given Chandler attribute.'

        if _attrDict is None:
            return name in self._values or name in self._references

        return name in _attrDict

    def _isAttaching(self):

        return (self._status & Item.ATTACHING) != 0

    def _setAttaching(self, attaching=True):

        if attaching:
            self._status |= Item.ATTACHING
        else:
            self._status &= ~Item.ATTACHING

    def isDeleting(self):

        return (self._status & Item.DELETING) != 0
    
    def isNew(self):

        return (self._status & Item.NEW) != 0
    
    def isDeleted(self):

        return (self._status & Item.DELETED) != 0
    
    def isStale(self):

        return (self._status & Item.STALE) != 0
    
    def _setStale(self):

        self._status |= Item.STALE

    def isDirty(self):

        return (self._status & Item.DIRTY) != 0

    def getDirty(self):

        return self._status & Item.DIRTY

    def setDirty(self, dirty=None, attribute=None):
        """Set a dirty bit on the item so that it gets persisted.

        Returns True if the dirty bit was changed from unset to set.
        Returns False otherwise."""

        if dirty is None:
            dirty = Item.ADIRTY

        if dirty:
            if self._status & Item.DIRTY == 0:
                repository = self.getRepository()
                if repository is not None and not repository.isLoading():
                    if attribute is not None:
                        if self.getAttributeAspect(attribute, 'persist',
                                                   default=True) == False:
                            return False
                    if repository.logItem(self):
                        self._status |= dirty
                        return True
                    elif self._status & Item.NEW:
                        repository.logger.error('logging of new item %s failed', self.getItemPath())
            else:
                self._status |= dirty
        else:
            self._status &= ~Item.DIRTY

        return False

    def _setSaved(self, version):

        self._version = version
        self._status &= ~Item.NEW
        self.setDirty(0)

    def delete(self, recursive=False):
        """Delete this item and detach all its item references.

        If this item has children, they are recursively deleted first if
        'recursive' is True.
        If this item has references to other items and the references delete
        policy is 'cascade' then these other items are deleted last.
        A deleted item is no longer reachable through the repository or other
        items. It is an error to access deleted items."""

        if not self._status & (Item.DELETED | Item.DELETING):

            if self._status & Item.STALE:
                raise ValueError, "item is stale: %s" %(self)

            if not recursive and self.hasChildren():
                raise ValueError, 'item %s has children, delete must be recursive' %(self)

            self.setDirty()
            self._status |= Item.DELETING
            others = []

            for child in self:
                child.delete(True)

            self._values.clear()

            for name in self._references.keys():
                policy = self.getAttributeAspect(name, 'deletePolicy',
                                                 default='remove')
                if policy == 'cascade':
                    value = self._references[name]
                    if value is not None:
                        if isinstance(value, ItemRef):
                            others.append(value.other(self))
                        elif isinstance(value, RefDict):
                            others.extend([other for other in value])
                    
                self.removeAttributeValue(name, _attrDict=self._references)

            self.getItemParent()._removeItem(self)
            self._setRoot(None)

            self._status |= Item.DELETED | Item.STALE
            self._status &= ~Item.DELETING

            for other in others:
                if other.refCount() == 0:
                    other.delete()
        
    def getItemName(self):
        '''Return this item's name.

        The item name is used to lookup an item in its parent container and
        construct the item's path in the repository.
        To rename an item use Item.rename().'''

        return self._name

    def getItemDisplayName(self):
        """Return this item's display name.

        By definition, the display name is, in order of precedence, the
        value of the 'displayName' attribute, the value of the attribute
        named by the item's Kind 'displayAttribute' attribute or the item's
        intrinsic name."""

        if self.hasAttributeValue('displayName'):
            return self.displayName

        if self._kind is not None:
            if self._kind.hasAttributeValue('displayAttribute'):
                displayAttribute = self._kind.displayAttribute
                if self.hasAttributeValue(displayAttribute):
                    return self.getAttributeValue(displayAttribute)
                
        return self._name

    def _refName(self, name):
        'deprecated'
        
        return self._uuid

    def refCount(self):
        'Return the total ref count for counted references on this item.'

        count = 0

        if not (self._status & Item.DELETED):
            for name in self._references.iterkeys():
                policy = self.getAttributeAspect(name, 'countPolicy',
                                                 default='none')
                if policy == 'count':
                    count += self._references[name]._refCount()

        return count

    def getUUID(self):
        'Return the Universally Unique ID for this item.'
        
        return self._uuid

    def getItemPath(self, path=None):
        'Return the path to this item relative to its repository.'

        if path is None:
            path = Path()
            
        self.getItemParent().getItemPath(path)
        path.append(self._name)

        return path

    def getRoot(self):
        """Return this item's repository root.

        All single-slash rooted paths are expressed relative to this root."""

        if self._root.isStale():
            self._root = self.getRepository()[self._root._uuid]
            
        return self._root

    def _setRoot(self, root):

        if root is not self._root:

            oldRepository = self.getRepository()
            self._root = root
            newRepository = self.getRepository()

            if oldRepository is not newRepository:

                if oldRepository is not None and newRepository is not None:
                    raise NotImplementedError, 'changing repositories'

                if oldRepository is not None:
                    oldRepository._unregisterItem(self)

                if newRepository is not None:
                    newRepository._registerItem(self)

                    self.setDirty()

            for child in self.iterChildren(load=False):
                child._setRoot(root)

    def getItemParent(self):
        """Return this item's container parent.

        To change the parent, use Item.move()."""

        if self._parent.isStale():
            self._parent = self.getRepository()[self._parent._uuid]
            
        return self._parent

    def _setKind(self, kind):

        if self._kind is not None:
            self._kind.removeValue('items', value=self)

        self._kind = kind

        if self._kind is not None:
            ref = ItemRef(self, 'kind', self._kind, 'items', 'list', False)
            self._references['kind'] = ref

    def getRepository(self):
        """Return this item's repository.

        The item's repository is defined as the item root's parent."""

        if self._root is None:
            return None
        else:
            return self._root._parent

    def rename(self, name):
        'Rename this item.'

        parent = self.getItemParent()
        link = parent._children._get(self._name)
        parent._removeItem(self)
        self._name = name
        parent._addItem(self, link._previousKey, link._nextKey)

    def move(self, newParent, previous=None, next=None):
        'Move this item under another container or make it a root.'

        if newParent is None:
            raise ValueError, 'newParent cannot be None'
            
        parent = self.getItemParent()
        if parent is not newParent:
            parent._removeItem(self)
            self._setParent(newParent)

    def _isRepository(self):
        return False

    def _isItem(self):
        return True

    def _setParent(self, parent, previous=None, next=None):

        if parent is not None:
            if parent._isRepository():
                parent = parent.view
            self._parent = parent
            self._setRoot(parent._addItem(self, previous, next))
        else:
            self._parent = None

    def _addItem(self, item, previous=None, next=None):

        name = item._name
        
        if self.__dict__.has_key('_children'):

            loading = self.getRepository().isLoading()
            current = self.getItemChild(name, not loading)
                
            if current is not None:
                raise ValueError, "A child '%s' exists already under %s" %(item._name, self.getItemPath())

        else:
            self._children = Children(self)

        self._children.__setitem__(name, item, previous, next)

        if '_notChildren' in self.__dict__ and name in self._notChildren:
            del self._notChildren[name]
            
        return self.getRoot()

    def _removeItem(self, item):

        del self._children[item.getItemName()]

    def getItemChild(self, name, load=True):
        'Return the child as named or None if not found.'

        if self._status & Item.STALE:
            raise ValueError, "item is stale: %s" %(self)

        child = None
        if self.__dict__.has_key('_children'):
            child = self._children.get(name, None, False)

        if load and child is None:
            hasNot = self.__dict__.has_key('_notChildren')
            if not hasNot or not self._notChildren.has_key(name):
                child = self.getRepository()._loadChild(self, name)
                if child is None:
                    if not hasNot:
                        self._notChildren = { name: name }
                    else:
                        self._notChildren[name] = name

        return child

    def __getitem__(self, key):

        if isinstance(key, str) or isinstance(key, unicode):
            child = self.getItemChild(key)
            if child is not None:
                return child
            raise KeyError, key

        raise TypeError, key

    def isRemote(self):
        'By default, an item is not remote.'

        return False

    def isItemOf(self, kind):

        if self._kind is kind:
            return True

        if self._kind is not None:
            return self._kind.isSubKindOf(kind)

        return False

    def walk(self, path, callable, _index=0, **kwds):
        """Walk a path and invoke a callable along the way.

        The callable's arguments should be (parent, childName, child, **kwds).
        The callable's child argument is None if the path didn't
        correspond to an existing item.
        The callable's return value is used to recursively continue walking
        unless this return values is None."""

        if _index == 0 and not isinstance(path, Path):
            path = Path(path)

        l = len(path)
        if l == 0 or _index >= l:
            return None

        if _index == 0:
            if path[0] == '//':
                return self.getRepository().walk(path, callable, 1, **kwds)

            elif path[0] == '/':
                return self.getRoot().walk(path, callable, 1, **kwds)

        if path[_index] == '.':
            if _index == l - 1:
                return self
            return self.walk(path, callable, _index + 1, **kwds)

        if path[_index] == '..':
            if _index == l - 1:
                return self.getItemParent()
            return self.getItemParent().walk(path, callable,
                                             _index + 1, **kwds)

        child = self.getItemChild(path[_index], kwds.get('load', True))
        child = callable(self, path[_index], child, **kwds)
        if child is not None:
            if _index == l - 1:
                return child
            return child.walk(path, callable, _index + 1, **kwds)

        return None

    def find(self, spec, _index=0, load=True):
        """Find an item as specified or return None if not found.
        
        Spec can be a Path, a UUID or a string in which case it gets coerced
        into one of the former. If spec is a path, the search is done relative
        to the item unless the path is absolute."""

        if isinstance(spec, Path):
            return self.walk(spec, lambda parent, name, child, **kwds: child,
                             load=load)

        elif isinstance(spec, UUID):
            return self.getRepository().find(spec, 0, load)

        elif isinstance(spec, str) or isinstance(spec, unicode):
            if (spec[0] != '/' and
                (len(spec) == 36 and spec[8] == '-' or len(spec) == 22)):
                return self.find(UUID(spec), 0, load)

            return self.walk(Path(spec),
                             lambda parent, name, child, **kwds: child,
                             0, load=load)

        return None

    def toXML(self):

        out = None
        
        try:
            out = cStringIO.StringIO()
            generator = XMLGenerator(out, 'utf-8')
            generator.startDocument()
            self._xmlItem(generator,
                          withSchema = (self._status & Item.SCHEMA) != 0)
            generator.endDocument()

            return out.getvalue()

        finally:
            if out is not None:
                out.close()

    def _saveItem(self, generator, version):

        self._xmlItem(generator,
                      withSchema = (self._status & Item.SCHEMA) != 0,
                      version = version, mode = 'save')

    def _xmlItem(self, generator, withSchema=False, version=None,
                 mode='serialize'):

        def xmlTag(tag, attrs, value, generator):

            generator.startElement(tag, attrs)
            generator.characters(value)
            generator.endElement(tag)

        isDeleted = self.isDeleted()

        attrs = { 'uuid': self._uuid.str64() }
        if withSchema:
            attrs['withSchema'] = 'True'
        if version is not None:
            attrs['version'] = str(version)
        generator.startElement('item', attrs)

        xmlTag('name', {}, self._name, generator)

        if not isDeleted:
            kind = self._kind
            if kind is not None:
                xmlTag('kind', { 'type': 'uuid' },
                       kind.getUUID().str64(), generator)

            if (withSchema or kind is None or
                kind.getItemClass() is not type(self)):
                xmlTag('class', { 'module': self.__module__ },
                       type(self).__name__, generator)

        attrs = {}
        parent = self.getItemParent()
        parentID = parent.getUUID().str64()

        if not isDeleted:
            if parent._isItem():
                link = parent._children._get(self._name)
                if link._previousKey is not None:
                    attrs['previous'] = link._previousKey
                if link._nextKey is not None:
                    attrs['next'] = link._nextKey

            if '_children' in self.__dict__:
                children = self._children
                if children._firstKey is not None:
                    attrs['first'] = children._firstKey
                if children._lastKey is not None:
                    attrs['last'] = children._lastKey

        xmlTag('container', attrs, parentID, generator)

        if not isDeleted:
            self._xmlAttrs(generator, withSchema, version, mode)
            self._xmlRefs(generator, withSchema, version, mode)

        generator.endElement('item')

    def _loadItem(self):

        return self

    def _unloadItem(self):

        if self._status & Item.DIRTY:
            raise ValueError, 'Item %s has changed, cannot be unloaded' %(self.getItemPath())

        if hasattr(type(self), 'onItemUnload'):
            self.onItemUnload()

        if not self._status & Item.STALE:
            repository = self.getRepository()

            self._status |= Item.DIRTY
            if self.hasAttributeValue('kind'):
                del self.kind

            self._values._unload()
            self._references._unload()
            repository._unregisterItem(self)

            self._parent._unloadChild(self._name)
            if '_children' in self.__dict__ and len(self._children) > 0:
                repository._registerChildren(self._uuid, self._children)

            self._status |= Item.STALE

    def _unloadChild(self, name):

        self._children._unload(name)

    def _xmlAttrs(self, generator, withSchema, version, mode):

        repository = self.getRepository()

        for key, value in self._values.iteritems():
            if self._kind is not None:
                attribute = self._kind.getAttribute(key)
            else:
                attribute = None
                
            if attribute is not None:
                persist = attribute.getAspect('persist', default=True)
            else:
                persist = True

            if persist:
                if attribute is not None:
                    attrType = attribute.getAspect('type')
                    attrCard = attribute.getAspect('cardinality',
                                                   default='single')
                    attrId = attribute.getUUID()
                else:
                    attrType = None
                    attrCard = 'single'
                    attrId = None

                ItemHandler.xmlValue(repository, key, value, 'attribute',
                                     attrType, attrCard, attrId, generator,
                                     withSchema)

    def _xmlRefs(self, generator, withSchema, version, mode):

        for key, value in self._references.iteritems():
            if self.getAttributeAspect(key, 'persist', default=True):
                value._xmlValue(key, self, generator, withSchema, version,
                                mode)

    def _refDict(self, name, otherName=None, persist=None):

        if otherName is None:
            otherName = self._otherName(name)
        if persist is None:
            persist = self.getAttributeAspect(name, 'persist', default=True)

        return self.getRepository().createRefDict(self, name,
                                                  otherName, persist)

    def __new__(cls, *args, **kwds):

        item = object.__new__(cls, *args, **kwds)
        item._status = Item.RAW

        return item

    __new__   = classmethod(__new__)

    class nil(object):
        def __nonzero__(self):
            return False
    Nil       = nil()
    
    DELETED   = 0x0001
    ADIRTY    = 0x0002
    DELETING  = 0x0004
    RAW       = 0x0008
    ATTACHING = 0x0010
    SCHEMA    = 0x0020
    NEW       = 0x0040
    STALE     = 0x0080
    HDIRTY    = 0x0100
    DIRTY     = ADIRTY | HDIRTY

class Children(LinkedMap):

    def __init__(self, item, dictionary=None):

        super(Children, self).__init__(dictionary)
        self._item = item

    def _setItem(self, item):

        self._item = item
        for link in self._itervalues():
            link._value._parent = item
        
    def linkChanged(self, link, key):

        if key is None:
            self._item.setDirty(dirty=Item.HDIRTY)
        else:
            link._value.setDirty(dirty=Item.HDIRTY)
    
    def __repr__(self):

        buffer = None

        try:
            buffer = cStringIO.StringIO()
            buffer.write('{(currenly loaded) ')
            first = True
            for key, value in self._iteritems():
                if not first:
                    buffer.write(', ')
                else:
                    first = False
                buffer.write(key.__repr__())
                buffer.write(': ')
                buffer.write(value.__repr__())
            buffer.write('}')

            return buffer.getvalue()

        finally:
            if buffer is not None:
                buffer.close()

    def _load(self, key):

        if self._item.getRepository()._loadChild(self._item, key) is not None:
            return True

        return False


class ItemValue(object):
    'A superclass for values that can be set on only one item attribute'
    
    def __init__(self):

        self._item = None
        self._attribute = None
        self._dirty = False

    def _setItem(self, item, attribute):

        if self._item is not None and self._item is not item:
            raise ValueError, 'item attribute value %s is already owned by another item %s' %(self, self._item)
        
        self._item = item
        if self._dirty:
            item.setDirty()

        self._attribute = attribute

    def _getItem(self):

        return self._item

    def _getAttribute(self):

        return self._attribute

    def _setDirty(self):

        if not self._dirty:
            self._dirty = True
            if self._item is not None:
                self._item.setDirty()
