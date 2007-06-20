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


from repository.item.Item import Item, ItemClass, override


class CollectionClass(ItemClass):

    def __init__(cls, name, bases, clsdict):

        if not hasattr(cls, '__collection__'):  # local or inherited
            raise AttributeError, (cls, '__collection__ is undefined')

        if '__collection__' in clsdict:         # local
            cls.__delegates__ = clsdict['__collection__'],

        super(CollectionClass, cls).__init__(name, bases, clsdict)


class Collection(Item):
    """
    This class is abstract. Base concrete subclasses must use the
    C{CollectionClass} metaclass, must be declared tied to a kind that
    provides the collection attribute, and must declare its name as in the
    example below::

        __metaclass__ = CollectionClass
        __collection__ = 'attrName'

    The type of collection value chosen (as declared in the kind definition)
    determines which methods are delegated from this item to the collection
    value, typically an C{AbstractSet} subclass instance or a C{RefList}
    instance.
    """

    @override(Item)
    def _collectionChanged(self, op, change, name, other, dirties):

        if name == self.__collection__:
            view = self.itsView
            watchers = view._watchers.get(self.itsUUID)
            if watchers and view.SUBSCRIBERS in watchers:
                view.queueNotification(self, op, change, name, other, dirties)

        super(Collection, self)._collectionChanged(op, change, name,
                                                   other, dirties)

    def __contains__(self, obj):

        return obj in getattr(self, self.__collection__)

    def __iter__(self):

        return iter(getattr(self, self.__collection__))

    def __len__(self):

        return len(getattr(self, self.__collection__))

    def __nonzero__(self):
        """
        A Collection item is considered C{False} if it is empty.
        """

        set = getattr(self, self.__collection__)
        index = set._anIndex()

        if index is not None:
            return True if index else False

        for i in set.iterkeys():
            return True

        return False

    def __eq__(self, other):

        return self is other

    def __ne__(self, other):

        return self is not other

    def _inspect(self, indent=0):

        return super(Collection, self)._inspectCollection(self.__collection__,
                                                          indent)

    def add(self, other):

        try:
            add = getattr(self, self.__collection__).add
        except AttributeError:
            raise NotImplementedError, (type(self), 'add not implemented')
        else:
            return add(other)

    def remove(self, other):

        try:
            remove = getattr(self, self.__collection__).remove
        except AttributeError:
            raise NotImplementedError, (type(self), 'remove not implemented')
        else:
            return remove(other)

    def getSourceCollection(self):

        return self.itsView, (self.itsUUID, self.__collection__)

    def isSubset(self, superset, reasons=None):
        """
        Tell if C{self} a subset of C{superset}.

        @param reasons: if specified, contains the C{(subset, superset)} pairs
                        that caused the predicate to fail.
        @type reasons: a C{set} or C{None}
        @return: C{True} or C{False}
        """

        superset = getattr(superset, superset.__collection__)
        return getattr(self, self.__collection__).isSubset(superset, reasons)

    def isSuperset(self, subset, reasons=None):
        """
        Tell if C{self} a superset of C{subset}.

        @param reasons: if specified, contains the C{(subset, superset)} pairs
                        that caused the predicate to fail.
        @type reasons: a C{set} or C{None}
        @return: C{True} or C{False}
        """

        subset = getattr(subset, subset.__collection__)
        return getattr(self, self.__collection__).isSubset(subset, reasons)
