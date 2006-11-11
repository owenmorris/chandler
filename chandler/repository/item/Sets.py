#   Copyright (c) 2005-2006 Open Source Applications Foundation
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


from itertools import izip

from chandlerdb.util.c import UUID, isuuid, Nil
from chandlerdb.item.c import CItem
from chandlerdb.persistence.c import CView
from chandlerdb.item.ItemValue import ItemValue
from repository.item.Monitors import Monitors
from repository.item.Indexed import Indexed
from repository.item.Collection import Collection

class AbstractSet(ItemValue, Indexed):

    def __init__(self, view, id):

        super(AbstractSet, self).__init__()
        self._init_indexed()

        self._view = view
        self._otherName = None
        self.id = id

    def __contains__(self, item, excludeMutating=False, excludeIndexes=False):
        raise NotImplementedError, "%s.__contains__" %(type(self))

    def sourceChanged(self, op, change, sourceOwner, sourceName, inner, other,
                      source=None):
        raise NotImplementedError, "%s.sourceChanged" %(type(self))

    def __repr__(self):
        return self._repr_()

    def __getitem__(self, uuid):

        return self._view[uuid]

    def __eq__(self, value):

        if self is value:
            return True

        return (type(value) is type(self) and
                list(value.iterSources()) == list(self.iterSources()))

    def __ne__(self, value):

        if self is value:
            return False

        return not (type(value) is type(self) and
                    list(value.iterSources()) == list(self.iterSources()))

    def __nonzero__(self):

        index = self._anIndex()
        if index is not None:
            return len(index) > 0

        for i in self.iterkeys():
            return True

        return False

    def isEmpty(self):

        return not self

    def __iter__(self, excludeIndexes=False):

        if not excludeIndexes:
            index = self._anIndex()
            if index is not None:
                view = self._view
                return (view[key] for key in index)

        return self._itervalues(excludeIndexes)

    def itervalues(self, excludeIndexes=False):

        return self.__iter__(excludeIndexes)

    def _itervalues(self, excludeIndexes=False):

        raise NotImplementedError, "%s._itervalues" %(type(self))

    def iterkeys(self, excludeIndexes=False):

        if not excludeIndexes:
            index = self._anIndex()
            if index is not None:
                return index.iterkeys()

        return self._iterkeys(excludeIndexes)

    # the slow way, via items, to be overridden by some implementations
    def _iterkeys(self, excludeIndexes=False):

        return (item.itsUUID for item in self.__iter__(excludeIndexes))

    def iterItems(self):

        return self.itervalues()

    def iterKeys(self):

        return self.iterkeys()

    def __len__(self):

        index = self._anIndex()
        if index is not None:
            return len(index)

        return self.countKeys()

    def countKeys(self):

        count = 0
        for key in self.iterkeys(True):
            count += 1

        return count

    def findSource(self, id):

        raise NotImplementedError, "%s.findSource" %(type(self))

    def _findSource(self, source, id):

        if isinstance(source, AbstractSet):
            if source.id == id:
                return source

        elif source[0] == id:
            return source

        return None

    def iterSources(self):

        raise NotImplementedError, "%s.iterSources" %(type(self))

    def iterInnerSets(self):

        raise NotImplementedError, "%s.iterInnerSets" %(type(self))

    def _iterSourceItems(self):

        for item, attribute in self.iterSources():
            yield item

    def _iterSources(self, source):

        if isinstance(source, AbstractSet):
            for source in source.iterSources():
                yield source
        else:
            yield (self._view[source[0]], source[1])

    def _inspect__(self, indent):

        return "\n%s<%s>" %('  ' * indent, type(self).__name__)

    def dir(self):
        """
        Debugging: print all items referenced in this set
        """
        for item in self:
            print item._repr_()

    def _getView(self):

        return self._view

    def _setView(self, view):

        self._view = view

    def _prepareSource(self, source):
        
        if isinstance(source, AbstractSet):
            return source._view, source
        elif isinstance(source, Collection):
            return source.getSourceCollection()
        elif isuuid(source[0]):
            return None, source
        else:
            return source[0].itsView, (source[0].itsUUID, source[1])

    def _sourceContains(self, item, source,
                        excludeMutating=False, excludeIndexes=False):

        if item is None:
            return False

        if not isinstance(source, AbstractSet):
            source = getattr(self._view[source[0]], source[1])

        return source.__contains__(item, excludeMutating, excludeIndexes)

    def _getSource(self, source):

        if isinstance(source, AbstractSet):
            return source
        
        return getattr(self._view[source[0]], source[1])

    def _inspectSource(self, source, indent):

        if isinstance(source, AbstractSet):
            return source._inspect_(indent)
        
        return self._view[source[0]]._inspectCollection(source[1], indent)

    def _aSourceIndex(self, source):

        if isinstance(source, AbstractSet):
            return source._anIndex()

        return getattr(self._view[source[0]], source[1])._anIndex()

    def _iterSource(self, source, excludeIndexes=False):

        if isinstance(source, AbstractSet):
            for item in source.__iter__(excludeIndexes):
                yield item
        else:
            for item in getattr(self._view[source[0]],
                                source[1]).__iter__(excludeIndexes):
                yield item

    def _iterSourceKeys(self, source, excludeIndexes=False):

        if isinstance(source, AbstractSet):
            return source.iterkeys(excludeIndexes)

        return getattr(self._view[source[0]],
                       source[1]).iterkeys(excludeIndexes)

    def _sourceLen(self, source):

        if isinstance(source, AbstractSet):
            return len(source)

        return len(getattr(self._view[source[0]], source[1]))

    def _reprSource(self, source, replace):

        if isinstance(source, AbstractSet):
            return source._repr_(replace)
        
        if replace is not None:
            replaceItem = replace[source[0]]
            if replaceItem is not Nil:
                source = (replaceItem.itsUUID, source[1])

        return "(UUID('%s'), '%s')" %(source[0].str64(), source[1])

    def _reprSourceId(self, replace):

        id = self.id
        if id is not None:
            if replace is not None:
                replaceItem = replace[id]
                if replaceItem is not Nil:
                    id = replaceItem.itsUUID
            return ", id=UUID('%s')" %(id.str64())

        return ''

    def _setSourceItem(self, source, item, attribute, oldItem, oldAttribute):
        
        if isinstance(source, AbstractSet):
            source._setOwner(item, attribute)

        elif item is not oldItem:
            view = self._view
            if not view.isLoading():
                if item is None:
                    sourceItem = view.findUUID(source[0])
                    if sourceItem is not None: # was deleted
                        oldItem._unwatchSet(sourceItem, source[1], oldAttribute)
                else:
                    item._watchSet(view[source[0]], source[1], attribute)

    def _setSourceView(self, source, view):

        if isinstance(source, AbstractSet):
            source._setView(view)

    def _sourceChanged(self, source, op, change,
                       sourceOwner, sourceName, other, actualSource):

        if isinstance(source, AbstractSet):
            if actualSource is not None:
                if source is not actualSource:
                    op = None
            else:
                op = source.sourceChanged(op, change, sourceOwner, sourceName,
                                          True, other)

        elif (sourceName == source[1] and
              (isuuid(sourceOwner) and sourceOwner == source[0] or
               sourceOwner is self._view[source[0]])):
            pass
        else:
            op = None

        if op == 'refresh':
            index = self._anIndex()
            if index is not None:
                sourceContains = self._sourceContains(other, source)
                indexContains = other.itsUUID in index

                if sourceContains and not indexContains:
                    op = 'add'
                elif not sourceContains and indexContains:
                    op = 'remove'

        return op

    def _collectionChanged(self, op, change, other, local=False):

        item = self._item
        attribute = self._attribute

        if item is not None:
            if change == 'collection':
                if op in ('add', 'remove'):
                    if not (local or self._otherName is None):
                        otherItem = self._view.find(other)
                        if otherItem is not None:
                            refs = otherItem._references
                            if op == 'add':
                                refs._addRef(self._otherName, item, attribute, True)
                            else:
                                refs._removeRef(self._otherName, item, None, True)
                        elif op == 'add':
                            raise AssertionError, ("op == 'add' but item not found", other)

                    if self._indexes:
                        dirty = False

                        if op == 'add':
                            for index in self._indexes.itervalues():
                                if other not in index:
                                    index.insertKey(other, index.getLastKey())
                                    dirty = True
                        else:
                            for index in self._indexes.itervalues():
                                if index.removeKey(other):
                                    dirty = True

                        if dirty:
                            self._setDirty(True)

                elif op == 'refresh':
                    pass

                else:
                    raise ValueError, op

            item._collectionChanged(op, change, attribute, other)

    def removeByIndex(self, indexName, position):

        raise TypeError, "%s contents are computed" %(type(self))

    def insertByIndex(self, indexName, position, item):

        raise TypeError, "%s contents are computed" %(type(self))

    def replaceByIndex(self, indexName, position, with):

        raise TypeError, "%s contents are computed" %(type(self))

    def _copy(self, item, attribute, copyPolicy, copyFn):

        # in the bi-ref case, set owner and value on item as needed
        # in non bi-ref case, Values sets owner and value on item

        otherName = self._otherName

        if otherName is not None:
            copy = item._references.get(attribute, Nil)
            if copy is not Nil:
                return copy

        policy = (copyPolicy or
                  item.getAttributeAspect(attribute, 'copyPolicy',
                                          False, None, 'copy'))

        replace = {}
        for sourceItem in self._iterSourceItems():
            if copyFn is not None:
                replace[sourceItem.itsUUID] = copyFn(item, sourceItem, policy)
            else:
                replace[sourceItem.itsUUID] = sourceItem

        copy = eval(self._repr_(replace))
        copy._setView(item.itsView)

        if otherName is not None:
            item._references[attribute] = copy
            copy._setOwner(item, attribute)

        return copy

    def _clone(self, item, attribute):

        clone = eval(self._repr_())
        clone._setView(item.itsView)

        return clone

    def copy(self, id=None):

        copy = eval(self._repr_())
        copy._setView(self._view)
        copy.id = id or self.id
        
        return copy

    def _check(self, logger, item, attribute, repair):

        return (super(AbstractSet, self)._check(logger, item, attribute,
                                                repair) and
                self._checkIndexes(logger, item, attribute, repair))

    def _setDirty(self, noMonitors=False):

        self._dirty = True
        item = self._item
        if item is not None:
            try:
                view = item.itsView
                verify = view._status & CView.VERIFY
                if verify:
                    view._status &= ~CView.VERIFY
                    
                if self._otherName is None:
                    item.setDirty(item.VDIRTY, self._attribute,
                                  item._values, noMonitors)
                else:
                    item.setDirty(item.RDIRTY, self._attribute,
                                  item._references, noMonitors)
            finally:
                if verify:
                    view._status |= CView.VERIFY

    @classmethod
    def makeValue(cls, string):
        return eval(string)

    @classmethod
    def makeString(cls, value):
        return value._repr_()

    def _setOwner(self, item, attribute):

        if item is None:
            self._removeIndexes()

        result = super(AbstractSet, self)._setOwner(item, attribute)

        if item is None:
            self._otherName = None
        else:
            self._otherName = item.itsKind.getOtherName(attribute, item, None)

        return result

    # refs part

    def _isRefs(self):
        return True
    
    def _isList(self):
        return False
    
    def _isSet(self):
        return True
    
    def _isDict(self):
        return False
    
    def _isItem(self):
        return False
    
    def _isUUID(self):
        return False

    def _setRef(self, other, alias=None, dictKey=None, otherKey=None,
                ignore=False):

        self._item.add(other)
        self._view._notifyChange(self._collectionChanged,
                                 'add', 'collection', other.itsUUID,
                                 True)

    def _removeRef(self, other, dictKey=None, noError=False):

        if not noError or other in self:
            self._item.remove(other)
            self._view._notifyChange(self._collectionChanged,
                                     'remove', 'collection', other.itsUUID,
                                     True)

    def _removeRefs(self):
        
        if self._otherName is not None:
            for item in self:
                item._references._removeRef(self._otherName, self._item)

    def _fillRefs(self):

        if self._otherName is not None:
            for item in self:
                item._references._setRef(self._otherName, self._item,
                                         self._attribute)

    def _unloadRef(self, other, dictKey=None):
        pass

    def _unloadRefs(self):
        pass

    def _clearDirties(self):
        self._clearIndexDirties()

    def clear(self):
        self._removeRefs()


class EmptySet(AbstractSet):

    def __init__(self, id=None):

        super(EmptySet, self).__init__(None, id)

    def _setOwner(self, item, attribute):

        result = super(EmptySet, self)._setOwner(item, attribute)
        if item is None:
            self._view = None
        else:
            self._view = item.itsView

        return result

    def __contains__(self, item, excludeMutating=False, excludeIndexes=False):

        return False

    def _itervalues(self, excludeIndexes=False):

        return iter(())

    def _iterkeys(self, excludeIndexes=False):

        return iter(())

    def countKeys(self):

        return 0

    def _reprSourceId(self, replace):

        id = self.id
        if id is not None:
            if replace is not None:
                replaceItem = replace[id]
                if replaceItem is not Nil:
                    id = replaceItem.itsUUID
            return "id=UUID('%s')" %(id.str64())

        return ''

    def _repr_(self, replace=None):

        return "%s(%s)" %(type(self).__name__, self._reprSourceId(replace))
        
    def sourceChanged(self, op, change, sourceOwner, sourceName, inner, other,
                      source=None):

        return None

    def findSource(self, id):

        return None

    def iterSources(self):

        return iter(())

    def iterInnerSets(self):

        return iter(())

    def _inspect_(self, indent):

        return '%s' %(self._inspect__(indent))


class Set(AbstractSet):

    def __init__(self, source, id=None):

        view, self._source = self._prepareSource(source)
        super(Set, self).__init__(view, id)

    def __contains__(self, item, excludeMutating=False, excludeIndexes=False):

        if item is None:
            return False

        if not excludeIndexes:
            index = self._anIndex()
            if index is not None:
                return item.itsUUID in index

        return self._sourceContains(item, self._source,
                                    excludeMutating, excludeIndexes)

    def _itervalues(self, excludeIndexes=False):

        return self._iterSource(self._source, excludeIndexes)

    def _iterkeys(self, excludeIndexes=False):

        return self._iterSourceKeys(self._source, excludeIndexes)

    def countKeys(self):

        return self._sourceLen(self._source)

    def _repr_(self, replace=None):

        return "%s(%s%s)" %(type(self).__name__,
                            self._reprSource(self._source, replace),
                            self._reprSourceId(replace))
        
    def _setOwner(self, item, attribute):

        oldItem, oldAttribute = super(Set, self)._setOwner(item, attribute)
        self._setSourceItem(self._source,
                            item, attribute, oldItem, oldAttribute)

        return oldItem, oldAttribute

    def _setView(self, view):

        super(Set, self)._setView(view)
        self._setSourceView(self._source, view)

    def sourceChanged(self, op, change, sourceOwner, sourceName, inner, other,
                      source=None):

        if change == 'collection':
            op = self._sourceChanged(self._source, op, change,
                                     sourceOwner, sourceName, other, source)

        elif change == 'notification':
            if other not in self:
                op = None

        if not (inner is True or op is None):
            self._collectionChanged(op, change, other)

        return op

    def findSource(self, id):

        return self._findSource(self._source, id)

    def iterSources(self):

        return self._iterSources(self._source)

    def iterInnerSets(self):

        if isinstance(self._source, AbstractSet):
            yield self._source

    def _inspect_(self, indent):

        return '%s%s' %(self._inspect__(indent),
                        self._inspectSource(self._source, indent + 1))


class BiSet(AbstractSet):

    def __init__(self, left, right, id=None):

        view, self._left = self._prepareSource(left)
        view, self._right = self._prepareSource(right)

        super(BiSet, self).__init__(view, id)

    def _repr_(self, replace=None):

        return "%s(%s, %s%s)" %(type(self).__name__,
                                self._reprSource(self._left, replace),
                                self._reprSource(self._right, replace),
                                self._reprSourceId(replace))
        
    def _setOwner(self, item, attribute):

        oldItem, oldAttribute = super(BiSet, self)._setOwner(item, attribute)
        self._setSourceItem(self._left, item, attribute, oldItem, oldAttribute)
        self._setSourceItem(self._right, item, attribute, oldItem, oldAttribute)

        return oldItem, oldAttribute

    def _setView(self, view):

        super(BiSet, self)._setView(view)
        self._setSourceView(self._left, view)
        self._setSourceView(self._right, view)

    def _op(self, leftOp, rightOp, other):

        raise NotImplementedError, "%s._op" %(type(self))

    def sourceChanged(self, op, change, sourceOwner, sourceName, inner, other,
                      source=None):

        if change == 'collection':
            leftOp = self._sourceChanged(self._left, op, change,
                                         sourceOwner, sourceName, other,
                                         source)
            rightOp = self._sourceChanged(self._right, op, change,
                                          sourceOwner, sourceName, other,
                                          source)
            if op == 'refresh':
                op = self._op(leftOp, rightOp, other) or 'refresh'
            else:
                op = self._op(leftOp, rightOp, other)

        elif change == 'notification':
            if other not in self:
                op = None

        if not (inner is True or op is None):
            self._collectionChanged(op, change, other)

        return op

    def findSource(self, id):

        source = self._findSource(self._left, id)
        if source is not None:
            return source

        source = self._findSource(self._right, id)
        if source is not None:
            return source

        return None

    def iterSources(self):

        for source in self._iterSources(self._left):
            yield source
        for source in self._iterSources(self._right):
            yield source

    def iterInnerSets(self):

        if isinstance(self._left, AbstractSet):
            yield self._left
        if isinstance(self._right, AbstractSet):
            yield self._right

    def _inspect_(self, indent):

        return '%s%s%s' %(self._inspect__(indent),
                          self._inspectSource(self._left, indent + 1),
                          self._inspectSource(self._right, indent + 1))


class Union(BiSet):

    def __contains__(self, item, excludeMutating=False, excludeIndexes=False):
        
        if item is None:
            return False

        if not excludeIndexes:
            index = self._anIndex()
            if index is not None:
                return item.itsUUID in index

        return (self._sourceContains(item, self._left,
                                     excludeMutating, excludeIndexes) or
                self._sourceContains(item, self._right,
                                     excludeMutating, excludeIndexes))

    def _itervalues(self, excludeIndexes=False):

        left = self._left
        for item in self._iterSource(left, excludeIndexes):
            yield item
        for item in self._iterSource(self._right, excludeIndexes):
            if not self._sourceContains(item, left, False, excludeIndexes):
                yield item

    def _iterkeys(self, excludeIndexes=False):

        if not excludeIndexes:
            leftIndex = self._aSourceIndex(self._left)
            if leftIndex is not None:
                for key in leftIndex:
                    yield key
                for key in self._iterSourceKeys(self._right):
                    if key not in leftIndex:
                        yield key
                return

        for key in self._iterSourceKeys(self._left, excludeIndexes):
            yield key
        left = self._getSource(self._left)
        for key in self._iterSourceKeys(self._right, excludeIndexes):
            if not left.__contains__(key, False, excludeIndexes):
                yield key

    def _op(self, leftOp, rightOp, other):

        left = self._left
        right = self._right

        if (leftOp == 'add' and not self._sourceContains(other, right) or
            rightOp == 'add' and not self._sourceContains(other, left)):
            return 'add'
        elif (leftOp == 'remove' and not self._sourceContains(other, right) or
              rightOp == 'remove' and not self._sourceContains(other, left)):
            return 'remove'

        return None


class Intersection(BiSet):

    def __contains__(self, item, excludeMutating=False, excludeIndexes=False):
        
        if item is None:
            return False

        if not excludeIndexes:
            index = self._anIndex()
            if index is not None:
                return item.itsUUID in index

        return (self._sourceContains(item, self._left,
                                     excludeMutating, excludeIndexes) and
                self._sourceContains(item, self._right,
                                     excludeMutating, excludeIndexes))

    def _itervalues(self, excludeIndexes=False):

        left = self._left
        right = self._right

        for item in self._iterSource(left, excludeIndexes):
            if self._sourceContains(item, right, False, excludeIndexes):
                yield item

    def _iterkeys(self, excludeIndexes=False):

        if not excludeIndexes:
            rightIndex = self._aSourceIndex(self._right)
            if rightIndex is not None:
                for key in self._iterSourceKeys(self._left):
                    if key in rightIndex:
                        yield key
                return

        right = self._getSource(self._right)
        for key in self._iterSourceKeys(self._left, excludeIndexes):
            if right.__contains__(key, False, excludeIndexes):
                yield key

    def _op(self, leftOp, rightOp, other):

        left = self._left
        right = self._right

        if (leftOp == 'add' and self._sourceContains(other, right) or
            rightOp == 'add' and self._sourceContains(other, left)):
            return 'add'
        elif (leftOp == 'remove' and self._sourceContains(other, right) or
              rightOp == 'remove' and self._sourceContains(other, left)):
            return 'remove'

        return None


class Difference(BiSet):

    def __contains__(self, item, excludeMutating=False, excludeIndexes=False):
        
        if item is None:
            return False

        if not excludeIndexes:
            index = self._anIndex()
            if index is not None:
                return item.itsUUID in index

        return (self._sourceContains(item, self._left,
                                     excludeMutating, excludeIndexes) and
                not self._sourceContains(item, self._right,
                                         excludeMutating, excludeIndexes))

    def _itervalues(self, excludeIndexes=False):

        left = self._left
        right = self._right

        for item in self._iterSource(left, excludeIndexes):
            if not self._sourceContains(item, right, False, excludeIndexes):
                yield item

    def _iterkeys(self, excludeIndexes=False):

        if not excludeIndexes:
            rightIndex = self._aSourceIndex(self._right)
            if rightIndex is not None:
                for key in self._iterSourceKeys(self._left):
                    if key not in rightIndex:
                        yield key
                return

        right = self._getSource(self._right)
        for key in self._iterSourceKeys(self._left, excludeIndexes):
            if not right.__contains__(key, False, excludeIndexes):
                yield key

    def _op(self, leftOp, rightOp, other):

        left = self._left
        right = self._right

        if (leftOp == 'add' and not self._sourceContains(other, right) or
            rightOp == 'remove' and self._sourceContains(other, left, True)):
            return 'add'

        elif (leftOp == 'remove' and not self._sourceContains(other, right) or
              rightOp == 'add' and self._sourceContains(other, left, True)):
            return 'remove'

        return None


class MultiSet(AbstractSet):

    def __init__(self, *sources, **kwds):

        self._sources = []
        view = None
        for source in sources:
            view, source = self._prepareSource(source)
            self._sources.append(source)

        super(MultiSet, self).__init__(view, kwds.get('id', None))

    def _repr_(self, replace=None):

        return "%s(%s%s)" %(type(self).__name__,
                            ", ".join([self._reprSource(source, replace)
                                       for source in self._sources]),
                            self._reprSourceId(replace))
        
    def _setOwner(self, item, attribute):

        oldItem, oldAttribute = super(MultiSet, self)._setOwner(item, attribute)
        for source in self._sources:
            self._setSourceItem(source, item, attribute, oldItem, oldAttribute)

        return oldItem, oldAttribute

    def _setView(self, view):

        super(MultiSet, self)._setView(view)
        for source in self._sources:
            self._setSourceView(source, view)

    def _op(self, ops, other):

        raise NotImplementedError, "%s._op" %(type(self))

    def sourceChanged(self, op, change, sourceOwner, sourceName, inner, other,
                      source=None):

        if change == 'collection':
            ops = [self._sourceChanged(_source, op, change,
                                       sourceOwner, sourceName, other, source)
                   for _source in self._sources]
            if op == 'refresh':
                op = self._op(ops, other) or 'refresh'
            else:
                op = self._op(ops, other)

        elif change == 'notification':
            if other not in self:
                op = None

        if not (inner is True or op is None):
            self._collectionChanged(op, change, other)

        return op

    def findSource(self, id):

        for source in self._sources:
            src = self._findSource(source, id)
            if src is not None:
                return src

        return None

    def iterSources(self):

        for source in self._sources:
            for src in self._iterSources(source):
                yield src

    def iterInnerSets(self):

        for source in self._sources:
            if isinstance(source, AbstractSet):
                yield source

    def _inspect_(self, indent):

        return '%s%s' %(self._inspect__(indent),
                        ''.join([self._inspectSource(source, indent + 1)
                                 for source in self._sources]))


class MultiUnion(MultiSet):

    def __contains__(self, item, excludeMutating=False, excludeIndexes=False):

        if item is None:
            return False

        if not excludeIndexes:
            index = self._anIndex()
            if index is not None:
                return item.itsUUID in index

        for source in self._sources:
            if self._sourceContains(item, source,
                                    excludeMutating, excludeIndexes):
                return True

        return False

    def _iterkeys(self, excludeIndexes=False):

        sources = self._sources
        for source in sources:
            for key in self._iterSourceKeys(source, excludeIndexes):
                unique = True
                for src in sources:
                    if src is source:
                        break
                    if self._sourceContains(key, src, False, excludeIndexes):
                        unique = False
                        break
                if unique:
                    yield key

    def _itervalues(self, excludeIndexes=False):

        sources = self._sources
        for source in sources:
            for item in self._iterSource(source, excludeIndexes):
                unique = True
                for src in sources:
                    if src is source:
                        break
                    if self._sourceContains(item, src, False, excludeIndexes):
                        unique = False
                        break
                if unique:
                    yield item

    def _op(self, ops, other):

        sources = self._sources
        for op, source in izip(ops, sources):
            if op is not None:
                unique = True
                for src in sources:
                    if src is source:
                        continue
                    if self._sourceContains(other, src):
                        unique = False
                        break
                if unique:
                    return op

        return None


class MultiIntersection(MultiSet):

    def __contains__(self, item, excludeMutating=False, excludeIndexes=False):

        if item is None:
            return False

        if not excludeIndexes:
            index = self._anIndex()
            if index is not None:
                return item.itsUUID in index

        for source in self._sources:
            if not self._sourceContains(item, source,
                                        excludeMutating, excludeIndexes):
                return False

        return True

    def _iterkeys(self, excludeIndexes=False):

        sources = self._sources
        if len(sources) > 1:
            source = sources[0]
            for key in self._iterSourceKeys(source, excludeIndexes):
                everywhere = True
                for src in sources:
                    if src is source:
                        continue
                    if not self._sourceContains(key, src,
                                                False, excludeIndexes):
                        everywhere = False
                        break
                if everywhere:
                    yield key

    def _itervalues(self, excludeIndexes=False):

        sources = self._sources
        if len(sources) > 1:
            source = sources[0]
            for item in self._iterSource(source, excludeIndexes):
                everywhere = True
                for src in sources:
                    if src is source:
                        continue
                    if not self._sourceContains(item, src,
                                                False, excludeIndexes):
                        everywhere = False
                        break
                if everywhere:
                    yield item

    def _op(self, ops, other):

        sources = self._sources
        if len(sources) > 1:
            for op, source in izip(ops, sources):
                if op is not None:
                    everywhere = True
                    for src in sources:
                        if src is source:
                            continue
                        if not self._sourceContains(other, src):
                            everywhere = False
                            break
                    if everywhere:
                        return op

        return None


class KindSet(Set):

    def __init__(self, kind, recursive=False, id=None):

        # kind is either a Kind item or an Extent UUID

        if isinstance(kind, UUID):
            self._extent = kind
        else:
            kind = kind.extent
            self._extent = kind.itsUUID

        self._recursive = recursive
        super(KindSet, self).__init__((kind, 'extent'), id)

    def __contains__(self, item, excludeMutating=False, excludeIndexes=False):

        if item is None:
            return False

        kind = self._view[self._extent].kind

        if isuuid(item):
            instance = self._view.find(item, False)
            if instance is None:
                return kind.isKeyForInstance(item, self._recursive)
            else:
                item = instance

        if self._recursive:
            contains = item.isItemOf(kind)
        else:
            contains = item.itsKind is kind

        if contains:
            if (excludeMutating and item.isMutating() and
                (item._futureKind is None or
                 not item._futureKind.isKindOf(kind))):
                return False
            return not item.isDeferred()
        
        return False

    def _sourceContains(self, item, source,
                        excludeMutating=False, excludeIndexes=False):

        return self.__contains__(item, excludeMutating, excludeIndexes)

    def _itervalues(self, excludeIndexes=False):

        return self._view[self._extent].iterItems(self._recursive)

    def _iterkeys(self, excludeIndexes=False):

        return self._view[self._extent].iterKeys(self._recursive)

    def _repr_(self, replace=None):

        return "%s(UUID('%s'), %s%s)" %(type(self).__name__,
                                        self._extent.str64(), self._recursive,
                                        self._reprSourceId(replace))
        
    def sourceChanged(self, op, change, sourceOwner, sourceName, inner, other,
                      source=None):

        if change == 'collection':
            op = self._sourceChanged(self._source, op, change,
                                     sourceOwner, sourceName, other, source)

        elif change == 'notification':
            if other not in self:
                op = None

        if not (inner is True or op is None):
            self._collectionChanged(op, change, other)

        return op

    def countKeys(self):

        return AbstractSet.countKeys(self)

    def iterSources(self):

        return iter(())

    def iterInnerSets(self):

        return iter(())

    def _inspect_(self, indent):

        return "%s\n%skind: %s" %(self._inspect__(indent),
                                  '  ' * (indent + 1),
                                  self._view[self._extent].kind.itsPath)


class FilteredSet(Set):

    def __init__(self, source, attrs=None, id=None):

        super(FilteredSet, self).__init__(source, id)
        self.attributes = attrs
    
    def __contains__(self, item, excludeMutating=False, excludeIndexes=False):

        if item is None:
            return False

        if not excludeIndexes:
            index = self._anIndex()
            if index is not None:
                return item.itsUUID in index

        if self._sourceContains(item, self._source,
                                excludeMutating, excludeIndexes):
            return self.filter(item.itsUUID)

        return False

    def _iterkeys(self, excludeIndexes=False):

        for uuid in self._iterSourceKeys(self._source, excludeIndexes):
            if self.filter(uuid):
                yield uuid

    def _itervalues(self, excludeIndexes=False):

        for item in self._iterSource(self._source, excludeIndexes):
            if self.filter(item.itsUUID):
                yield item

    def countKeys(self):

        count = 0
        for key in self._iterkeys(True):
            count += 1

        return count

    def _setOwner(self, item, attribute):

        oldItem, oldAttribute = super(FilteredSet, self)._setOwner(item,
                                                                   attribute)
        
        if item is not oldItem:
            if not self._view.isLoading():
                attrs = self.attributes
                if oldItem is not None:
                    if attrs:
                        def detach(op, name):
                            Monitors.detach(oldItem, '_filteredItemChanged',
                                            op, name, oldAttribute)
                        for name in attrs:
                            detach('init', name)
                            detach('set', name)
                            detach('remove', name)
                if item is not None:
                    if attrs:
                        def attach(op, name):
                            mon = Monitors.attach(item, '_filteredItemChanged',
                                                  op, name, attribute)
                            mon._status |= CItem.SYSMONITOR
                        for name in attrs:
                            attach('init', name)
                            attach('set', name)
                            attach('remove', name)

        return oldItem, oldAttribute

    def sourceChanged(self, op, change, sourceOwner, sourceName, inner, other,
                      source=None):

        if change == 'collection':
            op = self._sourceChanged(self._source, op, change,
                                     sourceOwner, sourceName, other, source)

            if op == 'add':
                if not self.filter(other):
                    op = None
            elif op == 'remove':
                index = self._anIndex()
                if index is not None:
                    if other not in index:
                        op = None
                elif not self.filter(other):
                    otherItem = self._view.find(other, False)
                    if not (otherItem is None or otherItem.isDeleting()):
                        op = None

        elif change == 'notification':
            if other not in self:
                op = None

        if not (inner is True or op is None):
            self._collectionChanged(op, change, other)

        return op

    def itemChanged(self, other, attribute):

        if self._sourceContains(other, self._source):
            matched = self.filter(other)

            if self._indexes:
                contains = other in self._indexes.itervalues().next()
            else:
                contains = None
                
            if matched and not contains is True:
                self._collectionChanged('add', 'collection', other)
            elif not matched and not contains is False:
                self._collectionChanged('remove', 'collection', other)


class ExpressionFilteredSet(FilteredSet):

    def __init__(self, source, expr, attrs=None, id=None):

        super(ExpressionFilteredSet, self).__init__(source, attrs, id)

        self.filterExpression = expr
        self._filter = eval("lambda view, uuid: " + self.filterExpression)
    
    def filter(self, uuid):

        try:
            return self._filter(self._view, uuid)
        except Exception, e:
            e.args = ("Error in filter", self.filterExpression) + e.args
            raise

    def _repr_(self, replace=None):

        return "%s(%s, \"\"\"%s\"\"\", %s%s)" %(type(self).__name__, self._reprSource(self._source, replace), self.filterExpression, self.attributes, self._reprSourceId(replace))

    def _inspect_(self, indent):

        i = indent + 1
        return "%s\n%sfilter: %s\n%s attrs: %s%s" %(self._inspect__(indent), '  ' * i, self.filterExpression, '  ' * i, ', '.join(str(a) for a in self.attributes), self._inspectSource(self._source, i))
    

class MethodFilteredSet(FilteredSet):

    def __init__(self, source, filterMethod, attrs=None, id=None):

        super(MethodFilteredSet, self).__init__(source, attrs, id)

        item, methodName = filterMethod
        self.filterMethod = (item.itsUUID, methodName)
    
    def filter(self, uuid):

        view = self._view
        uItem, methodName = self.filterMethod

        return getattr(view[uItem], methodName)(view, uuid)

    def _repr_(self, replace=None):

        uItem, methodName = self.filterMethod
        return "%s(%s, (UUID('%s'), '%s'), %s%s)" %(type(self).__name__, self._reprSource(self._source, replace), uItem.str64(), methodName, self.attributes, self._reprSourceId(replace))

    def _inspect_(self, indent):

        i = indent + 1
        return "%s\n%sfilter: %s\n%s attrs: %s%s" %(self._inspect__(indent), '  ' * i, self.filterMethod, '  ' * i, ', '.join(str(a) for a in self.attributes), self._inspectSource(self._source, i))
