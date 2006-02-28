__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.pim"

import logging, os, re

from application import schema
from repository.item.Sets import \
    Set, MultiUnion, Union, MultiIntersection, Intersection, Difference, \
    KindSet, FilteredSet
from repository.item.Collection import Collection

from osaf.pim.items import ContentItem
from osaf.pim.structs import ColorType

logger = logging.getLogger(__name__)
DEBUG = logger.getEffectiveLevel() <= logging.DEBUG


class CollectionColors(schema.Item):
    """
    Temporarily put the CollectionColors here until we refactor collection
    to remove display information
    """
    colors           = schema.Sequence (ColorType)
    colorIndex       = schema.One (schema.Integer)

    def nextColor (self):
        color = self.colors [self.colorIndex]
        self.colorIndex += 1
        if self.colorIndex == len (self.colors):
            self.colorIndex = 0
        return color


class ContentCollection(ContentItem, Collection):
    """
    The base class for Chandler Collection types.

    ContentCollection instances are items wrapping a collection value and
    provide a C{subscribers} ref collection for clients to subscribe to their
    notifications. Subscriber items must provide a C{subscribesTo} inverse
    attribute and a method of the following signature:
        C{onCollectionNotification(op, collection, name, item)}
    where C{op} is one of C{add}, C{remove}, C{refresh} or C{changed},
    C{collection} is the Collection item, C{name} is the attribute
    containing the collection value and C{item} the item in the collection
    that was added, removed, refreshed or changed.

    This class is abstract. Base concrete subclasses must use the
    C{schema.CollectionClass} metaclass and declare the collection attribute
    and its name as in the examples below:

        __metaclass__ = schema.CollectionClass
        __collection__ = 'ex1'

        ex1 = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))

    or:

        __metaclass__ = schema.CollectionClass
        __collection__ = 'ex2'

        ex2 = schema.Sequence(otherName='ex2_collections', initialValue=[])

    The type of collection value chosen (as declared above) determines which
    methods are delegated from this item to the collection value, typically
    an AbstractSet subclass instance or a RefList instance.
    """

    schema.kindInfo(
        displayName=u"ContentCollection"
    )

    """
      The following collection attributes may be moved once the dust
    settles on pje's external attribute mechanism
    """
    renameable              = schema.One(schema.Boolean, defaultValue = True)
    color                   = schema.One(ColorType)
    iconName                = schema.One(schema.Text)
    iconNameHasKindVariant  = schema.One(schema.Boolean, defaultValue = False)
    colorizeIcon            = schema.One(schema.Boolean, defaultValue = True)
    dontDisplayAsCalendar   = schema.One(schema.Boolean, defaultValue = False)
    outOfTheBoxCollection   = schema.One(schema.Boolean, defaultValue = False)
    """
      A dictionary mapping a KindName string to a new displayName.
    """
    displayNameAlternatives = schema.Mapping (schema.Text)

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

    schema.addClouds(
        copying = schema.Cloud(
            invitees,
            byRef=['contentsOwner']
        ),
        sharing = schema.Cloud( none = ["displayName"] ),
    )

    def setup(self):
        """
        setup the color of a collection
        """
        if not hasattr (self, 'color'):
            self.color = schema.ns('osaf.pim', self.itsView).collectionColors.nextColor()
        return self


    def __str__(self):
        """ for debugging """
        return "<%s%s:%s %s>" %(type(self).__name__, "", self.itsName,
                                self.itsUUID.str16())

    def isReadOnly(self):
        """
        Return True iff participating in only read-only shares
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

    schema.kindInfo(
        displayName=u"KindCollection"
    )

    kind = schema.One(schema.TypeReference('//Schema/Core/Kind'))
    recursive = schema.One(schema.Boolean, defaultValue=False)

    def __init__(self, *args, **kwds):

        super(KindCollection, self).__init__(*args, **kwds)
        setattr(self, self.__collection__, KindSet(self.kind, self.recursive))


def installParcel(parcel, old_version = None):
    """
    Parcel install time hook
    """
    pass


class ListCollection(ContentCollection):
    """
    A ContentCollection that contains only those items that are explicitly
    added to it. 

    Items in a ContentCollection are iterated over in order of insertion.

    A ListCollection is backed by a ref collection.
    """

    __metaclass__ = schema.CollectionClass
    __collection__ = 'refCollection'

    refCollection = schema.Sequence(otherName='collections', initialValue=[])

    schema.kindInfo(
        displayName=u"ListCollection"
    )

    trashFor = schema.Sequence('InclusionExclusionCollection',
                               otherName='trash', initialValue=[])

    def empty(self):
        for item in self:
            item.delete(True)


class DifferenceCollection(ContentCollection):
    """
    A ContentCollection containing the set theoretic difference of two
    ContentCollections.

    The C{sources} attribute (a list) contains the ContentCollection
    instances to be differenced.
    """

    __metaclass__ = schema.CollectionClass
    __collection__ = 'set'

    set = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))

    schema.kindInfo(
        displayName=u"DifferenceCollection"
    )

    sources = schema.Sequence(ContentCollection, initialValue=[])

    schema.addClouds(
        copying = schema.Cloud(byCloud=[sources]),
    )

    def __init__(self, *args, **kwds):

        super(DifferenceCollection, self).__init__(*args, **kwds)

        a, b = self.sources
        setattr(self, self.__collection__,
                Difference((a, a.__collection__), (b, b.__collection__)))


class UnionCollection(ContentCollection):
    """
    A ContentCollection containing the set theoretic union of at least two
    ContentCollections.

    The C{sources} attribute (a list) contains the ContentCollection
    instances to be unioned.
    """

    __metaclass__ = schema.CollectionClass
    __collection__ = 'set'

    set = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))

    schema.kindInfo(
        displayName=u"UnionCollection"
    )

    sources = schema.Sequence(ContentCollection, initialValue=[])

    schema.addClouds(
        copying = schema.Cloud(byCloud=[sources]),
    )

    def __init__(self, *args, **kwds):

        super(UnionCollection, self).__init__(*args, **kwds)
        self._sourcesChanged()
                
    def _sourcesChanged(self):

        if len(self.sources) == 2:
            a, b = self.sources
            set = Union((a, a.__collection__), (b, b.__collection__))
        else:
            set = MultiUnion(*[(i, i.__collection__) for i in self.sources])

        setattr(self, self.__collection__, set)

    def addSource(self, source):

        if source not in self.sources:
            self.sources.append(source)
            self._sourcesChanged()

            view = self.itsView
            sourceChanged = getattr(self, self.__collection__).sourceChanged
            for uuid in source.iterkeys():
                view._notifyChange(sourceChanged, 'add', 'collection',
                                   source, source.__collection__, False, uuid)

    def removeSource(self, source):

        if source in self.sources:
            view = self.itsView
            sourceChanged = getattr(self, self.__collection__).sourceChanged
            for uuid in source.iterkeys():
                view._notifyChange(sourceChanged, 'remove', 'collection',
                                   source, source.__collection__, False, uuid)

            self.sources.remove(source)
            self._sourcesChanged()


class IntersectionCollection(ContentCollection):
    """
    A ContentCollection containing the set theoretic intersection of at
    least 2 ContentCollections.

    The C{sources} attribute (a list) contains the ContentCollection
    instances to be intersected.
    """

    __metaclass__ = schema.CollectionClass
    __collection__ = 'set'

    set = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))

    schema.kindInfo(
        displayName=u"IntersectionCollection"
    )

    sources = schema.Sequence(ContentCollection, initialValue=[])

    schema.addClouds(
        copying = schema.Cloud(byCloud=[sources]),
    )

    def __init__(self, *args, **kwds):

        super(IntersectionCollection, self).__init__(*args, **kwds)

        if len(self.sources) == 2:
            a, b = self.sources
            set = Intersection((a, a.__collection__), (b, b.__collection__))
        else:
            set = MultiIntersection(*[(i, i.__collection__)
                                      for i in self.sources])

        setattr(self, self.__collection__, set)


# regular expression for finding the attribute name used by
# hasLocalAttributeValue
delPat = re.compile(".*(hasLocalAttributeValue|hasTrueAttributeValue)\(([^\)]*)\).*")

class FilteredCollection(ContentCollection):
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

    __metaclass__ = schema.CollectionClass
    __collection__ = 'set'

    set = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))

    schema.kindInfo(
        displayName=u"FilteredCollection"
    )

    source = schema.One(ContentCollection, initialValue=None)
    filterExpression = schema.One(schema.Text, initialValue="")
    filterAttributes = schema.Sequence(schema.Text, initialValue=[])

    schema.addClouds(
        copying = schema.Cloud(byCloud=[source]),
    )

    def __init__(self, *args, **kwds):

        super(FilteredCollection, self).__init__(*args, **kwds)

        # see if the expression contains hasLocalAttributeValue
        m = delPat.match(self.filterExpression)
        if m:
            delatt = m.group(2)
            if delatt is not None:
                # strip leading quotes
                if delatt.startswith("'") or delatt.startswith('"'):
                    delatt = delatt[1:-1] 
                delatt = [ delatt.replace("item.","") ]
        else:
            delatt = []

        # build a set of (item, monitor-operation) tuples
        attrTuples = set()
        for i in self.filterAttributes:
            attrTuples.add((i, "set"))
            for j in delatt:
                attrTuples.add((j, "remove"))

        setattr(self, self.__collection__,
                FilteredSet((self.source, self.source.__collection__),
                            self.filterExpression, tuple(attrTuples)))


class InclusionExclusionCollection(ContentCollection):
    """
    InclusionExclusionCollections implement inclusions, exclusions, source,
    and trash along with methods for add and remove
    """

    __metaclass__ = schema.CollectionClass
    __collection__ = 'set'

    set = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))

    inclusions = schema.One(ContentCollection)
    exclusions = schema.One(ContentCollection)
    sources = schema.Sequence(ContentCollection, initialValue=[])
    trash = schema.One(ListCollection, otherName='trashFor', initialValue=None)

    schema.addClouds(
        copying = schema.Cloud(byCloud=[sources]),
    )

    def add (self, item):
        """
          Add an item to the collection
        """
        if DEBUG:
            logger.debug("Adding %s to %s...",
                         item.getItemDisplayName().encode('ascii', 'replace'),
                         self.getItemDisplayName().encode('ascii', 'replace'))
        self.inclusions.add(item)

        if item in self.exclusions:
            if DEBUG:
                logger.debug("...removing from exclusions (%s)",
                             self.exclusions.getItemDisplayName().encode('ascii', 'replace'))
            self.exclusions.remove(item)

        # If a trash is associated with this collection, remove the item
        # from the trash.  This has the additional benefit of having the item
        # reappear in any collection which has the item in its inclusions

        if self.trash is not None and item in self.trash:
            if DEBUG:
                logger.debug("...removing from trash (%s)",
                             self.trash.getItemDisplayName().encode('ascii', 'replace'))
            self.trash.remove(item)

        if DEBUG:
            logger.debug("...done adding %s to %s",
                         item.getItemDisplayName().encode('ascii', 'replace'),
                         self.getItemDisplayName().encode('ascii', 'replace'))

    def remove (self, item):
        """
          Remove an item from the collection
        """

        if DEBUG:
            logger.debug("Removing %s from %s...",
                         item.getItemDisplayName().encode('ascii', 'replace'),
                         self.getItemDisplayName().encode('ascii', 'replace'))

        # Before we actually add this item to our exclusions list, let's see
        # how many other collections (that share our trash) this item is in.
        # If the item is only in this collection, we'll add it to the trash
        # later on.  We need to make this check now because in the following
        # step when we add the item to our exclusions list, that could
        # immediately add the item to the All collection which would be bad.
        # Bug 4551

        addToTrash = False
        if self.trash is not None:
            addToTrash = True
            for collection in self.trash.trashFor:
                if collection is not self and item in collection:
                    addToTrash = False
                    break

        if DEBUG:
            logger.debug("...adding to exclusions (%s)",
                         self.exclusions.getItemDisplayName().encode('ascii', 'replace'))
        self.exclusions.add (item)

        if item in self.inclusions:
            if DEBUG:
                logger.debug("...removing from inclusions (%s)",
                             self.inclusions.getItemDisplayName().encode('ascii', 'replace'))
            self.inclusions.remove (item)

        if addToTrash:
            if DEBUG:
                logger.debug("...adding to trash (%s)",
                             self.trash.getItemDisplayName().encode('ascii', 'replace'))
            self.trash.add(item)

        if DEBUG:
            logger.debug("...done removing %s from %s",
                         item.getItemDisplayName().encode('ascii', 'replace'),
                         self.getItemDisplayName().encode('ascii', 'replace'))

    def setup(self, source=None, exclusions=None,  trash="trashCollection"):
        """
        setup all the extra parts of a InclusionExclusionCollection. Sets the
        color, source, exclusions and trash collections. source, exclusions and
        trash may be collections or strings. If they are strings, then the
        corresponding collection is looked up in the osaf.pim namespace
        """

        def collectionLookup (collection):
            if isinstance (collection, str):
                collection = getattr (pimNameSpace, collection)
            return collection

        pimNameSpace = schema.ns('osaf.pim', self.itsView)
        
        source = collectionLookup (source)
        exclusions = collectionLookup (exclusions)
        trash = collectionLookup (trash)

        super (InclusionExclusionCollection, self).setup()

        self.inclusions = ListCollection(itsParent=self,
                                         displayName=u"(Inclusions)")
        if source is None:
            innerSource = self.inclusions
        else:
            innerSource = UnionCollection(itsParent=self,
                                          displayName=u"(Union of source and inclusions)",
                                          sources=[source, self.inclusions])

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

        if trash is not None:
            outerSource = DifferenceCollection(itsParent=self,
                                               displayName=u"(Difference between source and trash)",
                                               sources=[innerSource, trash])
            self.trash = trash
        else:
            outerSource = innerSource
            self.trash = exclusions

        self.sources = [outerSource, exclusions]
        setattr(self, self.__collection__,
                Difference((outerSource, outerSource.__collection__),
                           (exclusions, exclusions.__collection__)))

        return self


class IndexedSelectionCollection(ContentCollection):
    """
    A collection that adds an index, e.g.for sorting items, a
    selection and visibility attribute to another source collection.
    """

    __metaclass__ = schema.CollectionClass
    __collection__ = 'set'

    set = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))

    indexName   = schema.One(schema.Text, initialValue="__adhoc__")
    source      = schema.One(ContentCollection, defaultValue=None)

    def __init__(self, *args, **kwds):

        super(IndexedSelectionCollection, self).__init__(*args, **kwds)
        setattr(self, self.__collection__,
                Set((self.source, self.source.__collection__)))

    def getCollectionIndex(self):
        """
        Get the index. If it doesn't exist, create. Also create a RangeSet
        for storing the selection on the index

        If the C{indexName} attribute of this collection is set to
        "__adhoc__" then a numeric index will be created.  Otherwise
        the C{indexName} attribute should contain the name of the
        attribute (of an item) to be indexed.
        """
        if not self.hasIndex(self.indexName):
            if self.indexName == "__adhoc__":
                self.addIndex(self.indexName, 'numeric')
            else:
                self.addIndex(self.indexName, 'attribute', attribute=self.indexName)
            self.setRanges(self.indexName, [])
        return self.getIndex(self.indexName)

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

    def getSelectionRanges (self):
        """
        Return the ranges associated with the current index as an
        array of tuples, where each tuple representsa start and end of
        the range.
        """
        return self.getCollectionIndex().getRanges()
        
    def setSelectionRanges (self, ranges):
        """
        Sets the ranges associated with the current index with
        C(ranges) which should be an array of tuples, where each tuple
        represents a start and end of the range.  The ranges must be
        sorted ascending, non-overlapping and postive.
        """
        self.setRanges(self.indexName, ranges)

    def isSelected (self, range):
        """
        Returns True if the C(range) is completely inside the selected
        ranges of the index.  C(range) may be a tuple: (start, end) or
        an integer index, where negative indexing works like Python
        indexing.
        """
        return self.getCollectionIndex().isInRanges(range)

    def addSelectionRange (self, range):
        """
        Selects a C(range) of indexes. C(range) may be a tuple:
        (start, end) or an integer index, where negative indexing
        works like Python indexing.
        """
        self.addRange(self.indexName, range)

    def removeSelectionRange (self, range):
        """
        unselects a C(range) of indexes. C(range) may be a tuple:
        (start, end) or an integer index, where negative indexing
        works like Python indexing..
        """
        self.removeRange(self.indexName, range)
    #
    # Item-based selection methods
    #
    
    def setSelectionToItem (self, item):
        """
        Sets the entire selection to include only the C(item).
        """
        index = self.index (item)
        self.setRanges(self.indexName, [(index, index)])

    def getFirstSelectedItem (self):
        """
        Returns the first selected item in the index or None if there
        is no selection.
        """
        index = self.getCollectionIndex()._ranges.firstSelectedIndex()
        if index == None:
            return None
        return self[index]

    def isItemSelected(self, item):
        """
        returns True/False based on if the item is actually selected or not
        """
        return self.isSelected(self.index(item))

    def iterSelection(self):
        """
        Generator to get the selection
        """
        ranges = self.getSelectionRanges()
        if ranges is not None:
            for start,end in ranges:
                for idx in range(start,end+1):
                    yield self[idx]

    def selectItem (self, item):
        """
        Selects an C(item) in the index.
        """
        self.addSelectionRange (self.index (item))

    def unselectItem (self, item):
        """
        unSelects an C(item) in the index.
        """
        self.removeSelectionRange (self.index (item))

    #
    # index-based methods
    #

    def __getitem__ (self, index):
        """
        Support indexing using []
        """
        # Get the index. It's necessary to get the length, and if it doesn't exist
        # getCollectionIndex will create it.
        self.getCollectionIndex()
        return self.getByIndex(self.indexName, index)

    def index (self, item):
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
