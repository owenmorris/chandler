"""This module represents the data model of ZaoBao.
It includes:
1) The RSSData class that represents an RSS feed
"""

#Python modules
import marshal
import types
import exceptions
import threading
import mx.DateTime

from persistence.dict import PersistentDict

# Chandler modules
from application.model_deprecated.InformationItem import InformationItem
from application.model_deprecated.LocalRepository import LocalRepository

# ZaoBao modules
from OSAF.zaobao import rssparser
from OSAF.zaobao.Observable import Observable1

def loadLocalObjects():
    rssDict = {}
    repository = LocalRepository()
    for item in repository.objectList:
        if isinstance(item,RSSData):
            item._v_observers = []
            rssDict[id(item)] = item
    if len(rssDict) == 0: #@@@ fixme should change test to a virgin repository flag
        defaultRSSFeeds = (
            "http://blogs.osafoundation.org/zaobao/index.rdf",
            "http://blogs.osafoundation.org/mitch/index.rdf",
            "http://blogs.osafoundation.org/pieter/index.rdf",
            "http://blogs.osafoundation.org/chao/index.rdf",
            "http://blogs.osafoundation.org/devnews/index.rdf",
            "http://radio.weblogs.com/0118398/rss.xml",       
            "http://www.joelonsoftware.com/rss.xml",
            "http://www.scripting.com/rss.xml",
            "http://lessig.org/blog/index.xml",
            "http://werbach.com/blog/rss.xml",
            "http://partners.userland.com/nytRss/technology.xml",
            )
        for rssURL in defaultRSSFeeds:
            item = getNewRSSData(rssURL)
            rssDict[id(item)] = item
    return rssDict
 
def getNewRSSData(rssURL, isLocal=1):
    data = RSSData(rssURL)
    if isLocal:
        repository = LocalRepository()
        repository.addObject(data)
    return data
    
class RSSDataException(exceptions.Exception):
    def __init__(self, args=None):
        self.args = args

class RSSData(InformationItem,Observable1):
    """The data model for an RSS feed and an object wrapper around the
    rssparser module.
    Each instance contains just one instance variable, data,
    a dictionary that contains the follow keys from rssparser module:
        - channel; from rssparser module
        - etag; 
        - date; last modified date of this RSS feed
        - items; the payload of the rss feed
    In addition, I've added the following keys:
        - rssURL; url from this RSS feed
        - hasNewItems; does this feed contain new items not viewed yet by user
    """

    rdfs = PersistentDict()
    
    def __init__(self,data):
        InformationItem.__init__(self)
        Observable1.__init__(self)
        if not isinstance(data,types.DictType):
            rssURL = data
            self.data = rssparser.parse(rssURL)
            if (self.data['channel'] == {}):
                raise RSSDataException, 'No RSS Data could be retrieved from specified URL: ' + rssURL
            self.data['rssURL'] = rssURL
            self.data['hasNewItems'] = len(self.data.get('items',())) > 0
        else:
            self.data = data
        
    def __setstate__(self, state):
        super(InformationItem, self).__setstate__(state)
        if not hasattr(self,'_v_observers'):
            self._v_observers = []
        
    def hasNewItems(self):
        return self.data['hasNewItems']
    
    def setHasNewItems(self, hasItems, doSave=1):
        changed = (not self.data.has_key('hasNewItems') or
                                self.hasNewItems() != hasItems)
        if changed:
            self.data['hasNewItems'] = hasItems
            self.broadcast({'event':'RSS item changed','key':id(self)})
            self._p_changed = 1
            if doSave:
                repository = LocalRepository()
                repository.commit()
        
    def getTitle(self):
        try: return self.data['channel']['title']
        except KeyError: return ''
    
    def getCreator(self):
        try: return self.data['channel']['creator']
        except KeyError: return ''
    
    def getModifiedDateString(self):
        date = self.getModifiedDate()
        if (date):
            return date.localtime().strftime('%a %m/%d %I:%M %p')
        else: return ''
    
    def getModifiedDate(self):
        try: 
            date = self.data['channel']['date']
            return mx.DateTime.DateTimeFrom(date)
        except KeyError: 
            modifiedDate = self.data.get('modified')
            if modifiedDate and len(modifiedDate) > 5:
                return apply (mx.DateTime.DateTime,modifiedDate[0:5])
            else:
                return None
        
    def getETag(self):
        try: return self.data['channel']['etag']
        except KeyError: return ''
        
    def getSiteLink(self):
        try: return self.data['channel']['link']
        except KeyError: return ''
    
    def getRSSURL(self):
        return self.data['rssURL']
    
    def getItems(self):
        try: return self.data['items']
        except KeyError: return []
        
    
    def update(self, doSave=1):
        def diffItems(oldItems, newItems):
            """"Returns a list of items that are in newItems but not in oldItems.
            newItems and oldItems are both lists.
            This implementation does not scale well. If required to scale, we should
            convert the lists to dictionaries as described in Python cookbook recipe#1.8
            """
            return [newItem for newItem in newItems if newItem not in oldItems]

        rssURL = self.getRSSURL()
        newData = rssparser.parse(rssURL,
                                  self.getETag(),
                                  self.data.get('modified'))
        if (len(newData.get('items',[])) > 0 and 
            len(diffItems(self.data.get('items',[]), newData['items'])) > 0):
            self.data = newData
            self.data['rssURL'] = rssURL
            self.setHasNewItems(1,doSave)
    
