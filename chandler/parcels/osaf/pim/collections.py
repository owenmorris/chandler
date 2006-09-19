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


__parcel__ = "osaf.pim"

from application import schema

from chandlerdb.util.c import Default
from repository.item.Sets import \
    Set, MultiUnion, Union, MultiIntersection, Intersection, Difference, \
    KindSet, ExpressionFilteredSet, MethodFilteredSet, EmptySet
from repository.item.Collection import Collection

from osaf.pim.items import ContentItem


class ContentCollection(ContentItem, Collection):
    """
    The base class for Chandler Collection types.

    This class is abstract. Base concrete subclasses must use the
    C{schema.CollectionClass} metaclass and declare the collection attribute
    and its name as in the examples below::

        __metaclass__ = schema.CollectionClass
        __collection__ = 'ex1'

        ex1 = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))

    or::

        __metaclass__ = schema.CollectionClass
        __collection__ = 'ex2'

        ex2 = schema.Sequence(otherName='ex2_collections', initialValue=[])

    The type of collection value chosen (as declared above) determines which
    methods are delegated from this item to the collection value, typically
    an AbstractSet subclass instance or a RefList instance.
    """

    collectionList = schema.Sequence(
        'ContentCollection',
        doc="Views, e.g. the Calendar, that display collections need to know "
            "which collection are combined to make up the calendar. collectionList"
            "is an optional parameter for this purpose."
    )

    invitees = schema.Sequence(
        "osaf.pim.mail.EmailAddress",
        doc="The people who are being invited to share in this item; filled "
            "in when the user types in the DV's 'invite' box, then cleared on "
            "send (entries copied to the share object).\n\n"
            "Issue: Bad that we have just one of these per item collection, "
            "though an item collection could have multiple shares post-0.5",
        inverse="inviteeOf",
        initialValue=()
    )

    # redirections 
    about = schema.Descriptor(redirectTo="displayName")

    # other side of 'sources'
    sourceFor = schema.Sequence(otherName='sources')

    # other side of AppCollection.exclusions
    exclusionsFor = schema.Sequence()

    # other side of AppCollection.trash
    trashFor = schema.Sequence()

    schema.addClouds(
        copying = schema.Cloud(
            invitees,
            byRef=['contentsOwner']
        ),
        sharing = schema.Cloud(none=["displayName"]),
    )

    # this delete hook is necessary because clearing 'sourceFor' depends on
    # watchers still be being there.
    def onItemDelete(self, view, isDeferring):
        #KLUDGE put in as debugging aid after bug 6686 9/14/06
        #remove after 3 months
        if self.itsName == 'allCollection':
            raise ValueError, ('deleting allCollection', self)
        if not isDeferring and hasattr(self, 'sourceFor'):
            self.sourceFor.clear()

    def withoutTrash(self):
        """
        If this collection wraps the trash collection, return an equivalent
        collection that doesn't.
        """

        return self

    def isReadOnly(self):
        """
        Return C{True} iff participating in only read-only shares.
        """
        if not self.shares:
            return False

        for share in self.shares:
            if share.mode in ('put', 'both'):
                return False

        return True

    readOnly = property(isReadOnly)


class KindCollection(ContentCollection):
    """
    A ContentCollection of all of the items of a particular kind.

    The C{kind} attribute determines the C{Kind} of the items in the
    C{KindCollection}.

    The C{recursive} attribute determines whether items of subkinds are
    included (C{False}) by default).
    """

    __metaclass__ = schema.CollectionClass
    __collection__ = 'set'

    set = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))

    kind = schema.One(schema.TypeReference('//Schema/Core/Kind'))
    recursive = schema.One(schema.Boolean, defaultValue=False)

    def __init__(self, *args, **kwds):

        super(KindCollection, self).__init__(*args, **kwds)
        setattr(self, self.__collection__, KindSet(self.kind, self.recursive))


class ListCollection(ContentCollection):
    """
    A ContentCollection that contains only those items that are explicitly
    added to it.

    Items in a ContentCollection are iterated over in order of insertion.

    A ListCollection is backed by a ref collection.
    """

    __metaclass__ = schema.CollectionClass
    __collection__ = 'inclusions'

    # must be named 'inclusions' to match AppCollection
    inclusions = schema.Sequence(otherName='collections', initialValue=[])

    def empty(self):
        for item in self:
            item.delete(True)


class WrapperCollection(ContentCollection):
    """
    A class for collections wrapping other collections
    """

    __metaclass__ = schema.CollectionClass
    __collection__ = 'set'

    set = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))

    sources = schema.Sequence(ContentCollection, otherName='sourceFor',
                              doc="the collections being wrapped",
                              initialValue=[])
    schema.addClouds(copying=schema.Cloud(byCloud=[sources]))

    def __init__(self, *args, **kwds):

        super(WrapperCollection, self).__init__(*args, **kwds)

        self._sourcesChanged_()
        self.watchCollection(self, 'sources', '_sourcesChanged')

    def _sourcesChanged(self, op, item, attribute, sourceId):

        if op in ('add', 'remove'):
            view = self.itsView
            source = view[sourceId]
            name = source.__collection__

            if op == 'add':
                set = self._sourcesChanged_()
                sourceChanged = set.sourceChanged
                actualSource = set.findSource(sourceId)
                assert actualSource is not None
                for uuid in source.iterkeys():
                    view._notifyChange(sourceChanged, 'add', 'collection',
                                       source, name, False, uuid, actualSource)

            elif op == 'remove':
                set = getattr(self, self.__collection__)
                sourceChanged = set.sourceChanged
                actualSource = set.findSource(sourceId)
                assert actualSource is not None
                for uuid in source.iterkeys():
                    view._notifyChange(sourceChanged, 'remove', 'collection',
                                       source, name, False, uuid, actualSource)
                set = self._sourcesChanged_()

    def addSource(self, source):

        if source not in self.sources:
            self.sources.append(source)

    def removeSource(self, source):

        if source in self.sources:
            self.sources.remove(source)


class SingleSourceWrapperCollection(WrapperCollection):
    """
    A class for collections wrapping another collection
    """

    def _getSource(self):
        sources = self.sources
        if sources:
            return sources.first()
        return None
    def _setSource(self, source):
        sources = self.sources
        if sources:
            if sources.first() is source:
                return
            sources.clear()
        if source is not None:
            sources.append(source)
    def _delSource(self):
        self.sources.clear()
    source = property(_getSource, _setSource, _delSource)

    def __init__(self, *args, **kwds):

        source = kwds.pop('source', None)
        if source is not None:
            kwds['sources'] = [source]

        super(SingleSourceWrapperCollection, self).__init__(*args, **kwds)

    def _sourcesChanged_(self):
        
        source = self.source

        if source is None:
            set = EmptySet()
        else:
            set = Set(source)

        setattr(self, self.__collection__, set)
        return set


class DifferenceCollection(WrapperCollection):
    """
    A ContentCollection containing the set theoretic difference of two
    ContentCollections.

    The C{sources} attribute (a list) contains the ContentCollection
    instances to be differenced.
    """

    def _sourcesChanged_(self):

        sources = self.sources
        sourceCount = len(sources)

        if sourceCount == 0:
            set = EmptySet()
        elif sourceCount == 1:
            set = getattr(self, self.__collection__)
            source = sources.first()
            if instance(set, Difference):
                if set._left[0] == source.itsUUID:
                    set = Set(source)
                else:
                    set = EmptySet()
            else:
                set = Set(source)
        elif sourceCount == 2:
            a, b = self.sources
            set = Difference(a, b)
        else:
            raise ValueError, 'too many sources'

        setattr(self, self.__collection__, set)
        return set


class UnionCollection(WrapperCollection):
    """
    A ContentCollection containing the set theoretic union of at least two
    ContentCollections.
    """

    def _sourcesChanged_(self):

        sources = self.sources
        sourceCount = len(sources)

        # For now, when we join collections with Union, we pull trash
        # out of the equation with withoutTrash()
        if sourceCount == 0:
            set = EmptySet()
        elif sourceCount == 1:
            set = Set(sources.first().withoutTrash())
        elif sourceCount == 2:
            left, right = sources
            set = Union(left.withoutTrash(), right.withoutTrash())
        else:
            set = MultiUnion(*(source.withoutTrash()
                               for source in sources))

        setattr(self, self.__collection__, set)
        return set


class IntersectionCollection(WrapperCollection):
    """
    A ContentCollection containing the set theoretic intersection of at
    least two ContentCollections.
    """

    def _sourcesChanged(self, op, item, attribute, sourceId):

        if op in ('add', 'remove'):
            view = self.itsView
            source = view[sourceId]
            name = self.__collection__
            _collectionChanged = self._collectionChanged

            if op == 'add':
                set = getattr(self, name)
                wasEmpty = isinstance(set, EmptySet)
                if not wasEmpty:
                    sourceSet = getattr(source, source.__collection__)
                    for uuid in set.iterkeys():
                        if uuid not in sourceSet:
                            view._notifyChange(_collectionChanged,
                                               'remove', 'collection',
                                               name, uuid)
                set = self._sourcesChanged_()
                if wasEmpty and not isinstance(set, EmptySet):
                    for uuid in set.iterkeys():
                        view._notifyChange(_collectionChanged,
                                           'add', 'collection', name, uuid)

            elif (op == 'remove' and
                  not isinstance(getattr(self, name), EmptySet)):
                set = self._sourcesChanged_()
                sourceSet = getattr(source, source.__collection__)
                if isinstance(set, EmptySet):
                    for uuid in sourceSet.iterkeys():
                        view._notifyChange(_collectionChanged,
                                           'remove', 'collection', name, uuid)
                else:
                    for uuid in set.iterkeys():
                        if uuid not in sourceSet:
                            view._notifyChange(_collectionChanged,
                                               'add', 'collection', name, uuid)

    def _sourcesChanged_(self):

        sources = self.sources
        sourceCount = len(sources)

        # For now, when we join collections with Intersection, we pull trash
        # out of the equation with withoutTrash()
        if sourceCount < 2:
            set = EmptySet()
        elif sourceCount == 2:
            left, right = sources
            set = Intersection(left.withoutTrash(), right.withoutTrash())
        else:
            set = MultiIntersection(*(source.withoutTrash()
                                      for source in sources))

        setattr(self, self.__collection__, set)
        return set


class FilteredCollection(SingleSourceWrapperCollection):
    """
    A ContentCollection which is the result of applying a boolean predicate
    to every item of another ContentCollection.
    
    The C{source} attribute contains the ContentCollection instance to be
    filtered.

    The C{filterExpression} attribute is a string containing a Python
    expression. If the expression returns C{True} for an item in the
    C{source} it will be in the FilteredCollection.

    The C{filterAttributes} attribute is a list of attribute names
    (Strings), which are accessed by the C{filterExpression}.
    Failure to provide this list will result in missing notifications.
    """

    filterExpression = schema.One(schema.Text)
    filterMethod = schema.One(schema.Tuple)
    filterAttributes = schema.Sequence(schema.Symbol, initialValue=[])

    def _sourcesChanged_(self):

        source = self.source
        if source is None:
            s = EmptySet()
        else:
            attrTuples = set()
            for name in self.filterAttributes:
                attrTuples.add((name, "set"))
                attrTuples.add((name, "remove"))
            attrs = tuple(attrTuples)

            if hasattr(self, 'filterExpression'):
                s = ExpressionFilteredSet(source, self.filterExpression, attrs)
            else:
                s = MethodFilteredSet(source, self.filterMethod, attrs)

        setattr(self, self.__collection__, s)
        return s


class AppCollection(ContentCollection):
    """
    AppCollections implement inclusions, exclusions, source,
    and trash along with methods for add and remove.
    """

    __metaclass__ = schema.CollectionClass
    __collection__ = 'set'

    set = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))

    # must be named 'inclusions' to match ListCollection
    inclusions = schema.Sequence(otherName='collections', initialValue=[])

    exclusions = schema.One(inverse=ContentCollection.exclusionsFor)
    trash = schema.One(inverse=ContentCollection.trashFor, initialValue=None)

    # __collection__ denotes a bi-ref set, 
    # therefore it must be added to the copying cloud def for it to be copied.

    schema.addClouds(
        copying = schema.Cloud(
            byCloud=[inclusions, exclusions],
            byRef=[trash, __collection__]
        ),
    )

    def add(self, item):
        """
        Add an item to the collection.
        """
        self.inclusions.add(item)

        if item in self.exclusions:
            self.exclusions.remove(item)

        # If a trash is associated with this collection, remove the item
        # from the trash.  This has the additional benefit of having the item
        # reappear in any collection which has the item in its inclusions

        if self.trash is not None and item in self.trash:
            self.trash.remove(item)

    def remove(self, item):
        """
        Remove an item from the collection.
        """

        isDeleting = item.isDeleting()

        # adding to exclusions before determining if the item should be added to
        # the trash was a problem at one point (bug 4551), but since the mine/
        # not-mine mechanism changed, this doesn't seem to be a problem anymore,
        # and removing from a mine collection was actually misbehaving if the
        # test was done first, so now logic for moving to the trash has moved
        # back to after addition to exclusions and removal from inclusions.
        if not isDeleting:
            self.exclusions.add(item)

        if item in self.inclusions:
            self.inclusions.remove(item)

        if not (isDeleting or self.trash is None):
            for collection in self.trash.trashFor:
                if collection is not self and item in collection:
                    # it exists somewhere else, definitely don't add
                    # to trash
                    break
            else:
                # we couldn't find it anywhere else, so it goes in the trash
                self.trash.add(item)

    def __init__(self, itsName=None, itsParent=None,
                 itsKind=None, itsView=None,
                 source=None, exclusions=None, trash=Default,
                 *args, **kwds):
        super(AppCollection, self).__init__(itsName=itsName,
                                            itsParent=itsParent,
                                            itsKind=itsKind,
                                            itsView=itsView,
                                            *args, **kwds)
        self._setup(source, exclusions, trash)

    def _setup(self, source=None, exclusions=None, trash=Default):
        """
        Setup all the extra parts of an AppCollection. In general
        nobody should call this but __init__, but unfortunately
        sharing creates AppCollections without calling __init__
        so it should be the only caller of _setup.

        Sets the source, exclusions and trash collections.

        In general trash should only be the well known Trash
        collection or None. None indicates that this collection does
        not participate in Trash-based activities.

        The special value of Default for trash is only a sentinel to
        let us know that nothing has been passed in and that the
        default trash should be looked up in osaf.pim. During parcel
        loading, this allows us to pass the trash into the constructor
        and avoid trying to look it up in osaf.pim while osaf.pim is
        being loaded.
        """

        if trash is Default:
            # better hope osaf.pim has been loaded!
            trash = schema.ns('osaf.pim', self.itsView).trashCollection

        innerSource = (self, 'inclusions')
        if source is not None:
            innerSource = Union(source, innerSource)

        # Typically we will create an exclusions ListCollection; however,
        # a collection like 'All' will instead want to use the Trash collection
        # for exclusions

        if exclusions is None:
            exclusions = ListCollection(itsParent=self,
                                        displayName=u"(Exclusions)")
        self.exclusions = exclusions

        # You can designate a certain ListCollection to be used for this
        # collection's trash; in this case, an additional DifferenceCollection
        # will be created to remove any trash items from this collection. Any
        # collections which share a trash get the following benefits:
        # - Adding an item to the trash will make the item disappear from
        #   collections sharing that trash collection
        # - When an item is removed from a collection, it will automatically
        #   be moved to the trash if it doesn't appear in any collection which
        #   shares that trash

        set = Difference(innerSource, exclusions)
        if trash is not None:
            set = Difference(set, trash)
            self.trash = trash
        else:
            self.trash = exclusions

        setattr(self, self.__collection__, set)

    def withoutTrash(self):
        """
        Pull out the non-trash part of AppCollection.
        """
        
        # Smart collections are 'special' - they almost always include
        # the trash as a part of their structure on the _right side of
        # their Difference set. This means that when they are hooked
        # into a larger collection tree, they need to only give out
        # the _left side, which has no trash.
        
        if self.trash is schema.ns('osaf.pim', self.itsView).trashCollection:
            return self.set._left.copy(self.itsUUID)

        return self


class SmartCollection(AppCollection):
    """
    A SmartCollection is just an AppCollection that is user-facing.
    """
    __metaclass__ = schema.CollectionClass
    __collection__ = 'set'

    # it involves bi-refs because of 'otherName'
    # it's an AbstractSet because cardinality is 'set' (schema.Many)
    # it's an AbstractSet of bi-directional references
    set = schema.Many(inverse=ContentItem.appearsIn)

    # this delete hook is necessary because clearing the set of bi-refs
    # may depend on collections that are children of this one
    def onItemDelete(self, view, isDeferring):
        super(SmartCollection, self).onItemDelete(view, isDeferring)
        if not isDeferring:
            delattr(self, self.__collection__)


class InclusionExclusionCollection(SmartCollection):
    """
    For backwards compatibility with 0.6 clients.
    """
    # @@@MOR 0.6 sharing compatibility
    pass


class IndexedSelectionCollection(SingleSourceWrapperCollection):
    """
    A collection that adds an index, e.g. for sorting items, a
    selection and visibility attribute to another source collection.
    """

    indexName = schema.One(schema.Symbol, initialValue="__adhoc__")

    def _sourcesChanged_(self):
        
        source = self.source
        trash = schema.ns('osaf.pim', self.itsView).trashCollection

        if source is None:
            set = EmptySet()
        elif (isinstance(source, WrapperCollection) and
              trash not in source.sources):
            # bug 5899 - alpha2 workaround: When SmartCollections are
            # wrapped with IntersectionCollection/UnionCollection,
            # they drop the trash. So we artificially insert it back
            set = Difference(source, trash)
        else:
            set = Set(source)

        setattr(self, self.__collection__, set)
        return set

    def getCollectionIndex(self, indexName=None, attributes=None):
        """
        Get the index. If it doesn't exist, create. Also create a RangeSet
        for storing the selection on the index

        If the C{indexName} attribute of this collection is set to
        "__adhoc__" then a numeric index will be created.  Otherwise
        the C{indexName} attribute should contain the name of the
        attribute (of an item) to be indexed.
        """
        if indexName is None:
            indexName = self.indexName
        
        if not self.hasIndex(indexName):
            if indexName == "__adhoc__":
                self.addIndex(indexName, 'numeric')
            else:
                # for 0.7alpha2, hardcode 'date' as a secondary sort
                # for any query
                attributes = attributes or (indexName, 'date')
                self.addIndex(indexName, 'attribute', attributes=attributes)
            self.setRanges(indexName, [])
        return self.getIndex(indexName)

    def setCollectionIndex(self, newIndexName, toggleDescending=False, attributes=None):
        """
        Switches to a different index, bringing over the selection to
        the new index.

        If toggleDescending is C{True}, then when the indexName is set
        to the current indexName, the sort will toggle its Descending
        status, and reset the selection to match.
        """

        # assuming that we'll have to redo selection when sort is reversed?
        currentIndexName = self.indexName

        newIndex = self.getCollectionIndex(newIndexName, attributes)


        if currentIndexName != newIndexName:
            # new index - bring over the items one by one
            self.setRanges(newIndexName, [])

            for item in self.iterSelection():
                newItemIndex = self.positionInIndex(newIndexName, item)
                self.addRange(newIndexName, (newItemIndex, newItemIndex))
                
            self.indexName = newIndexName
        elif toggleDescending:
            itemMax = len(self) - 1
            newRanges = []
            # build the ranges in reverse, so the resulting ranges are
            # in order
            for start,end in reversed(self.getSelectionRanges()):
                (newStart, newEnd) = (itemMax - end, itemMax - start)
                newRanges.append((newStart, newEnd))

            self.setDescending (currentIndexName, not self.isDescending(currentIndexName))
            self.setSelectionRanges(newRanges)

    def __len__(self):

        return len(self.getCollectionIndex())

    def moveItemToLocation (self, item, location):
        """
        Moves an item to a new C{location} in an __adhoc__ index.
        """
        if location == 0:
            # Get the index. It's necessary to get the length, and if
            # it doesn't exist getCollectionIndex will create it.
            self.getCollectionIndex()
            before = None
        else:
            before = self [location - 1]
        self.placeInIndex(item, before, self.indexName)             

    #
    # General selection methods
    # 

    def isSelectionEmpty(self):
        return len(self.getSelectionRanges()) == 0

    def clearSelection(self):
        return self.setSelectionRanges([])

    #
    # Range-based selection methods
    # 

    def getSelectionRanges(self):
        """
        Return the ranges associated with the current index as an
        array of tuples, where each tuple represents a start and
        end of the range.
        """
        return self.getCollectionIndex().getRanges()
        
    def setSelectionRanges(self, ranges):
        """
        Sets the ranges associated with the current index with
        C{ranges} which should be an array of tuples, where each
        tuple represents a start and end of the range.  The C{ranges}
        must be sorted ascending, non-overlapping and postive.
        """
        self.setRanges(self.indexName, ranges)

    def isSelected(self, range):
        """
        Returns C{True} if the C{range} is completely inside the selected
        ranges of the index.  C{range} may be a tuple: (start, end) or
        an integer index, where negative indexing works like Python
        indexing.
        """
        return self.getCollectionIndex().isInRanges(range)

    def addSelectionRange(self, range):
        """
        Selects a C{range} of indexes. C{range} may be a tuple:
        (start, end) or an integer index, where negative indexing
        works like Python indexing.
        """
        self.addRange(self.indexName, range)

    def removeSelectionRange(self, range):
        """
        Unselects a C{range} of indexes. C{range} may be a tuple:
        (start, end) or an integer index, where negative indexing
        works like Python indexing.
        """
        self.removeRange(self.indexName, range)
    #
    # Item-based selection methods
    #
    
    def setSelectionToItem(self, item):
        """
        Sets the entire selection to include only the C{item}.
        """
        index = self.index (item)
        self.setRanges(self.indexName, [(index, index)])

    def getFirstSelectedItem(self):
        """
        Returns the first selected item in the index or C{None} if
        there is no selection.
        """
        index = self.getCollectionIndex()._ranges.firstSelectedIndex()
        if index == None:
            return None
        return self[index]

    def isItemSelected(self, item):
        """
        Returns C{True}/C{False} based on if the item is actually
        selected or not
        """
        return self.isSelected(self.index(item))

    def iterSelection(self):
        """
        Generator to get the selection.
        """
        ranges = self.getSelectionRanges()
        if ranges is not None:
            for start,end in ranges:
                for idx in range(start,end+1):
                    yield self[idx]

    def selectItem(self, item):
        """
        Selects an C{item} in the index.
        """
        self.addSelectionRange (self.index (item))

    def unselectItem(self, item):
        """
        Unselects an C{item} in the index.
        """
        self.removeSelectionRange (self.index (item))

    #
    # index-based methods
    #

    def __getitem__(self, index):
        """
        Support indexing using [].
        """
        # Get the index. It's necessary to get the length, and if it doesn't exist
        # getCollectionIndex will create it.
        self.getCollectionIndex()
        return self.getByIndex(self.indexName, index)

    def index(self, item):
        """
        Return the position of item in the index.
        """

        # Get the index. It's necessary to get the length, and if it doesn't
        # exist getCollectionIndex will create it.

        self.getCollectionIndex()
        return self.positionInIndex(self.indexName, item)

    def add(self, item):
        self.source.add(item)

    def clear(self):
        self.source.clear()

    def first(self):
        return self.source.first()

    def remove(self, item):
        self.source.remove(item)

    def empty(self):
        self.source.empty()
