__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from application.Application import app
from application.agents.model.Action import Action

import feedparser

_defaultBlogs = [ "http://www.pavlov.net/blog/rss10.rdf", \
                  "http://blogs.osafoundation.org/news/index.rdf", \
                  "http://blogs.osafoundation.org/devnews/index.rdf", \
                  "http://blogs.osafoundation.org/zaobao/index.rdf", \
                  "http://blogs.osafoundation.org/mitch/index.rdf", \
                  "http://blogs.osafoundation.org/chao/index.rdf", \
                  "http://blogs.osafoundation.org/pieter/index.rdf", \
                  "http://blogs.osafoundation.org/blogotomy/index.rdf", \
                  "http://lessig.org/blog/index.xml", \
                  "http://diveintomark.org/xml/rss.xml"]

BASE_PATH = '//Parcels/OSAF/examples/zaobao'

class UpdateAction(Action):
    def Execute(self, agent, notification):
        repository = app.repository

        for feed in self.__getFeeds():
            etag = feed.getAttributeValue('etag', default=None)
            lastModified = feed.getAttributeValue('lastModified', default=None)
            if lastModified:
                modified = lastModified.tuple()
            else:
                modified = None
            data = feedparser.parse(feed.link, etag, modified)
            feed.Update(data)

        repository.commit()

    def __getFeeds(self):
        repository = app.repository
        feedKind = repository.find(BASE_PATH + '/RSSFeed')

        feeds = []
        parent = repository.find(BASE_PATH)

        for url in _defaultBlogs:
            urlhash = str(hash(url))
            item = repository.find(BASE_PATH + '/' + urlhash)
            if not item:
                item = feedKind.newItem(urlhash, parent)
                item.link = url
            feeds.append(item)

        return feeds
