""" Classes used for contentmodel parcel and kinds.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.parcel.Parcel as Parcel
import repository.item.Item as Item

ContentItemParent = None
ContentItemKind = None
ProjectKind = None
GroupKind = None

class ContentModel(Parcel.Parcel):
    def __init__(self, name, parent, kind):
        Parcel.Parcel.__init__(self, name, parent, kind)

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

        global ContentItemParent
        ContentItemParent = parent
        assert ContentItemParent

        global ContentItemKind
        ContentItemKind = repository.find('//parcels/OSAF/contentmodel/ContentItem')
        assert ContentItemKind

        global ProjectKind
        ProjectKind = repository.find('//parcels/OSAF/contentmodel/Project')
        assert ProjectKind

        global GroupKind
        GroupKind = repository.find('//parcels/OSAF/contentmodel/Group')
        assert GroupKind

class ContentItem(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentItemParent
        if not kind:
            kind = ContentItemKind
        Item.Item.__init__(self, name, parent, kind)
        self.projects = []
        self.groups = []

class Project(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentItemParent
        if not kind:
            kind = ProjectKind
        Item.Item.__init__(self, name, parent, kind)
        self.itemsInProject = []
        self.name = ''

class Group(ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentItemParent
        if not kind:
            kind = GroupKind
        ContentItem.__init__(self, name, parent, kind)
        self.itemsInGroup = []
        self.name = ''
    
    
