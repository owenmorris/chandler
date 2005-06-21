
__revision__  = "$Revision: 5185 $"
__date__      = "$Date: 2005-05-01 23:42:25 -0700 (Sun, 01 May 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from chandlerdb.util.uuid import UUID
from repository.item.Values import ItemValue


class AbstractSet(ItemValue):

    def __init__(self, view):

        super(AbstractSet, self).__init__()
        self._view = view

    def __contains__(self, item):
        raise NotImplementedError, "%s.__contains__" %(type(self))

    def __iter__(self):
        raise NotImplementedError, "%s.__iter__" %(type(self))

    def _setChanged(self, op, setOwner, setName, other):
        raise NotImplementedError, "%s._setChanged" %(type(self))

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

        if item is not None:
            self._view = item.itsView

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

    def _sourceChanged(self, source, op, sourceOwner, sourceName, other, inner):

        if isinstance(source, AbstractSet):
            return source.sourceChanged(op, sourceOwner, sourceName,
                                        other, True)

        elif sourceOwner is self.itsView[source[0]] and sourceName == source[1]:
            return op

        else:
            return None

    @classmethod
    def makeValue(cls, string):
        return eval(string, globals(), locals())

    @classmethod
    def makeString(cls, value):
        return repr(value)

    itsView = property(_getView, _setView)


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

        return "Set(%s)" %(self._reprSource(self._source))
        
    def _setItem(self, item, attribute):

        oldItem, oldAttribute = super(Set, self)._setItem(item, attribute)
        self._setSourceItem(self._source,
                            item, attribute, oldItem, oldAttribute)

    def sourceChanged(self, op, sourceOwner, sourceName, other, inner):

        op = self._sourceChanged(self._source,
                                 op, sourceOwner, sourceName, other, inner)

        if not (inner is True or op is None):
            item = self._item
            if item is not None:
                item.collectionChanged(op, item, self._attribute, other)

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

    def _op(self, leftOp, rightOp, other):

        raise NotImplementedError, "%s._op" %(type(self))

    def sourceChanged(self, op, sourceOwner, sourceName, other, inner):

        leftOp = self._sourceChanged(self._left, op, sourceOwner, sourceName,
                                     other, inner)
        rightOp = self._sourceChanged(self._right, op, sourceOwner, sourceName,
                                      other, inner)
        op = self._op(leftOp, rightOp, other)

        if not (inner is True or op is None):
            item = self._item
            if item is not None:
                item.collectionChanged(op, item, self._attribute, other)

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
