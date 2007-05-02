#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from __future__ import with_statement

from chandlerdb.util.c import \
    UUID, _hash, _combine, isuuid, Nil, Default, Empty
from chandlerdb.schema.c import _countAccess
from chandlerdb.item.c import CItem, isitem, isitemref, ItemValue
from chandlerdb.item.ItemError import *

from repository.item.RefCollections import RefList, RefDict
from repository.item.Values import Values, References
from repository.item.PersistentCollections import \
     PersistentCollection, PersistentList, PersistentDict, \
     PersistentTuple, PersistentSet

from repository.util.Path import Path


def override(cls):
    def override(method):
        method.__override__ = cls
        return method
    return override


class ItemClass(type):

    __finals__ = set(name for name, value in CItem.__dict__.iteritems()
                     if callable(value) and not name.startswith('__'))

    def __init__(cls, clsName, bases, clsdict):

        for name, value in clsdict.iteritems():
            if name in ItemClass.__finals__:
                if not getattr(value, '__override__', Nil) in bases:
                    raise TypeError, (cls, name, 'is final')


class Item(CItem):
    """
    The root class for all items.
    """
    __metaclass__ = ItemClass

    def __init__(self, itsName=None, itsParent=None, itsKind=None,
                 _uuid=None, fireChanges=True, **values):
        """
        Construct an Item.

        @param itsName: The name of the item. It must be unique among the names
        this item's siblings. C{itsName} is optional, except for roots and is
        C{None} by default.
        @type itsName: a string or C{None} to create an anonymous item.
        @param itsParent: The parent of this item. All items require a parent
        unless they are a repository root in which case the parent argument
        is a repository view.
        @type itsParent: an item or the item's repository view.
        @param itsKind: The kind for this item. This kind has definitions for
        all the Chandler attributes that are to be used with this item.
        This parameter can be C{None} for Chandler attribute-less operation.
        Items have two sets of attributes: the regular implementation python
        attributes and the Chandler attributes. When an item is persisted
        only the Chandler attributes are saved.
        @type itsKind: an item
        @param values: extra keyword arguments to set values on the item
        after being constructed.
        @type values: C{name=value} pairs
        """

        # this constructor should not be run more than once
        if self.itsUUID is not None:
            return

        if itsParent is None:
            raise ValueError, 'parent cannot be None, for roots use a view'

        if itsName is None and not isitem(itsParent):
            raise AnonymousRootError, self

        super(Item, self).__init__(_uuid or UUID(), itsName or None, itsParent)

        cls = type(self)
        self._values = Values(self)
        self._references = References(self)
        self._kind = itsKind
        self._version = 0L

        if itsKind is not None:
            itsKind._setupClass(cls)

        try:
            if itsKind is not None:
                self.setDirty(Item.NDIRTY | Item.KDIRTY | Item.NODIRTY)
                itsKind.getInitialValues(self, True)
            else:
                self.setDirty(Item.NDIRTY | Item.NODIRTY)

            self._setInitialValues(values, fireChanges)
        finally:
            self._status &= ~Item.NODIRTY

        if fireChanges and itsKind is not None:
            self.itsView._notifyChange(itsKind.extent._collectionChanged,
                                       'add', 'collection', 'extent',
                                       self.itsUUID, ())

    # fire afterChange methods on initial keyword values
    # fire system monitors on all values, initial or set during afterChange
    def _setInitialValues(self, values, fireChanges):

        # defer all notifications globally so that bi-ref notifs don't fire
        # until all initial values are set below
        with self.itsView.notificationsDeferred():
            for name, value in values.iteritems():
                setattr(self, name, value)

        if fireChanges:
            self._status &= ~Item.NODIRTY
            try:
                self._status |= Item.SYSMONONLY
                for name in self._values.keys():
                    self._fireChanges('init', name, name in values)
                for name in self._references.keys():
                    self._fireChanges('init', name, name in values)
            finally:
                self._status &= ~Item.SYSMONONLY

    def _repr_(self):

        return CItem.__repr__(self)
    
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

        kind = self.itsKind

        if kind is not None:
            attribute = kind.getAttribute(name, True, self)
            if attribute is not None:
                return attribute.hasAspect(aspect)

        return False

    def setAttributeValue(self, name, value=None, _attrDict=None,
                          otherName=None, setDirty=True, _noFireChanges=False):
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

        _values = self._values
        _references = self._references
        
        if _attrDict is None:
            if name in _values:
                _attrDict = _values
                otherName = Nil
            elif name in _references:
                _attrDict = _references
            else:
                if otherName is None:
                    otherName = self.itsKind.getOtherName(name, self, Nil)
                if otherName is not Nil:
                    _attrDict = _references
                else:
                    _attrDict = _values

        isItem = isitem(value)
        wasRefs = False
        old = None

        if _attrDict is _references:
            if name in _attrDict:
                old = _attrDict[name]
                if old is value:
                    return value
                if old not in (None, Empty):
                    if isItem and isuuid(old):
                        if old == value.itsUUID:
                            return value
                    elif old._isRefs():
                        wasRefs = True
                        old._removeRefs()

        if isItem or value in (None, Empty):
            if _attrDict is _values:
                _values[name] = value
                dirty = Item.VDIRTY
            else:
                if otherName is None:
                    otherName = self.itsKind.getOtherName(name, self)
                _references._setValue(name, value, otherName, _noFireChanges)
                setDirty = False

        elif not isinstance(value, (RefList, RefDict, list, dict, tuple, set)):

            if _attrDict is not _values:
                from repository.item.Sets import AbstractSet
                if isinstance(value, AbstractSet):
                    _references[name] = value
                    value._setOwner(self, name)
                    value._fillRefs()
                    dirty = Item.VDIRTY
                else:
                    raise TypeError, ('Expecting an item or a ref collection',
                                      value)
            else:
                _values[name] = value
                if isinstance(value, ItemValue):
                    value._setOwner(self, name)
                dirty = Item.VDIRTY

        elif isinstance(value, (RefList, list)):
            if _attrDict is _references:
                if old in (None, Empty):
                    _references[name] = refList = self._refList(name)
                else:
                    if not wasRefs:
                        raise CardinalityError, (self, name, 'multi-valued')
                    refList = old

                refList.extend(value, _noFireChanges)
                value = refList
                setDirty = False
            else:
                attrValue = PersistentList(self, name, value, False)
                _values[name] = attrValue
                dirty = Item.VDIRTY

        elif isinstance(value, (RefDict, dict)):
            if _attrDict is _references:
                if old is None:
                    if otherName is None:
                        otherName = self.itsKind.getOtherName(name, self)
                    _references[name] = refDict = RefDict(self, name, otherName)
                else:
                    if not wasRefs:
                        raise CardinalityError, (self, name, 'multi-valued')
                    refDict = old

                refDict.update(value, _noFireChanges)
                value = refDict
                setDirty = False
            else:
                attrValue = PersistentDict(self, name, value, False)
                _values[name] = attrValue
                dirty = Item.VDIRTY
            
        elif isinstance(value, tuple):
            if _attrDict is _references:
                if old is None:
                    _references[name] = refList = self._refList(name)
                else:
                    if not wasRefs:
                        raise CardinalityError, (self, name, 'multi-valued')
                    refList = old

                refList.extend(value, _noFireChanges)
                value = refList
                setDirty = False
            else:
                attrValue = PersistentTuple(self, name, value)
                _values[name] = attrValue
                dirty = Item.VDIRTY
            
        elif isinstance(value, set):
            if _attrDict is _references:
                if old is None:
                    _references[name] = refList = self._refList(name)
                else:
                    if not wasRefs:
                        raise CardinalityError, (self, name, 'multi-valued')
                    refList = old

                refList.extend(value, _noFireChanges)
                value = refList
                setDirty = False
            else:
                attrValue = PersistentSet(self, name, value, False)
                _values[name] = attrValue
                dirty = Item.VDIRTY

        if setDirty:
            self.setDirty(dirty, name, _attrDict, _noFireChanges)
        
        return value

    def setFreeValue(self, name, item):

        self.setValue('freeValues', item, name, None, name)

    def addFreeValue(self, name, item):

        self.addValue('freeValues', item, name, None, name)

    def getFreeValue(self, name, default=Nil):

        return self.getValue('freeValues', name, None, default)

    def removeFreeValue(self, name, item=None):

        self.removeValue('freeValues', item, name)

    def _registerWatch(self, watchingItem, cls, key, *args):

        watchers = self.getValue('watchers', key, None, None)
        if watchers:
            for watcher in watchers:
                if (watcher.watchingItem is watchingItem and
                    type(watcher) is cls and watcher.compare(*args)):
                    return watcher

        watcher = cls(watchingItem, *args)
        self.addValue('watchers', watcher, key)

        if cls is WatchItem:
            self._status |= Item.P_WATCHED

        return watcher

    def _unregisterWatch(self, watchingItem, cls, key, *args):

        watchers = self.getValue('watchers', key, None, None)
        if watchers:
            for watch in watchers:
                if (watch.watchingItem is watchingItem and
                    type(watch) is cls and watch.compare(*args)):
                    watchers.remove(watch)

                    if cls is WatchItem and not watchers:
                        self._status &= ~Item.P_WATCHED

    def _watchSet(self, owner, attribute, name):
        return owner._registerWatch(self, WatchSet, attribute, name)

    def _unwatchSet(self, owner, attribute, name):
        owner._unregisterWatch(self, WatchSet, attribute, name)

    def watchCollection(self, owner, attribute, methodName):
        return owner._registerWatch(self, WatchCollection,
                                    attribute, methodName)

    def unwatchCollection(self, owner, attribute, methodName):
        owner._unregisterWatch(self, WatchCollection, attribute, methodName)

    def watchKind(self, kind, methodName):
        return kind.extent._registerWatch(self, WatchKind, 'extent', methodName)

    def unwatchKind(self, kind, methodName):
        kind.extent._unregisterWatch(self, WatchKind, 'extent', methodName)

    def watchItem(self, item, methodName):
        return item._registerWatch(self, WatchItem, item.itsUUID, methodName)

    def unwatchItem(self, item, methodName):
        item._unregisterWatch(self, WatchItem, item.itsUUID, methodName)

    def getAttributeValue(self, name, _attrDict=None, _attrID=None,
                          default=Default, noInherit=False):
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
        @return: a value
        """

        if self.isStale():
            raise StaleItemError, self

        _countAccess(self)

        if (_attrDict is self._values or
            _attrDict is None and name in self._values):
            value = self._values.get(name, Nil)
            if value is not Nil:
                if isitemref(value):
                    return value(True)
                return value

        elif (_attrDict is self._references or
              _attrDict is None and name in self._references):
            value = self._references._getRef(name, None, None, Nil)
            if value is not Nil:
                return value

        if not (noInherit or self.itsKind is None):
            if _attrID is not None:
                attribute = self.itsView[_attrID]
            else:
                attribute = self.itsKind.getAttribute(name, False, self)

            # schema-level attribute inheritFrom
            inherit = attribute.getAspect('inheritFrom', None)
            if inherit is not None:
                value = self
                for attr in inherit.split('.'):
                    value = value.getAttributeValue(attr, None, None, Nil)
                    if value is Nil:
                        break
                if value is not Nil:
                    return value

            # instance-level attribute inheritFrom
            inherit = self._references.get('inheritFrom')
            if inherit is not None:
                value = inherit.getAttributeValue(name, None, None, default)
                if value is not Default:
                    return value

            if default is not Default:
                return default

            value = attribute.c.getAspect('defaultValue', Nil)
            if value is not Nil:
                if isinstance(value, PersistentCollection):
                    value._setReadOnly(True)
                return value

            raise NoValueForAttributeError, (self, name)

        elif default is not Default:
            return default

        raise NoValueForAttributeError, (self, name)

    def removeAttributeValue(self, name, _attrDict=None, _attrID=None,
                             _noFireChanges=False):
        """
        Remove a value for a Chandler attribute.

        Calling this method instead of using python's C{del} operator is not
        necessary as python calls this method via the corresponding
        attribute descriptor.

        This method only deletes a local value. A value inherited via
        C{defaultValue} or C{inheritFrom} cannot be deleted and causes this
        method to do nothing.

        @param name: the name of the attribute
        @type name: a string
        @return: C{None}
        """

        if _attrDict is None:
            if name in self._values:
                _attrDict = self._values
            elif name in self._references:
                _attrDict = self._references
            elif hasattr(self, name): # inherited value
                return
            else:
                raise NoLocalValueForAttributeError, (self, name)

        if _attrDict is self._values:
            if name in _attrDict:
                del _attrDict[name]
                self.setDirty(Item.VDIRTY, name, _attrDict, True)
            elif hasattr(self, name):   # inherited value
                return
            else:
                raise NoLocalValueForAttributeError, (self, name)
        else:
            if name in _attrDict:
                value = _attrDict._getRef(name)
                otherName = self.itsKind.getOtherName(name, self)
                _attrDict._removeValue(name, value, otherName)
            elif hasattr(self, name):   # inherited value
                return
            else:
                raise NoLocalValueForAttributeError, (self, name)

        if not _noFireChanges:
            self._fireChanges('remove', name)

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

        if self._children is not None:
            if not load:
                for link in self._children._itervalues():
                    yield link.value
            else:
                for child in self._children:
                    yield child

    def iterChildrenKeys(self, load=True):

        if self.isStale():
            raise StaleItemError, self

        if self._children is not None:
            if not load:
                for uChild in self._children._iterkeys():
                    yield uChild
            else:
                for uChild in self._children.iterkeys():
                    yield uChild

    def iterAttributeValues(self, valuesOnly=False, referencesOnly=False,
                            changedOnly=False):
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
            values = self.itsValues
            for name, value in values._dict.iteritems():
                if not changedOnly or value._isDirty(name):
                    if isitemref(value):
                        value = value(True)
                    yield name, value

        if not valuesOnly:
            refs = self.itsRefs
            for name, ref in refs._dict.iteritems():
                if not changedOnly or refs._isDirty(name):
                    if isitemref(ref):
                        ref = ref()
                    yield name, ref

    def iterAttributeNames(self, valuesOnly=False, referencesOnly=False,
                           changedOnly=False):
        """
        Return a generator of attribute names for iterating over
        Chandler attributes of this item. 

        @param valuesOnly: if C{True}, iterate over attributes containing
        literal values only. C{False} by default.
        @type valuesOnly: boolean
        @param referencesOnly: if C{True}, iterate over attributes
        containing item reference values only. C{False} by default.
        @type referencesOnly: boolean
        """

        if not referencesOnly:
            values = self.itsValues
            for name in values._dict.iterkeys():
                if not changedOnly or values._isDirty(name):
                    yield name

        if not valuesOnly:
            refs = self.itsRefs
            for name in refs._dict.iterkeys():
                if not changedOnly or refs._isDirty(name):
                    yield name

    def check(self, recursive=False, repair=False):
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
        @param repair: if C{True}, perform repairs on failures.
        @return: C{True} if no errors were found, C{False} otherwise. Errors
        are logged in the Chandler execution log.
        """

        logger = self.itsView.logger
        view = self.itsView

        checkValues = self._values.check(repair)
        checkRefs = self._references.check(repair)
        result = checkValues and checkRefs

        name = self.itsName
        if name is not None:
            encoded = name.decode('ascii', 'replace').encode('ascii', 'replace')
            if encoded != name:
                logger.error("Name of item with UUID %s, '%s' contains non-ASCII characters", self.itsUUID, encoded)
                result = False

        kind = self._kind
        if kind is not None:
            if kind.itsView is not self.itsView:
                logger.error("kind %s for item %s is in view %s, not in item's view %s", kind.itsPath, self.itsPath, kind.itsView, self.itsView)
                return False
                
            for name, desc in kind.c.descriptors.iteritems():
                attrDict, required = desc.isValueRequired(self)
                if attrDict is not None:
                    if required and name not in attrDict:
                        logger.error("Required value for attribute %s on %s is missing", name, self._repr_())
                        result = False
        
        if self._children is not None:
            l = len(self._children)
            for uChild in list(self.iterChildrenKeys()):
                child = view[uChild]
                l -= 1
                if recursive:
                    check = child.check(True, repair)
                    result = result and check
                if l == 0:
                    break
            if l != 0:
                logger.error("Iterator on children of %s doesn't match length (%d left for %d total)", self._repr_(), l, len(self._children))
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
            return self.itsView.getItemVersion(0x7fffffff, self)

        return self.itsVersion
        
    def getValue(self, attribute, key=None, alias=None,
                 default=Nil, _attrDict=None):
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
            if default is Nil:
                raise NoValueForAttributeError, (self, attribute)
            return default

        if isinstance(value, (RefList, RefDict)):
            if key is not None:
                value = value.get(key, default)
                if value is default:
                    if value is Nil:
                        raise NoValueForAttributeError, (self, attribute, key)
                    return value
            if alias is not None:
                value = value.getByAlias(alias, default)
                if value is Nil:
                    raise NoValueForAttributeError, (self, attribute, alias)
            return value

        if isinstance(value, dict):
            value = value.get(key, default)
            if value is Nil:
                raise NoValueForAttributeError, (self, attribute, key)
            return value

        if isinstance(value, list):
            if key < len(value):
                return value[key]
            elif default is Nil:
                raise NoValueForAttributeError, (self, attribute, key)
            else:
                return default

        raise CardinalityError, (self, attribute, 'multi-valued')

    def setValue(self, attribute, value, key=None, alias=None, otherKey=None,
                 _attrDict=None):
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
            else:
                if self.itsKind.getOtherName(attribute, self, None):
                    _attrDict = self._references
                else:
                    _attrDict = self._values

        isItem = isitem(value)
        attrValue = _attrDict.get(attribute, Nil)
            
        if attrValue is Nil:
            card = self.getAttributeAspect(attribute, 'cardinality',
                                           False, None, 'single')

            if card == 'dict':
                if _attrDict is self._references:
                    if isItem:
                        otherName = self.itsKind.getOtherName(attribute, self)
                        attrValue = RefDict(self, attribute, otherName)
                    else:
                        raise TypeError, type(value)
                else:
                    attrValue = PersistentDict(self, attribute)
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
                    attrValue = PersistentList(self, attribute)
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
                    attrValue = PersistentSet(self, attribute)
                    _attrDict[attribute] = attrValue
                    attrValue.append(value)

                    return attrValue

            else:
                self.setAttributeValue(attribute, value, _attrDict)
                return value

            _attrDict[attribute] = attrValue

        if _attrDict is self._references:
            if isItem:
                if attrValue._isDict():
                    attrValue.set(key, value, alias, otherKey)
                else:
                    attrValue.set(value, alias, otherKey)
            else:
                raise TypeError, type(value)
        else:
            attrValue[key] = value

        return attrValue

    def addValue(self, attribute, value, key=None, alias=None, otherKey=None,
                 _attrDict=None):
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
            else:
                if self.itsKind.getOtherName(attribute, self, None):
                    _attrDict = self._references
                else:
                    _attrDict = self._values

        attrValue = _attrDict.get(attribute, Nil)
        if attrValue is Nil:
            return self.setValue(attribute, value, key, alias, otherKey,
                                 _attrDict)

        elif isinstance(attrValue, RefList):
            if isitem(value):
                attrValue.append(value, alias, otherKey)
            else:
                raise TypeError, type(value)
        elif isinstance(attrValue, RefDict):
            if isitem(value):
                attrValue.add(key, value, alias, otherKey)
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
                return key in value
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
            else:
                if self.itsKind.getOtherName(attribute, self, None):
                    _attrDict = self._references
                else:
                    _attrDict = self._values

        values = _attrDict.get(attribute, Nil)

        if values is not Nil:
            if isinstance(values, RefList):
                if alias is not None:
                    key = value.resolveAlias(alias)
                elif key is None:
                    key = value.itsUUID
                del values[key]
            elif isinstance(values, RefDict):
                if alias is None:
                    if value is None:
                        del values[key]
                    else:
                        del values[key][value.itsUUID]
                else:
                    del values[key][values.resolveAlias(alias)]
            elif isinstance(values, (list, set)):
                if key is not None:
                    value = values[key]
                values.remove(value)
            elif isinstance(values, dict):
                del values[key]
            else:
                raise TypeError, type(values)
        else:
            raise KeyError, 'No value for attribute %s' %(attribute)

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
        for cloud in self.itsKind.getClouds(cloudAlias):
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
        L{ItemRef<chandlerdb.item.c.ItemRef>} values.

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
        hooks = []
        item._fillItem(name, parent, kind, UUID(), self.itsView,
                       Values(), References(), 0, 0,
                       hooks, False)
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
            item._setInitialValues(Nil, True)
        finally:
            item._status &= ~Item.NODIRTY
            
        if kind is not None:
            item.setDirty(Item.NDIRTY | Item.KDIRTY)
        else:
            item.setDirty(Item.NDIRTY)

        view = item.itsView
        for hook in hooks:
            hook(view)
        if kind is not None:
            view._notifyChange(kind.extent._collectionChanged,
                               'add', 'collection', 'extent',
                               item.itsUUID, ())
        if hasattr(cls, 'onItemCopy'):
            item.onItemCopy(view, self)

        return item

    def clone(self, name=None, parent=None,
              exclude=(), fireChanges=True, **values):

        cls = type(self)
        item = cls.__new__(cls)
        kind = self._kind
        if kind is not None:
            kind._setupClass(cls)

        if parent is None:
            parent = self.itsParent
        hooks = []
        item._fillItem(name, parent, kind, UUID(), self.itsView,
                       Values(), References(), 0, 0,
                       hooks, False)

        try:
            item._status |= Item.NODIRTY
            item._values._clone(self._values, exclude)
            item._references._clone(self._references, exclude)
            item._setInitialValues(values, fireChanges)
        finally:
            item._status &= ~Item.NODIRTY
        
        if kind is not None:
            item.setDirty(Item.NDIRTY | Item.KDIRTY)
        else:
            item.setDirty(Item.NDIRTY)

        view = item.itsView
        for hook in hooks:
            hook(view)
        if kind is not None:
            view._notifyChange(kind.extent._collectionChanged,
                               'add', 'collection', 'extent',
                               item.itsUUID, ())
        if hasattr(cls, 'onItemClone'):
            item.onItemClone(view, self)

        return item

    def delete(self, recursive=False, deletePolicy=None, cloudAlias=None,
               _noFireChanges=False):
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
            if not self.isDeleted():
                clouds = self.itsKind.getClouds(cloudAlias)
                for cloud in clouds:
                    cloud.deleteItems(self, recursive, cloudAlias)

        elif not self._status & (Item.DELETED | Item.DELETING | Item.DEFERRING):

            if self.isStale():
                raise StaleItemError, self

            if not recursive and self.hasChildren():
                raise RecursiveDeleteError, self

            view = self.itsView

            if view.isDeferringDelete():
                self._deferDelete(view, deletePolicy)
            else:
                self._delete(view, recursive, deletePolicy,
                             _noFireChanges, False)

    def _deferDelete(self, view, deletePolicy):

        refs = self._references
        others = set()

        self._status |= Item.DEFERRING

        if hasattr(type(self), 'onItemDelete'):
            self.onItemDelete(view, True)

        if not self.isDeferred():
            self._status |= Item.DEFERRED
            self.setDirty(Item.NDIRTY)
        else:
            for tuple in view._deferredDeletes:
                if tuple[0] is self:
                    view._deferredDeletes.remove(tuple)
                    break

        view._deferredDeletes.append((self, 'delete', (deletePolicy,)))

        for child in self.iterChildren():
            child.delete(True, deletePolicy)

        if self.isWatched():
            view._notifyChange(self._itemChanged, 'set', ('itsStatus',))

        if self.itsKind is not None:
            view._notifyChange(self.itsKind.extent._collectionChanged,
                               'remove', 'collection', 'extent',
                               self.itsUUID, ())

        for name in refs.keys():
            policy = (deletePolicy or
                      self.getAttributeAspect(name, 'deletePolicy',
                                              False, None, 'remove'))
            if policy == 'cascade':
                value = refs._getRef(name)
                if value is not None:
                    if value._isRefs():
                        others.update(value.iterItems())
                    else:
                        others.add(value)

        for other in others:
            if other.refCount(True) == 0:
                other.delete(True, deletePolicy)

        if not self.isSchema():
            for name, value in refs.items():
                if value is not None:
                    if value._isRefs():
                        if name not in ('watches', 'monitors'):
                            value.clear()
                    else:
                        setattr(self, name, None)

        self._status &= ~Item.DEFERRING

    def _delete(self, view, recursive, deletePolicy, _noFireChanges, _keepRoot):

        refs = self._references
        others = set()

        self.setDirty(Item.NDIRTY)
        self._status |= Item.DELETING

        if hasattr(type(self), 'onItemDelete'):
            self.onItemDelete(view, False)

        for child in self.iterChildren():
            child.delete(True, deletePolicy)

        if self.isWatched():
            view._notifyChange(self._itemChanged, 'remove',
                               ('itsKind',))
            self._status &= ~Item.WATCHED

        if 'watches' in refs:
            for watch in self.watches:
                watch._delete(view, True, None, _noFireChanges, _keepRoot)
        view._unregisterWatches(self)

        if 'monitors' in refs:
            for monitor in self.monitors:
                monitor._delete(view, True, None, _noFireChanges, _keepRoot)

        for name in refs.keys():
            policy = (deletePolicy or
                      self.getAttributeAspect(name, 'deletePolicy',
                                              False, None, 'remove'))
            if policy == 'cascade':
                value = refs._getRef(name)
                if value is not None:
                    if value._isRefs():
                        others.update(value.iterKeys())
                    else:
                        others.add(value)

        for other in others:
            if isuuid(other):
                other = view.find(other)
                if other is None:
                    continue
            if other.refCount(True) == 0:
                other._delete(view, True, deletePolicy, _noFireChanges, _keepRoot)

        self._setKind(None, _noFireChanges)
        self.itsParent._removeItem(self)

        if _keepRoot:  # during merge (to delete deferred children)
            view._unregisterItem(self, False)
            self._status |= Item.DELETED
        else:
            view._unregisterItem(self, False)
            self._status |= Item.DELETED | Item.STALE

        self._status &= ~(Item.DELETING | Item.DEFERRED)

    def _effectDelete(self, op, args):

        if op == 'remove':
            name, value = args
            if hasattr(self, name):
                delattr(self, name)

        elif op == 'delete':
            deletePolicy, = args
            self.delete(True, deletePolicy)

    def refCount(self, counted=False, loaded=False):
        """
        Return the number of bi-directional references to this item.

        The number returned depends on:

            - C{counted}: if C{True}, return the number of references in
              attributes whose C{countPolicy} is C{count}.

            - C{loaded}: if C{True}, return the number of loaded references.

        These keyword arguments may be used together. If they are both
        C{False} this method returns the total number of references to this
        item.

        @return: an integer
        """

        count = 0

        if not self.isStale():
            for name in self._references._dict.iterkeys():
                if counted:
                    policy = self.getAttributeAspect(name, 'countPolicy',
                                                     False, None, 'none')
                    if policy == 'count':
                        count += self._references.refCount(name, loaded)
                else:
                    count += self._references.refCount(name, loaded)

        return count

    def _getPath(self, path=None):

        if path is None:
            path = Path()
            
        self.itsParent._getPath(path)
        path.append(self.itsName or self.itsUUID)

        return path

    def _setKind(self, kind, _noFireChanges=False):

        if kind is not self._kind:
            if self._status & Item.MUTATING:
                raise NotImplementedError, 'recursive kind change'

            self._futureKind = kind
            if not self._isKDirty():
                if self._kind is None:
                    self._pastKind = None
                else:
                    self._pastKind = self._kind.itsUUID

            self.setDirty(Item.KDIRTY | Item.MUTATING)
            view = self.itsView

            prevKind = self._kind
            if prevKind is not None:
                view._notifyChange(prevKind.extent._collectionChanged,
                                   'remove', 'collection', 'extent',
                                   self.itsUUID, (), kind)

                if kind is None:
                    self._values.clear()
                    self._references.clear()

                else:
                    def removeOrphans(attrDict):
                        for name in attrDict.keys():
                            curAttr = prevKind.getAttribute(name, False, self)
                            newAttr = kind.getAttribute(name, True)
                            if curAttr is not newAttr:
                                # if it wasn't removed by a reflexive bi-ref
                                if name in attrDict:
                                    self.removeAttributeValue(name, attrDict)

                    removeOrphans(self._values)
                    removeOrphans(self._references)

            self._kind = kind
            self._status &= ~Item.MUTATING
            del self._futureKind

            if kind is None:
                self.__class__ = Item
                if self.isWatched():
                    view._notifyChange(self._itemChanged,
                                       'remove', ('itsKind',))
            else:
                self.__class__ = kind.getItemClass()
                kind._setupClass(self.__class__)
                kind.getInitialValues(self, False)
                view._notifyChange(kind.extent._collectionChanged,
                                   'add', 'collection', 'extent',
                                   self.itsUUID, (), prevKind)
                if self.isWatched():
                    view._notifyChange(self._itemChanged,
                                       'set', ('itsKind',))

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

        @param kinds: any number of tuples as described above.
        @type kinds: tuple
        @return: the item's kind after the method completes
        """

        superKinds = []
        kind = self.itsKind
        if kind is not None:
            if kind.isMixin():
                superKinds[:] = kind.superKinds
            else:
                superKinds.append(kind)

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
        kind = self.itsKind
        
        if count == 0 and (kind is None or kind.isMixin()):
            kind = None
        elif count == 1 and kind is not None and kind.isMixin():
            kind = superKinds[0]
        else:
            if kind is None or kind.isMixin():
                kind = superKinds.pop(0)
            kind = kind.mixin(superKinds)

        self._setKind(kind)

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

    def getACL(self, name=None, default=Default):
        """
        Get an ACL from this item.

        An ACL can be obtained from the item or from individual attributes
        on the item.

        @param name: the name of the attribute to get the ACL from or C{None}
        to get the ACL for the item.
        @type name: a string
        @return: an L{ACL<repository.item.Access.ACL>} instance or C{None} if
        no ACL is set
        @param default: an optional default value to return when no ACL is
        found (by default an error is raised)
        """

        if self._acls is not None:
            acl = self._acls.get(name, Nil)
        else:
            acl = Nil

        if acl is Nil:
            acl = self.itsView.getACL(self.itsUUID, name, default)

        if acl is Default:
            raise ItemError, ('no acl found and no default provided', name)

        return acl

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

            if isitem(parent):
                children = parent._children
            else:
                children = parent._roots

            uuid = self.itsUUID

            if name is not None:
                if children.resolveAlias(name) not in (None, uuid):
                    raise ChildNameError, (parent, name)
                
            self._name = name
            children.setAlias(uuid, name)

            self.setDirty(Item.NDIRTY)
                
    def move(self, newParent):
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
        """

        if newParent is None:
            raise ValueError, 'newParent cannot be None'
            
        parent = self.itsParent
        if parent is not newParent:
            if parent is not None:
                parent._removeItem(self)
            self._parent = newParent
            self.setDirty(Item.NDIRTY)

    def _addItem(self, item):

        name = item.itsName

        if self._children is not None:
            if name is not None:
                loading = self.itsView.isLoading()
                key = self._children.resolveAlias(name, not loading)
                if not (key is None or key == item.itsUUID):
                    raise ChildNameError, (self, name)

        else:
            self._children = self.itsView._createChildren(self, True)

        self._children._append(item)

    def _removeItem(self, item):

        del self._children[item.itsUUID]

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

    def getNextChild(self, child):

        nextKey = self._children.nextKey(child.itsUUID)
        if nextKey is not None:
            return self.itsView[nextKey]

        return None

    def getFirstChild(self):

        firstKey = self._children.firstKey()
        if firstKey is not None:
            return self.itsView[firstKey]

        return None

    def getLastChild(self):

        lastKey = self._children.lastKey()
        if lastKey is not None:
            return self.itsView[lastKey]

        return None

    def getPreviousChild(self, child):

        nextKey = self._children.previousKey(child.itsUUID)
        if nextKey is not None:
            return self.itsView[nextKey]

        return None

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

        _kind = self.itsKind

        if _kind is kind:
            return True

        if _kind is not None:
            return _kind.isKindOf(kind)

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
                    return self.itsView.walk(path, callable, 1, **kwds)

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
                otherName = self.itsKind.getOtherName(attrName, self)
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
                child = self.find(name, kwds.get('load', True))
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
                pass
            elif isinstance(name, UUID):
                child = item.itsView.find(name, load)
                if child is None or child.itsParent is not item:
                    item = None
                else:
                    item = child
            else:
                item = item.getItemChild(name, load)

            if item is None:
                break

        return item

    def find(self, spec, load=True, attribute=None):
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
                    L{UUID<chandlerdb.util.c.UUID>} 
        @param attribute: the attribute for the ref-collections to search
        @type attribute: a string
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

        if isinstance(spec, UUID):
            return self.itsView.find(spec, load)

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

        if isinstance(path, (str, unicode)):
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
        @type uuid: L{UUID<chandlerdb.util.c.UUID>} or a uuid string
        @param load: load the item if it not yet loaded, C{True} by default
        @type load: boolean
        @return: an item or C{None} if not found
        """

        if isinstance(uuid, (str, unicode)):
            uuid = UUID(uuid)
        elif not isinstance(uuid, UUID):
            raise TypeError, '%s is not UUID or string' %(type(uuid))

        return self.itsView.find(uuid, load)

    def unloadItem(self):
        
        return self._unloadItem(True, self.itsView, True)

    def _unloadItem(self, reloadable, view, clean=True):

        if clean and self.isDirty():
            raise ItemUnloadError, self

        if hasattr(type(self), 'onItemUnload'):
            self.onItemUnload(view, clean)

        if not self.isStale():

            if self._values:
                self._values._unload(clean)
            if self._references:
                self._references._unload(clean)

            if self._children is not None:
                self._children.clear()
                self._children = None

            view._unregisterItem(self, reloadable)
            self._status |= Item.STALE

            if not reloadable:
                self._parent = None
                self._kind = None
            
    def _refList(self, name, otherName=None, dictKey=None):

        if otherName is None:
            otherName = self.itsKind.getOtherName(name, self)

        return self.itsView._createRefList(self, name, otherName, dictKey,
                                           False, True, None)


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

            elif isitem(value):
                print indent2, "%s:" %(name), value._repr_()

            else:
                print indent2, "%s: <%s>" %(name, type(value).__name__), repr(value)

    def _inspectCollection(self, name, indent=0):

        collection = getattr(self, name)
        indexes = collection._indexes

        if indexes is None:
            return "\n%s%s%s" %('  ' * indent, self._repr_(),
                                collection._inspect_(indent + 1))
        else:
            indexes = ', '.join((str(t) for t in indexes.iteritems()))
            return "\n%s%s\n%sindexes: %s%s" %('  ' * indent, self._repr_(),
                                               '  ' * (indent + 1), indexes,
                                               collection._inspect_(indent + 1))


class MissingClass(Item):
    pass


class Watch(Item):
    
    parent = Path('//Schema/Core/items/watches')

    def __init__(self, watchingItem):

        view = watchingItem.itsView
        super(Watch, self).__init__(None,
                                    view.find(Watch.parent),
                                    view.find(type(self).kind))

        self.watchingItem = watchingItem


class WatchSet(Watch):

    kind = Path('//Schema/Core/WatchSet')

    def __init__(self, watchingItem, attribute):

        super(WatchSet, self).__init__(watchingItem)
        self.attribute = attribute
        
    def __call__(self, op, change, owner, name, other, dirties):
        
        set = getattr(self.watchingItem, self.attribute)
        set.sourceChanged(op, change, owner, name, False, other, dirties)

    def compare(self, attribute):

        return self.attribute == attribute


class WatchCollection(Watch):

    kind = Path('//Schema/Core/WatchCollection')

    def __init__(self, watchingItem, methodName):

        super(WatchCollection, self).__init__(watchingItem)
        self.methodName = methodName
        
    def __call__(self, op, change, owner, name, other, dirties):

        getattr(self.watchingItem,
                self.methodName)(op, owner, name, other, dirties)

    def compare(self, methodName):

        return self.methodName == methodName


class WatchKind(Watch):

    kind = Path('//Schema/Core/WatchKind')

    def __init__(self, watchingItem, methodName):

        super(WatchKind, self).__init__(watchingItem)
        self.methodName = methodName
        
    def __call__(self, op, change, owner, name, other, dirties):

        if isuuid(owner):
            kind = self.itsView[owner].kind
        else:
            kind = owner.kind

        getattr(self.watchingItem, self.methodName)(op, kind, other, dirties)

    def compare(self, methodName):

        return self.methodName == methodName


class WatchItem(Watch):

    kind = Path('//Schema/Core/WatchItem')

    def __init__(self, watchingItem, methodName):

        super(WatchItem, self).__init__(watchingItem)
        self.methodName = methodName
        
    def __call__(self, op, uItem, dirties):

        getattr(self.watchingItem, self.methodName)(op, uItem, dirties)

    def compare(self, methodName):

        return self.methodName == methodName
