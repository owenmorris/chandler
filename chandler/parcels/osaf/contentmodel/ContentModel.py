""" Classes used for contentmodel parcel and kinds.
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.parcel.Parcel as Parcel
import repository.item.Item as Item

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
                itemKind.newItem('contentitems', userdata)

class ContentItem(Item.Item):
    def __init__(self, name, parent, kind):
        Item.Item.__init__(self, name, parent, kind)

class Project(Item.Item):
    def __init__(self, name, parent, kind):
        Item.Item.__init__(self, name, parent, kind)

class Group(ContentItem):
    def __init__(self, name, parent, kind):
        Item.Item.__init__(self, name, parent, kind)
    
    
