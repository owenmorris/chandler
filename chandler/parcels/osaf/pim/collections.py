__date__ = "$Date: 2005-07-08 00:29:48Z $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.pim"

from application import schema
from repository.item.Sets import Set, MultiUnion, Union, MultiIntersection, Difference, KindSet, FilteredSet
from repository.item.Item import Item
from chandlerdb.item.ItemError import NoSuchIndexError
from osaf.pim import items
import os

def mapChangesCallable(item, version, status, literals, references):
    """
    """

    # handle changes to items in a ListCollection
    if hasattr(item,'collections'): 
        for i in item.collections:
            i.contentsUpdated(item)
            break

    # handle changes to items in an existing KindCollection
    #@@@ this is not the most efficient way...
    kc = schema.ns("osaf.pim.collections", item.itsView).kind_collections
    for i in kc.collections:
        if item in i and hasattr(kc,'contentsUpdated'):
            kc.contentsUpdated(item)
            break

class AbstractCollection(items.ContentItem):
    """
    """
    schema.kindInfo(
        displayName="AbstractCollection"
    )

    indexName   = schema.One(schema.String, initialValue="__adhoc__")
    renameable  = schema.One(schema.Boolean)

    collectionList = schema.Sequence(
        'AbstractCollection',
        doc="Views, e.g. the Calendar, that display collections need to know "
            "which collection are combined to make up the calendar. collectionList"
            "is an optional parameter for this purpose.",
        defaultValue = []
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
    about = schema.Role(redirectTo="displayName")

    schema.addClouds(
        copying = schema.Cloud(
            invitees,
            byRef=['contentsOwner']
        ),
        sharing = schema.Cloud( none = ["displayName"] ),
    )

    rep = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'))
    subscribers = schema.Sequence(initialValue=[], otherName="subscribee")

    def collectionChanged(self, op, item, name, other, *args):
        if op:
            # use mapChanges to propagate any updates (not add/removes) that
            # happened since the last
            self.itsView.mapChanges(mapChangesCallable, True)
            self.notifySubscribers(op, item, name, other, *args)

    def notifySubscribers(self, op, item, name, other, *args):
        for i in self.subscribers:
            method_name = getattr(i, "collectionEventHandler", "onCollectionEvent")
            method = getattr(type(i), method_name)
            method(i, op, item, name, other, *args)

    def contentsUpdated(self, item):
        pass

    def __contains__(self, item):
        return self.rep.__contains__(item)

    def __iter__(self):
        for i in self.rep:
            yield i

    def __len__(self):
        try:
            return len(self.rep)
        except ValueError:
            self.createIndex()
            return len(self.rep)

    def createIndex (self):
        if self.indexName == "__adhoc__":
            self.rep.addIndex (self.indexName, 'numeric')
        else:
            self.rep.addIndex (self.indexName, 'attribute', attribute=self.indexName)

    def __getitem__ (self, index):
        try:
            return self.rep.getByIndex (self.indexName, index)
        except NoSuchIndexError:
            self.createIndex()
            return self.rep.getByIndex (self.indexName, index)

    def index (self, item):
        try:
            return self.rep.getIndexPosition (self.indexName, item)
        except NoSuchIndexError:
            self.createIndex()
            return self.resultSet.getIndexPosition (self.indexName, item)

class KindCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="KindCollection"
    )

    kind = schema.One(schema.TypeReference('//Schema/Core/Kind'), initialValue=None)
    recursive = schema.One(schema.Boolean, initialValue=False)
    directory = schema.One("KindCollectionDirectory", initialValue=None)

    def __init__(self, *args, **kw):
        super(KindCollection, self).__init__(*args, **kw)
        kc = schema.ns("osaf.pim.collections", self.itsView).kind_collections
        kc.collections.append(self)
    
    def contentsUpdated(self, item):
        self.rep.notify('changed', item)

    def onValueChanged(self, name):
        if name == "kind" or name == "recursive":
            self.rep = KindSet(self.kind, self.recursive)

class KindCollectionDirectory(schema.Item):
    collections = schema.Sequence(
        "KindCollection",
        inverse = KindCollection.directory,
        doc="all KindCollections - intended to be a singleton.  Use to propagate change notifications", initialValue=[])

def installParcel(parcel, old_version = None):
    KindCollectionDirectory.update(parcel, "kind_collections")

class ListCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="ListCollection"
    )

    refCollection = schema.Sequence(otherName='collections',initialValue=[])

    def __init__(self, *args, **kw):
        super(ListCollection, self).__init__(*args, **kw)
        self.rep = Set((self,'refCollection'))

    def add(self, item):
        self.refCollection.append(item)

    def clear(self):
        self.refCollection.clear()

    def first(self):
        self.refCollection.first()

    def remove(self, item):
        self.refCollection.remove(item)

    def contentsUpdated(self, item):
        self.rep.notify('changed', item)


class DifferenceCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="DifferenceCollection"
    )

    sources = schema.Sequence(AbstractCollection, initialValue=[])

    schema.addClouds(
        copying = schema.Cloud(byCloud=[sources]),
    )

    def onValueChanged(self, name):
        if name == "sources":
            if self.sources != None:
                assert len(self.sources) <= 2, "DifferenceCollection can only handle 2 sources"

                if len(self.sources) == 2:
                    self.rep = Difference((self.sources[0], "rep"),(self.sources[1], "rep"))

class UnionCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="UnionCollection"
    )

    sources = schema.Sequence(AbstractCollection, initialValue=[])

    schema.addClouds(
        copying = schema.Cloud(byCloud=[sources]),
    )

    def onValueChanged(self, name):
        if name == "sources":
            if self.sources != None and len(self.sources)> 1:
                if len(self.sources) == 2:
                    self.rep = Union((self.sources[0],"rep"),(self.sources[1],"rep"))
                else:
                    self.rep = MultiUnion(*[(i, "rep") for i in self.sources])


class IntersectionCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="IntersectionCollection"
    )

    sources = schema.Sequence(AbstractCollection, initialValue=[])

    schema.addClouds(
        copying = schema.Cloud(byCloud=[sources]),
    )

    def onValueChanged(self, name):
        if name == "sources":
            if self.sources != None and len(self.sources) > 1:
                self.rep = MultiIntersection(*[(i, "rep") for i in self.sources])

class FilteredCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="FilteredCollection"
    )

    source = schema.One(AbstractCollection, initialValue=None)
    filterExpression = schema.One(schema.String, initialValue="")
    filterAttributes = schema.Sequence(schema.String, initialValue=[])

    schema.addClouds(
        copying = schema.Cloud(byCloud=[source]),
    )

    def onValueChanged(self, name):
        if name == "source" or name == "filterExpression" or name =="filterAttributes":
            if self.source != None:
                try:
                    if self.filterExpression != "" and self.filterAttributes != []:

                        self.rep = FilteredSet((self.source, "rep"), self.filterExpression, self.filterAttributes)
                except AttributeError, ae:
                    pass


class InclusionExclusionCollection(UnionCollection):
    """
      User collections implement inclusions, exclusions and source sets along
    with methods for add and remove
    """
    def getInclusions (self):
        return self.sources[1]

    inclusions = property (getInclusions)

    def getExclusions (self):
        return self.sources[0].sources[1]

    exclusions = property (getExclusions)

    def getSource (self):
        return self.sources[0].sources[0]

    def setSource (self, value):
        self.sources[0].sources[0] = value

    source = property (getSource, setSource)

    def add (self, item):
        """
          Add an item to the inclusions. Optimize changes to inclusions and
        exclusions.
        """
        if item not in self.inclusions:
            self.inclusions.add (item)
            if item in self.exclusions:
                self.exclusions.remove (item)

    def remove (self, item):
        """
          Remove an item from the exclusions. Optimize changes to inclusions and
        exclusions.
        """
        if item not in self.exclusions:
            self.exclusions.add (item)
            if item in self.inclusions:
                self.inclusions.remove (item)

