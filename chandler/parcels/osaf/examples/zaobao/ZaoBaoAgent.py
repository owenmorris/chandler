from repository.item.Item import Item
from application.Application import app
from application.agents.model.Action import Action

import feedparser

_defaultBlogs = [ "http://www.pavlov.net/blog/index.rdf", \
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
RSSCHANNEL_KIND_PATH = BASE_PATH + '/RSSChannel'

DATA_NAME = 'Data'
DATA_PATH = BASE_PATH + '/' + DATA_NAME

class UpdateAction(Action):
    def Execute(self, agent, notification):
        repository = app.repository

        chanKind = repository.find(RSSCHANNEL_KIND_PATH)

        parent = repository.find(DATA_PATH)
        if not parent:
            parent = Item(DATA_NAME, repository.find(BASE_PATH), None)

        for url in _defaultBlogs:
            urlhash = str(hash(url))

            chan = repository.find(DATA_PATH + '/' + urlhash)
            if not chan:
                chan = chanKind.newItem(urlhash, parent)
            data = feedparser.parse(url)
            chan.Update(url, data)

        repository.commit()
