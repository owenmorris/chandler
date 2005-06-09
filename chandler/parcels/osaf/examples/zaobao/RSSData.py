__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.examples.zaobao.schema"

import application
from osaf.contentmodel.ContentModel import ContentItem
from osaf.contentmodel.ItemCollection import ItemCollection
from datetime import datetime
import time
from dateutil.parser import parse
import feedparser
import os, logging
from repository.item.Query import KindQuery

logger = logging.getLogger('ZaoBao')
logger.setLevel(logging.INFO)

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
    myKindPath = "//parcels/osaf/examples/zaobao/schema/RSSChannel"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super(RSSChannel, self).__init__(name, parent, kind, view)
        self.items = ItemCollection(view=view)

    def Update(self, data=None):
        logger.info("Updating channel: %s" % getattr(self, 'displayName',
                    self.url))

        etag = self.getAttributeValue('etag', default=None)
        lastModified = self.getAttributeValue('lastModified', default=None)
        if lastModified:
            lastModified = lastModified.timetuple()

        if not data:
            # fetch the data
            data = feedparser.parse(str(self.url), etag, lastModified)

        # set etag
        SetAttribute(self, data, 'etag')

        # set lastModified
        modified = data.get('modified')
        if modified:
            self.lastModified = datetime.fromtimestamp(time.mktime(modified)).replace(tzinfo=None)

        # if the feed is bad, raise the sax exception
        try:
            if data.bozo and not isinstance(data.bozo_exception, feedparser.CharacterEncodingOverride):
                logger.error("For url '%s', feedparser exception: %s" % (self.url, data.bozo_exception))
                raise data.bozo_exception
        except KeyError:
            print "Error"
            return

        self._DoChannel(data['channel'])
        count = self._DoItems(data['items'])
        if count:
            logger.info("...added %d RSSItems" % count)

    def addRSSItem(self, rssItem):
        """
            Add a single item, and add it to any listening collections
        """
        rssItem.channel = self
        self.items.add(rssItem)


    def _DoChannel(self, data):
        # fill in the item
        attrs = {'title':'displayName'}
        SetAttributes(self, data, attrs)
        self.items.displayName = self.displayName

        attrs = ['link', 'description', 'copyright', 'category', 'language']
        # @@@MOR attrs = ['link', 'description', 'copyright', 'creator', 'category', 'language']
        SetAttributes(self, data, attrs)

        date = data.get('date')
        if date:
            self.date = parse(str(date))

    def _DoItems(self, items):
        # make children

        # lets look for each existing item. This is ugly and is an O(n^2) problem
        # if the items are unsorted. Bleah.
        view = self.itsView

        count = 0

        for newItem in items:

            # Convert date to datetime object
            if newItem.date:
                newItem.date = parse(str(newItem.date))
            else:
                # Give the item a date so we can sort on it
                newItem.date = datetime.now()

            # Disregard timezone for now
            newItem.date = newItem.date.replace(tzinfo=None)

            found = False
            for oldItem in self.items.resultSet:
                # check to see if this doesn't already exist
                if oldItem.isSimilar(newItem):
                    found = True
                    oldItem.Update(newItem)
                    break

            if not found:
                # we have a new item - add it
                rssItem = RSSItem(view=view)
                rssItem.Update(newItem)
                try:
                    self.addRSSItem(rssItem)
                    count += 1
                except:
                    logger.error("Error adding an RSS item")

        return count

    def markAllItemsRead(self):
        for item in self.items:
            item.isRead = True

##
# RSSItem
##
class RSSItem(ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/examples/zaobao/schema/RSSItem"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super(RSSItem, self).__init__(name, parent, kind, view)
        self.displayName = "No Title"

    def Update(self, data):
        # fill in the item
        attrs = {'title':'displayName'}
        SetAttributes(self, data, attrs)

        attrs = ['link', 'category', 'author']
        # @@@MOR attrs = ['creator', 'link', 'category']
        SetAttributes(self, data, attrs)

        content = data.get('content')

        # Use the 'content' info first, falling back to what's in 'description'
        if content:
            content = content[0]['value']
        else:
            content = data.get('description')

        if content:
            self.content = self.getAttributeAspect('content', 'type').makeValue(content, indexed=True)

        self.date = data.date

    def isSimilar(self, feedItem):
        """
            Returns True if the two items are the same, False otherwise
            In this case, they're the same if title/link are the same, and
            if the feed item has a date, compare that too.
            Some feeds also define guids for items, so perhaps we should
            look at those too.
        """
        try:

            # If no date in the item, just consider it a matching date;
            # otherwise do compare datestamps:
            dateMatch = True
            haveFeedDate = 'date' in feedItem
            if haveFeedDate:
                if self.date != feedItem.date:
                    dateMatch = False

            if self.displayName == feedItem.title and \
               str(self.link) == feedItem.link and \
               dateMatch:
                    return True

        except:
            logger.error("RSS item comparison failed")

        return False
