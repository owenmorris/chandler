__date__ = "$Date: 2005-07-08 00:29:48Z $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.pim"

from application import schema
from repository.item.Sets import Set, Union, Intersection, Difference, KindSet
from repository.item.Item import Item
from osaf.pim import items
import os

class NotifyHandler(schema.Item):
    """
    An item that exists only to handle notifications
    we should change notifications to work on callables -- John is cool with that.
    """
    log = schema.Sequence(initialValue=[])
    collectionEventHandler = schema.One(schema.String, initialValue="onCollectionEvent")

    def checkLog(self, op, item, other):
        if len(self.log) == 0:
            return False
        rec = self.log[-1]
        return rec[0] == op and rec[1] == item and rec[2] == "rep" and rec[3] == other and rec[4] == ()
    

    def onCollectionEvent(self, op, item, name, other, *args):
        self.log.append((op, item, name, other, args))

class SimpleItem(schema.Item):
    """
    A dirt simple item -- think content item here, if you like
    """

    label = schema.One(schema.String, displayName="My Label")

class OtherSimpleItem(schema.Item):
    """
    Another dirt simple item -- think content item here, if you like
    """

    label = schema.One(schema.String, displayName="My Label")

def mapChangesCallable(item, version, status, literals, references):
    """
    """
    try: # handle changes to items in a ListCollection
        if item.collections: 
            for i in item.collections:
                i.contentsUpdated(item)
    except AttributeError:
        try: # handle changes to items in an existing KindCollection
            # is the item in a kind collection?
            kc = item.itsView.findPath('//userdata/%sKindCollection' % item.getKind(item.itsView).itsName)
            if kc is not None:
                kc.contentsUpdated(item)
        except AttributeError:
            pass
    except Exception, e:
        print "Exception in mapChangesCallable ",e

class AbstractCollection(items.ContentItem):
    """
    """
    schema.kindInfo(
        displayName="AbstractCollection"
    )

    indexName   = schema.One(schema.String, initialValue="__adhoc__")
    renameable  = schema.One(schema.Boolean)

    invitees = schema.Sequence(
        "osaf.pim.mail.EmailAddress",
        doc="The people who are being invited to share in this item; filled "
            "in when the user types in the DV's 'invite' box, then cleared on "
            "send (entries copied to the share object).\n\n"
            "Issue: Bad that we have just one of these per item collection, "
            "though an item collection could have multiple shares post-0.5",
        otherName="inviteeOf",  # can't use inverse here while ItemCollection lives!
        initialValue=()
    )   

    # redirections 
    about = schema.Role(redirectTo="displayName")

    schema.addClouds(
        copying = schema.Cloud(
            invitees,
            byCloud=[items.ContentItem.contentsOwner]
        ),
        sharing = schema.Cloud( none = ["displayName"] ),
    )

    rep = schema.One(schema.TypeReference('//Schema/Core/AbstractSet'), initialValue=None)
    subscribers = schema.Sequence(initialValue=[])

    def __init__(self, *args, **kw):
        super(AbstractCollection, self).__init__(*args, **kw)
        self.subscribers = []

    def collectionChanged(self, op, item, name, other, *args):
        if op:
            # use mapChanges to propagate any updates (not add/removes) that
            # happened since the last
            self.itsView.mapChanges(mapChangesCallable, True)
            self.notifySubscribers(op, item, name, other, *args)

    def notifySubscribers(self, op, item, name, other, *args):
        for i in self.subscribers:
            method_name = getattr(i, "collectionEventHandler")
            method = getattr(i, method_name)
            method(op, item, name, other, *args)

    def contentsUpdated(self, item):
        pass

    def __iter__(self):
        for i in self.rep:
            yield i

    def size(self):
        return len(self.rep)

    # index delegates
    def addIndex(self, indexName, indexType, **kwds):
        return self.rep.addIndex(indexName, indexType, **kwds)

    def removeIndex(self, indexName):
        return self.rep.removeIndex(indexName)

    def setIndexDescending(self, indexName, descending=True):
        return self.rep.setDescending(indexName, descending)

    def getByIndex(self, indexName, position):
        return self.rep.getByIndex(indexName, position)

    def removeByIndex(self, indexName, position):
        return self.rep.removeByIndex(indexName, position)

    def insertByIndex(self, indexName, position, item):
        return self.rep.insertByIndex(indexName, position, item)

    def replaceByIndex(self, indexName, position, with):
        return self.rep.replaceByIndex(indexName, position, with)
        
    def placeInIndex(self, item, after, *indexNames):
        return self.rep.placeInIndex(item, after, indexNames)
        
    def iterindexkeys(self, indexName):
        for key in self.rep.iterindexkeys(indexName):
            yield key
        
    def iterindexvalues(self, indexName):
        for value in self.rep.iterindexvalues(indexName):
            yield value
        
    def iterindexitems(self, indexName):
        for pair in self.rep.iterindexitems(indexName):
            yield pair
        
    def getIndexEntryValue(self, indexName, item):
        return self.rep.getIndexEntryValue(indexName, item)
        
    def setIndexEntryValue(self, indexName, item, value):
        return self.rep.setIndexEntryValue(indexName, item, value)
        
    def getIndexPosition(self, indexName, item):
        return self.rep.getIndexPosition(indexName, item)
        
    def firstInIndex(self, indexName):
        return self.rep.firstInIndex(indexName)
        
    def lastInIndex(self, indexName):
        return self.rep.lastInIndex(indexName)
        
    def nextInIndex(self, previous, indexName):
        return self.rep.nextInIndex(previous, indexName)

    def previousInIndex(self, next, indexName):
        return self.rep.previousInIndex(next, indexName)

class KindCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="KindCollection"
    )

    kind = schema.One(schema.TypeReference('//Schema/Core/Kind'), initialValue=None)

    def contentsUpdated(self, item):
#        print "KindCollection.contentsUpdated: ",item
        self._collectionChanged('changed' , 'rep', item)
        pass

    def onValueChanged(self, name):
        if name == "kind":
            try:
                self.rep = KindSet(self.kind)
            except AttributeError:
                pass

class ListCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="ListCollection"
    )

    refCollection = schema.Sequence(otherName=Item.collections,initialValue=[])

    def __init__(self, *args, **kw):
        super(ListCollection, self).__init__(*args, **kw)
        self.rep = Set((self,'refCollection'))
        self.refCollection = []

    def add(self, item):
        self.refCollection.append(item)

    def remove(self, item):
        self.refCollection.remove(item)

    def contentsUpdated(self, item):
        self._collectionChanged('changed' , 'rep', item)
        pass

class DifferenceCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="DifferenceCollection"
    )

    left = schema.One(AbstractCollection, initialValue=None)
    right = schema.One(AbstractCollection, initialValue=None)

    schema.addClouds(
        copying = schema.Cloud(byCloud=[left, right]),
    )

    def onValueChanged(self, name):
        if name == "left" or name == "right":
            try:
                if self.left != None and self.right != None:
                    self.rep = Difference((self.left, "rep"),(self.right, "rep"))
            except AttributeError:
                pass

class UnionCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="UnionCollection"
    )

    left = schema.One(AbstractCollection, initialValue=None)
    right = schema.One(AbstractCollection, initialValue=None)

    schema.addClouds(
        copying = schema.Cloud(byCloud=[left, right]),
    )

    def onValueChanged(self, name):
        if name == "left" or name == "right":
            try:
                if self.left != None and self.right != None:
                    self.rep = Union((self.left, "rep"),(self.right, "rep"))
            except AttributeError:
                pass

class IntersectionCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="IntersectionCollection"
    )

    left = schema.One(AbstractCollection, initialValue=None)
    right = schema.One(AbstractCollection, initialValue=None)

    schema.addClouds(
        copying = schema.Cloud(byCloud=[left, right]),
    )

    def onValueChanged(self, name):
        if name == "left" or name == "right":
            try:
                if self.left != None and self.right != None:
                    self.rep = Intersection((self.left, "rep"),(self.right, "rep"))
            except AttributeError:
                pass

class FilteredSet(Set):
    """
    """
    def __init__(self, source, expr):
        super(FilteredSet, self).__init__(source)
        self.filter = expr
    
    def __contains__(self, item):
        return self._sourceContains(item, self._source) and self.filter(item)

    def __iter__(self):
        for item in self._iterSource(self._source):
            if self.filter(item):
                yield item

    def sourceChanged(self, op, change, sourceOwner, sourceName, inner, other,
                      *args):
        op = self._sourceChanged(self._source, op, change,
                                 sourceOwner, sourceName, other, *args)

        if not (inner is True or op is None):
            item = self._item
            if item is not None:
                matched = self.filter(other)
                if op == 'changed': # changed is handled differently from normal
                    if matched:
                        op = 'add'
                    elif not matched and other in self:
                        op = 'remove'
                    else:
                        op = None
                elif not matched: # if we we fail the predicate, NOP
                    op = None
                item.collectionChanged(op, item, self._attribute, other)
                item._collectionChanged(op, self._attribute, other)

        return op

    def onValueChanged(self, name):
        pass

class FilteredCollection(AbstractCollection):
    """
    """
    schema.kindInfo(
        displayName="FilteredCollection"
    )

    source = schema.One(AbstractCollection, initialValue=None)
    filterExpression = schema.One(schema.String, initialValue="")

    schema.addClouds(
        copying = schema.Cloud(byCloud=[source]),
    )

    def onValueChanged(self, name):
        if name == "source" or name == "filterExpression":
            try:
                if self.source != None and self.filterExpression != "":
                    s = "lambda item: %s" % self.filterExpression
                    self.rep = FilteredSet((self.source, "rep"), eval(s))
            except AttributeError, ae:
                print ae
                pass
