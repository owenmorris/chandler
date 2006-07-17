#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


from chandlerdb.util.c import \
    UUID, SingleRef, _hash, _combine, isuuid, issingleref
from chandlerdb.schema.c import _countAccess
from chandlerdb.item.c import CItem, Nil, Default, isitem
from chandlerdb.item.ItemValue import ItemValue
from chandlerdb.item.ItemError import *

from repository.item.RefCollections import RefList, RefDict
from repository.item.Values import Values, References
from repository.item.Access import ACL
from repository.item.PersistentCollections import \
     PersistentCollection, PersistentList, PersistentDict, \
     PersistentTuple, PersistentSet

from repository.util.Path import Path
from repository.util.LinkedMap import LinkedMap


class Item(CItem):
    """
    The root class for all items.
    """

    def __init__(self, itsName=None, itsParent=None, itsKind=None,
                 _uuid=None, _noMonitors=False, fireOnValueChanged=True,
                 **values):
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
        if self._uuid is not None:
            return

        super(Item, self).__init__()

        cls = type(self)
        self._values = Values(self)
        self._references = References(self)
        self._uuid = _uuid or UUID()
        self._name = itsName or None
        self._kind = itsKind
        self._version = 0L

        if itsKind is not None:
            itsKind._setupClass(cls)

        if itsParent is None:
            raise ValueError, 'parent cannot be None, for roots use a view'

        if itsName is None and not isitem(itsParent):
            raise AnonymousRootError, self

        self._setParent(itsParent)

        try:
            if itsKind is not None:
                self.setDirty(Item.NDIRTY | Item.KDIRTY | Item.NODIRTY)
                itsKind.getInitialValues(self, True)
            else:
                self.setDirty(Item.NDIRTY | Item.NODIRTY)

            if values:
                self._setInitialValues(values, fireOnValueChanged)
        finally:
            self._status &= ~Item.NODIRTY

        if not (_noMonitors or (itsKind is None)):
            self.itsView._notifyChange(itsKind.extent._collectionChanged,
                                       'add', 'collection', 'extent',
                                       self.itsUUID)

    def _setInitialValues(self, values, fireOnValueChanged):

        for name, value in values.iteritems():
            setattr(self, name, value)

        if fireOnValueChanged:
            onValueChanged = getattr(self, 'onValueChanged', None)
            if onValueChanged is not None:
                for name in values.iterkeys():
                    onValueChanged(name)

    def __iter__(self):
        """
        (deprecated) Use L{iterChildren} instead.
        """

        raise DeprecationWarning, 'Use Item.iterChildren() instead'

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

    def _redirectTo(self, redirect, methodName, *args):
        
        item = self
        names = redirect.split('.')
        for i in xrange(len(names) - 1):
            item = getattr(item, names[i])

        return getattr(item, methodName)(names[-1], *args)
        
    def setAttributeValue(self, name, value=None, _attrDict=None,
                          otherName=None, setDirty=True, _noMonitors=False):
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
                redirect = self.getAttributeAspect(name, 'redirectTo',
                                                   False, None, None)
                if redirect is not None:
                    return self._redirectTo(redirect, 'setAttributeValue',
                                            value, None, None,
                                            setDirty, _noMonitors)

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
                if old is not None:
                    if isItem and isuuid(old):
                        if old == value.itsUUID:
                            return value
                    elif old._isRefs():
                        wasRefs = True
                        old._removeRefs()

        if isItem or value is None:
            if _attrDict is _values:
                if isItem:
                    _values[name] = value = SingleRef(value.itsUUID)
                else:
                    _values[name] = None
                dirty = Item.VDIRTY
            else:
                if otherName is None:
                    otherName = self.itsKind.getOtherName(name, self)
                _references._setValue(name, value, otherName, _noMonitors)
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
                if old is None:
                    _references[name] = refList = self._refList(name)
                else:
                    if not wasRefs:
                        raise CardinalityError, (self, name, 'multi-valued')
                    refList = old

                refList.extend(value, _noMonitors)
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

                refDict.update(value, _noMonitors)
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

                refList.extend(value, _noMonitors)
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

                refList.extend(value, _noMonitors)
                value = refList
                setDirty = False
            else:
                attrValue = PersistentSet(self, name, value, False)
                _values[name] = attrValue
                dirty = Item.VDIRTY

        if setDirty:
            self.setDirty(dirty, name, _attrDict, _noMonitors)
        
        return value

    def setFreeValue(self, name, item):

        self.setValue('freeValues', item, name, None, name)

    def addFreeValue(self, name, item):

        self.addValue('freeValues', item, name, None, name)

    def getFreeValue(self, name, default=Nil):

        return self.getValue('freeValues', name, None, default)

    def removeFreeValue(self, name, item=None):

        self.removeValue('freeValues', item, name)

    def _reIndex(self, op, item, attrName, collectionName, indexName):

        if op in ('set', 'remove'):
            collection = getattr(self, collectionName, None)
            if collection is not None and collection.__contains__(item, True):
                collection.placeInIndex(item, None, indexName)

    def _filteredItemChanged(self, op, item, attribute, name):

        if not (item.isDeleting() or self._isNoDirty()):
            getattr(self, name).itemChanged(item.itsUUID, attribute)

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
        @return: a value
        """

        if self.isStale():
            raise StaleItemError, self

        _countAccess(self)

        if (_attrDict is self._values or
            _attrDict is None and name in self._values):
            value = self._values.get(name, Nil)
            if value is not Nil:
                if issingleref(value):
                    item = self.itsView.find(value.itsUUID)
                    if item is not None:
                        return item
                return value

        elif (_attrDict is self._references or
              _attrDict is None and name in self._references):
            value = self._references._getRef(name, None, None, Nil)
            if value is not Nil:
                return value

        if self.itsKind is not None:
            if _attrID is not None:
                attribute = self.itsView[_attrID]
            else:
                attribute = self.itsKind.getAttribute(name, False, self)

            redirect = attribute.c.getAspect('redirectTo', None)
            if redirect is not None:
                value = self
                for attr in redirect.split('.'):
                    value = value.getAttributeValue(attr, None, None, default)
                    if value is default:
                        break
                return value

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

            if default is not Default:
                return default

            value = attribute.c.getAspect('defaultValue', Nil)
            if value is not Nil:
                if isinstance(value, PersistentCollection):
                    value.setReadOnly(True)
                return value

            raise NoValueForAttributeError, (self, name)

        elif default is not Default:
            return default

        raise NoValueForAttributeError, (self, name)

    def removeAttributeValue(self, name, _attrDict=None, _attrID=None,
                             _noMonitors=False):
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
            else:
                redirect = self.getAttributeAspect(name, 'redirectTo',
                                                   False, _attrID, None)
                if redirect is not None:
                    return self._redirectTo(redirect, 'removeAttributeValue',
                                            None, None, _noMonitors)

                if hasattr(self, name): # inherited value
                    return

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

        if not _noMonitors:
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

        if not load:
            if self._children is not None:
                for link in self._children._itervalues():
                    yield link.value

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
            for name, value in self._values._dict.iteritems():
                if issingleref(value):
                    item = self.itsView.find(value.itsUUID)
                    if item is not None:
                        value = item
                yield name, value

        if not valuesOnly:
            for name, ref in self._references._dict.iteritems():
                if ref is not None and isuuid(ref):
                    ref = self._references._getRef(name, ref)
                yield name, ref

    def iterAttributeNames(self, valuesOnly=False, referencesOnly=False):
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
            for name in self._values._dict.iterkeys():
                yield name

        if not valuesOnly:
            for name in self._references._dict.iterkeys():
                yield name

    def check(self, recursive=False, checkItem=True):
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

        logger = self.itsView.logger

        checkValues = self._values.check()
        checkRefs = self._references.check()
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
                
            for name, desc in kind._getDescriptors(type(self)).iteritems():
                attrDict, required = desc.isValueRequired(self)
                if attrDict is not None:
                    if required and name not in attrDict:
                        logger.error("Required value for attribute %s on %s is missing", name, self._repr_())
                        result = False
        
        if self._children is not None:
            l = len(self._children)
            for child in self.iterChildren():
                l -= 1
                if recursive:
                    check = child.check(True)
                    result = result and check
                if l == 0:
                    break
            if l != 0:
                logger.error("Iterator on children of %s doesn't match length (%d left for %d total)", self._repr_(), l, len(self._children))
                return False

        if result and checkItem:
            result = self.checkItem()

        return result

    def checkItem(self):
        """
        A placeholder for subclasses to do more checking.

        This method is meant to be used by developers to do implement checks
        that the repository cannot do on its own such as semantic
        constraints checking.

        Failure should be logged, exceptions should not be raised.

        @return: C{True} if all checks pass, C{False} otherwise
        """
        return True

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
                redirect = self.getAttributeAspect(attribute, 'redirectTo',
                                                   False, None, None)
                if redirect is not None:
                    return self._redirectTo(redirect, 'setValue',
                                            value, key, alias, otherKey)

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
                redirect = self.getAttributeAspect(attribute, 'redirectTo',
                                                   False, None, None)
                if redirect is not None:
                    return self._redirectTo(redirect, 'addValue',
                                            value, key, alias, otherKey)

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
            else:
                redirect = self.getAttributeAspect(attribute, 'redirectTo',
                                                   False, None, None)
                if redirect is not None:
                    return self._redirectTo(redirect, 'removeValue',
                                            value, key, alias)

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

    def _collectItems(self, items, filter=None):

        def collectItems(item):
            parent = item.itsParent
            if isitem(parent) and not parent in items:
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
                    
                for key, value in _item._references._dict.items():
                    if value is not None:
                        if value._isRefs():
                            for other in value:
                                collectOther(other)
                        else:
                            if isuuid(value):
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
        L{SingleRef<chandlerdb.util.c.SingleRef>} values.

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
        item._fillItem(name, parent, kind, UUID(),
                       Values(item), References(item), 0, 0,
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
                               'add', 'collection', 'extent', item.itsUUID)
        if hasattr(cls, 'onItemCopy'):
            item.onItemCopy(view, self)

        return item

    def clone(self, name=None, parent=None,
              exclude=(), fireOnValueChanged=True, **values):

        cls = type(self)
        item = cls.__new__(cls)
        kind = self._kind
        if kind is not None:
            kind._setupClass(cls)

        if parent is None:
            parent = self.itsParent
        hooks = []
        item._fillItem(name, parent, kind, UUID(),
                       Values(item), References(item), 0, 0,
                       hooks, False)

        try:
            item._status |= Item.NODIRTY
            item._values._clone(self._values, exclude)
            item._references._clone(self._references, exclude)

            if values:
                item._setInitialValues(values, fireOnValueChanged)
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
                               'add', 'collection', 'extent', item.itsUUID)
        if hasattr(cls, 'onItemClone'):
            item.onItemClone(view, self)

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

        elif not self._status & (Item.DELETED | Item.DELETING | Item.DEFERRING):

            if self.isStale():
                raise StaleItemError, self

            if not recursive and self.hasChildren():
                raise RecursiveDeleteError, self

            view = self.itsView

            if view.isDeferringDelete():
                self._status |= Item.DEFERRING

                if hasattr(type(self), 'onItemDelete'):
                    self.onItemDelete(view, True)

                for child in self.iterChildren():
                    child.delete(True, deletePolicy)

                if not self.isDeferred():
                    self._status |= Item.DEFERRED
                    self.setDirty(Item.NDIRTY)
                else:
                    for tuple in view._deferredDeletes:
                        if tuple[0] is self:
                            view._deferredDeletes.remove(tuple)
                            break

                view._deferredDeletes.append((self, deletePolicy))
                self._status &= ~Item.DEFERRING
            
            else:
                refs = self._references
                values = self._values
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
                        watch.delete(True, None, None, True)
                view._unregisterWatches(self)

                if 'monitors' in refs:
                    for monitor in self.monitors:
                        monitor.delete(True, None, None, True)

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
                        other.delete(recursive, deletePolicy)

                self._setKind(None, _noMonitors)

                self.itsParent._removeItem(self)
                self._setRoot(None, view)

                self._status |= Item.DELETED | Item.STALE
                self._status &= ~(Item.DELETING | Item.DEFERRED)

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

    def getItemDisplayName(self):
        """
        Return this item's display name.

        By definition, the display name is, in order of precedence:
            - the value of the C{displayName} attribute
            - the value of the attribute named by the item's kind
              C{displayAttribute} attribute
            - the item's intrinsic name
            - the item's base64 encoded UUID surrounded by {}

        @return: a unicode
        """

        if 'displayName' in self._values:
            return self.displayName

        if self._kind is not None:
            if 'displayAttribute' in self._kind._values:
                displayAttribute = self._kind.displayAttribute
                if self.hasLocalAttributeValue(displayAttribute):
                    return unicode(self.getAttributeValue(displayAttribute))

        return unicode(self._name or '{%s}' % (self._uuid.str64()))

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

    def _refCount(self):

        count = 0

        if not self.isStale():
            count += self._values._refCount()
            count += self._references._refCount()
            if self._children is not None:
                count += self._children._refCount()
            if not self._parent.isStale():
                count += 1  #parent

        return count

    def _getPath(self, path=None):

        if path is None:
            path = Path()
            
        self.itsParent._getPath(path)
        path.append(self.itsName or self.itsUUID)

        return path

    def _setRoot(self, root, oldView):

        if root is not self._root:
            if root is None:
                newView = None
            else:
                newView = root._parent

            if oldView is not newView:
                if oldView is not None and newView is not None:
                    raise NotImplementedError, 'changing views'

                if oldView is not None:
                    oldView._unregisterItem(self, False)

                if newView is not None:
                    newView._registerItem(self)

            self._root = root

            for child in self.iterChildren(False):
                child._setRoot(root, oldView)

        elif root is not None:
            root.itsView._registerItem(self)

    def _setKind(self, kind, _noMonitors=False):

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
                                   self.itsUUID, kind)

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
                                   'add', 'collection', 'extent', self.itsUUID,
                                   prevKind)
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
            acl = self.itsView.getACL(self._uuid, name, default)

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
            oldView = parent.itsView
            parent._removeItem(self)
            self._setParent(newParent, oldView)
            self.setDirty(Item.NDIRTY)

    def _setParent(self, parent, oldView=None):

        if parent is not None:
            if self._parent is not parent:
                if parent._isRepository():
                    parent = parent.view
                self._parent = parent
                self._setRoot(parent._addItem(self), oldView)
            elif parent._isView():
                self._setRoot(self, oldView)
            else:
                self._setRoot(parent.itsRoot, oldView)
        else:
            self._parent = None

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

        return self.itsRoot

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

    def _unloadItem(self, reloadable, view, clean=True):

        if self.isDirty():
            raise DirtyItemError, self

        if hasattr(type(self), 'onItemUnload'):
            self.onItemUnload(view, clean)

        if not self.isStale():

            if self._values:
                self._values._unload(clean)
            if self._references:
                self._references._unload(clean)

            self._parent._unloadChild(self)
            if self._children is not None:
                self._children.clear()
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

    def _refList(self, name, otherName=None, dictKey=None, persisted=None):

        if otherName is None:
            otherName = self.itsKind.getOtherName(name, self)
        if persisted is None:
            persisted = self.getAttributeAspect(name, 'persisted',
                                                False, None, True)

        return self.itsView._createRefList(self, name, otherName, dictKey,
                                           persisted, False, True, None)


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
            indexes = ''
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
        
    def __call__(self, op, change, owner, name, other):
        
        set = getattr(self.watchingItem, self.attribute);
        set.sourceChanged(op, change, owner, name, False, other)

    def compare(self, attribute):

        return self.attribute == attribute


class WatchCollection(Watch):

    kind = Path('//Schema/Core/WatchCollection')

    def __init__(self, watchingItem, methodName):

        super(WatchCollection, self).__init__(watchingItem)
        self.methodName = methodName
        
    def __call__(self, op, change, owner, name, other):

        getattr(self.watchingItem, self.methodName)(op, owner, name, other)

    def compare(self, methodName):

        return self.methodName == methodName


class WatchKind(Watch):

    kind = Path('//Schema/Core/WatchKind')

    def __init__(self, watchingItem, methodName):

        super(WatchKind, self).__init__(watchingItem)
        self.methodName = methodName
        
    def __call__(self, op, change, owner, name, other):

        if isuuid(owner):
            kind = self.itsView[owner].kind
        else:
            kind = owner.kind

        getattr(self.watchingItem, self.methodName)(op, kind, other)

    def compare(self, methodName):

        return self.methodName == methodName


class WatchItem(Watch):

    kind = Path('//Schema/Core/WatchItem')

    def __init__(self, watchingItem, methodName):

        super(WatchItem, self).__init__(watchingItem)
        self.methodName = methodName
        
    def __call__(self, op, uItem, names):

        getattr(self.watchingItem, self.methodName)(op, uItem, names)

    def compare(self, methodName):

        return self.methodName == methodName
