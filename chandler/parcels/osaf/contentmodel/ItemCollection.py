__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.contentmodel"

import application.Globals as Globals
from osaf.contentmodel import ContentModel
import repository.query.Query as Query
from chandlerdb.item.ItemError import NoSuchIndexError
from application import schema

class ItemCollection(ContentModel.ContentItem, Query.Query):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/ItemCollection"

    schema.kindInfo(
        displayName="Item Collection"
    )

    inclusions = schema.Sequence(
        ContentModel.ContentItem,
        inverse=ContentModel.ContentItem.itemCollectionInclusions,
        initialValue=(),
    )

    exclusions = schema.Sequence(
        ContentModel.ContentItem,
        inverse=ContentModel.ContentItem.itemCollectionExclusions,
        initialValue=(),
    )

    _rule       = schema.One(schema.String, initialValue="")
    kindFilter  = schema.Sequence(schema.String, initialValue=[])
    ruleIsStale = schema.One(schema.Boolean, initialValue=True)
    indexName   = schema.One(schema.String, initialValue="__adhoc__")
    renameable  = schema.One(schema.Boolean)

    source      = schema.Sequence(initialValue=())
    destination = schema.Sequence(inverse=source)

    invitees = schema.Sequence( #mail:EmailAddress
        doc="The people who are being invited to share in this item; filled "
            "in when the user types in the DV's 'invite' box, then cleared on "
            "send (entries copied to the share object).\n\n"
            "Issue: Bad that we have just one of these per item collection, "
            "though an item collection could have multiple shares post-0.5",
        otherName="inviteeOf",
        initialValue=()
    )   

    # redirections 
    about = schema.Role(redirectTo="displayName")

    def add (self, item):
        """
          Add an item to the inclusions. Optimize changes to inclusions and
        exclusions.
        """
        if item not in self.inclusions:
            self.inclusions.append (item)
            if item in self.exclusions:
                self.exclusions.remove (item)
            if item not in self._resultSet:
                self._resultSet.append (item)
            self.ruleIsStale = True

    def remove (self, item):
        """
          Remove an item from the exclusions. Optimize changes to inclusions and
        exclusions.
        """
        if item not in self.exclusions:
            if self._rule:
                self.exclusions.append (item)
            if item in self.inclusions:
                self.inclusions.remove (item)
            if item in self._resultSet:
                self._resultSet.remove (item)
            self.ruleIsStale = True

    def addFilterKind (self, item):
        """
          Add an kind to the list of kinds to filter
        """
        kindPath = str (item.itsPath)
        if kindPath not in self.kindFilter:
            self.kindFilter.append (kindPath)
            self.ruleIsStale = True

    def removeFilterKind (self, item):
        """
          Remove a kind from the list of kinds to filter. If item is not None remove all filters
        """
        if item is not None:
            self.kindFilter.remove (str (item.itsPath))
        else:
            del self.kindFilter[:]
        self.ruleIsStale = True

    def getRule (self):
        return self._rule

    def setRule (self, value):
        self._rule = value
        self.ruleIsStale = True

    rule = property (getRule, setRule)

    def _ensureQueryIsCurrent (self):
        """
           Make sure that we update the queryString if the rule is stale,
        then let our superclass handle its part.
        """
        if self.ruleIsStale:
            args = {}
            argNumber = 0
            newQueryString = self._rule
                
            for sourceItem in self.source:
                if newQueryString:
                    newQueryString = "union (" + newQueryString + ", for i in $" + str (argNumber) + " where True)"
                else:
                    newQueryString = "for i in $" + str (argNumber) + " where True"
                args ["$" + str (argNumber)] = (sourceItem.itsUUID, "_resultSet")
                argNumber += 1

            if len (self.inclusions):
                if newQueryString:
                    newQueryString = "union (" + newQueryString + ", for i in $" + str (argNumber) + " where True)"
                else:
                    newQueryString = "for i in $" + str (argNumber) + " where True"
                args ["$" + str (argNumber)] = (self.itsUUID, "inclusions")
                argNumber += 1

            if newQueryString:
                if len (self.exclusions) > 0:
                    newQueryString = "difference (" + newQueryString + ", for i in $" + str (argNumber) + " where True)"
                    args ["$" + str (argNumber) + ""] = (self.itsUUID, "exclusions")
                    argNumber += 1

                if len (self.kindFilter) > 0:
                    for kindPath in self.kindFilter:
                        newQueryString = "intersect (" + newQueryString + ", for i inevery '" + kindPath + "' where True)"
            self.queryString = newQueryString
            self.args = args
            self.ruleIsStale = False
        return super (ItemCollection, self)._ensureQueryIsCurrent ()

    def shareSend (self):
        """
          Share this Item, or Send it (if it's an Email)
        """
        # message the mainView to do the bulk of the work, showing progress
        Globals.views[0].postEventByName ('ShareItem', {'item': self})

    def __getitem__ (self, index):
        try:
            return self.resultSet.getByIndex (self.indexName, index)
        except NoSuchIndexError:
            self.createIndex()
            return self.resultSet.getByIndex (self.indexName, index)

    def __delitem__(self, index):
        self.remove (self.resultSet [index])

    def createIndex (self):
        if self.indexName == "__adhoc__":
            self.resultSet.addIndex (self.indexName, 'numeric')
        else:
            self.resultSet.addIndex (self.indexName, 'attribute', attribute=self.indexName)

    def index (self, item):
        try:
            return self.resultSet.getIndexPosition (self.indexName, item)
        except NoSuchIndexError:
            self.createIndex()
            return self.resultSet.getIndexPosition (self.indexName, item)

    def subscribe(self, *arguments, **keywords):
        for item in self.source:
            item.subscribe (self, "")
        super (ItemCollection, self).subscribe (*arguments, **keywords)

    def unsubscribe(self, *arguments, **keywords):
        super (ItemCollection, self).unsubscribe (*arguments, **keywords)
        for item in self.source:
            item.unsubscribe (self)

    def ExportItemData(self, clipboardHandler):
        # Create data for this kind of item in the clipboard handler
        # The data is used for Drag and Drop or Cut and Paste
        super(ItemCollection, self).ExportItemData (clipboardHandler)

        # Let the clipboard handler know we've got an ItemCollection to export
        clipboardHandler.ExportItemFormat(self, 'ItemCollection')

