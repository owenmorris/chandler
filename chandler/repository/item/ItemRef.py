
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import model.item.Item
from model.util.UUID import UUID
from model.util.Path import Path


class ItemRef(object):
    'A wrapper around a bi-directional link between two items.'
    
    def __init__(self, item, name, other, otherName, otherCard=None):

        super(ItemRef, self).__init__()
        self.attach(item, name, other, otherName, otherCard)

    def __repr__(self):

        return '<ItemRef: %s>' %(self._other)

    def _getItem(self):

        return self._item

    def _setItem(self, item):
        pass

    def getItem(self):
        'Return the item this link was established from.'
        
        return self._item

    def getOther(self):
        'Return the opposite item this link was established from.'

        other = self._other._loadItem()

        if other is not None:
            self._other = other
            return other

        raise DanglingRefError, '%s <-> %s' %(self._item, self._other)

    def attach(self, item, name, other, otherName, otherCard=None):

        assert item is not None, 'item is None'
        assert other is not None, 'other is None'

        self._item = item
        self._other = other

        if type(other) is not ItemStub:
            if other.hasAttributeValue(otherName):
                old = other.getAttributeValue(otherName)
                if isinstance(old, RefDict):
                    refName = item.refName(otherName)
                    old[refName] = self
                    return
            else:
                if otherCard is None:
                    otherCard = other.getAttributeAspect(otherName,
                                                         'cardinality',
                                                         'single')
                if otherCard == 'dict':
                    old = other._refDict(otherName, name)
                    other._references[otherName] = old
                    old[item.refName(otherName)] = self
                    return
                elif otherCard == 'list':
                    old = other._refDict(otherName, name, True)
                    other._references[otherName] = old
                    refName = item.refName(otherName)
                    old[refName] = self
                    return
            
            other.setAttributeValue(otherName, self,
                                    _attrDict=other._references)

    def detach(self, item, name, other, otherName):

        old = other.getAttributeValue(otherName, _attrDict=other._references)
        if isinstance(old, RefDict):
            old._removeRef(item.refName(otherName))
        else:
            other._removeRef(otherName)

    def reattach(self, item, name, old, new, otherName):

        self.detach(item, name, old, otherName)
        self.attach(item, name, new, otherName)

    def other(self, item):
        'Return the other end of the ref relative to item.'

        if self.getItem() is item:
            return self.getOther()
        elif self.getOther() is item:
            return self.getItem()
        else:
            raise ValueError, "%s doesn't reference %s" %(self, item)

    def _endpoints(self, item, name, other, otherName):

        if self._item is item:
            if self._other is other:
                return (item, name, other, otherName)
            return (item, name, None, otherName)
        elif self._other is item:
            if self._item is other:
                return (other, otherName, item, name)
            return (other, otherName, None, name)

        return (None, name, None, otherName)

    def _refCount(self):

        return 1

    def _saveValue(self, name, item, generator, withSchema=False):

        def typeName(value):
            
            if isinstance(value, UUID):
                return 'uuid'
            if isinstance(value, Path):
                return 'path'

            raise ValueError, "%s not supported here" %(type(value))

        other = self.other(item)
        attrs = { 'type': 'uuid' }

        if isinstance(name, UUID):
            attrs['nameType'] = "uuid"
            attrs['name'] = name.str64()
        elif isinstance(name, str) or isinstance(name, unicode):
            attrs['name'] = str(name)
        else:
            raise NotImplementedError, "refName: %s, type: %s" %(name,
                                                                 type(name))

        if withSchema:
            otherName = item._otherName(name)
            attrs['otherName'] = otherName
            attrs['otherCard'] = other.getAttributeAspect(otherName,
                                                          'cardinality',
                                                          'single')

        generator.startElement('ref', attrs)
        generator.characters(other.getUUID().str64())
        generator.endElement('ref')


class ItemStub(object):
    
    def __init__(self, item, args):

        super(ItemStub, self).__init__()

        self.item = item
        self.args = args

    def __repr__(self):

        return '<ItemStub: %s>' %(self.args.spec)

    def _loadItem(self):

        other = self.item.find(self.args.spec)
        if other is not None:
            self.args._attach(self.item, other)

        return other
    

class RefArgs(object):
    'A wrapper around arguments necessary to make and store an ItemRef'
    
    def __init__(self, attrName, refName, spec, otherName, otherCard,
                 valueDict, previous=None, next=None):

        super(RefArgs, self).__init__()
        
        self.attrName = attrName
        self.refName = refName
        self.spec = spec
        self.otherName = otherName
        self.otherCard = otherCard
        self.valueDict = valueDict
        self.previous = previous
        self.next = next
        self.ref = None
        
    def attach(self, item, repository):

        if isinstance(self.spec, UUID):
            other = repository.find(self.spec, load=False)
        else:
            other = item.find(self.spec, load=False)
            
        if self.refName is None:
            if other is None:
                raise ValueError, "refName to %s is unspecified, %s should be loaded before %s" %(self.spec, self.spec, item.getItemPath())
            else:
                self.refName = other.refName(self.attrName)

        if other is not None:
            self._attach(item, other)

        else:
            self.ref = ItemRef(item, self.attrName,
                               ItemStub(item, self), self.otherName,
                               self.otherCard)
            repository._addStub(self.ref)
            self.valueDict.__setitem__(self.refName, self.ref, 
                                       self.previous, self.next)

    def _attach(self, item, other):
        
        value = other._references.get(self.otherName)
        
        if value is None:
            if self.ref is not None:
                self.ref.attach(item, self.attrName,
                                other, self.otherName, self.otherCard)
            else:
                self.ref = ItemRef(item, self.attrName,
                                   other, self.otherName, self.otherCard)
                self.valueDict.__setitem__(self.refName, self.ref, 
                                           self.previous, self.next)

        elif isinstance(value, ItemRef):
            if isinstance(value._other, ItemStub):
                value._other = item
                self.valueDict.__setitem__(self.refName, value,
                                           self.previous, self.next)

        elif isinstance(value, RefDict):
            otherRefName = item.refName(self.otherName)
            if value.has_key(otherRefName):
                value = value._getRef(otherRefName)
                if isinstance(value._other, ItemStub):
                    value._other = item
                    self.valueDict.__setitem__(self.refName, value,
                                               self.previous, self.next)
            else:
                if self.ref is not None:
                    self.ref.attach(item, self.attrName,
                                    other, self.otherName, self.otherCard)
                else:
                    self.ref = ItemRef(item, self.attrName,
                                       other, self.otherName, self.otherCard)
                    self.valueDict.__setitem__(self.refName, self.ref,
                                               self.previous, self.next)

        else:
            raise ValueError, value


class Values(dict):

    def __init__(self, item):

        super(Values, self).__init__()
        self._setItem(item)

    def _setItem(self, item):

        self._item = item

    def _getItem(self):

        return self._item

    def __setitem__(self, key, value):

        if self._item is not None:
            self._item.setDirty()

        return super(Values, self).__setitem__(key, value)

    def __delitem__(self, key):

        if self._item is not None:
            self._item.setDirty()

        super(Values, self).__delitem__(key)


class References(Values):

    def _setItem(self, item):

        for ref in self.itervalues():
            ref._setItem(item)

        self._item = item

    def __setitem__(self, key, value, *args):

        return super(References, self).__setitem__(key, value)


class RefLink(object):

    def __init__(self, value):

        super(RefLink, self).__init__(self)
        self._value = value
        
    def _setNext(self, next, key, refDict):

        if next is None:
            refDict._last = key

        self._next = next
        refDict._changeRef(key)

    def _setPrevious(self, previous, key, refDict):

        if previous is None:
            refDict._first = key
                
        self._previous = previous
        refDict._changeRef(key)


class RefDict(References):

    def __init__(self, item, name, otherName, ordered=False):

        self._name = name
        self._otherName = otherName
        self._ordered = ordered

        if ordered:
            self._first = self._last = None
        
        super(RefDict, self).__init__(item)

    def _setItem(self, item):

        self._item = item

    def __repr__(self):

        return '<%s: %s.%s.%s>' %(type(self).__name__,
                                  self._getItem().getItemPath(),
                                  self._name, self._otherName)

    def __contains__(self, obj):

        if isinstance(obj, model.item.Item.Item):
            return self.has_key(obj.refName(self._name))

        return self.has_key(obj)

    def update(self, valueDict):

        for value in valueDict.iteritems():
            self[value[0]] = value[1]

    def extend(self, valueList):

        if self._ordered:
            for value in valueList:
                self.append(value)
        else:
            raise NotImplementedError, 'RefDict was not created ordered'

    def append(sef, value):

        if self._ordered:
            self.__setitem__(value.refName(self._name), value, self._last)
        else:
            raise NotImplementedError, 'RefDict was not created ordered'

    def clear(self):

        for key in self.keys():
            del self[key]

    def dir(self):

        for item in self:
            print item

    def __getitem__(self, key):

        ref = self._get(key)
        if type(ref) is RefLink:
            ref = ref._value
            
        return ref.other(self._getItem())

    def __setitem__(self, key, value, previous=None, next=None):

        self._changeRef(key)
        
        old = super(RefDict, self).get(key)
        if old is not None:

            if type(old) is RefLink:
                old = old._value

            item = self._getItem()
            if type(value) is ItemRef:
                old.detach(item, self._name,
                           old.other(item), self._otherName)
            else:
                old.reattach(item, self._name,
                             old.other(item), value, self._otherName)
                return old

        if type(value) is not ItemRef:
            value = ItemRef(self._getItem(), self._name,
                            value, self._otherName)

        if self._ordered:
            value = RefLink(value)

            if previous is None and next is None:
                previous = self._last
                if previous is not None and previous != key:
                    self._get(previous)._setNext(key, previous, self)

            if previous is None or previous != key:
                value._setPrevious(previous, key, self)
            if next is None or next != key:
                value._setNext(next, key, self)

        return super(RefDict, self).__setitem__(key, value)

    def place(self, item, after=None):
        """Place an item in this collection after another one.

        The reference collection must be created ordered, that is, the
        corresponding attribute must be of cardinality 'list'.
        Both items must already belong to the collection. To place an item
        first, omit 'after' or pass it None."""
        
        if not self._ordered:
            raise NotImplementedError, 'RefDict was not created ordered'

        key = item.refName(self._name)
        if self.has_key(key):
            current = self._get(key)
            if current._previous is not None:
                previous = self._get(current._previous)
            else:
                previous = None
            if current._next is not None:
                next = self._get(current._next)
            else:
                next = None
        else:
            raise ValueError, "This collection contains no reference to %s" %(item.getItemPath())

        if after is not None:
            afterKey = after.refName(self._name)
            if self.has_key(afterKey):
                after = self._get(afterKey)
                afterNextKey = after._next
            else:
                raise ValueError, "This collection contains no reference to %s" %(after.getItemPath())
        else:
            afterKey = None
            afterNextKey = self._first

        if key == afterKey:
            return

        if previous is not None:
            previous._setNext(current._next, current._previous, self)
        if next is not None:
            next._setPrevious(current._previous, current._next, self)

        current._setNext(afterNextKey, key, self)
        if afterNextKey is not None:
            self._get(afterNextKey)._setPrevious(key, afterNextKey, self)
        if after is not None:
            after._setNext(key, afterKey, self)

        current._setPrevious(afterKey, key, self)
            
    def __delitem__(self, key):

        self._removeRef(key, True)

    def _removeRef(self, key, _detach=False):

        value = self._get(key)

        if _detach:
            if type(value) is RefLink:
                ref = value._value
            else:
                ref = value
            ref.detach(self._item, self._name,
                       ref.other(self._item), self._otherName)

        if type(value) is RefLink:
            if value._previous is not None:
                self._get(value._previous)._setNext(value._next,
                                                    value._previous, self)
            else:
                self._first = value._next
            if value._next is not None:
                self._get(value._next)._setPrevious(value._previous,
                                                    value._next, self)
            else:
                self._last = value._previous
                
        super(RefDict, self).__delitem__(key)

    def _changeRef(self, key):

        self._item.setDirty()

    def _getRef(self, key):

        value = self._get(key)
        if type(value) is RefLink:
            return value._value

        return value

    def _get(self, key):

        return super(RefDict, self).__getitem__(key)

    def get(self, key, default=None):

        value = super(RefDict, self).get(key)

        if value is not default:
            if type(value) is RefLink:
                value = value._value
            return value.other(self._item)

        return default

    def first(self):
        """Return the first referenced item.

        Returns None if the collection is empty. The reference collection
        must be created ordered, that is, the corresponding attribute must
        be of cardinality 'list'."""

        if self._ordered:
            if self._first:
                return self[self._first]
            else:
                return None

        raise NotImplementedError, 'RefDict was not created ordered'

    def last(self):
        """Return the last referenced item.

        Returns None if the collection is empty. The reference collection
        must be created ordered, that is, the corresponding attribute must
        be of cardinality 'list'."""

        if self._ordered:
            if self._last:
                return self[self._last]
            else:
                return None

        raise NotImplementedError, 'RefDict was not created ordered'
        
    def next(self, previous):
        """Return the next referenced item relative to previous.

        Returns None if previous is the last referenced item in the
        collection. The reference collection must be created ordered, that
        is, the corresponding attribute must be of cardinality 'list'."""

        if self._ordered:
            next = self._get(previous.refName(self._name))._next
            if next:
                return self[next]
            else:
                return None

        raise NotImplementedError, 'RefDict was not created ordered'

    def previous(self, next):
        """Return the previous referenced item relative to next.

        Returns None if next is the first referenced item in the
        collection. The reference collection must be created ordered, that
        is, the corresponding attribute must be of cardinality 'list'."""

        if self._ordered:
            previous = self._get(next.refName(self._name))._previous
            if previous:
                return self[previous]
            else:
                return None

        raise NotImplementedError, 'RefDict was not created ordered'

    def _refCount(self):

        return len(self)

    def _getCard(self):

        if self._ordered:
            return 'list'
        else:
            return 'dict'

    def _saveValue(self, name, item, generator, withSchema=False):

        def addAttr(attrs, attr, key):

            if isinstance(key, UUID):
                attrs[attr + 'Type'] = 'uuid'
                attrs[attr] = key.str64()
            elif isinstance(key, str) or isinstance(key, unicode):
                attrs[attr] = str(name)
            else:
                raise NotImplementedError, "refName: %s, type: %s" %(key,
                                                                     type(key))

        if len(self) > 0:

            if withSchema:
                for other in self:
                    break

            attrs = { 'name': name }
            if withSchema:
                otherName = item._otherName(name)
                otherCard = other.getAttributeAspect(otherName, 'cardinality',
                                                     'single')
                attrs['cardinality'] = self._getCard()
                attrs['otherName'] = otherName
                attrs['otherCard'] = otherCard

            generator.startElement('ref', attrs)
            self._saveValues(generator)
            generator.endElement('ref')

    def _saveValues(self, generator):

        raise NotImplementedError, 'RefDict._saveValues'

    def iterkeys(self):

        if not self._ordered:
            return super(RefDict, self).iterkeys()

        class linkIter(object):

            def __init__(self, refDict):

                super(linkIter, self).__init__()

                self._current = refDict._first
                self._refDict = refDict

            def __iter__(self):

                return self

            def next(self):

                if self._current is None:
                    raise StopIteration

                key = self._current
                link = self._refDict._get(key)
                self._current = link._next

                return key

        return linkIter(self)

    def __iter__(self):

        class _iter(object):

            def __init__(self, iter, refDict):

                super(_iter, self).__init__()
                self.iter = iter
                self.refDict = refDict

            def next(self):

                return self.refDict[self.iter.next()]

        return _iter(self.iterkeys(), self)

    def values(self):

        values = []
        for item in self:
            values.append(item)

        return values

    def _values(self):

        values = []
        for key in self.iterkeys():
            values.append(self._get(key))

        return values

    def itervalues(self):

        for value in self:
            yield value

    def _itervalues(self):

        for key in self.iterkeys():
            yield self._get(key)

    def iteritems(self):

        for key in self.iterkeys():
            yield (key, self[key])

    def _iteritems(self):

        for key in self.iterkeys():
            yield (key, self._get(key))

    def copy(self):

        raise NotImplementedError, 'RefDict.copy is not supported'

    def items(self):

        items = []
        for key in self.iterkeys():
            items.append((key, self[key]))

    def _items(self):

        items = []
        for key in self.iterkeys():
            items.append((key, self._get(key)))


class DanglingRefError(ValueError):
    pass
