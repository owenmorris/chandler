"""This module represents the data model of ZaoBao.
It includes:
1) The RSSChannel class that represents an RSS feed
"""

#Python modules
import types
import exceptions
import threading
import mx.DateTime
import time

#Chandler modules
from model.item.Item import Item
from application.Application import app
from application.agents.Notifications.NotificationManager import NotificationManager
from application.agents.Notifications.Notification import Notification

# ZaoBao modules
from OSAF.zaobao import feedparser
from OSAF.zaobao.Observable import Observable1

FEED_CHANGED_NOTIFICATION = 'zaobao/feedsChanged'

rssDict = None
def loadLocalObjects():
    global rssDict
    if not rssDict:
        rssDict = {}
        for item in app.repository.find("//ZaoBao"):
            if isinstance(item,RSSChannel):
                item._v_observers = []
                rssDict[id(item)] = item
    return rssDict
    #if len(rssDict) == 0: #@@@ fixme should change test to a virgin repository flag
        #defaultRSSFeeds = (
            #"http://blogs.osafoundation.org/zaobao/index.rdf",
            #"http://blogs.osafoundation.org/mitch/index.rdf",
            #"http://blogs.osafoundation.org/pieter/index.rdf",
            #"http://blogs.osafoundation.org/chao/index.rdf",
            #"http://blogs.osafoundation.org/devnews/index.rdf",
            #"http://blogs.osafoundation.org/blogotomy/index.rdf",
            #"http://toyblog.typepad.com/lemon/index.rdf",       
            #"http://www.joelonsoftware.com/rss.xml",
            #"http://www.scripting.com/rss.xml",
            #"http://lessig.org/blog/index.xml",
            #"http://werbach.com/blog/rss.xml",
            #"http://partners.userland.com/nytRss/technology.xml",
            #)
        #for rssURL in defaultRSSFeeds:
            #item = getNewRSSChannel(rssURL)
            #rssDict[id(item)] = item
    #return rssDict
 
def getNewRSSChannel(rssURL, isLocal=1):
    newChannel = RSSChannelFactory(app.repository).newItem(rssURL)
    return newChannel
    #if isLocal:
        #repository = LocalRepository()
        #repository.addObject(data)
    #return data

def updateRSSFeeds():
    loadLocalObjects()
    notificationManager = app.model.notificationManager
    notificationManager.DeclareNotification(FEED_CHANGED_NOTIFICATION,
                                            NotificationManager.SYSTEM_CLIENT,
                                            'unknown','')
    threading.Thread(target=_updateRSSFeedsLoop).start()
    
def _updateRSSFeeds():
    global rssDict
    #while 1:
    needUpdate = False
    for anRSSChannel in rssDict.values():
        print 'update channel ' + anRSSChannel.getTitle()
        if anRSSChannel.update(0):
            feedsChangedNotification = Notification(FEED_CHANGED_NOTIFICATION,
                                                    "booleanType",'zaobaoDaemon')
            feedsChangedNotification.SetData(anRSSChannel)
            #notificationManager.PostNotification(feedsChangedNotification)
            needUpdate = True
    if needUpdate:
        app.repository.commit()

def _updateRSSFeedsLoop():
    while 1:
        _updateRSSFeeds()
        time.sleep(10)
        
class RSSChannelFactory:
    def __init__(self,rep):
        self._container = rep.find("//ZaoBao")
        self._kind = rep.find("//Schema/RSSSchema/RSSChannel")
        
    def newItem(self,rssURL):
        item = RSSChannel(rssURL,None,self._container,self._kind)
        return item
    
class RSSChannelException(exceptions.Exception):
    def __init__(self, args=None):
        self.args = args

class RSSChannel(Item,Observable1):
    """The data model for an RSS feed and an object wrapper around the
    feedparser module.
    Each instance contains just one instance variable, data,
    a dictionary that contains the follow keys from feedparser module:
        - channel; from feedparser module
        - etag; 
        - date; last modified date of this RSS feed
        - items; the payload of the rss feed
    In addition, I've added the following keys:
        - rssURL; url from this RSS feed
        - isUnread; does this feed contain new items not viewed yet by user
    """

    def __init__(self,rssURL,name,parent,kind,**_kwds):
        Item.__init__(self,name,parent,kind,**_kwds)
        Observable1.__init__(self)
        parserData = feedparser.parse(rssURL)
        if (parserData['channel'] == {}):
            self.delete() #@@@ verify it's ok to delete an object before __init__ is completed
            raise RSSChannelException, 'No RSS Data could be retrieved from specified URL: ' + rssURL
        self.setChannel(parserData,rssURL)
        
    def setChannel(self,parserData,rssURL):
        channel = parserData['channel']
        self.setAttribute("creator",channel.get('creator',''))
        self.setAttribute("description",channel.get('description',''))
        self.setAttribute("link",channel.get('link',''))
        self.setAttribute("title",channel.get('title',''))
        self.setAttribute("category",channel.get('category',''))
        self.setAttribute("language",channel.get('language','en-us'))
        self.setAttribute("encoding",channel.get('encoding',''))
        self.setAttribute("etag",parserData.get('etag',''))
        self.setModifiedDate(parserData)
        self.setAttribute("rssURL",rssURL)
        items = self.getItemsFromParseData(parserData)
        self.updateItems(items)
        self.setAttribute('isUnread',len(items) > 0)         
    
    def updateItems(self, items):
        try:
            self.items.clear()
        except AttributeError:
            pass
        for item in items:
            self.attach('items',item)
            
    def updateChannel(self, parseData):
        self.setModifiedDate(parseData)
        etag = parseData.get('etag')
        if etag: self.setAttribute('etag',etag)
            
        for (key, value) in parseData['channel'].items():
            if (key == 'creator' or key == 'description' or
                key == 'link' or key == 'title' or
                key == 'category' or key == 'language' or
                key == 'encoding'):
                    self.setAttribute(key,value)

    def getItemsFromParseData(self,parseData):
        items = [RSSItemFactory(app.repository).newItem(itemData)
                 for itemData in parseData['items']]
        return items
    
    def hasNewItems(self):
        return self.isUnread
    
    def setHasNewItems(self, hasItems, doSave=1):
       changed = self.isUnread != hasItems
       if changed:
           self.setAttribute('isUnread',hasItems)
           self.broadcast({'event':'RSS item changed','key':id(self)})
           if doSave:
               app.repository.commit()
       
    def getTitle(self):
        return self.title
    
    def getCreator(self):
        return self.creator
    
    def getETag(self):
        return self.etag
    
    def getSiteLink(self):
        return self.link
    
    def getRSSURL(self):
        return self.rssURL
    
    def getItems(self):
        return self.items.values()
    
    def getModifiedDate(self):
        return self.lastModified
    
    def setModifiedDate(self, parseData):
        try:
            date = parseData['channel']['date']
            lastModified = mx.DateTime.DateTimeFrom(date)
        except KeyError:
            modifiedDate = parseData.get('modified')
            if modifiedDate and len(modifiedDate) > 5:
                lastModified = apply(mx.DateTime.DateTime,modifiedDate[0:3])
            else:
                lastModified = None
        if lastModified:
            self.setAttribute('lastModified',lastModified)
        
    def getModifiedDateString(self):
        date = self.lastModified
        if (date):
            return date.localtime().strftime('%a %m/%d %I:%M %p')
        else: return ''
    
    def getModifiedDateTuple(self):
        date = self.lastModified
        if (date):
            return date.localtime().tuple()
        else: return None
        
    def update(self, doSave=1):
        def diffItems(oldItems, newItems):
            """"Returns a list of items that are in newItems but not in oldItems.
            newItems and oldItems are both lists.
            This implementation does not scale well. If required to scale, we should
            convert the lists to dictionaries as described in Python cookbook recipe#1.8
            """
            return [newItem for newItem in newItems if newItem not in oldItems]

        rssURL = self.rssURL
        newData = feedparser.parse(rssURL,
                                  self.etag,
                                  self.getModifiedDateTuple())
        newItems = self.getItemsFromParseData(newData)
        self.updateChannel(newData)
        
        if (len(newItems) > 0 and 
            len(diffItems(self.items, newItems)) > 0):
            self.updateItems(newItems)
            self.setHasNewItems(1,doSave)
            if doSave: app.repository.commit()
            return 1
        return None
    
class RSSItemFactory:
    def __init__(self,rep):
        self._container = rep.find('//ZaoBao')
        self._kind = rep.find('//Schema/RSSSchema/RSSItem')
        
    def newItem(self, itemData):
        item = RSSItem(itemData, itemData.get('title',''),self._container,self._kind)
        item.updateAttributes(itemData)
        return item
    
class RSSItem(Item):
    def updateAttributes(self, itemData):
        self.setAttribute('creator',itemData.get('creator',''))
        self.setAttribute('description',itemData.get('description',''))
        self.setAttribute('link',itemData.get('link',''))
        self.setAttribute('title',itemData.get('title',''))
        self.setAttribute('category',itemData.get('category',''))
        try:
            date = itemData['date']
            lastModified = mx.DateTime.DateTimeFrom(date)
        except KeyError:
            lastModified = None
        self.setAttribute('lastModified',lastModified)
        