
__revision__  = "$Revision: 5185 $"
__date__      = "$Date: 2005-05-01 23:42:25 -0700 (Sun, 01 May 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from chandlerdb.util.uuid import UUID
from repository.item.Values import ItemValue
from repository.item.Monitors import Monitors
from repository.item.Query import KindQuery
from repository.item.Indexed import Indexed


class AbstractSet(ItemValue, Indexed):

    def __init__(self, view):

        super(AbstractSet, self).__init__()

        self._view = view
        self._indexes = None

    def __contains__(self, item):
        raise NotImplementedError, "%s.__contains__" %(type(self))

    def __iter__(self):
        raise NotImplementedError, "%s.__iter__" %(type(self))

    def _setChanged(self, op, setOwner, setName, other):
        raise NotImplementedError, "%s._setChanged" %(type(self))

    def __getitem__(self, uuid):

        return self._getView()[uuid]

    def iterkeys(self):

        for item in self:
            yield item.itsUUID

    def dir(self):
        """
        Debugging: print all items referenced in this set
        """
        for item in self:
            print item._repr_()

    def _setItem(self, item, attribute):

        oldItem = self._item
        oldAttribute = self._attribute

        super(AbstractSet, self)._setItem(item, attribute)
        return oldItem, oldAttribute

    def _getView(self):

        item = self._item
        if item is not None:
            return item.itsView
        else:
            return self._view

    def _setView(self, view):

        self._view = view

    def _prepareSource(self, source):

        if isinstance(source, AbstractSet):
            return source._view, source
        elif isinstance(source[0], UUID):
            return None, source
        else:
            return source[0].itsView, (source[0].itsUUID, source[1])

    def _sourceContains(self, item, source):

        if isinstance(source, AbstractSet):
            return item in source

        return item in getattr(self.itsView[source[0]], source[1])

    def _iterSource(self, source):

        if isinstance(source, AbstractSet):
            for item in source:
                yield item
        else:
            for item in getattr(self.itsView[source[0]], source[1]):
                yield item

    def _reprSource(self, source):

        if isinstance(source, AbstractSet):
            return repr(source)

        return "(UUID('%s'), '%s')" %(source[0].str64(), source[1])

    def _setSourceItem(self, source, item, attribute, oldItem, oldAttribute):
        
        if isinstance(source, AbstractSet):
            source._setItem(item, attribute)

        elif item is not oldItem:
            view = self.itsView
            if not view.isLoading():
                if item is None:
                    oldItem.unwatchCollection(view[source[0]], source[1],
                                              'set', oldAttribute)
                else:
                    item.watchCollection(view[source[0]], source[1],
                                         'set', attribute)

    def _setSourceView(self, source, view):

        if isinstance(source, AbstractSet):
            source._setView(view)

    def _sourceChanged(self, source, op, change, sourceOwner, sourceName, other,
                       *args):

        if isinstance(source, AbstractSet):
            return source.sourceChanged(op, change, sourceOwner, sourceName,
                                        True, other, *args)

        if (change == 'collection' and
            sourceOwner is self.itsView[source[0]] and sourceName == source[1]):
            return op

        return None

    def _collectionChanged(self, op, other):

        item = self._item

        if item is not None:
            if self._indexes:
                key = other.itsUUID
                if op == 'add':
                    for index in self._indexes.itervalues():
                        index.insertKey(key, index.getLastKey())
                elif op == 'remove':
                    for index in self._indexes.itervalues():
                        index.removeKey(key)
                else:
                    raise ValueError, op

            item.collectionChanged(op, item, self._attribute, other)
            item._collectionChanged(op, self._attribute, other)

    def removeByIndex(self, indexName, position):

        raise TypeError, "%s contents are computed" %(type(self))

    def insertByIndex(self, indexName, position, item):

        raise TypeError, "%s contents are computed" %(type(self))

    def replaceByIndex(self, indexName, position, with):

        raise TypeError, "%s contents are computed" %(type(self))

    @classmethod
    def makeValue(cls, string):
        return eval(string)

    @classmethod
    def makeString(cls, value):
        return repr(value)

    itsView = property(_getView, lambda self, view: self._setView(view))


class Set(AbstractSet):

    def __init__(self, source):

        view, self._source = self._prepareSource(source)
        super(Set, self).__init__(view)

    def __contains__(self, item):

        return self._sourceContains(item, self._source)

    def __iter__(self):

        for item in self._iterSource(self._source):
            yield item

    def __repr__(self):

        return "%s(%s)" %(type(self).__name__, self._reprSource(self._source))
        
    def _setItem(self, item, attribute):

        oldItem, oldAttribute = super(Set, self)._setItem(item, attribute)
        self._setSourceItem(self._source,
                            item, attribute, oldItem, oldAttribute)

    def _setView(self, view):

        super(Set, self)._setView(view)
        self._setSourceView(self._source, view)

    def sourceChanged(self, op, change, sourceOwner, sourceName, inner, other,
                      *args):

        op = self._sourceChanged(self._source, op, change,
                                 sourceOwner, sourceName, other, *args)

        if not (inner is True or op is None):
            self._collectionChanged(op, other)

        return op


class BiSet(AbstractSet):

    def __init__(self, left, right):

        view, self._left = self._prepareSource(left)
        view, self._right = self._prepareSource(right)

        super(BiSet, self).__init__(view)

    def __repr__(self):

        return "%s(%s, %s)" %(type(self).__name__,
                              self._reprSource(self._left),
                              self._reprSource(self._right))
        
    def _setItem(self, item, attribute):

        oldItem, oldAttribute = super(BiSet, self)._setItem(item, attribute)
        self._setSourceItem(self._left, item, attribute, oldItem, oldAttribute)
        self._setSourceItem(self._right, item, attribute, oldItem, oldAttribute)

    def _setView(self, view):

        super(BiSet, self)._setView(view)
        self._setSourceView(self._left, view)
        self._setSourceView(self._right, view)

    def _op(self, leftOp, rightOp, other):

        raise NotImplementedError, "%s._op" %(type(self))

    def sourceChanged(self, op, change, sourceOwner, sourceName, inner, other,
                      *args):

        leftOp = self._sourceChanged(self._left, op, change,
                                     sourceOwner, sourceName, other, *args)
        rightOp = self._sourceChanged(self._right, op, change,
                                      sourceOwner, sourceName, other, *args)
        op = self._op(leftOp, rightOp, other)

        if not (inner is True or op is None):
            self._collectionChanged(op, other)

        return op


class Union(BiSet):

    def __contains__(self, item):
        
        return (self._sourceContains(item, self._left) or
                self._sourceContains(item, self._right))

    def __iter__(self):

        left = self._left
        for item in self._iterSource(left):
            yield item

        for item in self._iterSource(self._right):
            if not self._sourceContains(item, left):
                yield item

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

    def __contains__(self, item):
        
        return (self._sourceContains(item, self._left) and
                self._sourceContains(item, self._right))

    def __iter__(self):

        left = self._left
        right = self._right

        for item in self._iterSource(left):
            if self._sourceContains(item, right):
                yield item

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

    def __contains__(self, item):
        
        return (self._sourceContains(item, self._left) and
                not self._sourceContains(item, self._right))

    def __iter__(self):

        left = self._left
        right = self._right

        for item in self._iterSource(left):
            if not self._sourceContains(item, right):
                yield item

    def _op(self, leftOp, rightOp, other):

        left = self._left
        right = self._right

        if (leftOp == 'add' and not self._sourceContains(other, right) or
            rightOp == 'remove' and self._sourceContains(other, left)):
            return 'add'

        elif (leftOp == 'remove' and not self._sourceContains(other, right) or
              rightOp == 'add' and self._sourceContains(other, left)):
            return 'remove'

        return None


class KindSet(AbstractSet):

    def __init__(self, kind, recursive=False):

        if isinstance(kind, UUID):
            view, self._kind = None, kind
        else:
            view, self._kind = kind.itsView, kind.itsUUID

        self._recursive = recursive
        super(KindSet, self).__init__(view)

    def __contains__(self, item):

        if self._recursive:
            return item.isItemOf(self.itsView[self._kind])
        else:
            return item.itsKind is self.itsView[self._kind]

    def __iter__(self):

        for item in KindQuery(self._recursive).run([self.itsView[self._kind]]):
            yield item

    def __repr__(self):

        return "%s(UUID('%s'), %s)" %(type(self).__name__,
                                      self._kind.str64(), self._recursive)
        
    def _setItem(self, item, attribute):

        oldItem, oldAttribute = super(KindSet, self)._setItem(item, attribute)
        
        if item is not oldItem:
            if not self.itsView.isLoading():
                if oldItem is not None:
                    Monitors.detach(oldItem, '_kindChanged',
                                    'schema', 'kind', oldAttribute)
                if item is not None:
                    Monitors.attach(item, '_kindChanged',
                                    'schema', 'kind', attribute)

    def sourceChanged(self, op, change, sourceOwner, sourceName, inner, other,
                      *args):

        if change == 'kind':
            if self._item is sourceOwner and self._attribute == sourceName:
                kind = args[0]

                if self._recursive:
                    if not kind.isKindOf(self.itsView[self._kind]):
                        op = None
                else:
                    if kind is not self.itsView[self._kind]:
                        op = None

                if not (inner is True or op is None):
                    self._collectionChanged(op, other)
            else:
                op = None
        else:
            op = None

        return op
