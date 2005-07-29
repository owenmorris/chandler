
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from chandlerdb.util.uuid import UUID, _hash, _combine
from chandlerdb.schema.descriptor import _countAccess
from chandlerdb.item.item import CItem, Nil, Default
from chandlerdb.item.ItemError import *

from repository.item.RefCollections import RefList
from repository.item.Values import Values, References, ItemValue
from repository.item.Access import ACL
from repository.item.PersistentCollections import \
     PersistentCollection, PersistentList, PersistentDict, \
     PersistentTuple, PersistentSet

from repository.util.SingleRef import SingleRef
from repository.util.Path import Path
from repository.util.LinkedMap import LinkedMap


class Item(CItem):
    'The root class for all items.'

    def __init__(self, name=None, parent=None, kind=None,
                 _uuid=None, _noMonitors=False, **values):
        """
        Construct an Item.

        @param name: The name of the item. It must be unique among the names
        this item's siblings. C{name} is optional, except for roots and is
        C{None} by default.
        @type name: a string or C{None} to create an anonymous item.
        @param parent: The parent of this item. All items require a parent
        unless they are a repository root in which case the parent argument
        is a repository view.
        @type parent: an item or the item's repository view.
        @param kind: The kind for this item. This kind has definitions for
        all the Chandler attributes that are to be used with this item.
        This parameter can be C{None} for Chandler attribute-less operation.
        Items have two sets of attributes: the regular implementation python
        attributes and the Chandler attributes. When an item is persisted
        only the Chandler attributes are saved.
        @type kind: an item
        @param values: extra keyword arguments to set values on the item
        after being constructed.
        @type values: C{name=value} pairs
        """

        # this constructor should not be run more than once
        if self._uuid is not None:
            return

        super(Item, self).__init__()

        cls = type(self)
        self._values = Values(self)
        self._references = References(self)
        self._uuid = _uuid or UUID()
        self._name = name or None
        self._kind = kind
        self._version = 0

        if kind is not None:
            kind._setupClass(cls)

        if parent is None:
            if kind is not None:
                parent = kind.itsView
            else:
                raise ValueError, 'parent cannot be None'

        if name is None and not parent._isItem():
            raise AnonymousRootError, self

        self._setParent(parent)

        if kind is not None:
            kind.getInitialValues(self, self._values, self._references)

        self.setDirty(Item.NDIRTY)

        for name, value in values.iteritems():
            self.setAttributeValue(name, value)

        if not (_noMonitors or (kind is None) or (Item._monitorsClass is None)):
            Item._monitorsClass.invoke('schema', self, 'kind', None)

    def _fillItem(self, name, parent, kind, **kwds):

        self._status = kwds.get('status', 0)
        self._version = kwds['version']
        self._values = kwds.get('values')
        self._references = kwds.get('references')
        self._uuid = kwds['uuid']
        self._name = name or None
        self._kind = kind

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

        _status = self._status
        
        if _status & Item.RAW:
            return super(Item, self).__repr__()

        if _status & Item.DELETED:
            status = ' (deleted)'
        elif _status & Item.STALE:
            status = ' (stale)'
        elif _status & Item.NEW:
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
            attribute = self._kind.getAttribute(name, True, self)
            if attribute is not None:
                return attribute.hasAspect(aspect)

        return False

    def getAttributeAspect(self, name, aspect,
                           noError=False, _attrID=None, default=Default):
        """
        Return the value for an attribute aspect.

        An attribute aspect is one of an attribute's many attributes
        described in the list below. All aspects are optional.

            - C{required}: C{True} if the attribute is required to have a
              value, C{False} otherwise, the default. This aspects takes a
              boolean value.
            - C{persisted}: C{True}, the default, if the attribute's value is
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
                attribute = self._kind.getAttribute(name, noError, self)

            if attribute is not None:
                if aspect != 'redirectTo':
                    redirect = attribute.getAspect('redirectTo', None)
                    if redirect is not None:
                        item = self
                        names = redirect.split('.')
                        for i in xrange(len(names) - 1):
                            item = item.getAttributeValue(names[i])
                        return item.getAttributeAspect(names[-1], aspect,
                                                       noError, None, default)
                    
                return attribute.getAspect(aspect, default)

        if default is Default:
            return None

        return default
        
    def setAttributeValue(self, name, value=None, _attrDict=None, _attrID=None,
                          setDirty=True, setAliases=False):
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
        _values = self._values
        _references = self._references
        
        if _attrDict is None:
            if name in _values:
                _attrDict = _values
                otherName = Nil
            elif name in _references:
                _attrDict = _references
            else:
                otherName = self._kind.getOtherName(name, _attrID, self, Nil)
                if otherName is not Nil:
                    _attrDict = _references
                else:
                    redirect = self.getAttributeAspect(name, 'redirectTo',
                                                       False, _attrID, None)
                    if redirect is not None:
                        item = self
                        names = redirect.split('.')
                        for i in xrange(len(names) - 1):
                            item = item.getAttributeValue(names[i])

                        return item.setAttributeValue(names[-1], value,
                                                      None, None,
                                                      setDirty, setAliases)

                    else:
                        _attrDict = _values

        isItem = value is not None and isinstance(value, Item)
        old = None

        if _attrDict is _references:
            if name in _attrDict:
                old = _attrDict[name]
                if old is value:
                    return value
                if isinstance(old, RefList):
                    old.clear()

        if isItem or value is None:
            card = self.getAttributeAspect(name, 'cardinality',
                                           False, _attrID, 'single')

            if card != 'single':
                raise CardinalityError, (self, name, 'single-valued')

            if _attrDict is _values:
                if isItem:
                    _values[name] = value = SingleRef(value.itsUUID)
                else:
                    _values[name] = None
                dirty = Item.VDIRTY
            else:
                if otherName is None:
                    otherName = self._kind.getOtherName(name, _attrID, self)
                _references._setValue(name, value, otherName)
                setDirty = False

        elif isinstance(value, list):
            if _attrDict is _references:
                if old is None:
                    _references[name] = refList = self._refList(name)
                else:
                    assert isinstance(old, RefList)
                    refList = old

                refList.extend(value)
                value = refList
                setDirty = False
            else:
                companion = self.getAttributeAspect(name, 'companion',
                                                    False, _attrID, None)
                attrValue = PersistentList((self, name, companion), value)
                _values[name] = attrValue
                setDirty = False

        elif isinstance(value, dict):
            if _attrDict is _references:
                if old is None:
                    _references[name] = refList = self._refList(name)
                else:
                    assert isinstance(old, RefList)
                    refList = old

                refList.update(value, setAliases)
                value = refList
                setDirty = False
            else:
                companion = self.getAttributeAspect(name, 'companion',
                                                    False, _attrID, None)
                attrValue = PersistentDict((self, name, companion), value)
                _values[name] = attrValue
                setDirty = False
            
        elif isinstance(value, tuple):
            if _attrDict is _references:
                if old is None:
                    _references[name] = refList = self._refList(name)
                else:
                    assert isinstance(old, RefList)
                    refList = old

                refList.update(value, setAliases)
                value = refList
                setDirty = False
            else:
                companion = self.getAttributeAspect(name, 'companion',
                                                    False, _attrID, None)
                attrValue = PersistentTuple((self, name, companion), value)
                _values[name] = attrValue
                dirty = Item.VDIRTY
            
        elif isinstance(value, set):
            if _attrDict is _references:
                if old is None:
                    _references[name] = refList = self._refList(name)
                else:
                    assert isinstance(old, RefList)
                    refList = old

                refList.update(value, setAliases)
                value = refList
                setDirty = False
            else:
                companion = self.getAttributeAspect(name, 'companion',
                                                    False, _attrID, None)
                attrValue = PersistentSet((self, name, companion), value)
                _values[name] = attrValue
                setDirty = False
            
        elif isinstance(value, ItemValue):
            value._setItem(self, name)
            _values[name] = value
            dirty = Item.VDIRTY
            
        else:
            _values[name] = value
            dirty = Item.VDIRTY

        if setDirty:
            self.setDirty(dirty, name, _attrDict)
        
        return value

    def _reIndex(self, op, item, attrName, collectionName, indexName):

        if op == 'set':
            collection = getattr(self, collectionName, None)
            if collection is not None and item in collection:
                collection.placeInIndex(item, None, indexName)

    def _kindChanged(self, op, item, attribute, prevKind, name):

        if self._status & Item.NODIRTY:
            return

        if op == 'schema' and attribute == 'kind':
            kind = item._kind
            set = getattr(self, name)

            if prevKind is not None:
                set.sourceChanged('remove', 'kind',
                                  self, name, False, item, prevKind)
            if kind is not None:
                set.sourceChanged('add', 'kind',
                                  self, name, False, item, kind)

    def _collectionChanged(self, op, name, other):

        if self._status & Item.NODIRTY:
            return

        if op == 'remove':
            if name == 'watchers':
                dispatch = self._values.get('watcherDispatch', None)
                if dispatch is not None:
                    dispatch.filterItem(other, 2)

        dispatch = self._values.get('watcherDispatch', None)
        if dispatch:
            watchers = dispatch.get(name, None)
            if watchers:
                for (watcher, args) in watchers:
                    if len(args) == 2 and args[0] == 'set':
                        set = getattr(watcher, args[1])
                        set.sourceChanged(op, 'collection',
                                          self, name, False, other)
                    else:
                        watcher.collectionChanged(op, self, name, other, *args)

    def _registerCollectionWatch(self, watcher, name, args):

        dispatch = self._values.get('watcherDispatch', None)
        watcher = (watcher, tuple(args))
        if dispatch is None:
            self.watcherDispatch = { name: set([watcher]) }
        else:
            watchers = dispatch.get(name, None)
            if watchers is None:
                dispatch[name] = set([watcher])
            else:
                watchers.add(watcher)

    def _unregisterCollectionWatch(self, watcher, name, args):

        dispatch = self._values.get('watcherDispatch', None)
        if dispatch:
            watcher = (watcher, tuple(args))
            try:
                watchers = dispatch[name]
                watchers.remove(watcher)
            except KeyError:
                pass

    def collectionChanged(self, op, item, name, other, *args):
        pass

    def watchCollection(self, owner, name, *args):
        owner._registerCollectionWatch(self, name, args)

    def unwatchCollection(self, owner, name, *args):
        owner._unregisterCollectionWatch(self, name, args)

    def getAttributeValue(self, name, _attrDict=None, _attrID=None,
                          default=Default):
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

        if self.isStale():
            raise StaleItemError, self

        _countAccess(self)

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
                attribute = self._kind.getAttribute(name, False, self)

            inherit = attribute.getAspect('inheritFrom', None)
            if inherit is not None:
                value = self
                for attr in inherit.split('.'):
                    value = value.getAttributeValue(attr, None, None, Nil)
                    if value is Nil:
                        break
                if value is not Nil:
                    if isinstance(value, PersistentCollection):
                        value.setReadOnly(True)
                    return value

            redirect = attribute.getAspect('redirectTo', None)
            if redirect is not None:
                value = self
                for attr in redirect.split('.'):
                    value = value.getAttributeValue(attr, None, None, default)
                    if value is default:
                        break
                return value

            if default is not Default:
                return default

            value = attribute.getAspect('defaultValue', Nil)
            if value is not Nil:
                if isinstance(value, PersistentCollection):
                    value.setReadOnly(True)
                return value

            self._values._setNoinherit(name)

            raise NoValueForAttributeError, (self, name)

        elif default is not Default:
            return default

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
                                                   False, _attrID, None)
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
            otherName = self._kind.getOtherName(name, _attrID, self)
            _attrDict._removeValue(name, value, otherName)

        if hasattr(type(self), 'onValueChanged'):
            self.onValueChanged(name)
        Item._monitorsClass.invoke('remove', self, name)

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
        
        if self.isStale():
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
            if kind.itsView is not self.itsView:
                self.itsView.logger.error("kind %s for item %s is in view %s, not in item's view %s", kind.itsPath, self.itsPath, kind.itsView, self.itsView)
                return False
                
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

        value = self.getAttributeValue(attribute, _attrDict, None, Nil)
        if value is Nil:
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
            if attribute in self._values:
                _attrDict = self._values
            elif attribute in self._references:
                _attrDict = self._references
            elif self._kind.getOtherName(attribute, None, self, None):
                _attrDict = self._references
            else:
                redirect = self.getAttributeAspect(attribute, 'redirectTo',
                                                   False, None, None)
                if redirect is not None:
                    item = self
                    attributes = redirect.split('.')
                    for i in xrange(len(attributes) - 1):
                        item = item.getAttributeValue(attributes[i])

                    return item.setValue(attributes[-1], value, key, alias)

                else:
                    _attrDict = self._values

        isItem = isinstance(value, Item)
        attrValue = _attrDict.get(attribute, Nil)
            
        if attrValue is Nil:
            card = self.getAttributeAspect(attribute, 'cardinality',
                                           False, None, 'single')

            if card == 'dict':
                if _attrDict is self._references:
                    if isItem:
                        attrValue = self._refList(attribute)
                    else:
                        raise TypeError, type(value)
                else:
                    companion = self.getAttributeAspect(attribute, 'companion',
                                                        False, None, None)
                    attrValue = PersistentDict((self, attribute, companion))
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
                                                        False, None, None)
                    attrValue = PersistentList((self, attribute, companion))
                    _attrDict[attribute] = attrValue
                    attrValue.append(value)

                    return attrValue

            elif card == 'set':
                if _attrDict is self._references:
                    if isItem:
                        attrValue = self._refList(attribute)
                    else:
                        raise TypeError, type(value)
                else:
                    companion = self.getAttributeAspect(attribute, 'companion',
                                                        False, None, None)
                    attrValue = PersistentSet((self, attribute, companion))
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
            if attribute in self._values:
                _attrDict = self._values
            elif attribute in self._references:
                _attrDict = self._references
            elif self._kind.getOtherName(attribute, None, self, None):
                _attrDict = self._references
            else:
                redirect = self.getAttributeAspect(attribute, 'redirectTo',
                                                   False, None, None)
                if redirect is not None:
                    item = self
                    attributes = redirect.split('.')
                    for i in xrange(len(attributes) - 1):
                        item = item.getAttributeValue(attributes[i])

                    return item.addValue(attributes[-1], value, key, alias)

                else:
                    _attrDict = self._values

        attrValue = _attrDict.get(attribute, Nil)
        if attrValue is Nil:
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

        value = self.getAttributeValue(attribute, _attrDict, None, Nil)

        if value is not Nil:
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

        attrValue = self.getAttributeValue(attribute, _attrDict, None, Nil)
        if attrValue is Nil:
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
            if attribute in self._values:
                _attrDict = self._values
            elif attribute in self._references:
                _attrDict = self._references
            elif self._kind.getOtherName(attribute, None, self, None):
                _attrDict = self._references
            else:
                redirect = self.getAttributeAspect(attribute, 'redirectTo',
                                                   False, None, None)
                if redirect is not None:
                    item = self
                    attributes = redirect.split('.')
                    for i in xrange(len(attributes) - 1):
                        item = item.getAttributeValue(attributes[i])

                    return item.removeValue(attributes[-1], value, key, alias)

                else:
                    _attrDict = self._values

        values = _attrDict.get(attribute, Nil)

        if values is not Nil:
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

    def _setStale(self):

        self._status |= Item.STALE

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

    def setDirty(self, dirty, attribute=None, attrDict=None, noMonitors=False):
        """
        Mark this item to get committed with the current transaction.

        Returns C{True} if the dirty bit was changed from unset to set.
        Returns C{False} otherwise.

        If C{attribute} denotes a transient attribute (whose C{persisted}
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
                    if hasattr(type(self), 'onValueChanged'):
                        self.onValueChanged(attribute)
                    Item._monitorsClass.invoke('set', self, attribute)
                
            _countAccess(self)
            dirty |= Item.FDIRTY

            view = self.getRepositoryView()
            view._status |= view.FDIRTY
            
            if not self.isDirty():
                if not view.isLoading():
                    if attribute is not None:
                        if not self.getAttributeAspect(attribute, 'persisted',
                                                       True, None, True):
                            return False
                    if view._logItem(self):
                        self._status |= dirty
                        return True
                    elif self.isNew():
                        view.logger.error('logging of new item %s failed', self.itsPath)
            else:
                self._status |= dirty

        else:
            self._status &= ~(Item.DIRTY | Item.ADIRTY | Item.FDIRTY)
            self._values._clearDirties()
            self._references._clearDirties()
            if self._children is not None:
                self._children._clearDirties()

        return False

    def _collectItems(self, items, filter=None):

        def collectItems(item):
            parent = item.itsParent
            if parent._isItem() and not parent in items:
                if filter is None or filter(parent) is True:
                    return collectItems(parent)

            def collectChildren(_item):
                if not _item in items:
                    if filter is None or filter(_item) is True:
                        items.add(_item)
                    for child in _item.iterChildren():
                        collectItems(child)

            def collectReferences(_item):
                def collectOther(__item):
                    if __item not in items:
                        if filter is None or filter(__item) is True:
                            collectItems(__item)
                    
                for key, value in _item._references.items():
                    if value is not None:
                        if value._isRefList():
                            for other in value:
                                collectOther(other)
                        else:
                            if value._isUUID():
                                value = self.find(value)
                            collectOther(value)

            collectChildren(item)
            collectReferences(item)
            kind = item._kind
            if not (kind is None or kind in items):
                if filter is None or filter(kind) is True:
                    collectItems(kind)

        collectItems(self)

    def getItemCloud(self, cloudAlias, items=None, trace=None):
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
            cloud.getItems(self, cloudAlias, items, None, trace)

        return items.values()

    def copy(self, name=None, parent=None, copies=None,
             copyPolicy=None, cloudAlias=None, copyFn=None, kind=None):
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
        if kind is None:
            kind = self._kind
        if kind is not None:
            kind._setupClass(cls)

        if parent is None:
            parent = self.itsParent
        item._fillItem(name, parent, kind, uuid = UUID(), version = 0,
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
                return Nil

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
            item.onItemCopy(item.itsView, self)

        return item

    def delete(self, recursive=False, deletePolicy=None, cloudAlias=None,
               _noMonitors=False):
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

            if self.isStale():
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

            for name in self._references.keys():
                policy = (deletePolicy or
                          self.getAttributeAspect(name, 'deletePolicy',
                                                  False, None, 'remove'))
                if policy == 'cascade':
                    value = self._references._getRef(name)
                    if value is not None:
                        if value._isRefList():
                            others.extend([other for other in value])
                        else:
                            others.append(value)

            for other in others:
                if other.refCount(True) == 0:
                    other.delete(recursive, deletePolicy)

            self.__setKind(None, _noMonitors)

            self.itsParent._removeItem(self)
            self._setRoot(None, view)

            self._status |= Item.DELETED | Item.STALE
            self._status &= ~Item.DELETING

    def _copyExport(self, view, cloudAlias, matches):

        uuid = self._uuid

        if not uuid in matches:
            kind = self._kind
            if kind is None:
                itemParent = self.itsParent
                parent = itemParent.findMatch(view, matches)
                if parent is None:
                    parent = itemParent._copyExport(view, cloudAlias, matches)
                    if parent is None:
                        raise ValueError, 'match for parent (%s) not found' %(self.itsParent.itsPath)
                matches[self._uuid] = self.copy(self._name, parent)
            else:
                for cloud in kind.getClouds(cloudAlias):
                    cloud.exportItems(self, view, cloudAlias, matches)

        return matches[uuid]
            
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

        if not self.isStale():
            for name in self._references.iterkeys():
                if counted:
                    policy = self.getAttributeAspect(name, 'countPolicy',
                                                     False, None, 'none')
                    if policy == 'count':
                        count += self._references.refCount(name, loaded)
                else:
                    count += self._references.refCount(name, loaded)

        return count

    def _refCount(self):

        count = 0

        if not self.isStale():
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
                    raise NotImplementedError, 'changing views'

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
        if kind is not None and kind.isStale():
            kind = self.getRepositoryView()[kind._uuid]
            self._kind = kind
                
        return kind

    def __setKind(self, kind, _noMonitors=False):

        if kind is not self._kind:
            self.setDirty(Item.NDIRTY)

            if self._kind is not None:
                if kind is None:
                    self._values.clear()
                    self._references.clear()

                else:
                    def removeOrphans(attrDict):
                        for name in attrDict.keys():
                            curAttr = self._kind.getAttribute(name, False, self)
                            newAttr = kind.getAttribute(name, True)
                            if curAttr is not newAttr:
                                # if it wasn't removed by a reflexive bi-ref
                                if name in attrDict:
                                    self.removeAttributeValue(name, attrDict)

                    removeOrphans(self._values)
                    removeOrphans(self._references)

            prevKind = self._kind
            self._kind = kind

            if kind is None:
                self.__class__ = Item
            else:
                self.__class__ = kind.getItemClass()
                kind._setupClass(self.__class__)
                kind.getInitialValues(self, self._values, self._references)

            if not _noMonitors:
                if kind is not None or prevKind is not None:
                    Item._monitorsClass.invoke('schema', self, 'kind', prevKind)

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
            acl = self._acls.get(name, Nil)
        else:
            acl = Nil

        if acl is Nil:
            acl = self.getRepositoryView().getACL(self._uuid, name,
                                                  self._version)

        return acl

    def getRepositoryView(self):
        """
        Return this item's repository view.

        The item's repository view is defined as the item's root's parent.
        @return: a repository view
        """

        try:
            return self._root._parent
        except AttributeError:
            return None

    def __setRepositoryView(self, view):

        view.importItem(self)

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

        if self.isStale():
            raise StaleItemError, self

        child = None
        if name is not None and self._children is not None:
            child = self._children.getByAlias(name, None, load)

        return child

    def __getitem__(self, key):

        child = self.getItemChild(key)
        if child is not None:
            return child
        raise KeyError, key

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
        The callable may be C{None} in which case it is equivalent to:

            - C{lambda parent, name, child, **kwds: child}

        A C{load} keyword can be used to prevent loading of items by setting
        it to C{False}. Items are loaded as needed by default.

        @param path: an item path
        @type path: a L{Path<repository.util.Path.Path>} instance
        @param callable: a function, method, lambda body, or None
        @type callable: a python callable
        @param kwds: optional keywords passed to the callable
        @return: the item the walk finished on or C{None}
        """

        l = len(path)
        if l == 0 or _index >= l:
            return None

        attrName = kwds.get('attribute', None)
        if attrName is not None:
            attr = self._kind.getAttribute(attrName, False, self)
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
                otherName = self._kind.getOtherName(attrName, None, self)
                parent = self.getAttributeValue(otherName, self._references)
                otherAttr = self._kind.getAttribute(otherName, False, self)
                if otherAttr.cardinality == 'list':
                    parent = parent.first()
            else:
                parent = self.itsParent

            if _index == l - 1:
                return parent
            
            return parent.walk(path, callable, _index + 1, **kwds)

        if attr is not None:
            children = self.getAttributeValue(attrName, self._references,
                                              None, None)
            if children is not None:
                child = children.getByAlias(path[_index], None,
                                            kwds.get('load', True))
        else:
            name = path[_index]
            if isinstance(name, UUID):
                child = self.findUUID(name, kwds.get('load', True))
                if child is not None and child.itsParent is not self:
                    child = None
            else:
                child = self.getItemChild(name, kwds.get('load', True))
        
        if callable is not None:
            child = callable(self, path[_index], child, **kwds)
        if child is not None:
            if _index == l - 1:
                return child
            return child.walk(path, callable, _index + 1, **kwds)

        return None

    def _fwalk(self, path, load=True):

        item = self
        for name in path:

            if name == '//':
                item = item.itsView
            elif name == '/':
                item = item.itsRoot
            elif name == '..':
                item = item.itsParent
            elif name == '.':
                item = item
            elif isinstance(name, UUID):
                item = item.itsView.find(name, load)
            else:
                item = item.getItemChild(name, load)

            if item is None:
                break

        return item

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
                    L{UUID<chandlerdb.util.uuid.UUID>} 
        @param attribute: the attribute for the ref-collections to search
        @type attribute: a string
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

        if isinstance(spec, UUID):
            return self.getRepositoryView().find(spec, load)

        if isinstance(spec, Path):
            if attribute is None:
                return self._fwalk(spec, load)
            return self.walk(spec, None, attribute=attribute, load=load)

        raise TypeError, '%s, %s is not Path or UUID' %(spec, type(spec))

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

        if attribute is None:
            return self._fwalk(path, load)

        return self.walk(path, None, attribute=attribute, load=load)

    def findUUID(self, uuid, load=True):
        """
        Find an item by UUID.

        See L{find} for more information.

        @param uuid: a UUID
        @type uuid: L{UUID<chandlerdb.util.uuid.UUID>} or a uuid string
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

        if isinstance(uuid, str) or isinstance(uuid, unicode):
            uuid = UUID(uuid)
        elif not isinstance(uuid, UUID):
            raise TypeError, '%s is not UUID or string' %(type(uuid))

        return self.getRepositoryView().find(uuid, load)

    def findMatch(self, view, matches=None):

        uuid = self._uuid

        if matches is not None:
            match = matches.get(uuid)
        else:
            match = None
            
        if match is None:
            match = view.find(uuid)
            if match is None and self._name is not None:
                match = view.find(self.itsPath)
                if not (match is None or matches is None):
                    matches[uuid] = match

        return match

    def _unloadItem(self, reloadable, view):

        if self.isDirty():
            raise DirtyItemError, self

        if hasattr(type(self), 'onItemUnload'):
            self.onItemUnload(view)

        if not self.isStale():

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

    def _refList(self, name, otherName=None, persisted=None):

        if otherName is None:
            otherName = self._kind.getOtherName(name, None, self)
        if persisted is None:
            persisted = self.getAttributeAspect(name, 'persisted',
                                                False, None, True)

        return self.getRepositoryView()._createRefList(self, name, otherName,
                                                       persisted, False, True,
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

    def hashItem(self):
        """
        Compute a hash value from this item's class, kind and attribute values.

        The hash value is computed from the item's class name, kind hash,
        and persistent attribute name-value pairs. The version, uuid,
        parent, children of the item are not used in the computation. The
        returned hash value can be used to compare items for schema and
        value sameness.

        @return: an integer
        """

        cls = type(self)

        hash = _hash('.'.join((cls.__module__, cls.__name__)))
        if self._kind is not None:
            hash = _combine(hash, self._kind.hashItem())
        hash = _combine(hash, self._values._hashValues())
        hash = _combine(hash, self._references._hashValues())

        return hash

    def printItem(self, recursive=False, _level=0):
        """
        A pretty-printer for items.
    
        @param recursive: Whether to also recurse down to child items,
        C{False} by default. 
        @type recursive: boolean
        """

        self._printItemHeader(_level)
        self._printItemBody(_level)

        if recursive:
            for child in self.iterChildren():
                print
                child.printItem(True, _level + 1)

    def _printItemHeader(self, _level):

        print ' ' * _level,
    
        if self._kind is not None:
            print self.itsPath, "(Kind: %s)" % (self._kind.itsPath)
        else:
            print self.itsPath

    def _printItemBody(self, _level):

        indent2 = ' ' * (_level + 2)
        indent4 = ' ' * (_level + 4)

        displayedAttrs = {}
        for (name, value) in self.iterAttributeValues():
            displayedAttrs[name] = value

        keys = displayedAttrs.keys()
        keys.sort()
        for name in keys:
            value = displayedAttrs[name]

            if isinstance(value, RefList):
                print indent2, "%s: (list)" %(name)
                for item in value:
                    print indent4, item._repr_()

            elif isinstance(value, dict):
                print indent2, "%s: (dict)" %(name)
                for k, v in value.iteritems():
                    print indent4, "%s: <%s>" %(k, type(v).__name__), repr(v)

            elif isinstance(value, list):
                print indent2, "%s: (list)" %(name)
                for v in value:
                    print indent4, "<%s>" %(type(v).__name__), repr(v)

            elif isinstance(value, Item):
                print indent2, "%s:" %(name), value._repr_()

            else:
                print indent2, "%s: <%s>" %(name, type(value).__name__), repr(value)


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
                       fset = __setRepositoryView,
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
