__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from repository.item.Item import Item
from repository.item.Query import KindQuery
from OSAF.framework.agents.schema.Action import Action
from OSAF.examples.zaobao.RSSData import ZaoBaoParcel, RSSChannel

import feedparser

_defaultBlogs = [ \
                  "http://www.osafoundation.org/rss/2.0/", \
                  "http://blogs.osafoundation.org/devnews/index.rdf", \
                  "http://blogs.osafoundation.org/zaobao/index.rdf", \
                  "http://blogs.osafoundation.org/mitch/index.rdf", \
                  "http://blogs.osafoundation.org/chao/index.rdf", \
                  "http://blogs.osafoundation.org/pieter/index.rdf", \
                  "http://blogs.osafoundation.org/blogotomy/index.rdf", \
                  "http://lessig.org/blog/index.xml", \
                  "http://diveintomark.org/xml/rss.xml",
                  "http://www.scripting.com/rss.xml",
                  "http://xml.newsisfree.com/feeds/15/2315.xml"]

def UpdateChannel(chan):
    try:
        etag = chan.getAttributeValue('etag', default=None)
        lastModified = chan.getAttributeValue('lastModified', default=None)
        if lastModified:
            modified = lastModified.tuple()
        else:
            modified = None
        data = feedparser.parse(chan.url, etag, modified)

        if data['status'] == 404:
            return

        chan.Update(data)
    except:
        pass

def MainThreadCommit():
    Globals.repository.commit()

class UpdateAction(Action):
    def Execute(self, agent, notification):
        repository = self.getRepository()

        repository.commit()
        #print 'Updating feeds...'
        for feed in self.__getFeeds():
            UpdateChannel(feed)
        repository.commit()
        #print 'Updated feeds'

        Globals.application.PostAsyncEvent(MainThreadCommit)

    def __getFeeds(self):

        chanKind = ZaoBaoParcel.getRSSChannelKind()

        feeds = []

        for item in KindQuery().run([chanKind]):
            feeds.append(item)

        # auto generate some feeds if there aren't any in the repository
        if len(feeds) == 0:
            for url in _defaultBlogs:
                item = RSSChannel()
                item.url = url
                feeds.append(item)

        return feeds
