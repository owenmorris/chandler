__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
from osaf.contentmodel.ContentModel import ContentItem
from osaf.contentmodel.ItemCollection import ItemCollection
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
            raise

    return channel

class RSSChannel(ItemCollection):
    myKindID = None
    myKindPath = "//parcels/osaf/examples/zaobao/RSSChannel"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super(RSSChannel, self).__init__(name, parent, kind, view)
        self.items = []

    def Update(self, data=None):
        etag = self.getAttributeValue('etag', default=None)
        lastModified = self.getAttributeValue('lastModified', default=None)
        if lastModified:
            lastModified = lastModified.tuple()

        if not data:
            # fetch the dat
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

    def addCollection(self, collection):
        """
            Add a new collection, and update it with the list of all known items to date
        """
        for rssItem in self.items:
            collection.add(rssItem)
            
        self.itemCollections.append(collection)
            
    def addRSSItem(self, rssItem):
        """
            Add a single item, and add it to any listening collections
        """
        self.addValue('items', rssItem)
        for collection in self.itemCollections:
            collection.add(rssItem)
        

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
                
        # lets look for each existing item. This is ugly and is an O(n^2) problem
        # if the items are unsorted. Bleah.
        view = self.itsView
        if len(items) == 0:
            return
            
        for newItem in items:
            found = False
            for oldItem in self.items:
                # check to see if this doesn't already exist
                if oldItem.isSimilar(newItem):
                    found = True
                    break
                    
            if not found:
                # we have a new item - add it
                rssItem = RSSItem(view=view)
                rssItem.Update(newItem)
                try: 
                    self.addRSSItem(rssItem)
                except Exception, e:
                    print "Error adding an item: " + str(e)
                    raise

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
            
    def isSimilar(self, feedItem):
        """
            Returns True if the two items are the same, False otherwise
        """
        try:
            haveLocalDate = self.hasLocalAttributeValue('date')
            haveFeedDate = 'date' in feedItem
            
            # not every item has a date, so if neither item has a date, then
            # in a sense their dates are equivalent
            if self.displayName == feedItem.title and \
                ((haveFeedDate and haveLocalDate and \
                  self.date == mx.DateTime.DateTimeFrom(str(feedItem.date))) or \
                  not haveFeedDate and not haveLocalDate):
                return True
            else:
                return False
        except Exception, e:
            print "oops: " + str(e)
            return False

            
