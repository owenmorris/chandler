__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import application.Globals as Globals
from osaf.contentmodel.ContentModel import ContentItem
import mx.DateTime
import feedparser


def SetAttribute(self, data, attr, nattr=None):
    if not nattr:
        nattr = attr
    value = data.get(attr)
    if value:
        type = self.getAttributeAspect(nattr, 'type', default=None)
        if type is not None:
            value = type.makeValue(value)
        self.setAttributeValue(nattr, value)

def SetAttributes(self, data, attributes):
    if isinstance(attributes, dict):
        for attr, nattr in attributes.iteritems():
            SetAttribute(self, data, attr, nattr=nattr)
    elif isinstance(attributes, list):
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
    myKindID = None
    myKindPath = "//parcels/osaf/examples/zaobao/RSSChannel"

    def __init__(self, name=None, parent=None, kind=None):
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

        for itemData in items:
            #print 'new item'
            item = RSSItem()
            item.Update(itemData)
            self.addValue('items', item)


##
# RSSItem
##
class RSSItem(ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/examples/zaobao/RSSItem"

    def __init__(self, name=None, parent=None, kind=None):
        super(RSSItem, self).__init__(name, parent, kind)

    def Update(self, data):
        # fill in the item
        attrs = {'title':'displayName'}
        SetAttributes(self, data, attrs)

        attrs = ['link', 'category']
        # @@@MOR attrs = ['creator', 'link', 'category']
        SetAttributes(self, data, attrs)

        description = data.get('description')
        if description:
            self.content = self.getAttributeAspect('content', 'type').makeValue(description, indexed=True)

        date = data.get('date')
        if date:
            self.date = mx.DateTime.DateTimeFrom(str(date))
