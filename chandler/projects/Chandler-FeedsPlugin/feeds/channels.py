#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

__all__ = ["FeedChannel", "FeedItem"]

__parcel__    = "feeds"

import time, logging, urllib
from datetime import datetime
from PyICU import ICUtzinfo, TimeZone
from osaf.pim.calendar.TimeZone import convertToICUtzinfo
from dateutil.parser import parse as dateutil_parse
from application import schema
from util import feedparser, indexes
from xml.sax import SAXParseException
from osaf import pim
from osaf.pim.notes import Note
from i18n import MessageFactory
from twisted.web import client
from twisted.internet import reactor
from osaf.pim.calendar.TimeZone import formatTime
from repository.util.URL import URL
from repository.util.Lob import Lob

_ = MessageFactory("Chandler-FeedsPlugin")

logger = logging.getLogger(__name__)

FETCH_FAILED = 0
FETCH_NOCHANGE = 1
FETCH_UPDATED = 2

def date_parse(s):
    """Parse using dateutil's parse, then convert to ICUtzinfo timezones."""
    return convertToICUtzinfo(dateutil_parse(s))

class FeedUpdateTaskClass:
    """
    This class implements a periodic task that checks and reads new feeds
    on 30 minutes interval.
    """
    
    def __init__(self, item):
        """
        This method initializes a periodic task for updating feeds.
        """
        # store our parcels view
        self.view = item.itsView
        
    def run(self):
        """
        This method implements a periodic task for updating feeds.
        """
        # update our view
        self.view.refresh(notify=False)
        # call refresh on all followed feed channels
        for channel in FeedChannel.iterItems(self.view):
            channel.refresh()
        # return true to keep the timer running
        return True

def setAttribute(self, data, attr, newattr=None):
    """
    This function sets a given attribute overriding the name with newattr.
    """
    if not newattr:
        newattr = attr
    value = data.get(attr)
    if value:
        type = self.getAttributeAspect(newattr, "type", None)
        if type is not None:
            value = type.makeValue(value)
        self.setAttributeValue(newattr, value)

def setAttributes(self, data, attributes):
    """
    This function sets a group, which can be a dictionary or a list, of attributes.
    """
    if isinstance(attributes, dict):
        for attr, newattr in attributes.iteritems():
            setAttribute(self, data, attr, newattr=newattr)
    elif isinstance(attributes, list):
        for attr in attributes:
            setAttribute(self, data, attr)

class ConditionalHTTPClientFactory(client.HTTPClientFactory):
    """
    This class implements HTTP network access services for retrieving RSS feeds.
    """

    def __init__(self, url, lastModified=None, etag=None, method="GET",
                 postdata=None, headers=None, agent="Chandler", timeout=0,
                 cookies=None, followRedirect=1):
        """
        This method initializes a HTTP conduict.
        """
        # optimize our server access by using the "Last-Modified" and
        # "ETag" fields of the HTTP request header.
        if lastModified or etag:
            if headers is None:
                headers = { }
            if lastModified:
                headers["if-modified-since"] = lastModified
            if etag:
                headers["if-none-match"] = etag
        # initialize a HTTP conduict...
        client.HTTPClientFactory.__init__(self, url, method=method,
            postdata=postdata, headers=headers, agent=agent, timeout=timeout,
            cookies=cookies, followRedirect=followRedirect)
        # ... and set a callback handler for failures.
        self.deferred.addCallback(
            lambda data: (data, self.status, self.response_headers)
        )

    def noPage(self, reason):
        """
        This method implements a callback for situations when an RSS feed
        could not be retrieved.
        """
        if self.status == "304":
            client.HTTPClientFactory.page(self, "")
        else:
            client.HTTPClientFactory.noPage(self, reason)


class FeedChannel(pim.ListCollection):
    """
    This class implements a feed channel collection that is visualized
    in the sidebar.
    """   
    #
    # FeedChannel repository interface
    #
    link = schema.One(schema.URL)
    category = schema.One(schema.Text)
    author = schema.One(schema.Text)
    date = schema.One(schema.DateTime)
    url = schema.One(schema.URL)
    etag = schema.One(schema.Text)
    lastModified = schema.One(schema.DateTime)
    copyright = schema.One(schema.Text)
    language = schema.One(schema.Text)
    ignoreContentChanges = schema.One(schema.Boolean, initialValue=False)
    isEstablished = schema.One(schema.Boolean, initialValue=False)
    isPreviousUpdateSuccessful = schema.One(schema.Boolean, initialValue=True)
    logItem = schema.One(initialValue=None)
    schema.addClouds(sharing = schema.Cloud(author, copyright, link, url))
    
    def __init__(self, *args, **kw):
        """
        This method initializes a feed channel.
        """
        super(FeedChannel, self).__init__(*args, **kw)
        self.addIndex("link", "value", attribute="link")
        
    def refresh(self, callback=None):
        """
        This method updates a feed channel content.
        """
        # Make sure we have the feedsView copy of the channel item
        feedsView = self.itsView
        feedsView.refresh(notify=False)
        item = feedsView.findUUID(self.itsUUID)
        return item.download().addCallback(item.feedFetchSuccess, callback).addErrback(
            item.feedFetchFailed, callback)

    def download(self):
        """
        This method uses a HTTP conduict to download an RSS channel feed.
        """
        url = str(self.url)
        etag = str(getattr(self, "etag", None))
        lastModified = getattr(self, "lastModified", None)
        if lastModified:
            lastModified = lastModified.strftime("%a, %d %b %Y %H:%M:%S %Z")

        (scheme, host, port, path) = client._parse(url)
        scheme = str(scheme)
        host = str(host)
        path = str(path)
        factory = ConditionalHTTPClientFactory(url=url,
            lastModified=lastModified, etag=etag, timeout=60)
        reactor.connectTCP(host, port, factory)

        return factory.deferred
    
    def feedFetchSuccess(self, info, callback=None):
        """
        This method implements a callback for succesful RSS feed downloads.
        """
        
        (data, status, headers) = info
        # getattr returns a unicode object which needs to be converted to
        # bytes for logging
        channel = getattr(self, "displayName", None)
        if channel is None:
            channel = str(self.url)
        else:
            channel = channel.encode("ascii", "replace")
            
        if not data:
            # Page hasn"t changed (304)
            logger.info("Channel has not changed: %s" % channel)
            return FETCH_NOCHANGE
        
        logger.info("Channel downloaded: %s" % channel)
        
        # set etag
        etag = headers.get("etag", None)
        if etag:
            self.etag = etag[0]
            
        # set lastModified
        lastModified = headers.get("last-modified", None)
        if lastModified:
            self.lastModified = date_parse(lastModified[0])
            
        count = self.parse(data)
        if count:
            logger.info("...added %d FeedItems" % count)
            
        self.isEstablished = True
        self.isPreviousUpdateSuccessful = True
        self.logItem = None
        
        self.itsView.commit()
        
        if callback:
            callback(self.itsUUID, True)
            
        return FETCH_UPDATED

    def feedFetchFailed(self, failure, callback=None):
        """
        This method implements a callback for failed RSS feed downloads.
        """
        # getattr returns a unicode object which needs to be converted to
        # bytes for logging
        channel = getattr(self, "displayName", None)
        if channel is None:
            channel = str(self.url)
        else:
            channel = channel.encode("ascii", "replace")
            
        logger.error("Failed to update channel: %s; Reason: %s",
            channel, failure.getErrorMessage())
        
        if self.isEstablished:
            if self.isPreviousUpdateSuccessful:
                self.isPreviousUpdateSuccessful = False
                item = FeedItem(itsView=self.itsView)
                item.displayName = _(u"Feed channel is unreachable")
                item.author = _(u"Chandler Feeds Parcel")
                item.category = _(u"Internal")
                item.date = datetime.now(ICUtzinfo.default)
                item.content = view.createLob(_(u"This feed channel is currently unreachable"))
                self.addFeedItem(item)
                self.logItem = item
                self.itsView.commit()
            else:
                if self.logItem:
                    self.logItem.content = view.createLob(u"This feed channel has been unreachable from " + unicode(formatTime(self.logItem.date)) + u" to " + unicode(formatTime(datetime.now(ICUtzinfo.default))))
                    self.itsView.commit()
                    
        if callback:
            callback(self.itsUUID, False)
            
        return FETCH_FAILED

    def parse(self, rawData):
        """
        This method uses an external library method to parse the RSS feed content
        and then fills the channel attributes.
        """
        data = feedparser.parse(rawData)
        # For fun, keep the latest copy of the feed inside the channel item
        self.body = unicode(rawData, "utf-8")
        return self.fillAttributes(data)


    def fillAttributes(self, data):
        """
        """
        # Map some external attribute names to internal attribute names:
        attrs = {"title":"displayName", "description":"body"}
        setAttributes(self, data["channel"], attrs)
        
        # These attribute names don"t need remapping:
        attrs = ["link", "copyright", "category", "language"]
        setAttributes(self, data["channel"], attrs)
        
        date = data["channel"].get("date")
        if date:
            self.date = date_parse(str(date))
        
        # parse feed items.
        return self._parseItems(data["items"])

    def addFeedItem(self, feedItem):
        """
        Add a single item, and add it to any listening collections.
        """
        feedItem.channel = self
        self.add(feedItem)

    def _parseItems(self, items):
        """
        This method parses all the news items in the RSS feed.
        """
        view = self.itsView
        
        count = 0
        
        for newItem in items:
            # Convert date to datetime object
            if getattr(newItem, "date_parsed", None):
                try:
                    # date_parsed is a tuple of 9 integers, like gmtime( )
                    # returns...
                    # date_parsed seems to always be converted to GMT, so
                    # let's make a datetime object using values from
                    # date_parsed, coupled with a GMT tzinfo...
                    kwds = dict(tzinfo=ICUtzinfo.getInstance('UTC'))
                    itemDate = datetime(*newItem.date_parsed[:5], **kwds)
                    # logger.debug("%s, %s, %s" % \
                    #     (newItem.date, newItem.date_parsed, itemDate))
                    newItem.date = itemDate
                except:
                    logger.exception("Could not get date: %s (%s)" % \
                        (newItem.date, newItem.date_parsed))
                    newItem.date = None
            # Get the item content, using the "content" attribute first,
            # falling back to what"s in"description"
            content = newItem.get("content")
            if content:
                content = content[0]["value"]
            else:
                content = newItem.get("description")
            title = newItem.get("title")
            matchingItem = None
            link = getattr(newItem, "link", None)
            if link:
                # Find all FeedItems that have this link
                matchingItem = indexes.valueLookup(self, "link", "link", link)
            # If no matching items (based on link), it"s new
            # If matching item, if title or description have changed,
            # update the item and mark it unread
            if matchingItem is None:
                feedItem = FeedItem(itsView=view)
                feedItem.refresh(newItem)
                self.addFeedItem(feedItem)
                logger.debug("Added new item: %s", title)
                count += 1
            else:
                # A FeedItem exists within this Channel that has the
                # same link.  @@@MOR For now I am only going to allow one
                # FeedItem at a time (per Channel) to link to the same place,
                # since it seems like that gets the behavior we want.
                oldTitle = matchingItem.displayName
                titleDifferent = (oldTitle != title)
                # If no date in the item, just consider it a matching date;
                # otherwise do compare datestamps:
                dateDifferent = False
                haveFeedDate = "date" in newItem
                if haveFeedDate:
                    if matchingItem.date != newItem.date:
                        dateDifferent = True
                if not self.ignoreContentChanges:
                    oldContent = matchingItem.content.getReader().read()
                    contentDifferent = (oldContent != content)
                else:
                    contentDifferent = False
                if contentDifferent or titleDifferent or dateDifferent:
                    matchingItem.refresh(newItem)
                    if matchingItem.read:
                        matchingItem.updated = True
                    matchingItem.read = False
                    msg = "Updated item: %s (content %s, title %s, date %s)"
                    logger.debug(msg, title, contentDifferent, titleDifferent,
                                 dateDifferent)
        return count

    def markAllItemsRead(self):
        """
        This method marks all items in this feed channel as read.
        """
        for item in self:
            item.read = True

    @schema.observer(author)
    def onAuthorChange(self, op, attr):
        self.updateDisplayWho(op, attr)
    
    def addDisplayWhos(self, whos):
        super(FeedChannel, self).addDisplayWhos(whos)
        author = getattr(self, 'author', None)
        if author is not None:
            whos.append((10, author, 'author'))

class FeedItem(pim.ContentItem):
    """
    This class implements a feed channel item that is visualized
    in the summary and detail views.
    """
    #
    # FeedItem repository interface
    #
    link = schema.One(schema.URL, initialValue=None)
    category = schema.One(schema.Text)
    author = schema.One(schema.Text)
    date = schema.One(schema.DateTime)
    channel = schema.One(FeedChannel)
    content = schema.One(schema.Lob)
    updated = schema.One(schema.Boolean)
    body = schema.Descriptor(redirectTo="content")
    schema.addClouds(sharing = schema.Cloud(link, category, author, date))

    def __init__(self, *args, **kw):
        """
        This method initializes a new feed item.
        """
        kw.setdefault("displayName", _(u"No Title"))
        super(FeedItem, self).__init__(*args, **kw)

    def _compareLink(self, other):
        """
        This method compares two feed items.
        """
        return cmp(str(self.link).lower(), str(other.link).lower())

    def refresh(self, data):
        """
        This method updates a feed item content.
        """
        # fill in the item
        attrs = {"title":"displayName"}
        setAttributes(self, data, attrs)

        attrs = ["link", "category", "author"]
        # @@@MOR attrs = ["creator", "link", "category"]
        setAttributes(self, data, attrs)

        content = data.get("content")

        # Use the "content" info first, falling back to what"s in "description"
        if content:
            content = content[0]["value"]
        else:
            content = data.get("description")

        if content:
            self.content = self.getAttributeAspect("content", "type").makeValue(content, indexed=True)

        if "date" in data:
            self.date = date_parse(str(data.date))
        else:
            # No date was available in the feed, so assign it "now"
            self.date = datetime.now(ICUtzinfo.default)

    @schema.observer(author)
    def onAuthorChange(self, op, attr):
        self.updateDisplayWho(op, attr)
    
    def addDisplayWhos(self, whos):
        super(FeedItem, self).addDisplayWhos(whos)
        author = getattr(self, 'author', None)
        if author is not None:
            whos.append((10, author, 'author'))
