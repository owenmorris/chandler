__revision__  = "$Revision: 6435 $"
__date__      = "$Date: 2005-08-09 09:43:05 -0700 (Tue, 09 Aug 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__    = "feeds"

import time, os, logging, datetime, urllib
from PyICU import ICUtzinfo, TimeZone
from dateutil.parser import parse as date_parse
from application import schema
from util import feedparser
from xml.sax import SAXParseException
import socket
import application
from osaf import pim
from i18n import OSAFMessageFactory as _
from twisted.web import client
from twisted.internet import reactor

logger = logging.getLogger(__name__)


# The Feeds repository view, used for background updates
view = None

def getFeedsView(repository):
    global view
    if view is None:
        view = repository.createView("Feeds")
    return view



class FeedUpdateTaskClass:

    def __init__(self, item):
        self.repository = item.itsView.repository
        pass

    def run(self):
        updateFeeds(self.repository)
        return True     # run it again next time


def updateFeeds(repository):
    view = getFeedsView(repository)
    view.refresh()

    for channel in FeedChannel.iterItems(view):
        channel.update()


def newChannelFromURL(view, url):

    url = str(url)

    channel = FeedChannel(itsView=view)
    channel.displayName = url
    channel.url = channel.getAttributeAspect('url', 'type').makeValue(url)

    return channel



# sets a given attribute overriding the name with newattr
def SetAttribute(self, data, attr, newattr=None):
    if not newattr:
        newattr = attr
    value = data.get(attr)
    if value:
        type = self.getAttributeAspect(newattr, 'type', None)
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



class ConditionalHTTPClientFactory(client.HTTPClientFactory):

    def __init__(self, url, lastModified=None, etag=None, method='GET',
                 postdata=None, headers=None, agent="Chandler", timeout=0,
                 cookies=None, followRedirect=1):

        if lastModified or etag:
            if headers is None:
                headers = { }
            if lastModified:
                headers['if-modified-since'] = lastModified
            if etag:
                headers['if-none-match'] = etag

        client.HTTPClientFactory.__init__(self, url, method=method,
            postdata=postdata, headers=headers, agent=agent, timeout=timeout,
            cookies=cookies, followRedirect=followRedirect)

        self.deferred.addCallback(
            lambda data: (data, self.status, self.response_headers)
        )

    def noPage(self, reason):
        if self.status == '304':
            client.HTTPClientFactory.page(self, '')
        else:
            client.HTTPClientFactory.noPage(self, reason)


class FeedChannel(pim.ListCollection):

    schema.kindInfo(displayName=u"Feed Channel")

    link = schema.One(
        schema.URL,
        displayName=_(u"link")
    )

    category = schema.One(
        schema.Text,
        displayName=_(u"Category")
    )

    author = schema.One(
        schema.Text,
        displayName=_(u"Author")
    )

    date = schema.One(
        schema.DateTime,
        displayName=_(u"Date")
    )

    url = schema.One(
        schema.URL,
        displayName=u"URL"
    )

    etag = schema.One(
        schema.Text,
        displayName=u"eTag"
    )

    lastModified = schema.One(
        schema.DateTime,
        displayName=u"Last Modified"
    )

    copyright = schema.One(
        schema.Text,
        displayName=u"Copyright"
    )

    language = schema.One(
        schema.Text,
        displayName=u"Language"
    )

    isUnread = schema.One(
        schema.Boolean,
        displayName=u"Is Unread"
    )

    schema.addClouds(
        sharing = schema.Cloud(author, copyright, link, url)
    )

    who = schema.Descriptor(redirectTo="author")
    about = schema.Descriptor(redirectTo="about")


    def update(self):

        # Make sure we have the feedsView copy of the channel item
        feedsView = getFeedsView(self.itsView.repository)
        feedsView.refresh()
        item = feedsView.findUUID(self.itsUUID)

        return item.download().addCallback(item.feedFetchSuccess).addErrback(
            item.feedFetchFailed)


    def download(self):
        url = str(self.url)
        etag = getattr(self, 'etag', None)
        lastModified = getattr(self, 'lastModified', None)
        if lastModified:
            lastModified = lastModified.strftime("%a, %d %b %Y %H:%M:%S %Z")

        (scheme, host, port, path) = client._parse(url)
        factory = ConditionalHTTPClientFactory(url=url,
            lastModified=lastModified, etag=etag)
        reactor.connectTCP(host, port, factory)

        return factory.deferred



    def feedFetchSuccess(self, info):

        (data, status, headers) = info

        # getattr returns a unicode object which needs to be converted to
        # bytes for logging
        channel = getattr(self, 'displayName', None)
        if channel is None:
            channel = str(self.url)
        else:
            channel = channel.encode('ascii', 'replace')

        if not data:
            # Page hasn't changed (304)
            logger.info("Channel hasn't changed: %s" % channel)
            return

        logger.info("Channel downloaded: %s" % channel)

        # set etag
        etag = headers.get('etag', None)
        if etag:
            self.etag = etag[0]

        # set lastModified
        lastModified = headers.get('last-modified', None)
        if lastModified:
            self.lastModified = date_parse(lastModified[0])

        count = self.parse(data)
        if count:
            logger.info("...added %d FeedItems" % count)

        self.itsView.commit()


    def feedFetchFailed(self, failure):

        # getattr returns a unicode object which needs to be converted to
        # bytes for logging
        channel = getattr(self, 'displayName', None)
        if channel is None:
            channel = str(self.url)
        else:
            channel = channel.encode('ascii', 'replace')

        logger.error("Failed to update channel: %s; Reason: %s",
            channel, failure.getErrorMessage())


    def parse(self, rawData):
        data = feedparser.parse(rawData)

        # Map some external attribute names to internal attribute names:
        attrs = {'title':'displayName', 'description':'body'}
        SetAttributes(self, data['channel'], attrs)

        # These attribute names don't need remapping:
        attrs = ['link', 'copyright', 'category', 'language']
        SetAttributes(self, data['channel'], attrs)

        date = data['channel'].get('date')
        if date:
            self.date = date_parse(str(date))

        return self._parseItems(data['items'])


    def addFeedItem(self, feedItem):
        """
            Add a single item, and add it to any listening collections
        """
        feedItem.channel = self
        self.add(feedItem)


    def _parseItems(self, items):
        # make children

        # lets look for each existing item. This is ugly and is an O(n^2) problem
        # if the items are unsorted. Bleah.
        view = self.itsView

        count = 0

        for newItem in items:

            # Convert date to datetime object
            if getattr(newItem, 'date_parsed', None):

                try:

                    # date_parsed is a tuple of 9 integers, like gmtime( )
                    # returns...
                    d = newItem.date_parsed

                    # date_parsed seems to always be converted to GMT, so
                    # let's make a datetime object using values from
                    # date_parsed, coupled with a GMT tzinfo...
                    itemDate = datetime.datetime(d[0], d[1], d[2], d[3], d[4],
                        d[5], 0, ICUtzinfo(TimeZone.getGMT()))

                    logger.debug("%s, %s, %s" % \
                        (newItem.date, newItem.date_parsed, itemDate))

                    newItem.date = itemDate

                except:
                    logger.exception("Couldn't get date: %s (%s)" % \
                        (newItem.date, newItem.date_parsed))
                    newItem.date = None

            found = False
            for oldItem in self:
                # check to see if this doesn't already exist
                if oldItem.isSimilar(newItem):
                    found = True
                    oldItem.update(newItem)
                    break

            if not found:
                # we have a new item - add it
                if not hasattr(newItem, 'date'):
                    # No date was available in the feed, so assign it 'now'
                    newItem.date = datetime.datetime.now(ICUtzinfo.getDefault())
                feedItem = FeedItem(itsView=view)
                feedItem.update(newItem)


                try:
                    self.addFeedItem(feedItem)
                    count += 1
                except:
                    logger.error("Error adding an Feed item")

        return count

    def markAllItemsRead(self):
        for item in self:
            item.read = True

##
# FeedItem
##
class FeedItem(pim.ContentItem):

    schema.kindInfo(displayName=u"Feed Item")

    link = schema.One(
        schema.URL,
        displayName=_(u"link")
    )

    category = schema.One(
        schema.Text,
        displayName=_(u"Category")
    )

    author = schema.One(
        schema.Text,
        displayName=_(u"Author")
    )

    date = schema.One(
        schema.DateTime,
        displayName=_(u"Date")
    )

    channel = schema.One(
        FeedChannel,
        displayName=u"Channel"
    )

    content = schema.One(
        schema.Lob,
        displayName=u"Content"
    )

    about = schema.Descriptor(redirectTo="displayName")
    who = schema.Descriptor(redirectTo="author")
    body = schema.Descriptor(redirectTo="content")

    schema.addClouds(
        sharing = schema.Cloud(link, category, author, date)
    )

    def __init__(self, *args, **kw):
        kw.setdefault('displayName', _(u"No Title"))
        super(FeedItem, self).__init__(*args, **kw)

    def update(self, data):
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

        if 'date' in data:
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
            logger.exception("Feed item comparison failed")
            logger.error("Failed in %s", feedItem.title)
            logger.error("%s vs %s" % (self.date, feedItem.date))

        return False
