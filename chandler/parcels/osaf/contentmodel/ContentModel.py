""" Classes used for contentmodel parcel and kinds.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application.Parcel import Parcel
import repository.item.Item as Item

import application.Globals as Globals

class ContentModel(Parcel):

    # The parcel knows the UUIDs for the Kinds, once the parcel is loaded
    contentItemKindID = None
    projectKindID = None
    groupKindID = None

    # The parcel knows the UUID for the parent, once the parcel is loaded
    contentItemParentID = None
    
    def _setUUIDs(self, parent):
        ContentModel.contentItemParentID = parent.itsUUID

        ContentModel.contentItemKindID = self['ContentItem'].itsUUID
        ContentModel.projectKindID = self['Project'].itsUUID
        ContentModel.groupKindID = self['Group'].itsUUID

    def onItemLoad(self):
        super(ContentModel, self).onItemLoad()
        repository = self.itsView
        parent = repository.findPath('//userdata/contentitems')
        self._setUUIDs(parent)

    def startupParcel(self):
        super(ContentModel, self).startupParcel()
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

class ContentItem(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.getContentItemParent()
        if not kind:
            kind = ContentModel.getContentItemKind()
        super (ContentItem, self).__init__(name, parent, kind)

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
    

