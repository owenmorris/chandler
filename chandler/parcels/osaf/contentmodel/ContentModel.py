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

    # The parcel knows the UUID for the parent, once the parcel is loaded
    contentItemParentID = None
    
    def __init__(self, name, parent, kind):
        Parcel.Parcel.__init__(self, name, parent, kind)

    def _setUUIDs(self, parent):
        ContentModel.contentItemParentID = parent.getUUID()
        ContentModel.contentItemKindID = self.find('ContentItem').getUUID()
        ContentModel.projectKindID = self.find('Project').getUUID()
        ContentModel.groupKindID = self.find('Group').getUUID()

    def onItemLoad(self):
        super(ContentModel, self).onItemLoad()
        repository = self.getRepository()
        parent = repository.find('//userdata/contentitems')
        self._setUUIDs(parent)

    def startupParcel(self):
        Parcel.Parcel.startupParcel(self)
        repository = self.getRepository()
        parent = repository.find('//userdata/contentitems')
        if not parent:
            itemKind = repository.find('//Schema/Core/Item')
            userdata = repository.find('//userdata')
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

class ContentItem(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = ContentModel.getContentItemKind()
        Item.Item.__init__(self, name, parent, kind)
        self.projects = []
        self.groups = []

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
        Item.Item.__init__(self, name, parent, kind)
        self.itemsInProject = []
        self.name = ''

class Group(ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = ContentModel.getGroupKind()
        ContentItem.__init__(self, name, parent, kind)
        self.itemsInGroup = []
        self.name = ''
    
    
