__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import application.Globals as Globals
from repository.item.Item import Item
from repository.util.Path import Path
from osaf.contentmodel.ContentModel import ContentItem
import mx.DateTime
import types
import feedparser

##
# ZaoBaoParcel
##
class ZaoBaoParcel(application.Parcel.Parcel):
    def _setUUIDs(self, parent):

        # hackery to avoid threading conflicts
        ZaoBaoParcel.RSSItemParentID = parent.itsUUID
        
        ZaoBaoParcel.RSSChannelKindID = self['RSSChannel'].itsUUID
        ZaoBaoParcel.RSSItemKindID = self['RSSItem'].itsUUID

    def onItemLoad(self):
        super(ZaoBaoParcel, self).onItemLoad()

        # @@@ hackery to avoid threading conflicts
        repository = self.itsView
        parent = repository.findPath('//userdata/zaobaoitems')
        
        self._setUUIDs(parent)

    def startupParcel(self):
        super(ZaoBaoParcel, self).startupParcel()

        # @@@ hackery to avoid threading conflicts
        # Create a separate parent for RSSItems
        repository = self.itsView
        parent = repository.findPath('//userdata/zaobaoitems')
        if not parent:
            itemKind = repository.findPath('//Schema/Core/Item')
            userdata = repository.getRoot('userdata')
            if not userdata:
                userdata = itemKind.newItem('userdata', repository)
            parent = itemKind.newItem('zaobaoitems', userdata)
        
        self._setUUIDs(parent)

    # @@@ hackery to avoid threading conflicts
    # Keep track of a separate parent for RSSItems

    def getRSSItemParent(cls):
        assert cls.RSSItemParentID, "ZaoBaoParcel not yet loaded"
        return Globals.repository[cls.RSSItemParentID]

    getRSSItemParent = classmethod(getRSSItemParent)

    def getRSSChannelKind(cls):
        assert cls.RSSChannelKindID, "ZaoBaoParcel not yet loaded"
        return Globals.repository[cls.RSSChannelKindID]

    getRSSChannelKind = classmethod(getRSSChannelKind)

    def getRSSItemKind(cls):
        assert cls.RSSItemKindID, "ZaoBaoParcel not yet loaded"
        return Globals.repository[cls.RSSItemKindID]

    getRSSItemKind = classmethod(getRSSItemKind)
    
    # The parcel knows the UUIDs for the Kinds, once the parcel is loaded
    RSSChannelKindID = None
    RSSItemKindID = None


def SetAttribute(self, data, attr, nattr=None):
    if not nattr:
        nattr = attr
    value = data.get(attr)
    if value:
        self.setAttributeValue(nattr, value)

def SetAttributes(self, data, attributes):
    if type(attributes) == types.DictType:
        for attr, nattr in attributes.items():
            SetAttribute(self, data, attr, nattr=nattr)
    elif type(attributes) == types.ListType:
        for attr in attributes:
            SetAttribute(self, data, attr)


##
# RSSChannel
##
def NewChannelFromURL(url, update = True):
    data = feedparser.parse(url)

    if data['channel'] == {} or data['status'] == 404:
        return None

    channel = RSSChannel()
    channel.url = url

    if update:
        try:
            channel.Update(data)
        except:
            channel.delete()
            channel = None

    return channel

class RSSChannel(ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        # @@@ parent is hackery to avoid threading conflicts
        if not parent:
            parent = ZaoBaoParcel.getRSSItemParent()
        if not kind:
            kind = ZaoBaoParcel.getRSSChannelKind()
        super(RSSChannel, self).__init__(name, parent, kind)
        self.items = []

    def Update(self):
        etag = self.getAttributeValue('etag', default=None)
        lastModified = self.getAttributeValue('lastModified', default=None)
        if lastModified:
            lastModified = lastModified.tuple()

        # fetch the data
        data = feedparser.parse(str(self.url), etag, lastModified)

        # set etag
        SetAttribute(self, data, 'etag')

        # set lastModified
        modified = data.get('modified')
        if modified:
            self.lastModified = mx.DateTime.mktime(modified)

        # if the feed is bad, raise the sax exception
        try:
            if data['bozo'] == 1:
                raise data['bozo_exception']
        except KeyError:
            return

        self._DoChannel(data['channel'])
        self._DoItems(data['items'])

    def _DoChannel(self, data):
        # fill in the item
        attrs = {'title':'displayName'}
        SetAttributes(self, data, attrs)

        attrs = ['link', 'description', 'copyright', 'creator', 'category', 'language']
        SetAttributes(self, data, attrs)

        date = data.get('date')
        if date:
            self.date = mx.DateTime.DateTimeFrom(str(date))

    def _DoItems(self, items):
        # make children
        #print 'len items:', len(items)

        # XXX because feedparser is currently broken and gives us
        # all new entries when a feed changes, we need to delete
        # all the existing items
        if len(items) > 0:
            for item in self.items:
                item.delete()

        for itemData in items:
            #print 'new item'
            item = RSSItem()
            item.Update(itemData)
            self.addValue('items', item)


##
# RSSItem
##
class RSSItem(ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        # @@@ parent is hackery to avoid threading conflicts
        if not parent:
            parent = ZaoBaoParcel.getRSSItemParent()
        if not kind:
            kind = ZaoBaoParcel.getRSSItemKind()
        super(RSSItem, self).__init__(name, parent, kind)

    def Update(self, data):
        # fill in the item
        attrs = {'title':'displayName'}
        SetAttributes(self, data, attrs)

        attrs = ['creator', 'link', 'category']
        SetAttributes(self, data, attrs)

        description = data.get('description')
        if description:
            self.content = self.getAttributeAspect('content', 'type').makeValue(description, indexed=True)

        date = data.get('date')
        if date:
            self.date = mx.DateTime.DateTimeFrom(str(date))
