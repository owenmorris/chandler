__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.contentmodel.ContentModel as ContentModel
import repository.query.Query as RepositoryQuery

class ItemCollection(ContentModel.ContentItem):

    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = Globals.repository.findPath("//parcels/osaf/contentmodel/ItemCollection")
        super (ItemCollection, self).__init__(name, parent, kind)

    def subscribe (self, callbackItem=None, callbackMethodName=None):
        """
          Subscribed ItemCollections will automatically results up to date. Optionally,
        you can specify a method on an item to be called when the results change. There
        may be more than one subscriber.
        """
        if not self.isPinned():
            self.setPinned()
            query = self.createRepositoryQuery()
            query.subscribe (self, "onItemCollectionChanged")
            self.notifyOfChanges ("multiple changes")
        if callbackItem is not None:
            self._callbacks [callbackItem.itsUUID] = callbackMethodName

    def createRepositoryQuery (self):
        self._callbacks = {} # transient
        self._query = RepositoryQuery.Query (Globals.repository) # transient
        self._updateCount = 0 # transient
        self.queryStringStale = True
        return self._query

    def unsubscribe (self, callbackItem=None):
        """
          If you don't specify a callbackItemUUID, all subscriptions will be removed.

          When an ItemCollections is unsubcribed, resultsStale may be inaccurate and
        the results will not be updated automatically. To update results on an unsubscribed
        ItemCollection, call updateResults.        
        """
        if callbackItem is None:
            self._callbacks = {}
        else:
            del self._callbacks [callbackItem.itsUUID]

        if len (self._callbacks) == 0:
            remainingSubscribers = self._query.unsubscribe (self)
            if remainingSubscribers == 0:
                del self._query
                del self._callbacks
                self.setPinned (False)
    
    def onItemCollectionChanged (self, action):
        self.resultsStale = True
        self.notifyOfChanges (action)

    def notifyOfChanges (self, action):
        if self.isPinned() and self._updateCount == 0:
            for callbackUUID in self._callbacks.keys():
                item = Globals.repository.find (callbackUUID)
                method = getattr (type(item), self._callbacks [callbackUUID])
                method (item, action)

    def add (self, item):
        """
          Add an item to the _inclusions
        """
        if item not in self._inclusions:
            self._inclusions.append (item)
            if item in self._exclusions:
                self._exclusions.remove (item)
            if item not in self._results:
                self._results.append (item)
            self.queryStringStale = True
            self.notifyOfChanges ("entered")

    def remove (self, item):
        """
          Remove an item from the _exclusions
        """
        if item not in self._exclusions:
            self._exclusions.append (item)
            if item in self._inclusions:
                self._inclusions.remove (item)
            if item in self._results:
                self._results.remove (item)
            self.queryStringStale = True
            self.notifyOfChanges ("exited")

    def addFilterKind (self, item):
        """
          Add an kind to the list of kinds to filter
        """
        kindPath = str (item.itsPath)
        if kindPath not in self._filterKinds:
            self._filterKinds.append (kindPath)
            self.queryStringStale = True
            self.notifyOfChanges ("exited")

    def removeFilterKind (self, item):
        """
          Remove an kind to the list of kinds to filter. If item = None remove all filters
        """
        if item:
            self._filterKinds.remove (str (item.itsPath))
        else:
            del self._filterKinds[:]
        self.queryStringStale = True
        self.notifyOfChanges ("entered")

    def beginUpdate (self):
        """
          When making lots of modifications to _inclusions, exclusion, rule or _filterKinds
        surround the changes with beginUpdate and endUpdate to avoid causing each change
        to send a separate notification as in:

          itemCollection.beginUpdate()
          try:
              for item in list:
                  itemCollection.add (item)
          finally:
              itemCollection.endUpdate()

          Don't call beginUpdate unless the ItemCollection is subscribed.
        """
        self._updateCount += 1

    def endUpdate (self):
        """
          See endUpdate.
        """
        self._updateCount -= 1
        if self._updateCount == 0:
            self.notifyOfChanges ("multiple changes")

    def getRule (self):
        return self._rule

    def setRule (self, value):
        """
          When setting the rule, make sure we set resultsStale and queryStringStale
        """
        self.resultsStale = True
        self.queryStringStale = True
        self._rule = value

    rule = property (getRule, setRule)

    def getResults (self):
        """
          Override getting results to make sure it isn't stale
        """
        if self.resultsStale or self.queryStringStale:
            self.updateResults()
        return self._results

    results = property (getResults)

    def updateResults (self):
        """
         Refresh the cached query results by executing the repository query if necessary
        """
        try:
            query = self._query
        except AttributeError:
            query = self.createRepositoryQuery()
            
        if self.queryStringStale:
            query.queryString, query.args = self.calculateQueryStringAndArgs()
            query.execute ()
            self.queryStringStale = False
            self.resultsStale = True
        if self.resultsStale or not self.isPinned():
            self._results = [index for index in query]
            self.resultsStale = False

    def calculateQueryStringAndArgs (self):
        args = {}
        rule = self._rule
        if len (self._inclusions):
            if rule:
                rule = "union (" + rule + ", for i in $0 where True)"
            else:
                rule = "for i in $0 where True"
            args ["$0"] = (self.itsUUID, "_inclusions")
        if rule:
            if len (self._exclusions):
                rule = "difference (" + rule + ", for i in $1 where True)"
                args ["$1"] = (self.itsUUID, "_exclusions")
            if len (self._filterKinds) != 0:
                for kindPath in self._filterKinds:
                    rule = "intersect (" + rule + ", for i in '" + kindPath + "' where True)"
        return (rule, args)

    def __len__ (self):
        return len (self.results)

    def __iter__ (self):
        for item in self.results:
            yield item

    def __contains__ (self, item):
        return item in self.results

    def __getitem__ (self, index):
        iterator = iter(self.results)
        item = iterator.next()
        for count in xrange (index):
            item = iterator.next()
        return item

    def __delitem__(self, index):
        self.remove (self.results [index])

    def index (self, item):
        index = 0
        for testItem in self.results:
            if testItem is item:
                return index
            index += 1
        raise IndexError

