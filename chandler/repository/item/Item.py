
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import cStringIO

from repository.item.RefCollections import RefList
from repository.item.Values import Values, References, ItemValue
from repository.item.Access import ACL
from repository.item.PersistentCollections import PersistentCollection
from repository.item.PersistentCollections import PersistentList
from repository.item.PersistentCollections import PersistentDict
from repository.item.ItemError import *

from repository.util.SingleRef import SingleRef
from chandlerdb.util.UUID import UUID
from repository.util.Path import Path
from repository.util.LinkedMap import LinkedMap


class Item(object):
    'The root class for all items.'
    
    def __init__(self, name, parent, kind):
        """
        Construct an Item.

        @param name: The name of the item. It must be unique among the names
        this item's siblings. C{name} may be C{None}.
        @type name: a string or C{None} to create an anonymous item.
        @param parent: The parent of this item. All items require a parent
        unless they are a repository root in which case the parent argument
        is the repository.
        @type parent: an item or the item's repository view
        @param kind: The kind for this item. This kind has definitions for
        all the Chandler attributes that are to be used with this item.
        This parameter can be C{None} for Chandler attribute-less operation.
        Items have two sets of attributes: the regular implementation python
        attributes and the Chandler attributes. When an item is persisted
        only the Chandler attributes are saved.
        @type kind: an item
        """

        # This needs to be the top of the inheritance diamond, hence we're
        # not calling super() here.

        if parent is None:
            raise ValueError, 'parent cannot be None'

        cls = type(self)
        
        if kind is None:
            try:
                uuid = cls.__dict__['_defaultKind']
            except KeyError:
                uuid = None

            if uuid is not None:
                kind = parent.find(uuid)
                if kind is None:
                    raise NoSuchDefaultKindError, (self, cls)

        self.__dict__.update({ '_status': Item.NEW,
                               '_version': 0L,
                               '_lastAccess': 0L,
                               '_uuid': UUID(),
                               '_values': Values(self),
                               '_references': References(self),
                               '_name': name or None,
                               '_kind': kind })

        if kind is not None:
            kind._setupClass(cls)

        if not parent._isItem():
            if kind is not None:
                parent = kind.getAttributeValue('defaultParent', default=parent)
                if parent is None:
                    raise NoSuchDefaultParentError, (self, kind)
            if name is None and not parent._isItem():
                raise ValueError, 'repository root cannot be anonymous'

        self._setParent(parent)

        if kind is not None:
            kind.getInitialValues(self, self._values, self._references)

        self.setDirty(Item.NDIRTY)

    def _fillItem(self, name, parent, kind, **kwds):

        self.__dict__.update({ '_uuid': kwds['uuid'],
                               '_name': name or None,
                               '_kind': kind,
                               '_status': kwds.get('status', 0),
                               '_version': kwds['version'],
                               '_lastAccess': 0L,
                               '_values': kwds.get('values'),
                               '_references': kwds.get('references') })

        self._setParent(parent)

        if self._parent is None or self._parent.isStale():
            raise AssertionError, 'stale or None parent'
        if self._root is None or self._root.isStale():
            raise AssertionError, 'stale or None root'

    def __iter__(self):
        """
        (deprecated) Use L{iterChildren} instead.
        """

        raise DeprecationWarning, 'Use Item.iterChildren() instead'

    def _repr_(self):

        return Item.__repr__(self)
    
    def __repr__(self):
        """
        The debugging string representation of an item.

        It follows the following format:

        C{<classname (status): name uuid>}

        where:
          - C{classname} is the name of the class implementing the item
          - C{status} is displayed when the item is stale or deleted
          - C{name} is displayed if the item's name is not None
          - C{uuid} is the item's UUID

        @return: a string representation of an item.
        """

        if self._status & Item.RAW:
            return super(Item, self).__repr__()

        if self._status & Item.DELETED:
            status = ' (deleted)'
        elif self._status & Item.STALE:
            status = ' (stale)'
        elif self._status & Item.NEW:
            status = ' (new)'
        else:
            status = ''

        if self._name is None:
            name = ''
        else:
            name = ' ' + self._name

        return "<%s%s:%s %s>" %(type(self).__name__, status, name,
                                self._uuid.str16())

    def hasAttributeAspect(self, name, aspect):
        """
        Tell whether an attribute has a value set for the aspect.

        See the L{getAttributeAspect} method for more information on
        attribute aspects.
        @param name: the name of the attribute being queried
        @type name: a string
        @param aspect: the name of the aspect being queried
        @type aspect: a string
        @return: C{True} or C{False}
        """

        if self._kind is not None:
            attribute = self._kind.getAttribute(name, True)
            if attribute is not None:
                return attribute.hasAspect(aspect)

        return False

    def getAttributeAspect(self, name, aspect, _attrID=None, **kwds):
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
              schema attribute item and is read-only when it is a collection
              or a Lob. Other mutable types, such as Structs, should be used
              with care as mutating a defaultValue causes it to appear
              changed by all items returning it. By default, an attribute
              has no default value. See C{initialValue}, C{inheritFrom} and
              C{redirectTo} below. This aspect takes any type of value.
            - C{initialValue}: similar to C{defaultValue} but the initial
              value is set as the value of the attribute the first time it is
              returned. A copy of the initial value is set when it is a
              collection. This aspect takes any type of value.
            - C{inheritFrom}: one or several attribute names chained
              together by periods naming attributes to recursively inherit a
              value from. When several names are used, all but the last name
              are expected to name attributes containing a reference to the
              next item to inherit from by applying the next name. This
              aspect takes a string value.
            - C{redirectTo}: one or several attribute names chained
              together by periods naming attributes to recursively obtain a
              value or aspect value from or set a value to. When several
              names are used, all but the last name are expected to name
              attributes containing a reference to the next item to redirect
              to by applying the next name. This aspect takes a string
              value.
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
            - C{copyPolicy}: when an item is copied this policy defines
              what happens to items that are referenced by this
              attribute. Possible C{copyPolicy} values are:
                - C{remove}, the default. The reference is not copied.
                - C{copy}, the reference is copied.
                - C{cascade}, the referenced item is copied recursively and
                  a reference to this copy is set.
              This aspect takes a string value.
            - C{deletePolicy}: when an item is deleted this policy defines
              what happens to items that are referenced by this
              attribute. Possible C{deletePolicy} values are:
                - C{remove}, the default.
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

        If the attribute's C{redirectTo} aspect is set, this method is
        redirected just like C{getAttributeValue}.

        If the attribute is not defined for the item's kind,
        a subclass of C{AttributeError} is raised.

        @param name: the name of the attribute being queried
        @type name: a string
        @param aspect: the name of the aspect being queried
        @type aspect: a string
        @param kwds: optional keywords of which only C{default} is
        supported and used to return a default value for an aspect that has
        no value set for the attribute.
        @return: a value
        """

        if self._kind is not None:

            if _attrID is not None:
                attribute = self.find(_attrID)
            else:
                noError = kwds.get('noError', False)
                attribute = self._kind.getAttribute(name, noError=noError)

            if attribute is not None:
                if aspect != 'redirectTo':
                    redirect = attribute.getAspect('redirectTo', default=None)
                    if redirect is not None:
                        item = self
                        names = redirect.split('.')
                        for i in xrange(len(names) - 1):
                            item = item.getAttributeValue(names[i])
                        return item.getAttributeAspect(names[-1], aspect,
                                                       **kwds)
                    
                return attribute.getAspect(aspect, **kwds)

        return kwds.get('default', None)
        
    def setAttributeValue(self, name, value=None, setAliases=False,
                          _attrDict=None, setDirty=True, _attrID=None):
        """
        Set a value on a Chandler attribute.

        Calling this method instead of using the regular python attribute
        assignment syntax is unnecessary.
        @param name: the name of the attribute.
        @type name: a string.
        @param value: the value being set
        @type value: anything compatible with the attribute's type
        @param setAliases: when the attribute is to contain a
        L{ref collection<repository.item.RefCollections.RefList>} and the
        C{value} is a dictionary, use the keys in the dictionary as aliases
        into the ref collection when this parameter is C{True}
        @type setAliases: boolean
        @return: the value actually set.
        """

        otherName = None
        
        if _attrDict is None:
            if self._values.has_key(name):
                _attrDict = self._values
                otherName = Item.Nil
            elif self._references.has_key(name):
                _attrDict = self._references
            else:
                otherName = self._kind.getOtherName(name, default=Item.Nil)
                if otherName is not Item.Nil:
                     _attrDict = self._references
                else:
                    redirect = self.getAttributeAspect(name, 'redirectTo',
                                                       default=None,
                                                       _attrID=_attrID)
                    if redirect is not None:
                        item = self
                        names = redirect.split('.')
                        for i in xrange(len(names) - 1):
                            item = item.getAttributeValue(names[i])

                        return item.setAttributeValue(names[-1], value)

                    else:
                        _attrDict = self._values

        isItem = isinstance(value, Item)
        old = None

        if _attrDict is self._references:
            if name in _attrDict:
                old = _attrDict[name]
                if old is value:
                    return value
                if isinstance(old, RefList):
                    old.clear()

        if isItem or value is None:
            card = self.getAttributeAspect(name, 'cardinality')

            if card != 'single':
                raise CardinalityError, (self, name, 'single-valued')

            if _attrDict is self._values:
                if isItem:
                    self._values[name] = value = SingleRef(value.itsUUID)
                else:
                    self._values[name] = None
                dirty = Item.VDIRTY
            else:
                if otherName is None:
                    otherName = self._kind.getOtherName(name)
                self._references._setValue(name, value, otherName)
                setDirty = False

        elif isinstance(value, list):
            if _attrDict is self._references:
                if old is None:
                    self._references[name] = refList = self._refList(name)
                else:
                    assert isinstance(old, RefList)
                    refList = old

                refList.extend(value)
                value = refList
                setDirty = False
            else:
                companion = self.getAttributeAspect(name, 'companion',
                                                    default=None)
                attrValue = PersistentList(self, name, companion)
                self._values[name] = attrValue
                attrValue.extend(value)
                setDirty = False

        elif isinstance(value, dict):
            if _attrDict is self._references:
                if old is None:
                    self._references[name] = refList = self._refList(name)
                else:
                    assert isinstance(old, RefList)
                    refList = old

                refList.update(value, setAliases)
                value = refList
                setDirty = False
            else:
                companion = self.getAttributeAspect(name, 'companion',
                                                    default=None)
                attrValue = PersistentDict(self, name, companion)
                self._values[name] = attrValue
                attrValue.update(value)
                setDirty = False
            
        elif isinstance(value, ItemValue):
            value._setItem(self, name)
            self._values[name] = value
            dirty = Item.VDIRTY
            
        else:
            self._values[name] = value
            dirty = Item.VDIRTY

        if setDirty:
            self.setDirty(dirty, name, _attrDict)
        
        return value

    def _reIndex(self, op, item, attrName, collectionName, indexName):

        if op == 'set':
            refList = self.getAttributeValue(collectionName, default=None,
                                             _attrDict=self._references)
            if refList is not None and item._uuid in refList:
                refList.placeItem(item, None, indexName)

    def getAttributeValue(self, name, _attrDict=None, _attrID=None, **kwds):
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
            5. And finally, if all of the above failed, a subclass of
               C{AttributeError} is raised.

        @param name: the name of the attribute
        @type name: a string
        @param kwds: an optional C{default} key/value pair
        @type kwds: the value for the C{default} keyword can be of any type
        @return: a value
        """

        if self._status & Item.STALE:
            raise StaleItemError, self

        self._lastAccess = Item._countAccess()

        try:
            if (_attrDict is self._values or
                _attrDict is None and name in self._values):
                value = self._values[name]
                if isinstance(value, SingleRef):
                    value = self.getRepositoryView().find(value.itsUUID)
                return value

            elif (_attrDict is self._references or
                  _attrDict is None and name in self._references):
                return self._references._getRef(name)

        except KeyError:
            pass

        if not (self._kind is None or self._values._isNoinherit(name)):
            if _attrID is not None:
                attribute = self.find(_attrID)
            else:
                attribute = self._kind.getAttribute(name)

            inherit = attribute.getAspect('inheritFrom', default=None)
            if inherit is not None:
                value = self
                for attr in inherit.split('.'):
                    value = value.getAttributeValue(attr)
                if isinstance(value, PersistentCollection):
                    value.setReadOnly(True)
                return value

            redirect = attribute.getAspect('redirectTo', default=None)
            if redirect is not None:
                value = self
                for attr in redirect.split('.'):
                    value = value.getAttributeValue(attr)
                return value

            if 'default' in kwds:
                return kwds['default']

            value = attribute.getAspect('defaultValue', default=Item.Nil)
            if value is not Item.Nil:
                if isinstance(value, PersistentCollection):
                    value.setReadOnly(True)
                return value

            self._values._setNoinherit(name)

            raise NoValueForAttributeError, (self, name)

        elif 'default' in kwds:
            return kwds['default']

        raise NoValueForAttributeError, (self, name)

    def removeAttributeValue(self, name, _attrDict=None, _attrID=None):
        """
        Remove a value for a Chandler attribute.

        Calling this method instead of using python's C{del} operator is not
        necessary as python calls this method, via
        L{__delattr__}.

        @param name: the name of the attribute
        @type name: a string
        @return: C{None}
        """

        if _attrDict is None:
            if name in self._values:
                _attrDict = self._values
            elif name in self._references:
                _attrDict = self._references
            else:
                redirect = self.getAttributeAspect(name, 'redirectTo',
                                                   default=None,
                                                   _attrID=_attrID)
                if redirect is not None:
                    item = self
                    names = redirect.split('.')
                    for i in xrange(len(names) - 1):
                        item = item.getAttributeValue(names[i])

                    return item.removeAttributeValue(names[-1])
                
                raise NoLocalValueForAttributeError, (self, name)

        if _attrDict is self._values:
            try:
                del _attrDict[name]
            except KeyError:
                raise NoLocalValueForAttributeError, (self, name)
            self.setDirty(Item.VDIRTY, name, _attrDict, True)
        else:
            try:
                value = _attrDict._getRef(name)
            except KeyError:
                raise NoLocalValueForAttributeError, (self, name)
            _attrDict._removeValue(name, value, self._kind.getOtherName(name))

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

        return (self._children is not None and
                name is not None and
                self._children.resolveAlias(name, load) is not None)

    def hasChildren(self):
        """
        Tell whether this item has any children.

        @return: C{True} or C{False}
        """

        return (self._children is not None and
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
            raise InvalidChildError, (self, child)
        if not (after is None or after.itsParent is self):
            raise InvalidChildError, (self, after)
        
        key = child._uuid
        if after is None:
            afterKey = None
        else:
            afterKey = after._uuid

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
            raise StaleItemError, self

        if not load:
            if self._children is not None:
                for link in self._children._itervalues():
                    yield link.getValue(self._children)

        elif self._children is not None:
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
            for name, value in self._values.iteritems():
                if isinstance(value, SingleRef):
                    value = self.getRepositoryView().find(value.itsUUID)
                yield name, value

        if not valuesOnly:
            for name, ref in self._references.iteritems():
                if ref is not None and ref._isUUID():
                    ref = self._references._getRef(name, ref)
                yield name, ref

    def check(self, recursive=False):
        """
        Run consistency checks on this item.

        Currently, this method verifies that:
            - each literal attribute value is of a type compatible with its
              C{type} aspect (see L{getAttributeAspect}).
            - each attribute value is of a cardinality compatible with its
              C{cardinality} aspect.
            - each reference attribute value's endpoints are compatible with
              each other, that is their C{otherName} aspects match the
              other's name.

        @param recursive: if C{True}, check this item and its children
        recursively. If C{False}, the default, check only this item.
        @return: C{True} if no errors were found, C{False} otherwise. Errors
        are logged in the Chandler execution log.
        """

        checkValues = self._values.check()
        checkRefs = self._references.check()
        result = checkValues and checkRefs

        kind = self._kind
        if kind is not None:
            for name, desc in kind._getDescriptors(type(self)).iteritems():
                attrDict, required = desc.isValueRequired(self)
                if required and name not in attrDict:
                    self.itsView.logger.error("Required value for attribute %s on %s is missing", name, self._repr_())
                    result = False
        
        if recursive and self._children is not None:
            l = len(self._children)
            for child in self.iterChildren():
                l -= 1
                check = child.check(True)
                result = result and check
            if l != 0:
                self.itsView.logger.error("Iterator on children of %s doesn't match length (%d left for %d total)", self._repr_(), l, len(self._children))
                return False

        return result

    def getVersion(self, latest=False):
        """
        Return the version number of this item.

        @param latest: if C{True}, return the latest version number of this
        item as it stands now in the repository; if C{False}, the default,
        return the current version number of this item in this view.
        @type latest: boolean
        @return: integer
        """

        if latest:
            return self.getRepositoryView().getItemVersion(0x7fffffff, self)

        return self._version
        
    def getValue(self, attribute, key=None, alias=None,
                 default=None, _attrDict=None):
        """
        Return a value from a Chandler collection attribute.

        The collection is obtained using
        L{getAttributeValue} and the return value is extracted by using the
        C{key} or C{alias} argument. If the collection does not exist or
        there is no value for C{key} or C{alias}, C{default} is returned,
        C{None} by default. Unless this defaulting behavior is needed, there
        is no reason to use this method instead of the regular python syntax
        for accessing instance attributes and collection elements. The
        C{alias} argument can be used instead of C{key} when the collection
        is a L{ref collection<repository.item.RefCollections.RefList>}.

        @param attribute: the name of the attribute
        @type attribute: a string
        @param key: the key into the collection, optional if C{alias} is used
        @type key: integer for lists, anything for dictionaries
        @param alias: the alias into the ref collection
        @type alias: a string
        @param default: an optional C{default} value, C{None} by default
        @type default: anything
        @return: a value
        """

        value = self.getAttributeValue(attribute, default=Item.Nil,
                                       _attrDict=_attrDict)
            
        if value is Item.Nil:
            return default

        if alias is not None:
            return value.getByAlias(alias, default)

        if isinstance(value, dict):
            return value.get(key, default)

        if isinstance(value, dict):
            return value.get(key, default)

        if isinstance(value, list):
            if key < len(value):
                return value[key]
            else:
                return default

        raise CardinalityError, (self, attribute, 'multi-valued')

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
        collection is a
        L{ref collection<repository.item.RefCollections.RefList>}. 
        @type key: integer for lists, anything for dictionaries
        @param alias: when the collection is a
        L{ref collection<repository.item.RefCollections.RefList>}, C{alias}
        may be used to specify an alias for the reference to insert into the
        collection
        @type alias: a string
        @param value: the value to set
        @type value: anything compatible with the attribute's type
        @return: the collection that was changed or created
        """

        if _attrDict is None:
            if self._values.has_key(attribute):
                _attrDict = self._values
            elif self._references.has_key(attribute):
                _attrDict = self._references
            elif self._kind.getOtherName(attribute, default=None):
                _attrDict = self._references
            else:
                redirect = self.getAttributeAspect(attribute, 'redirectTo',
                                                   default=None)
                if redirect is not None:
                    item = self
                    attributes = redirect.split('.')
                    for i in xrange(len(attributes) - 1):
                        item = item.getAttributeValue(attributes[i])

                    return item.setValue(attributes[-1], value, key, alias)

                else:
                    _attrDict = self._values

        isItem = isinstance(value, Item)
        attrValue = _attrDict.get(attribute, Item.Nil)
            
        if attrValue is Item.Nil:
            card = self.getAttributeAspect(attribute, 'cardinality',
                                           default='single')

            if card == 'dict':
                if _attrDict is self._references:
                    if isItem:
                        attrValue = self._refList(attribute)
                    else:
                        raise TypeError, type(value)
                else:
                    companion = self.getAttributeAspect(attribute, 'companion',
                                                        default=None)
                    attrValue = PersistentDict(self, attribute, companion)
                    _attrDict[attribute] = attrValue
                    attrValue[key] = value
                    
                    return attrValue

            elif card == 'list':
                if _attrDict is self._references:
                    if isItem:
                        attrValue = self._refList(attribute)
                    else:
                        raise TypeError, type(value)
                else:
                    companion = self.getAttributeAspect(attribute, 'companion',
                                                        default=None)
                    attrValue = PersistentList(self, attribute, companion)
                    _attrDict[attribute] = attrValue
                    attrValue.append(value)

                    return attrValue

            else:
                self.setAttributeValue(attribute, value, _attrDict)
                return value

            _attrDict[attribute] = attrValue

        if _attrDict is self._references:
            if isItem:
                attrValue.append(value, alias)
            else:
                raise TypeError, type(value)
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
        @param key: the key into the collection, not used with lists or
        L{ref collections<repository.item.RefCollections.RefList>}
        @type key: anything
        @param alias: when the collection is a
        L{ref collection<repository.item.RefCollections.RefList>}, C{alias}
        may be used to specify an alias for the reference to insert into the
        collection
        @type alias: a string
        @param value: the value to set
        @type value: anything compatible with the attribute's type
        @return: the collection that was changed or created
        """

        if _attrDict is None:
            if self._values.has_key(attribute):
                _attrDict = self._values
            elif self._references.has_key(attribute):
                _attrDict = self._references
            elif self._kind.getOtherName(attribute, default=None):
                _attrDict = self._references
            else:
                redirect = self.getAttributeAspect(attribute, 'redirectTo',
                                                   default=None)
                if redirect is not None:
                    item = self
                    attributes = redirect.split('.')
                    for i in xrange(len(attributes) - 1):
                        item = item.getAttributeValue(attributes[i])

                    return item.addValue(attributes[-1], value, key, alias)

                else:
                    _attrDict = self._values

        attrValue = _attrDict.get(attribute, Item.Nil)
        if attrValue is Item.Nil:
            return self.setValue(attribute, value, key, alias, _attrDict)

        elif isinstance(attrValue, RefList):
            if isinstance(value, Item):
                attrValue.append(value, alias)
            else:
                raise TypeError, type(value)
        elif isinstance(attrValue, dict):
            attrValue[key] = value
        elif isinstance(attrValue, list):
            attrValue.append(value)
        else:
            return self.setAttributeValue(attribute, value, _attrDict)

        return attrValue

    def hasKey(self, attribute, key=None, alias=None, _attrDict=None):
        """
        Tell if a Chandler collection attribute has a value for a given key.

        The collection is obtained using L{getAttributeValue}.

        If the collection is a list of literals, C{key} must be an
        integer and C{True} is returned if it is in range.

        @param attribute: the name of the attribute
        @type attribute: a string
        @param key: the key into the collection, not used with lists
        @type key: anything
        @param alias: when the collection is a
        L{ref collection<repository.item.RefCollections.RefList>}, C{alias}
        may be used to specify an alias for the reference to check
        @type alias: a string
        @return: C{True} or C{False}
        """

        value = self.getAttributeValue(attribute, default=Item.Nil,
                                       _attrDict=_attrDict)

        if value is not Item.Nil:
            if isinstance(value, dict):
                if alias is not None:
                    return value.resolveAlias(alias) is not None
                return value.has_key(key)
            elif isinstance(value, list):
                return 0 <= key and key < len(value)
            elif value is not None:
                raise CardinalityError, (self, attribute, 'multi-valued')

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

        if isinstance(attrValue, RefList) or isinstance(attrValue, list):
            return value in attrValue

        elif isinstance(attrValue, dict):
            for v in attrValue.itervalues():
                if v == value:
                    return True

        else:
            return attrValue == value

        return False

    def removeValue(self, attribute, value=None, key=None, alias=None,
                    _attrDict=None):
        """
        Remove a value from a Chandler collection attribute.

        This method only operates on collections actually owned by this
        attribute, not on collections inherited or otherwise defaulted via
        L{getAttributeValue}.

        If C{value} is not provided and there is no value for the provided
        C{key} or C{alias}, C{KeyError} is raised.

        To remove a value from a dictionary of literals, a C{key} must be
        provided.

        The C{alias} argument can be used instead of C{key} when the
        collection is a
        L{ref collection<repository.item.RefCollections.RefList>}.

        @param attribute: the name of the attribute
        @type attribute: a string
        @param value: the value to remove
        @type value: anything
        @param key: the key into the collection
        @type key: integer for lists, anything for dictionaries
        @param alias: when the collection is a
        L{ref collection<repository.item.RefCollections.RefList>}, C{alias}
        may be used instead to specify an alias for the reference to insert
        into the collection
        @type alias: a string
        """

        if _attrDict is None:
            if self._values.has_key(attribute):
                _attrDict = self._values
            elif self._references.has_key(attribute):
                _attrDict = self._references
            elif self._kind.getOtherName(attribute, default=None):
                _attrDict = self._references
            else:
                redirect = self.getAttributeAspect(attribute, 'redirectTo',
                                                   default=None)
                if redirect is not None:
                    item = self
                    attributes = redirect.split('.')
                    for i in xrange(len(attributes) - 1):
                        item = item.getAttributeValue(attributes[i])

                    return item.removeValue(attributes[-1], value, key, alias)

                else:
                    _attrDict = self._values

        values = _attrDict.get(attribute, Item.Nil)

        if values is not Item.Nil:
            if key is not None or alias is not None:
                if alias is not None:
                    key = value.resolveAlias(alias)
                    if key is None:
                        raise KeyError, 'No value for alias %s' %(alias)
                del values[key]
            elif _attrDict is self._references:
                del values[value._uuid]
            elif isinstance(values, list):
                values.remove(value)
            elif isinstance(values, dict):
                raise TypeError, 'To remove from dict value on %s, key must be specified' %(attribute)
            else:
                raise TypeError, type(values)
        else:
            raise KeyError, 'No value for attribute %s' %(attribute)

    def hasLocalAttributeValue(self, name, _attrDict=None):
        """
        Tell if a Chandler attribute has a locally defined value, that is, a
        value stored on an attribute named C{name} on this item.

        @param name: the name of the attribute
        @type name: a string
        @return: C{True} or C{False}
        """

        if _attrDict is None:
            return name in self._values or name in self._references

        return name in _attrDict

    def isAttributeDirty(self, name, _attrDict=None):
        """
        Tell if an attribute's local value has changed.

        @param name: the name of the attribute
        @type name: a string
        @return: C{True} or C{False}
        """

        if _attrDict is None:
            return (self._values._isDirty(name) or
                    self._references._isDirty(name))
        else:
            return _attrDict._isDirty(name)

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

    def isPinned(self):
        """
        Tell whether this item is pinned.

        A pinned item is not freed from memory or marked stale, until it
        is un-pinned or deleted.
        
        @return: C{True} or C{False}
        """

        return (self._status & Item.PINNED) != 0

    def setPinned(self, pinned=True):
        """
        Pin or Un-pin this item.

        A pinned item is not freed from memory or marked stale until it
        is un-pinned or deleted with L{delete}.
        """

        if pinned:
            self._status |= Item.PINNED
        else:
            self._status &= ~Item.PINNED

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

    def setDirty(self, dirty, attribute=None, attrDict=None, noMonitors=False):
        """
        Mark this item to get committed with the current transaction.

        Returns C{True} if the dirty bit was changed from unset to set.
        Returns C{False} otherwise.

        If C{attribute} denotes a transient attribute (whose C{persist}
        aspect is C{False}), then this method has no effect and returns
        C{False}.

        @param dirty: one of L{Item.VDIRTY <VDIRTY>},
        L{Item.RDIRTY <RDIRTY>}, L{Item.CDIRTY <CDIRTY>}, or a bitwise or'ed
        combination, defaults to C{Item.VDIRTY}.
        @type dirty: an integer
        @param attribute: the name of the attribute that was changed,
        optional, defaults to C{None} which means that no attribute was
        changed
        @type attribute: a string
        @return: C{True} or C{False}
        """

        if self._status & Item.NODIRTY:
            return False

        if dirty:

            if dirty & Item.VRDIRTY:
                assert attribute is not None
                assert attrDict is not None
                attrDict._setDirty(attribute)
                if not noMonitors:
                    Item._monitorsClass.invoke('set', self, attribute)
                
            self._lastAccess = Item._countAccess()
            if self._status & Item.DIRTY == 0:
                view = self.getRepositoryView()
                if view is not None and not view.isLoading():
                    if attribute is not None:
                        if not self.getAttributeAspect(attribute, 'persist',
                                                       noError=True,
                                                       default=True):
                            return False
                    if view._logItem(self):
                        self._status |= dirty
                        return True
                    elif self._status & Item.NEW:
                        view.logger.error('logging of new item %s failed', self.itsPath)
            else:
                self._status |= dirty

        else:
            self._status &= ~(Item.DIRTY | Item.ADIRTY)
            self._values._clearDirties()
            self._references._clearDirties()
            if self._children is not None:
                self._children._clearDirties()

        return False

    def getItemCloud(self, cloudAlias, items=None):
        """
        Get the items in a cloud by using this item as entrypoint.

        @param cloudAlias: the alias of the cloud(s) to use from this item's
        kind.
        @type cloudAlias: a string
        @return: the list containing the items member of the cloud.
        """

        if self._kind is None:
            raise KindlessItemError, self

        if items is None:
            items = {}
        for cloud in self._kind.getClouds(cloudAlias):
            cloud.getItems(self, cloudAlias, items)

        return items.values()

    def copy(self, name=None, parent=None, copies=None,
             copyPolicy=None, cloudAlias=None, copyFn=None):
        """
        Copy this item.

        The item's literal attribute values are copied.
        The item's reference attribute values are copied if the
        C{copyPolicy} aspect on the attribute is C{copy} or C{cascade}.

        By default, an attribute's copyPolicy aspect is C{remove} for
        bi-directional references and C{copy} for
        L{SingleRef<repository.util.SingleRef.SingleRef>} values.

        Attribute copy policies can be overriden with a
        L{Cloud<repository.schema.Cloud.Cloud>} instance to drive the copy
        operation by using the C{cloudAlias} argument.

        If this item has an C{onItemCopy} method defined, it is invoked on
        the copy with the original as argument after the original's
        attribute values were copied.

        @param name: the name of the item's copy
        @type name: a string
        @param parent: the parent of the item's copy, the original's parent
        by default
        @type parent: an item
        @param copies: an optional dictionary keyed on the original item
        UUIDs that contains all the copies made during the copy
        @type copies: dict
        @param copyPolicy: an optional copyPolicy to override the reference
        attributes copy policies with.
        @type copyPolicy: a string
        @param cloudAlias: the optional alias name of a cloud in the item's
        kind clouds list.
        @type cloudAlias: a string
        @return: the item copy
        """

        if copies is None:
            copies = {}
        elif self._uuid in copies:
            return copies[self._uuid]

        if cloudAlias is not None:
            clouds = self._kind.getClouds(cloudAlias)
            for cloud in clouds:
                cloud.copyItems(self, name, parent, copies, cloudAlias)
            return copies.get(self._uuid)
            
        cls = type(self)
        item = cls.__new__(cls)
        item._fillItem(name, parent or self.itsParent, self._kind,
                       uuid = UUID(), version = self._version,
                       values = Values(item), references = References(item))
        item._status |= Item.NEW
        copies[self._uuid] = item

        def copyOther(copy, other, policy):
            if policy == 'copy':
                return other
            elif other is not None and policy == 'cascade':
                otherCopy = copies.get(other.itsUUID, None)
                if otherCopy is None:
                    if self.itsParent is copy.itsParent:
                        parent = other.itsParent
                    else:
                        parent = copy.itsParent
                    otherCopy = other.copy(None, parent, copies, copyPolicy,
                                           None, copyOther)
                return otherCopy
            else:
                return Item.Nil

        if copyFn is None:
            copyFn = copyOther

        try:
            item._status |= Item.NODIRTY
            item._values._copy(self._values, copyPolicy, copyFn)
            item._references._copy(self._references, copyPolicy, copyFn)
        finally:
            item._status &= ~Item.NODIRTY
            
        item.setDirty(Item.NDIRTY)

        if hasattr(cls, 'onItemCopy'):
            item.onItemCopy(self)

        return item

    def delete(self, recursive=False, deletePolicy=None, cloudAlias=None):
        """
        Delete this item.

        By default, an attribute's deletePolicy aspect is C{remove} for
        bi-directional references.

        If this item has references to other items and the C{deletePolicy}
        aspect of the attributes containing them is C{cascade} then these
        other items are deleted too when their count of counted references
        is zero. References in an attribute are counted when the countPolicy
        of the attribute is C{count}. It is C{none} by default.

        Attribute delete policies can be overriden with a
        L{Cloud<repository.schema.Cloud.Cloud>} instance to drive the delete
        operation by using the C{cloudAlias} argument.

        It is an error to delete an item with children unless C{recursive}
        is set to C{True}.

        If this item has an C{onItemDelete} method defined, it is invoked
        before the item's deletion process is started.

        @param deletePolicy: an optional deletePolicy to override the reference
        attributes delete policies with.
        @type deletePolicy: a string
        @param cloudAlias: the optional alias name of a cloud in the item's
        kind clouds list.
        @type cloudAlias: a string
        @param recursive: C{True} to recursively delete this item's children
        too, C{False} otherwise (the default).
        @type recursive: boolean
        """

        if cloudAlias is not None:
            clouds = self._kind.getClouds(cloudAlias)
            for cloud in clouds:
                cloud.deleteItems(self, recursive, cloudAlias)
            
        elif not self._status & (Item.DELETED | Item.DELETING):

            if self._status & Item.STALE:
                raise StaleItemError, self

            if not recursive and self.hasChildren():
                raise RecursiveDeleteError, self

            view = self.getRepositoryView()

            if hasattr(type(self), 'onItemDelete'):
                self.onItemDelete(view)

            self.setDirty(Item.NDIRTY)
            self._status |= Item.DELETING
            others = []

            for child in self.iterChildren():
                child.delete(recursive=True, deletePolicy=deletePolicy)

            self._values.clear()

            for name in self._references.keys():
                policy = (deletePolicy or
                          self.getAttributeAspect(name, 'deletePolicy',
                                                  default='remove'))
                if policy == 'cascade':
                    value = self._references._getRef(name)
                    if value is not None:
                        if value._isRefList():
                            others.extend([other for other in value])
                        else:
                            others.append(value)
                    
                self.removeAttributeValue(name, _attrDict=self._references)

            self.itsParent._removeItem(self)
            self._setRoot(None, view)

            self._status |= Item.DELETED | Item.STALE
            self._status &= ~Item.DELETING

            for other in others:
                if other.refCount(counted=True) == 0:
                    other.delete(recursive=recursive, deletePolicy=deletePolicy)

            self._kind = None
            
    def __getName(self):

        return self._name

    def getItemDisplayName(self):
        """
        Return this item's display name.

        By definition, the display name is, in order of precedence:
            - the value of the C{displayName} attribute
            - the value of the attribute named by the item's kind
              C{displayAttribute} attribute
            - the item's intrinsic name
            - the item's base64 encoded UUID surrounded by {}

        @return: a string
        """

        if 'displayName' in self._values:
            return self.displayName

        if self._kind is not None:
            if 'displayAttribute' in self._kind._values:
                displayAttribute = self._kind.displayAttribute
                if self.hasLocalAttributeValue(displayAttribute):
                    return self.getAttributeValue(displayAttribute)
                
        return self._name or '{%s}' %(self._uuid.str64())

    def getItemDisplayString(self):
        """
        Return a user-readable string representation of this item.

        This method is intended to be overriden.
        It calls L{getItemDisplayName} by default.
        """

        return self.getItemDisplayName();

    def refCount(self, counted=False, loaded=False):
        """
        Return the number of bi-directional references to this item.

        The number returned depends on:

            - C{counted}: if C{True}, return the number of references in
              attributes whose C{countPolicy} is C{count).

            - C{loaded}: if C{True}, return the number of loaded references.

        These keyword arguments may be used together. If they are both
        C{False} this method returns the total number of references to this
        item.

        @return: an integer
        """

        count = 0

        if not (self._status & Item.STALE):
            for name in self._references.iterkeys():
                if counted:
                    policy = self.getAttributeAspect(name, 'countPolicy',
                                                     default='none')
                    if policy == 'count':
                        count += self._references.refCount(name, loaded)
                else:
                    count += self._references.refCount(name, loaded)

        return count

    def _refCount(self):

        count = 0

        if not (self._status & Item.STALE):
            count += self._values._refCount()
            count += self._references._refCount()
            if self._children is not None:
                count += self._children._refCount()
            count += 1  #parent

        return count

    def __getUUID(self):
        
        return self._uuid

    def _getPath(self, path=None):

        if path is None:
            path = Path()
            
        self.itsParent._getPath(path)
        path.append(self._name or self._uuid)

        return path

    def _getRoot(self):

        if self._root.isStale():
            self._root = self.getRepositoryView()[self._root._uuid]
            
        return self._root

    def _setRoot(self, root, oldView):

        if root is not self._root:
            self._root = root
            newView = self.getRepositoryView()

            if oldView is not newView:

                if oldView is not None and newView is not None:
                    raise NotImplementedError, 'changing repositories'

                if oldView is not None:
                    oldView._unregisterItem(self, False)

                if newView is not None:
                    newView._registerItem(self)

            for child in self.iterChildren(load=False):
                child._setRoot(root, oldView)

        elif root is not None:
            root.itsView._registerItem(self)

    def __getParent(self):

        if self._parent.isStale():
            self._parent = self.getRepositoryView()[self._parent._uuid]
            
        return self._parent

    def __getKind(self):

        kind = self._kind
        if kind is not None and kind._status & Item.STALE:
            kind = self.getRepositoryView()[kind._uuid]
            self._kind = kind
                
        return kind

    def __setKind(self, kind):

        if kind is not self._kind:
            self.setDirty(Item.NDIRTY)

            if self._kind is not None:
                if kind is None:
                    self._values.clear()
                    self._references.clear()

                else:
                    def removeOrphans(attrDict):
                        for name in attrDict.keys():
                            curAttr = self._kind.getAttribute(name)
                            try:
                                newAttr = kind.getAttribute(name)
                            except AttributeError:
                                newAttr = None
                            if curAttr is not newAttr:
                                self.removeAttributeValue(name,
                                                          _attrDict=attrDict)

                    removeOrphans(self._values)
                    removeOrphans(self._references)

            self._kind = kind

            if kind is None:
                self.__class__ = Item
            else:
                self.__class__ = kind.getItemClass()
                kind._setupClass(self.__class__)
                kind.getInitialValues(self, self._values, self._references)

    def mixinKinds(self, *kinds):
        """
        Mixin kinds into this item's kind.

        A new kind for the item is created if necessary by combining the
        current kind and the kinds passed into a superKinds list. When
        removing kinds from a mixin item, its kind may revert to a non-mixin
        kind.

        This method does not affect items of the same kind as this item's
        kind. It affects only this item. When the same mixin operation is
        performed on other items of this item's kind, they get assigned the
        same resulting kind as this item after this call completes.

        The class of the item is set to the kind's item class which may be a
        combination of the item classes of the kinds making up the mixin kind.

        The *kinds arguments passed in are tuples as follows:

            - C{('add', newKind)}: add C{newKind} to the end of the
              mixin kind's superKinds list.

            - C{('remove', kind)}: remove C{kind} from the superKinds. This
              operation is only supported when the item is already an item
              of a mixin kind.

            - C{('before', kind, newKind)}: insert C{newKind} before
              C{kind}. This operation is only supported when the item is
              already an item of a mixin kind.

            - C{('after', kind, newKind)}: insert C{newKind} after
              C{kind}. This operation is only supported when the item is
              already an item of a mixin kind.

        @param *kinds: any number of tuples as described above.
        @type *kinds: tuple
        @return: the item's kind after the method completes
        """

        superKinds = []
        if self._kind is not None:
            if self._kind.isMixin():
                superKinds[:] = self._kind.superKinds
            else:
                superKinds.append(self._kind)

        for kind in kinds:
            if kind[0] == 'remove':
                del superKinds[superKinds.index(kind[1])]
            elif kind[0] == 'add':
                superKinds.append(kind[1])
            elif kind[0] == 'before':
                superKinds.insert(superKinds.index(kind[1]), kind[2])
            elif kind[0] == 'after':
                superKinds.insert(superKinds.index(kind[1]) + 1, kind[2])
            else:
                raise ValueError, kind[0]

        count = len(superKinds)
        kind = self._kind
        
        if count == 0 and (kind is None or kind.isMixin()):
            kind = None
        elif count == 1 and kind is not None and kind.isMixin():
            kind = superKinds[0]
        else:
            if kind is None or kind.isMixin():
                kind = superKinds.pop(0)
            kind = kind.mixin(superKinds)

        self.__setKind(kind)

        return kind

    def setACL(self, acl, name=None):
        """
        Set an ACL on this item.

        An ACL can be set for the item or for individual attributes on the
        item.

        @param acl: an L{ACL<repository.item.Access.ACL>} instance
        @param name: the name of the attribute to set the ACL for or C{None},
        the default, to set the ACL for the item.
        @type name: a string
        """

        if self._acls is None:
            self._acls = { name: acl }
        else:
            self._acls[name] = acl
        
        self.setDirty(Item.ADIRTY)

    def removeACL(self, name=None):
        """
        Remove an ACL from this item.

        An ACL can be removed for the item or for individual attributes on the
        item.

        @param name: the name of the attribute to remove the ACL for or
        C{None}, the default, to remove the ACL for the item.
        @type name: a string
        """

        self.setACL(None, name)

    def getACL(self, name=None):
        """
        Get an ACL from this item.

        An ACL can be obtained from the item or from individual attributes
        on the item.

        @param name: the name of the attribute to get the ACL from or C{None}
        to get the ACL for the item.
        @type name: a string
        @return: an L{ACL<repository.item.Access.ACL>} instance or C{None} if
        no ACL is set
        """

        if self._acls is not None:
            acl = self._acls.get(name, Item.Nil)
        else:
            acl = Item.Nil

        if acl is Item.Nil:
            acl = self.getRepositoryView().getACL(self._uuid, name, self._version)

        return acl

    def getRepositoryView(self):
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
        If C{name} is C{None}, the item becomes anonymous.

        @param name: the new name for the item or C{None}
        @type name: a string
        """

        name = name or None
            
        if name != self._name:
            parent = self.itsParent

            if parent._isItem():
                children = parent._children
            else:
                children = parent._roots

            if name is not None and children.resolveAlias(name) is not None:
                raise ChildNameError, (parent, name)
                
            self._name = name
            children.setAlias(self._uuid, name)

            self.setDirty(Item.NDIRTY)
                
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
            oldView = parent.getRepositoryView()
            parent._removeItem(self)
            self._setParent(newParent, previous, next, oldView)
            self.setDirty(Item.NDIRTY)

    def _isRepository(self):
        return False

    def _isView(self):
        return False

    def _isItem(self):
        return True

    def _isRefList(self):
        return False

    def _isUUID(self):
        return False

    def _setParent(self, parent, previous=None, next=None, oldView=None):

        if parent is not None:
            if self._parent is not parent:
                if parent._isRepository():
                    parent = parent.view
                self._parent = parent
                self._setRoot(parent._addItem(self, previous, next), oldView)
            elif parent._isView():
                self._setRoot(self, oldView)
            else:
                self._setRoot(parent.itsRoot, oldView)
        else:
            self._parent = None

    def _addItem(self, item, previous=None, next=None):

        name = item._name

        if self._children is not None:
            if name is not None:
                loading = self.getRepositoryView().isLoading()
                if self._children.resolveAlias(name, not loading) is not None:
                    raise ChildNameError, (self, item._name)

        else:
            self._children = self.getRepositoryView()._createChildren(self,
                                                                      True)

        self._children.__setitem__(item._uuid, item, previous, next, name)

        return self.itsRoot

    def _removeItem(self, item):

        del self._children[item._uuid]

    def _setChildren(self, children):

        self._children = children

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
            raise StaleItemError, self

        child = None
        if name is not None and self._children is not None:
            child = self._children.getByAlias(name, None, load)

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
            return self._kind.isKindOf(kind)

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
        @type path: a L{Path<repository.util.Path.Path>} instance
        @param callable: a function, method, or lambda body
        @type callable: a python callable
        @param kwds: optional keywords passed to the callable
        @return: the item the walk finished on or C{None}
        """

        l = len(path)
        if l == 0 or _index >= l:
            return None

        attrName = kwds.get('attribute', None)
        if attrName is not None:
            attr = self._kind.getAttribute(attrName)
        else:
            attr = None
        
        if _index == 0:
            if path[0] == '//':
                if attr is not None:
                    return attr._walk(path, callable, **kwds)
                else:
                    return self.getRepositoryView().walk(path, callable, 1,
                                                         **kwds)

            elif path[0] == '/':
                if attr is not None:
                    return attr._walk(path, callable, **kwds)
                else:
                    return self.itsRoot.walk(path, callable, 1, **kwds)

        if path[_index] == '.':
            if _index == l - 1:
                return self
            return self.walk(path, callable, _index + 1, **kwds)

        if path[_index] == '..':
            if attr is not None:
                otherName = self._kind.getOtherName(attrName)
                parent = self.getAttributeValue(otherName,
                                                _attrDict=self._references)
                otherAttr = self._kind.getAttribute(otherName)
                if otherAttr.cardinality == 'list':
                    parent = parent.first()
            else:
                parent = self.itsParent

            if _index == l - 1:
                return parent
            
            return parent.walk(path, callable, _index + 1, **kwds)

        if attr is not None:
            children = self.getAttributeValue(attrName,
                                              _attrDict=self._references,
                                              default=None)
            if children is not None:
                child = children.getByAlias(path[_index], default=None,
                                            load=kwds.get('load', True))
        else:
            name = path[_index]
            if isinstance(name, UUID):
                child = self.findUUID(name, kwds.get('load', True))
                if child is not None and child.itsParent is not self:
                    child = None
            else:
                child = self.getItemChild(name, kwds.get('load', True))
            
        child = callable(self, path[_index], child, **kwds)
        if child is not None:
            if _index == l - 1:
                return child
            return child.walk(path, callable, _index + 1, **kwds)

        return None

    def find(self, spec, attribute=None, load=True):
        """
        Find an item.

        An item can be found by a path determined by its name and container
        or by a uuid generated for it at creation time. If C{spec} is a
        relative path, it is evaluated relative to C{self}.

        This method returns C{None} if the item is not found or if it is
        found but not yet loaded and C{load} was set to C{False}.

        See the L{findPath} and L{findUUID} methods for versions of this
        method that can also be called with a string.

        @param spec: a path or UUID
        @type spec: L{Path<repository.util.Path.Path>} or
                    L{UUID<chandlerdb.util.UUID.UUID>} 
        @param attribute: the attribute for the ref-collections to search
        @type attribute: a string
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

        if isinstance(spec, UUID):
            return self.getRepositoryView().find(spec, load)

        if isinstance(spec, Path):
            return self.walk(spec, lambda parent, name, child, **kwds: child,
                             attribute=attribute, load=load)

        raise TypeError, '%s is not Path or UUID' %(type(spec))

    def findPath(self, path, attribute=None, load=True):
        """
        Find an item by path.

        See L{find} for more information.

        @param path: a path
        @type path: L{Path<repository.util.Path.Path>} or a path string
        @param attribute: the attribute for the ref-collections to search
        @type attribute: a string
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

        if isinstance(path, str) or isinstance(path, unicode):
            path = Path(path)
        elif not isinstance(path, Path):
            raise TypeError, '%s is not Path or string' %(type(path))

        return self.walk(path, lambda parent, name, child, **kwds: child,
                         attribute=attribute, load=load)

    def findUUID(self, uuid, load=True):
        """
        Find an item by UUID.

        See L{find} for more information.

        @param uuid: a UUID
        @type uuid: L{UUID<chandlerdb.util.UUID.UUID>} or a uuid string
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

        if isinstance(uuid, str) or isinstance(uuid, unicode):
            uuid = UUID(uuid)
        elif not isinstance(uuid, UUID):
            raise TypeError, '%s is not UUID or string' %(type(uuid))

        return self.getRepositoryView().find(uuid, load)

    def _unloadItem(self, reloadable):

        if self._status & Item.DIRTY:
            raise DirtyItemError, self

        view = self.getRepositoryView()

        if hasattr(type(self), 'onItemUnload'):
            self.onItemUnload(view)

        if not self._status & Item.STALE:

            if self._values:
                self._values._unload()
            if self._references:
                self._references._unload()

            self._parent._unloadChild(self)
            if self._children is not None:
                self._children._clear_()
                self._children._item = None
                self._children = None

            view._unregisterItem(self, reloadable)

            if not reloadable:
                self._parent = None
                self._root = None
                self._kind = None
            
            self._status |= Item.STALE

    def _unloadChild(self, child):

        if self._children is not None:
            self._children._unloadChild(child)

    def _refList(self, name, otherName=None, persist=None):

        if otherName is None:
            otherName = self._kind.getOtherName(name)
        if persist is None:
            persist = self.getAttributeAspect(name, 'persist', default=True)

        return self.getRepositoryView()._createRefList(self, name, otherName,
                                                       persist, False, True,
                                                       None)

    def _commitMerge(self, version):

        self._version = version
        status = self._status

        if status & Item.CMERGED:
            self._children._commitMerge()
        if status & Item.VMERGED:
            self._values._commitMerge()
        if status & (Item.RMERGED | Item.VMERGED):
            self._references._commitMerge()

    def _revertMerge(self):

        status = self._status

        if status & Item.CMERGED:
            self._children._revertMerge()
        if status & Item.VMERGED:
            self._values._revertMerge()
        if status & (Item.RMERGED | Item.VMERGED):
            self._references._revertMerge()

        self._status &= ~Item.MERGED

    def _countAccess(cls):

        cls.__access__ += 1
        return cls.__access__

    _countAccess = classmethod(_countAccess)

    def __new__(cls, *args, **kwds):

        item = object.__new__(cls, *args, **kwds)
        item.__dict__.update({ '_status': Item.RAW,
                               '_parent': None,
                               '_children': None,
                               '_root': None,
                               '_acls': None })

        return item

    __new__   = classmethod(__new__)

    class nil(object):
        def __nonzero__(self):
            return False
    Nil        = nil()
    
    DELETED    = 0x0001
    VDIRTY     = 0x0002           # literal or ref changed
    DELETING   = 0x0004
    RAW        = 0x0008
    ATTACHING  = 0x0010
    SCHEMA     = 0x0020
    NEW        = 0x0040
    STALE      = 0x0080
    NDIRTY     = 0x0100           # parent or name changed
    CDIRTY     = 0x0200           # children list changed
    RDIRTY     = 0x0400           # ref collection changed
    CORESCHEMA = 0x0800           # core schema item
    CONTAINER  = 0x1000           # has children
    ADIRTY     = 0x2000           # acl(s) changed
    PINNED     = 0x4000           # auto-refresh, don't stale
    NODIRTY    = 0x8000           # turn off dirtying

    VMERGED    = VDIRTY << 16
    RMERGED    = RDIRTY << 16
    NMERGED    = NDIRTY << 16
    CMERGED    = CDIRTY << 16

    VRDIRTY    = VDIRTY | RDIRTY
    DIRTY      = VDIRTY | RDIRTY | NDIRTY | CDIRTY
    MERGED     = VMERGED | RMERGED | NMERGED | CMERGED
    SAVEMASK   = (DIRTY | ADIRTY |
                  NEW | DELETED |
                  SCHEMA | CORESCHEMA | CONTAINER)

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

    itsView = property(fget = getRepositoryView,
                       doc =
                       """
                       Return this item's repository view.
                       
                       See L{getRepositoryView} for more information.
                       """)

    itsKind = property(fget = __getKind,
                       fset = __setKind,
                       doc = 
                       """
                       Return or set this item's kind.

                       When setting an item's kind, only the values for
                       attributes common to both current and new kind are
                       retained. After the new kind is set, its attributes'
                       optional L{initial values<getAttributeAspect>} are
                       set for attributes for which there is no value on the
                       item. Setting an item's kind to C{None} clears all
                       its values.
                       """)


class Children(LinkedMap):

    def __init__(self, item, new):

        super(Children, self).__init__(new)

        self._item = None
        self._setItem(item)

    def _setItem(self, item):

        if self._item is not None:
            assert item._uuid == self._item._uuid

            for link in self._itervalues():
                link.getValue(self)._parent = item

        if item is not None and item._isItem():
            item._status |= Item.CONTAINER
            
        self._item = item

    def _refCount(self):

        return super(Children, self).__len__() + 1
        
    def linkChanged(self, link, key):

        self._item.setDirty(Item.CDIRTY)

    def _unloadChild(self, child):

        self._unloadRef(child)
    
    def __repr__(self):

        buffer = None

        try:
            buffer = cStringIO.StringIO()
            buffer.write('{(currenly loaded) ')
            first = True
            for link in self._itervalues():
                if not first:
                    buffer.write(', ')
                else:
                    first = False
                buffer.write(link.getValue(self)._repr_())
            buffer.write('}')

            return buffer.getvalue()

        finally:
            if buffer is not None:
                buffer.close()

    def _saveValues(self, version):
        raise NotImplementedError, "%s._saveValues" %(type(self))
