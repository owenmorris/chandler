""" Classes used for contentmodel parcel and kinds.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.parcel.Parcel as Parcel
import repository.item.Item as Item

import application.Globals as Globals

class ContentModel(Parcel.Parcel):

    # The parcel knows the UUIDs for the Kinds, once the parcel is loaded
    contentItemKindID = None
    projectKindID = None
    groupKindID = None
    itemCollectionKindID = None

    # The parcel knows the UUID for the parent, once the parcel is loaded
    contentItemParentID = None
    
    def _setUUIDs(self, parent):
        ContentModel.contentItemParentID = parent.itsUUID

        ContentModel.contentItemKindID = self['ContentItem'].itsUUID
        ContentModel.projectKindID = self['Project'].itsUUID
        ContentModel.groupKindID = self['Group'].itsUUID
        ContentModel.itemCollectionKindID = self['ItemCollection'].itsUUID

    def onItemLoad(self):
        super(ContentModel, self).onItemLoad()
        repository = self.itsView
        parent = repository.findPath('//userdata/contentitems')
        self._setUUIDs(parent)

    def startupParcel(self):
        Parcel.Parcel.startupParcel(self)
        repository = self.itsView
        parent = repository.findPath('//userdata/contentitems')
        if not parent:
            itemKind = repository.findPath('//Schema/Core/Item')
            userdata = repository.getRoot('userdata')
            if not userdata:
                userdata = itemKind.newItem('userdata', repository)
            parent = itemKind.newItem('contentitems', userdata)
        self._setUUIDs(parent)

    def getContentItemParent(cls):
        assert cls.contentItemParentID, "ContentModel parcel not yet loaded"
        return Globals.repository[cls.contentItemParentID]

    getContentItemParent = classmethod(getContentItemParent)

    def getContentItemKind(cls):
        assert cls.contentItemKindID, "ContentModel parcel not yet loaded"
        return Globals.repository[cls.contentItemKindID]

    getContentItemKind = classmethod(getContentItemKind)

    def getProjectKind(cls):
        assert cls.projectKindID, "ContentModel parcel not yet loaded"
        return Globals.repository[cls.projectKindID]

    getProjectKind = classmethod(getProjectKind)
    
    def getGroupKind(cls):
        assert cls.groupKindID, "ContentModel parcel not yet loaded"
        return Globals.repository[cls.groupKindID]

    getGroupKind = classmethod(getGroupKind)

    def getItemCollectionKind(cls):
        assert cls.itemCollectionKindID, "ContentModel parcel not yet loaded"
        return Globals.repository[cls.itemCollectionKindID]

    itemCollectionKindID = classmethod(getItemCollectionKind)

class ContentItem(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = ContentModel.getContentItemKind()
        super (ContentItem, self).__init__(name, parent, kind)

    def getWho(self):
        """Returns a string representation of the whoAttribute"""

        if not self.hasAttributeValue(self.whoAttribute): return " "
        
        cardinality = self.getAttributeAspect(self.whoAttribute,
                                              'cardinality')
        if (cardinality == 'single'):
            whoString = str(self.getAttributeValue(self.whoAttribute))
        else:
            whoString = None
            for who in self.getAttributeValue(self.whoAttribute):
                if whoString:
                    whoString = "%s, %s" % (whoString,
                                            who.getItemDisplayName())
                else:
                    whoString = who.getItemDisplayName()

        if not whoString: return " "

        return whoString

    def getAbout(self):
        """Returns a string representation of the aboutAttribute"""
        if not self.hasAttributeValue(self.aboutAttribute): return " "
        
        aboutString = str(self.getAttributeValue(self.aboutAttribute))
        return aboutString

    def getDate(self):
        """Returns a string representation of the dateAttribute"""
        if not self.hasAttributeValue(self.dateAttribute): return " "
        
        date = self.getAttributeValue(self.dateAttribute)

        if not date: return " "
        
        dateString = date.Format("%B %d, %Y    %I:%M %p")
        return dateString

class Project(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = ContentModel.getProjectKind()
        super (Project, self).__init__(name, parent, kind)

class Group(ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = ContentModel.getGroupKind()
        super (Group, self).__init__(name, parent, kind)
    


class ItemCollection(Item.Item):
    def __init__(self, *args, **kwds):
        super(ItemCollection, self).__init__(*args, **kwds)

        # these are all Item attributes
        self.rule = None
        self.inclusions = []
        self.exclusions = []

        # our result cache
        self.results = []

        self.onItemLoad()

    def onItemLoad(self):
        # subscribe to query_changed notifications incase our query changes
        events = [Globals.repository.findPath('//parcels/osaf/framework/query_changed')]
        Globals.notificationManager.Subscribe(events, id(self), self._queryChangedCallback)

        # refresh the result cache
        self.__refresh()

    def onItemUnload(self):
        Globals.notificationManager.Unsubscribe(id(self))

    def _queryChangedCallback(self, notification):
        # if the query that changed is ours, we must refresh our result cache
        if self.rule:
            if notification.data['query'] == self.rule.itsUUID:
                self.__refresh()


    # python container functions
    def __nonzero__(self):
        return True

    def __len__(self):
        return len(self.results)

    def __iter__(self):
        repository = self.getRepositoryView()
        results = self.results
        for uuid in results:
            yield repository[uuid]

    def __contains__(self, item):
        return item.itsUUID in self.results

    def __getitem__(self, index):
        return self.getRepositoryView()[self.results[index]]

    def index(self, item):
        return self.results.index(item.itsUUID)

    # Inclusion and Exclusion APIs
    def include(self, item):
        uuid = item.itsUUID
        self.inclusions.append(uuid)

        if uuid not in self.results:
            self.results.append(uuid)
            self.__dirty()

    def removeInclusion(self, item):
        self.inclusions.remove(item.itsUUID)

        self.results.remove(uuid)
        self.__dirty()

    def exclude(self, item):
        uuid = item.itsUUID
        self.exclusions.append(uuid)

        if uuid in self.results:
            self.results.remove(uuid)
            self.__dirty()

    def removeExclusion(self, item):
        self.exclusions.remove(item.itsUUID)
        self.__refresh()


    # result cache building
    def __refresh(self):
        results = []

        inclusions = self.inclusions
        exclusions = self.exclusions
        rule = self.rule
        if not rule:
            rule = []

        for item in rule:
            uuid = item.itsUUID
            if uuid not in exclusions:
                results.append(uuid)

        for uuid in inclusions:
            if uuid not in exclusions:
                results.append(uuid)

        self.results = results

        self.__dirty()

    def __dirty(self):
        # post collection_changed notification
        self.getRepositoryView().findPath('//parcels/osaf/contentmodel/collection_changed').Post( {'collection' : self.itsUUID} )
