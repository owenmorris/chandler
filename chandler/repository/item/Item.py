
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
from repository.util.SAX import XMLOffFilter, XMLOnFilter, XMLThruFilter


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
        self._access = 0L
        self._uuid = UUID()

        self._values = Values(self)
        self._references = References(self)
        
        self._name = name or self._uuid.str64()
        self._kind = kind
        self._root = None

        self._setParent(parent)

        if kind is not None:
            kind.getInitialValues(self, self._values, self._references)

    def _fillItem(self, name, parent, kind, **kwds):

        self._uuid = kwds['uuid']
        self._name = name or self._uuid.str64()
        self._kind = kind
        self._root = None
        self._status = 0
        self._version = kwds['version']
        self._access = 0L

        kwds['values']._setItem(self)
        self._values = kwds['values']
        
        kwds['references']._setItem(self)
        self._references = kwds['references']

        self._setParent(parent, kwds.get('previous'), kwds.get('next'))

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

        @return: a string representation of an item.
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
        @return: an attribute value
        """

        return self.getAttributeValue(name)

    def __setattr__(self, name, value):
        """
        This method is called whenever an attribute's value is set.

        It resolves whether the attribute is a Chandler attribute or a regular
        python attribute and dispatches to the relevant methods.
        @param name: the name of the attribute being set.
        @type name: a string
        @param value: the value being set
        @type value: anything
        @return: the value actually set.
        """

        if name[0] != '_':
            if name in self._values:
                return self.setAttributeValue(name, value,
                                              _attrDict=self._values)
            elif name in self._references:
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
        @return: C{None}
        """

        if name in self._values:
            self.removeAttributeValue(name, _attrDict=self._values)
        elif name in self._references:
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
            raise TypeError, 'Undefined other endpoint for %s.%s' %(self.itsPath, name)

        return otherName

    def hasAttributeAspect(self, name, aspect):
        """
        Tell whether an attribute as value set for the aspect.

        See the L{getAttributeAspect} method for more information on
        attribute aspects.
        @param name: the name of the attribute being queried
        @type name: a string
        @param aspect: the name of the aspect being queried
        @type aspect: a string
        @return: C{True} or C{False}
        """

        if self._kind is not None:
            attribute = self._kind.getAttribute(name)
            if attribute is not None:
                return attribute.hasAspect(aspect)

        return False

    def getAttributeAspect(self, name, aspect, **kwds):
        """
        Return the value for an attribute aspect.

        An attribute aspect is one of an attribute's many attributes
        described in the list below. All aspects are optional.

            - C{required}: C{True} if the attribute is required to have a
              value, C{False} otherwise, the default. This aspects takes a
              boolean value.
            - C{persist}: C{True}, the default, if the attribute's value is
              persisted when the owning item is saved; C{False}
              otherwise. This aspect takes a boolean value.
            - C{cardinality}: C{single}, the default if the attribute is
              to have one single value, C{list} or C{dict}, if the attribute
              is to have a list or dictionary of values. This aspect takes a
              string value.
            - C{type}: a reference to the type item describing the type(s) of
              value(s) this attribute can store. By default, if this aspect
              is not set, an attribute can store value(s) of any type. This
              aspect takes an item of kind C{Type} as value.
            - C{defaultValue}: the value to return when there is no value
              set for this attribute. This default value is owned by the
              attribute item and is a read-only when it is a collection. By
              default, an attribute has no default value. See
              C{initialValue} and C{inheritFrom} below. This aspect takes
              any type of value.
            - C{initialValue}: similar to C{defaultValue} but the initial
              value is set as the value of the attribute the first time it is
              returned. A copy of the initial value is set when it is a
              collection. This aspect takes any type of value.
            - C{inheritFrom}: one or several attribute names chained
              together by periods naming attributes to inherit a value
              from. When several names are used, all but the last name are
              expected to name attributes containing a reference to the next
              item to inherit from by applying the next name. This aspect
              takes a string value.
            - C{otherName}: for bi-directional reference attributes, this
              aspect names the attribute used to attach the other endpoint
              on the other item, ie the referenced item. This is the aspect
              that determines whether the attribute stored bi-directional
              references to items. This aspect takes a string value.
            - C{companion}: for mixed collection attributes, this aspect
              names the attribute used to store the bi-directional
              references to the items stored in the mixed collection. By
              default, if the companion aspect is not set, the entire
              repository is considered. This aspect takes a string value.
            - C{deletePolicy}: when an item is deleted this policy defines
              what happens to items that are referenced by this
              attribute. Possible C{deletePolicy} values are:
                - C{remove}, the default
                - C{cascade}, which causes the referenced item(s) to get
                  deleted as well. See C{countPolicy} below.
              This aspect takes a string value.
            - C{countPolicy}: when an attribute's C{deletePolicy} is
              C{cascade} this aspect can be used to modify the delete
              behaviour to only delete the referenced item if its reference
              count is 0. The reference count of an item is defined by the
              total number of references it holds in attributes where the
              C{countPolicy} is set to C{count}. By default, an attribute's
              C{countPolicy} is C{none}. This aspect takes a string value.

        @param name: the name of the attribute being queried
        @type name: a string
        @param aspect: the name of the aspect being queried
        @type aspect: a string
        @param kwds: optional keywords of which only C{default} is
        supported and used to return a default value for an aspect that has
        no set value for this attribute.
        @return: a value
        """

        if self._kind is not None:
            attribute = self._kind.getAttribute(name)
            if attribute is not None:
                return attribute.getAspect(aspect, **kwds)

        return kwds.get('default', None)

    def setAttributeValue(self, name, value=None, _attrDict=None):
        """
        Set a value on a Chandler attribute.

        Calling this method instead of using the regular python attribute
        assignment syntax is unnecessary.
        @param name: the name of the attribute.
        @type name: a string.
        @param value: the value being set
        @type value: anything compatible with the attribute's type
        @return: the value actually set.
        """

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
                self._values[name] = value = SingleRef(value.itsUUID)

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
        """
        Return a Chandler attribute value.

        Unless the optional keywords described below are used, calling this
        method instead of using regular python attribute access syntax is
        not necessary as python calls this method, via
        L{__getattr__} when a non Chandler attribute of this name is not
        found.

        If the attribute has no value set then the following attempts are
        made at infering one (in this order):
            1. If the attribute has an C{initialValue} aspect set (see
               L{getAttributeAspect} for more information on attribute
               aspects) then this value is set for the attribute and
               returned.
            2. If the attribute has an C{inheritFrom} aspect set then the
               value inherited along C{inheritFrom} is the value returned.
            3. If the C{default} keyword is passed to this method then its
               value is returned.
            4. If the attribute has a C{defaultValue} aspect set then it is
               returned. If this default value is a collection then it is
               read-only.
            5. And finally, if all of the above failed, an C{AttributeError}
               is raised.

        @param name: the name of the attribute
        @type name: a string
        @param kwds: an optional C{default} key/value pair
        @type kwds: the value for the C{default} keyword can be of any type
        @return: a value
        """

        if self._status & Item.STALE:
            raise ValueError, "item is stale: %s" %(self)

        self._access = Item._countAccess()

        try:
            if (_attrDict is self._values or
                _attrDict is None and name in self._values):
                value = self._values[name]
                if isinstance(value, SingleRef):
                    value = self.getRepository().find(value.itsUUID)
                return value

            elif (_attrDict is self._references or
                  _attrDict is None and name in self._references):
                value = self._references[name]
                if isinstance(value, ItemRef):
                    return value.other(self)
                return value

        except KeyError:
            pass

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

        raise AttributeError, "%s has no value for '%s'" %(self.itsPath,
                                                           name)

    def removeAttributeValue(self, name, _attrDict=None):
        """
        Remove a value for a Chandler attribute.

        Calling this method instead of using python's C{del} operator is not
        necessary as python calls this method, via
        L{__delattr__}.

        @param name: the name of the attribute
        @type name: a string
        @return: C{None}
        """

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
        """
        Tell whether this item has a child of that name.

        By setting the optional C{load} argument to C{False}, this method
        can be restricted to only check among the currently loaded children
        of this item.

        @param name: the name of the child to verify
        @type name: a string
        @param load: whether to check only among loaded children
        @type load: a boolean, C{True} by default
        @return: C{True} or C{False}
        """

        return ('_children' in self.__dict__ and
                not ('_notChildren' in self.__dict__ and
                     name in self._notChildren) and
                self._children.has_key(name, load))

    def hasChildren(self):
        """
        Tell whether this item has any children.

        @return: C{True} or C{False}
        """

        return (self.__dict__.has_key('_children') and
                self._children._firstKey is not None)

    def placeChild(self, child, after):
        """
        Place a child after another one in this item's children collection.

        To place a child in first position, pass C{None} for C{after}.
        See also L{move} to change this item's parent.

        @param child: the child item to place
        @type child: an item
        @param after: the sibling of C{child} to precede it
        @type after: an item
        @return: C{None}
        """

        if not (child.itsParent is self):
            raise ValueError, '%s not a child of %s' %(child, self)
        if not (after is None or after.itsParent is self):
            raise ValueError, '%s not a child of %s' %(after, self)
        
        key = child._name
        if after is None:
            afterKey = None
        else:
            afterKey = after._name

        self._children.place(key, afterKey)

    def dir(self, recursive=True):
        """
        Print out a listing of each child under this item.

        By default, this method recurses down children of this item.

        @param recursive: whether to recurse down the children or not
        @type recursive: a boolean, C{True} by default
        @return: C{None}
        """
        
        for child in self.iterChildren():
            print child.itsPath
            if recursive:
                child.dir(True)

    def iterChildren(self, load=True):
        """
        Return a python generator used to iterate over the children of this
        item.

        This method is invoked by python's L{__iter__}, usually
        from a C{for} loop construct. Optionally, this method can be used to
        iterate over only the currently loaded children of this item.

        @param load: C{True}, the default, to iterate over all the children
        of this item. C{False} to iterate over only its currently loaded
        children items.
        @type load: boolean
        """
        
        if self._status & Item.STALE:
            raise ValueError, "item is stale: %s" %(self)

        if not load:
            if self.__dict__.has_key('_children'):
                for child in self._children._itervalues():
                    yield child._value

        elif self.__dict__.has_key('_children'):
            for child in self._children:
                yield child

    def iterAttributeValues(self, valuesOnly=False, referencesOnly=False):
        """
        Return a generator of C{(name, value)} tuples for iterating over
        Chandler attribute values of this item. 

        @param valuesOnly: if C{True}, iterate over literal values
        only. C{False} by default.
        @type valuesOnly: boolean
        @param referencesOnly: if C{True}, iterate over item reference
        values only. C{False} by default.
        @type referencesOnly: boolean
        """

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
        """
        Run consistency checks on this item.

        Currently, this method verifies that:
            - each literal attribute value is of a type compatible with its
              C{type} aspect (see L{getAttributeAspect}).
            - each attribute value is a of a cardinality compatible with its
              C{cardinality} aspect.
            - each reference attribute value's endpoints are compatible with
              each other, that is their C{otherName} aspects match the
              other's name.

        @param recursive: if C{True}, check this item and its children
        recursively. If C{False}, the default, check only this item.
        @return: C{True} if no errors were found, C{False} otherwise. Errors
        are logged in the Chandler execution log.
        """

        logger = self.getRepository().logger
        result = True

        def checkValue(name, value, attrType):

            if not attrType.recognizes(value):
                logger.error('Value %s of type %s in attribute %s on %s is not recognized by type %s', value, type(value), name, self.itsPath, attrType.itsPath)

                return False

            return True

        def checkCardinality(name, value, cardType, attrCard):

            if not isinstance(value, cardType):
                logger.error('Value %s of type %s in attribute %s on %s is not an instance of type %s which is required for cardinality %s', value, type(value), name, self.itsPath, cardType, attrCard)

                return False

            return True

        for key, value in self._values.iteritems():
            attribute = self._kind.getAttribute(key)
            if attribute is None:
                logger.error('Item %s has a value for attribute %s but its kind %s has no definition for this attribute', self.itsPath, key, self._kind.itsPath)
                result = False
            else:
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
            for child in self.iterChildren():
                check = child.check(True)
                result = result and check

        return result
        
    def getValue(self, attribute, key, default=None, _attrDict=None):
        """
        Return a value from a Chandler collection attribute.

        The collection is obtained using
        L{getAttributeValue} and the return value is extracted by using the
        C{key} argument. If the collection does not exist or there is no
        value for C{key}, C{default} is returned, C{None} by default. Unless
        this defaulting behavior is needed, there is no reason to use this
        method instead of the regular python syntax for accessing instance
        attributes and collection elements.

        @param attribute: the name of the attribute
        @type attribute: a string
        @param key: the key into the collection
        @type key: integer for lists, anything for dictionaries
        @param default: an optional C{default} value, C{None} by default
        @type default: anything
        @return: a value
        """

        value = self.getAttributeValue(attribute, default=Item.Nil,
                                       _attrDict=_attrDict)
            
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
        """
        Set a value into a Chandler collection attribute.

            - If the attribute doesn't yet have a value, the proper
              collection is created for it.
            - If the collection is a list and C{key} is an integer out of the
              list's range, an exception is raised.
            - If the attribute is not a collection attribute, the value is
              simply set.
        
        @param attribute: the name of the attribute
        @type attribute: a string
        @param key: the key into the collection, not used when the
        collection is a collection of item references
        @type key: integer for lists, anything for dictionaries
        @param value: the value to set
        @type value: anything compatible with the attribute's type
        @return: the collection that was changed or created
        """

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
        """
        Add a value to a Chandler collection attribute.

            - If the attribute doesn't yet have a value, the proper
              collection is created for it.
            - If the collection is a list, C{key} is not used.
            - If the attribute is not a collection attribute, the value is
              simply set.
        
        @param attribute: the name of the attribute
        @type attribute: a string
        @param key: the key into the collection, not used with lists
        @type key: anything
        @param value: the value to set
        @type value: anything compatible with the attribute's type
        @return: the collection that was changed or created
        """

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
            return self.setValue(attribute, value, key, alias, _attrDict)

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
                return self.setAttributeValue(attribute, value, _attrDict)

            return attrValue

    def hasKey(self, attribute, key, _attrDict=None):
        """
        Tell if a Chandler collection attribute has a value for a given key.

        The collection is obtained using L{getAttributeValue}.

        If the collection is a list of literals, C{key} must be an
        integer and C{True} is returned if it is in range.

        @param attribute: the name of the attribute
        @type attribute: a string
        @param key: the key into the collection, not used with lists
        @type key: anything
        @return: C{True} or C{False}
        """

        value = self.getAttributeValue(attribute, default=Item.Nil,
                                       _attrDict=_attrDict)

        if value is not Item.Nil:
            if isinstance(value, dict):
                return value.has_key(key)
            elif isinstance(value, list):
                return 0 <= key and key < len(value)
            elif value is not None:
                raise TypeError, "%s is not multi-valued" %(attribute)

        return False

    def hasValue(self, attribute, value, _attrDict=None):
        """
        Tell if a Chandler collection attribute has a given value.

        The collection is obtained using L{getAttributeValue}.
        If the attribute is not a collection, C{True} is returned if
        C{value} is the same as attribute's value.

        @param attribute: the name of the attribute
        @type attribute: a string
        @param value: the value looked for
        @type value: anything
        @return: C{True} or C{False}
        """

        attrValue = self.getAttributeValue(attribute, default=Item.Nil,
                                           _attrDict=_attrDict)
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

    def removeValue(self, attribute, key=None, _attrDict=None):
        """
        Remove a value from a Chandler collection attribute, for a given key.

        This method only operates on collections actually owned by this
        attribute, not on collections inherited or otherwise defaulted via
        L{getAttributeValue}.

        If there is no value for the provided key, C{KeyError} is raised.

        @param attribute: the name of the attribute
        @type attribute: a string
        @param key: the key into the collection
        @type key: integer for lists, anything for dictionaries
        """

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
        """
        Tell if a Chandler attribute has a locally defined value.

        @param name: the name of the attribute
        @type name: a string
        @return: C{True} or C{False}
        """

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
        """
        Tell whether this item is in the process of being deleted.

        @return: C{True} or C{False}
        """
        
        return (self._status & Item.DELETING) != 0
    
    def isNew(self):
        """
        Tell whether this item is new.

        A new item is defined as an item that was before committed to the
        repository.
        
        @return: C{True} or C{False}
        """

        return (self._status & Item.NEW) != 0
    
    def isDeleted(self):
        """
        Tell whether this item is deleted.

        @return: C{True} or C{False}
        """

        return (self._status & Item.DELETED) != 0
    
    def isStale(self):
        """
        Tell whether this item pointer is out of date.

        A stale item pointer is defined as an item pointer that is no longer
        valid. When an item is unloaded, the item pointer is marked
        stale. The item pointer can be refreshed by reloading the item via the
        L{find} method, passing it the item's C{uuid} obtained via the
        L{itsUUID} property.
        
        Stale items are encountered when item pointers are kept across
        transaction boundaries. It is recommended to keep the item's
        C{uuid} instead.

        @return: C{True} or C{False}
        """

        return (self._status & Item.STALE) != 0
    
    def _setStale(self):

        self._status |= Item.STALE

    def isDirty(self):
        """
        Tell whether this item was changed and needs to be committed.

        @return: C{True} or C{False}
        """
        
        return (self._status & Item.DIRTY) != 0

    def getDirty(self):
        """
        Return the dirty flags currently set on this item.

        @return: an integer
        """

        return self._status & Item.DIRTY

    def setDirty(self, dirty=None, attribute=None):
        """
        Mark this item to get committed with the current transaction.

        Returns C{True} if the dirty bit was changed from unset to set.
        Returns C{False} otherwise.

        If C{attribute} is used and denotes a transient attribute (whose
        C{persist} aspect is C{False}), then this method has no effect and
        returns C{False}.

        @param dirty: one of L{Item.VDIRTY <VDIRTY>},
        L{Item.RDIRTY <RDIRTY>}, L{Item.CDIRTY <CDIRTY>},
        L{Item.SDIRTY, <SDIRTY>} or a bitwise or'ed combination, defaults to
        C{Item.VDIRTY}.
        @type dirty: an integer
        @param attribute: the name of the attribute that was changed,
        optional, defaults to C{None} which means that no attribute was
        changed
        @type attribute: a string
        @return: C{True} or C{False}
        """

        if dirty is None:
            dirty = Item.VDIRTY

        if dirty:
            self._access = Item._countAccess()
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
                        repository.logger.error('logging of new item %s failed', self.itsPath)
            else:
                self._status |= dirty
        else:
            self._status &= ~Item.DIRTY

        return False

    def delete(self, recursive=False):
        """
        Delete this item.

        If this item has references to other items and the C{deletePolicy}
        aspect of the attributes containing them is C{cascade} then these
        other items are deleted too.

        It is an error to delete an item with children unless C{recursive}
        is set to C{True}.

        @param recursive: C{True} to recursively delete this item's children
        too, C{False} otherwise (the default).
        @type recursive: boolean
        """

        if not self._status & (Item.DELETED | Item.DELETING):

            if self._status & Item.STALE:
                raise ValueError, "item is stale: %s" %(self)

            if not recursive and self.hasChildren():
                raise ValueError, 'item %s has children, delete must be recursive' %(self)

            self.setDirty()
            self._status |= Item.DELETING
            others = []

            for child in self.iterChildren():
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

            self.itsParent._removeItem(self)
            self._setRoot(None)

            self._status |= Item.DELETED | Item.STALE
            self._status &= ~Item.DELETING

            for other in others:
                if other.refCount() == 0:
                    other.delete()
        
    def __getName(self):

        return self._name

    def getItemDisplayName(self):
        """
        Return this item's display name.

        By definition, the display name is, in order of precedence:
            - the value of the C{displayName} attribute
            - the value of the attribute named by the item's kind
              C{displayAttribute} attribute
            - or the item's intrinsic name

        @return: a string
        """

        if self.hasAttributeValue('displayName'):
            return self.displayName

        if self._kind is not None:
            if self._kind.hasAttributeValue('displayAttribute'):
                displayAttribute = self._kind.displayAttribute
                if self.hasAttributeValue(displayAttribute):
                    return self.getAttributeValue(displayAttribute)
                
        return self._name

    def _refName(self, name):
        
        return self._uuid

    def refCount(self):
        """
        Return the number of counted references to this item.

        A reference is counted if the C{countPolicy} aspect of the attribute
        containing it is C{count}.

        @return: an integer
        """

        count = 0

        if not (self._status & Item.DELETED):
            for name in self._references.iterkeys():
                policy = self.getAttributeAspect(name, 'countPolicy',
                                                 default='none')
                if policy == 'count':
                    count += self._references[name]._refCount()

        return count

    def __getUUID(self):
        
        return self._uuid

    def _getPath(self, path=None):

        if path is None:
            path = Path()
            
        self.itsParent._getPath(path)
        path.append(self._name)

        return path

    def _getRoot(self):

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

    def __getParent(self):

        if self._parent.isStale():
            self._parent = self.getRepository()[self._parent._uuid]
            
        return self._parent

    def __getKind(self):

        return self._kind

    def getRepository(self):
        """
        Return this item's repository view.

        The item's repository view is defined as the item's root's parent.
        @return: a repository view
        """

        if self._root is None:
            return None
        else:
            return self._root._parent

    def rename(self, name):
        """
        Rename this item.

        The name of an item needs to be unique among its siblings.
        If C{name} is C{None}, the base64 representation of the item's
        C{UUID} is used instead.

        @param name: the new name for the item or C{None}
        @type name: a string
        """

        parent = self.itsParent
        link = parent._children._get(self._name)
        parent._removeItem(self)
        self._name = name or self._uuid.str64()
        parent._addItem(self, link._previousKey, link._nextKey)

    def move(self, newParent, previous=None, next=None):
        """
        Move this item under another container.

        The item's name needs to be unique among its siblings.
        To make the item into a repository root, use the repository as
        container.

        Use C{previous} or {next} to place the item among its siblings.
        By default, the item is added last into the sibling collection.
        See also L{placeChild} to place the item without changing its
        parent.

        @param newParent: the container to move the item to
        @type newParent: an item or the repository
        @param previous: the optional item to place this item after
        @type previous: an item
        @param next: the optional item to place this item before
        @type next: an item
        """

        if newParent is None:
            raise ValueError, 'newParent cannot be None'
            
        parent = self.itsParent
        if parent is not newParent:
            parent._removeItem(self)
            self._setParent(newParent, previous, next)

    def _isRepository(self):
        return False

    def _isItem(self):
        return True

    def _setParent(self, parent, previous=None, next=None):

        if parent is not None:
            if parent._isRepository():
                parent = parent.view
            self._parent = parent
            self._root = None
            self._setRoot(parent._addItem(self, previous, next))
        else:
            self._parent = None

    def _addItem(self, item, previous=None, next=None):

        name = item._name
        
        if self.__dict__.has_key('_children'):

            loading = self.getRepository().isLoading()
            current = self.getItemChild(name, not loading)
                
            if current is not None:
                raise ValueError, "A child '%s' exists already under %s" %(item._name, self.itsPath)

        else:
            self._children = Children(self)

        self._children.__setitem__(name, item, previous, next)

        if '_notChildren' in self.__dict__ and name in self._notChildren:
            del self._notChildren[name]
            
        return self.itsRoot

    def _removeItem(self, item):

        name = item._name
        del self._children[name]

        if '_notChildren' in self.__dict__:
            self._notChildren[name] = name
        else:
            self._notChildren = { name: name }

    def getItemChild(self, name, load=True):
        """
        Return the named child or C{None} if not found.

        The regular python C{[]} syntax may be used on the item to get
        children from it except that when the child is not found,
        C{KeyError} is raised.

        @param name: the name of the child sought
        @type name: a string
        @param load: load the item if not currently loaded
        @type load: boolean
        @return: an item
        """

        if self._status & Item.STALE:
            raise ValueError, "item is stale: %s" %(self)

        child = None
        if '_children' in self.__dict__:
            child = self._children.get(name, None, False)

        if load and child is None:
            hasNot = '_notChildren' in self.__dict__
            if not (hasNot and name in self._notChildren):
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
        """
        Tell whether this item is a remote item.

        @return: C{False}
        """

        return False

    def isItemOf(self, kind):
        """
        Tell whether this item is of a certain kind.

        Like python's C{isinstance} function, this method tells whether an
        item is of kind C{kind} or of a subkind thereof.

        @param kind: a kind
        @type kind: an item of kind C{Kind}
        @return: boolean
        """

        if self._kind is kind:
            return True

        if self._kind is not None:
            return self._kind.isSubKindOf(kind)

        return False

    def walk(self, path, callable, _index=0, **kwds):
        """
        Walk a path and invoke a callable along the way.

        The callable's arguments need to be defined as C{parent},
        C{childName}, C{child} and C{**kwds}.
        The callable is passed C{None} for the C{child} argument if C{path}
        doesn't correspond to an existing item.
        The callable's return value is used to recursively continue walking
        when it is not C{None}.

        For example: L{find} calls this method when passed a path with the
        callable being the simple lambda body:

            - C{lambda parent, name, child, **kwds: child}

        A C{load} keyword can be used to prevent loading of items by setting
        it to C{False}. Items are loaded as needed by default.

        @param path: an item path
        @type path: a C{Path} instance or a string representing a path
        @param callable: a function, method, or lambda body
        @type callable: a python callable
        @param kwds: optional keywords passed to the callable
        @return: the item the walk finished on or C{None}
        """

        if _index == 0 and not isinstance(path, Path):
            path = Path(path)

        l = len(path)
        if l == 0 or _index >= l:
            return None

        if _index == 0:
            if path[0] == '//':
                return self.getRepository().walk(path, callable, 1, **kwds)

            elif path[0] == '/':
                return self.itsRoot.walk(path, callable, 1, **kwds)

        if path[_index] == '.':
            if _index == l - 1:
                return self
            return self.walk(path, callable, _index + 1, **kwds)

        if path[_index] == '..':
            if _index == l - 1:
                return self.itsParent
            return self.itsParent.walk(path, callable, _index + 1, **kwds)

        child = self.getItemChild(path[_index], kwds.get('load', True))
        child = callable(self, path[_index], child, **kwds)
        if child is not None:
            if _index == l - 1:
                return child
            return child.walk(path, callable, _index + 1, **kwds)

        return None

    def find(self, spec, _index=0, load=True):
        """
        Find an item.

        An item can be found by a path determined by its name and container
        or by a uuid generated for it at creation time. If C{spec} is a
        relative path, it is evaluated relative to C{self}.

        This method returns C{None} if the item is not found or if it is
        found but not yet loaded and C{load} was set to C{False}.

        @param spec: a path or UUID
        @type spec: Path, UUID or a string representation thereof
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

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
        """
        Generate an XML representation of this item.

        This method is not a general purpose serialization method for items
        but it can be used for debugging.

        @return: an XML string
        """
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

    def _saveItem(self, generator, version, mergeWith=None):

        withSchema = (self._status & Item.SCHEMA) != 0

        if mergeWith is None:
            self._xmlItem(generator, withSchema, version, 'save')
            self._status |= Item.SAVED

        else:
            oldDoc, oldDirty, newDirty = mergeWith
            if oldDirty & newDirty:
                raise ValueError, "merges overlap (%0.4x:%0.4x)" %(oldDirty,
                                                                   newDirty)
            def mergeNewOld(*attributes):
                class merger(XMLOffFilter):
                    def startElement(_self, tag, attrs):
                        if tag == 'item':
                            attrs['version'] = str(version)
                        XMLOffFilter.startElement(_self, tag, attrs)
                    def endElement(_self, tag):
                        if tag == 'item':
                            self._xmlAttrs(generator, withSchema,
                                           version, 'save')
                        XMLOffFilter.endElement(_self, tag)

                merger(generator, *attributes).parse(oldDoc)
                self._status |= Item.MERGED

            def mergeOldNew(dirty, *attributes):
                class merger(XMLThruFilter):
                    def endElement(_self, tag):
                        if tag == 'item':
                            XMLOnFilter(generator, *attributes).parse(oldDoc)
                        XMLThruFilter.endElement(_self, tag)

                out = cStringIO.StringIO()
                xml = XMLGenerator(out, 'utf-8')
                xml.startDocument()
                self._xmlItem(xml, withSchema, version, 'save',
                              Item.DIRTY & ~dirty)
                xml.endDocument()
                newDoc = out.getvalue()
                out.close()

                merger(generator).parse(newDoc)
                self._status |= Item.MERGED
                
            if newDirty == Item.VDIRTY:
                mergeNewOld('attribute')
            elif newDirty == Item.RDIRTY:
                mergeNewOld('ref')
            elif newDirty == Item.VRDIRTY:
                mergeNewOld('attribute', 'ref')
            elif oldDirty == Item.VDIRTY:
                mergeOldNew(Item.VDIRTY, 'attribute')
            elif oldDirty == Item.RDIRTY:
                mergeOldNew(Item.RDIRTY, 'ref')
            elif oldDirty == Item.VRDIRTY:
                mergeOldNew(Item.VRDIRTY, 'attribute', 'ref')
            else:
                raise NotImplementedError, "merge %0.4x:%0.4x" %(oldDirty,
                                                                 newDirty)

    def _xmlItem(self, generator, withSchema=False, version=None,
                 mode='serialize', save=None):

        def xmlTag(tag, attrs, value, generator):

            generator.startElement(tag, attrs)
            generator.characters(value)
            generator.endElement(tag)

        isDeleted = self.isDeleted()
        if save is None:
            save = Item.DIRTY

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
                       kind.itsUUID.str64(), generator)

            if (withSchema or kind is None or
                kind.getItemClass() is not type(self)):
                xmlTag('class', { 'module': self.__module__ },
                       type(self).__name__, generator)

        attrs = {}
        parent = self.itsParent
        parentID = parent.itsUUID.str64()

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
            if save & Item.VDIRTY:
                self._xmlAttrs(generator, withSchema, version, mode)
            if save & Item.RDIRTY:
                self._xmlRefs(generator, withSchema, version, mode)

        generator.endElement('item')

    def _loadItem(self):

        return self

    def _unloadItem(self):

        if self._status & Item.DIRTY:
            raise ValueError, 'Item %s has changed, cannot be unloaded' %(self.itsPath)

        if hasattr(type(self), 'onItemUnload'):
            self.onItemUnload()

        if not self._status & Item.STALE:
            repository = self.getRepository()

            self._status |= Item.DIRTY

            if self._values:
                self._values._unload()
            if self._references:
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
                    attrId = attribute.itsUUID
                else:
                    attrType = None
                    attrCard = 'single'
                    attrId = None

                try:
                    ItemHandler.xmlValue(repository, key, value, 'attribute',
                                         attrType, attrCard, attrId, generator,
                                         withSchema)
                except Exception, e:
                    e.args = ("while saving attribute '%s' of item %s, %s" %(key, self.itsPath, e.args[0]),)
                    raise

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

    def _countAccess(cls):

        cls.__access__ += 1
        return cls.__access__

    _countAccess = classmethod(_countAccess)

    def __new__(cls, *args, **kwds):

        item = object.__new__(cls, *args, **kwds)
        item._status = Item.RAW

        return item

    __new__   = classmethod(__new__)

    class nil(object):
        def __nonzero__(self):
            return False
    Nil        = nil()
    
    DELETED    = 0x0001
    VDIRTY     = 0x0002           # literal value(s) changed
    DELETING   = 0x0004
    RAW        = 0x0008
    ATTACHING  = 0x0010
    SCHEMA     = 0x0020
    NEW        = 0x0040
    STALE      = 0x0080
    SDIRTY     = 0x0100           # name of sibling(s) changed
    CDIRTY     = 0x0200           # parent or first/last child changed
    RDIRTY     = 0x0400           # ref or ref collection value changed
    MERGED     = 0x0800
    SAVED      = 0x1000

    VRDIRTY    = VDIRTY | RDIRTY
    DIRTY      = VDIRTY | SDIRTY | CDIRTY | RDIRTY

    __access__ = 0L

    itsName = property(fget = __getName,
                       fset = rename,
                       doc =
                       """
                       Return this item's name.

                       The item name is used to lookup an item in its parent
                       container and construct the item's path in the
                       repository. 
                       An item may be renamed by setting this property.

                       The name of an item must be unique among all its
                       siblings. 
                       """)

    itsUUID = property(fget = __getUUID,
                       doc =
                       """
                       Return the Universally Unique ID for this item.

                       The UUID for an item is generated when the item is
                       first created and never changes. This UUID is valid
                       for the life of the item.

                       The UUID is a 128 bit number intended to be unique in
                       the entire universe and is implemented as specified
                       in the IETF's U{UUID draft
                       <www.ics.uci.edu/pub/ietf/webdav/uuid-guid/draft-leach-uuids-guids-01.txt>}
                       spec. 
                       """)

    itsPath = property(fget = _getPath,
                       doc = 
                       """
                       Return the path to this item relative to its repository.

                       A path is a C{/} separated sequence of item names.
                       """)

    itsParent = property(fget = __getParent,
                         fset = move,
                         doc = 
                         """
                         Return this item's parent.

                         An item may be moved by setting this property.
                         """)

    itsRoot = property(fget = _getRoot,
                       doc = 
                       """
                       Return this item's repository root.

                       A repository root is a direct child of the repository.
                       All single-slash rooted paths are expressed relative
                       to this root when used with this item.
                       """)

    itsKind = property(fget = __getKind,
                       doc = 
                       """
                       Return this item's kind.
                       """)


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
            self._item.setDirty(dirty=Item.CDIRTY)
        else:
            link._value.setDirty(dirty=Item.SDIRTY)
    
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
    'A superclass for values that are owned by an item.'
    
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
                self._item.setDirty(attribute=self._attribute,
                                    dirty=Item.VDIRTY)
