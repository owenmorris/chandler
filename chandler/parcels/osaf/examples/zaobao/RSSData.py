__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
from osaf.contentmodel.ContentModel import ContentItem
import mx.DateTime
import feedparser


# sets a given attribute overriding the name with newattr
def SetAttribute(self, data, attr, newattr=None):
    if not newattr:
        newattr = attr
    value = data.get(attr)
    if value:
        type = self.getAttributeAspect(newattr, 'type', default=None)
        if type is not None:
            value = type.makeValue(value)
        self.setAttributeValue(newattr, value)

def SetAttributes(self, data, attributes):
    if isinstance(attributes, dict):
        for attr, newattr in attributes.iteritems():
            SetAttribute(self, data, attr, newattr=newattr)
    elif isinstance(attributes, list):
        for attr in attributes:
            SetAttribute(self, data, attr)


##
# RSSChannel
##
def NewChannelFromURL(view, url, update = True):
    data = feedparser.parse(url)

    if data['channel'] == {} or data['status'] == 404:
        return None

    channel = RSSChannel(view=view)
    channel.url = url

    if update:
        try:
            channel.Update(data)
        except:
            channel.delete()
            channel = None

    return channel

class RSSChannel(ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/examples/zaobao/RSSChannel"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super(RSSChannel, self).__init__(name, parent, kind, view)
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

        attrs = ['link', 'description', 'copyright', 'category', 'language']
        # @@@MOR attrs = ['link', 'description', 'copyright', 'creator', 'category', 'language']
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

        view = self.itsView
        for itemData in items:
            #print 'new item'
            rssItem = RSSItem(view=view)
            rssItem.Update(itemData)
            self.addValue('items', rssItem)

##
# RSSItem
##
class RSSItem(ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/examples/zaobao/RSSItem"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super(RSSItem, self).__init__(name, parent, kind, view)

    def Update(self, data):
        # fill in the item
        attrs = {'title':'displayName'}
        SetAttributes(self, data, attrs)

        attrs = ['link', 'category', 'author']
        # @@@MOR attrs = ['creator', 'link', 'category']
        SetAttributes(self, data, attrs)

        description = data.get('description')
        if description:
            self.content = self.getAttributeAspect('content', 'type').makeValue(description, indexed=True)

        date = data.get('date')
        if date:
            self.date = mx.DateTime.DateTimeFrom(str(date))
