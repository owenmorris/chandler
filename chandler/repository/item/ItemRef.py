
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import model.item.Item
from model.util.UUID import UUID
from model.util.Path import Path


class ItemRef(object):
    'A wrapper around a bi-directional link between two items.'
    
    def __init__(self, refDict, item, name, other, otherName,
                 otherCard=None, loading=False):

        super(ItemRef, self).__init__()
        self.attach(refDict, item, name, other, otherName, otherCard, loading)

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

        return self._other

    def attach(self, refDict, item, name, other, otherName,
               otherCard=None, loading=False):

        self._attach(item, name, other, otherName, otherCard, loading)
        if not loading:
            refDict._attach(self, item, name, other, otherName)

    def _attach(self, item, name, other, otherName, otherCard=None,
                loading=False):

        if item is None:
            raise ValueError, 'Originating endpoint is None'

        self._item = item
        self._other = other

        if other is not None:
            if other.hasAttribute(otherName):
                old = other.getAttribute(otherName)
                if isinstance(old, RefDict):
                    old.__setitem__(item.refName(otherName), self, loading)
                    if not loading:
                        old._attach(self, other, otherName, item, name)
                    return
            else:
                if otherCard is None:
                    otherCard = other.getAttrAspect(otherName, 'Cardinality',
                                                    'single')
                if otherCard == 'dict':
                    old = other._refDict(otherName, name)
                    other._references[otherName] = old
                    old.__setitem__(item.refName(otherName), self, loading)
                    if not loading:
                        old._attach(self, other, otherName, item, name)
                    return
                elif otherCard == 'list':
                    old = other._refDict(otherName, name, True)
                    other._references[otherName] = old
                    old.__setitem__(item.refName(otherName), self, loading)
                    if not loading:
                        old._attach(self, other, otherName, item, name)
                    return
            
            other.setAttribute(otherName, self, _attrDict=other._references)

    def detach(self, refDict, item, name, other, otherName):

        self._detach(item, name, other, otherName)
        refDict._detach(self, item, name, other, otherName)
        
    def _detach(self, item, name, other, otherName):

        if other is not None:
            old = other.getAttribute(otherName, _attrDict=other._references)
            if isinstance(old, RefDict):
                old._removeRef(item.refName(otherName))
            else:
                other._removeRef(otherName)

    def reattach(self, refDict, item, name, old, new, otherName,
                 loading=False):

        self.detach(item, refDict, name, old, otherName)
        self.attach(item, refDict, name, new, otherName, loading=loading)

    def other(self, item):
        'Return the other end of the ref relative to item.'

        if self.getItem() is item:
            return self.getOther()
        elif self.getOther() is item:
            return self.getItem()
        else:
            raise ValueError, "%s doesn't reference %s" %(self, item)

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
        if other is None:
            raise ValueError, "dangling ref at %s.%s" %(item.getPath(), name)

        attrs = { 'type': 'uuid' }

        if isinstance(name, UUID):
            attrs['nameType'] = "uuid"
            attrs['name'] = name.str64()
        elif not isinstance(name, str) and not isinstance(name, unicode):
            attrs['nameType'] = typeName(name)
            attrs['name'] = str(name)
        else:
            attrs['name'] = name

        if withSchema:
            otherName = item._otherName(name)
            attrs['otherName'] = otherName
            attrs['otherCard'] = other.getAttrAspect(otherName, 'Cardinality',
                                                     'single')

        generator.startElement('ref', attrs)
        generator.characters(other.getUUID().str64())
        generator.endElement('ref')


class RefArgs(object):
    'A wrapper around arguments necessary to make and store an ItemRef'
    
    def __init__(self, attrName, refName, other, otherName, otherCard,
                 valueDict):

        super(RefArgs, self).__init__()
        
        self.attrName = attrName
        self.refName = refName
        self.other = other
        self.otherName = otherName
        self.valueDict = valueDict
        self.otherCard = otherCard

    def attach(self, item, repository, loading=False):

        if isinstance(self.other, UUID):
            other = repository.find(self.other)
        else:
            other = item.find(self.other)
            
        if self.refName is None:
            if other is None:
                raise ValueError, "refName to %s is unspecified, %s should be loaded before %s" %(self.other, self.other, item.getPath())
            else:
                self.refName = other.refName(self.attrName)

        if other is not None:
            value = other._references.get(self.otherName)

            if value is None:
                ref = ItemRef(self.valueDict, item, self.attrName,
                              other, self.otherName, self.otherCard,
                              loading)
                self.valueDict.__setitem__(self.refName, ref, loading)

            elif isinstance(value, ItemRef):
                if value._other is None:
                    value._other = item
                    self.valueDict[self.refName] = value
                    if not loading:
                        self.valueDict._attach(value, other, self.otherName,
                                               item, self.attrName)

            elif isinstance(value, RefDict):
                otherRefName = item.refName(self.otherName)
                if value.has_key(otherRefName):
                    value = value._getRef(otherRefName)
                    if value._other is None:
                        value._other = item
                        self.valueDict.__setitem__(self.refName, value,
                                                   loading)
                        if not loading:
                            self.valueDict._attach(value, other,
                                                   self.otherName,
                                                   item, self.attrName)
                else:
                    ref = ItemRef(self.valueDict, item, self.attrName,
                                  other, self.otherName, self.otherCard,
                                  loading)
                    self.valueDict.__setitem__(self.refName, ref, loading)

        else:
            value = ItemRef(self.valueDict, item, self.attrName,
                            other, self.otherName, self.otherCard, loading)
            self.valueDict.__setitem__(self.refName, value, loading)
            repository._appendRef(item, self.attrName,
                                  self.other, self.otherName,
                                  self.otherCard, value, self.valueDict)
        

class Attributes(dict):

    def __init__(self, item):

        super(Attributes, self).__init__()
        self._setItem(item)

    def _setItem(self, item):

        self._item = item

    def _getItem(self):

        return self._item

    def __setitem__(self, key, value, loading=False):

        if not loading and self._item is not None:
            self._item.setDirty()

        super(Attributes, self).__setitem__(key, value)

    def __delitem__(self, key, loading=False):

        if not loading and self._item is not None:
            self._item.setDirty()

        super(Attributes, self).__delitem__(key)


class References(Attributes):

    def _setItem(self, item):

        for ref in self.itervalues():
            ref._setItem(item)

        self._item = item

    def _attach(self, itemRef, item, name, other, otherName):
        pass

    def _detach(self, itemRef, item, name, other, otherName):
        pass


class RefDict(References):

    def __init__(self, item, name, otherName, ordered=False):

        self._name = name
        self._otherName = otherName

        super(RefDict, self).__init__(item)

        if ordered:
            self._keyList = []
        else:
            self._keyList = None

    def _setItem(self, item):

        self._item = item

    def __repr__(self):

        return '<%s: %s.%s.%s>' %(type(self).__name__,
                                  self._getItem().getPath(),
                                  self._name, self._otherName)

    def __contains__(self, obj):

        if isinstance(obj, model.item.Item.Item):
            return super(RefDict, self).has_key(obj.refName(self._name))

        return super(RefDict, self).has_key(obj)

    def has_key(self, key):

        if self._keyList is not None and isinstance(key, int):
            return 0 <= key and key < len(self._keyList)

        return super(RefDict, self).has_key(key)

    def update(self, valueDict):

        for value in valueDict.iteritems():
            self[value[0]] = value[1]

    def extend(self, valueList):

        if self._keyList is not None:
            for value in valueList:
                self.append(value)
        else:
            raise NotImplementedError, 'RefDict was not created ordered'

    def append(sef, value):

        if self._keyList is not None:
            self[value.refName(self._name)] = value
        else:
            raise NotImplementedError, 'RefDict was not created ordered'

    def clear(self):

        for key in self.keys():
            del self[key]

    def dir(self):

        if self._keyList is not None:
            for key in self._keyList:
                print self[key]
        else:
            for item in self:
                print item

    def __getitem__(self, key):

        try:
            ref = super(RefDict, self).__getitem__(key)
        except KeyError:
            if self._keyList is not None and isinstance(key, int):
                ref = super(RefDict, self).__getitem__(self._keyList[key])
            else:
                raise
            
        return ref.other(self._getItem())

    def __setitem__(self, key, value, loading=False):

        if self._keyList is not None and isinstance(key, int):
            key = self._keyList[key]
            
        old = super(RefDict, self).get(key)
        
        if isinstance(old, ItemRef):
            item = self._getItem()
            if isinstance(value, ItemRef):
                old.detach(self, item, self._name,
                           old.other(item), self._otherName)
            else:
                old.reattach(self, item, self._name,
                             old.other(item), value, self._otherName,
                             loading)
                return

        if not isinstance(value, ItemRef):
            value = ItemRef(self, self._getItem(), self._name,
                            value, self._otherName, loading=loading)
            
        if self._keyList is not None and not super(RefDict, self).has_key(key):
            self._keyList.append(key)
            
        super(RefDict, self).__setitem__(key, value, loading)

    def __delitem__(self, key):

        if self._keyList is not None:
            if isinstance(key, int):
                key = self._keyList.pop(key)
            else:
                index = self._keyList.index(key)
                del self._keyList[index]
                
        value = self._getRef(key)
        item = self._getItem()
        value.detach(self, item, self._name,
                     value.other(item), self._otherName)
        self._removeRef(key)

    def _removeRef(self, key):

        if self._keyList is not None and isinstance(key, int):
            key = self._keyList.pop(key)

        super(RefDict, self).__delitem__(key)

    def _getRef(self, key):

        return super(RefDict, self).get(key)

    def get(self, key, default=None):

        value = super(RefDict, self).get(key, default)
        if value is not default:
            value = value.other(self._getItem())

        return value

    def __iter__(self):

        class keyIter(object):

            def __init__(self, refDict):

                super(keyIter, self).__init__()

                if refDict._keyList is not None:
                    self._iter = refDict._keyList.__iter__()
                else:
                    self._iter = refDict.iterkeys()
                    
                self._refDict = refDict

            def next(self):

                return self._refDict[self._iter.next()]

        return keyIter(self)

    def _refCount(self):

        return len(self)

    def _getCard(self):

        if self._keyList is None:
            return 'dict'
        else:
            return 'list'

    def _saveValue(self, name, item, generator, withSchema=False):

        if len(self) > 0:

            if withSchema:
                for other in self:
                    break

            attrs = { 'name': name }
            if withSchema:
                otherName = item._otherName(name)
                otherCard = other.getAttrAspect(otherName, 'Cardinality',
                                                'single')
                attrs['cardinality'] = self._getCard()
                attrs['otherName'] = otherName
                attrs['otherCard'] = otherCard

            generator.startElement('ref', attrs)
            self._saveValues(generator)
            generator.endElement('ref')

    def _saveValues(self, generator):

        raise NotImplementedError, 'RefDict._saveValues'

    def values(self):

        values = []
        for item in self:
            values.append(item)

        return values

    def _values(self):

        return super(RefDict, self).values()

    def itervalues(self):

        for value in self:
            yield value

    def _itervalues(self):

        return super(RefDict, self).itervalues()

    def iteritems(self):

        for key in self.iterkeys():
            yield (key, self[key])

    def _iteritems(self):

        return super(RefDict, self).iteritems()

    def copy(self):

        raise NotImplemented, 'RefDict.copy is not supported'

    def items(self):

        items = []
        for key in self.iterkeys():
            items.append((key, self[key]))

    def _items(self):

        return super(RefDict, self).items()
    
