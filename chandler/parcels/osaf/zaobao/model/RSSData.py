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
import os

#Chandler modules
from model.item.Item import Item
from model.schema import Kind
from application.Application import app
from application.agents.Notifications.NotificationManager import NotificationManager
from application.agents.Notifications.Notification import Notification

# ZaoBao modules
from OSAF.zaobao import feedparser

FEED_CHANGED_NOTIFICATION = 'zaobao/feedsChanged'
rssDict = None
_defaultBlogs = (
    "http://blogs.osafoundation.org/news/index.rdf",
    "http://blogs.osafoundation.org/zaobao/index.rdf",
    "http://blogs.osafoundation.org/mitch/index.rdf",
    "http://blogs.osafoundation.org/chao/index.rdf",
    "http://blogs.osafoundation.org/pieter/index.rdf",
    "http://blogs.osafoundation.org/blogotomy/index.rdf",
    "http://lessig.org/blog/index.xml",
    "http://diveintomark.org/xml/rss.xml"
    )

def OnInit(loader):
    if not app.repository.find('//ZaoBao'):
        zaobaoPath = os.path.join(app.chandlerDirectory, 'parcels',
                                  'OSAF', 'zaobao', 'model',
                                  'zaobao.xml')
        loader.load(zaobaoPath)
        Item("Items",app.repository.find('//ZaoBao'),None)
        notificationManager = app.model.notificationManager
        notificationManager.DeclareNotification(FEED_CHANGED_NOTIFICATION,
                                                NotificationManager.SYSTEM_CLIENT,
                                                'unknown','')
        threading.Thread(target=_loadInitialFeeds).start()
        #_loadInitialFeeds()
        
def _loadInitialFeeds():
    global rssDict
    rssDict = {}
    for rssURL in _defaultBlogs:
        try:
            item = getNewRSSChannel(rssURL)
        except Exception,e: #ignore all errors for default feeds
            pass
  
def loadLocalObjects():
    global rssDict
    if not rssDict:
        rssDict = {}
        items = app.repository.find("//ZaoBao")
        if items:
            for item in items:
                if isinstance(item,RSSChannel):
                    rssDict[id(item)] = item
    return rssDict
 
def getNewRSSChannel(rssURL, isLocal=1):
    newChannel = RSSChannelFactory(app.repository).newItem(rssURL)
    return newChannel
    #if isLocal:
        #repository = LocalRepository()
        #repository.addObject(data)
    #return data

def updateRSSFeeds():
    loadLocalObjects()
    threading.Thread(target=_updateRSSFeedsLoop).start()
    
def _updateRSSFeeds():
    needUpdate = False
    for anRSSChannel in rssDict.values():
        if anRSSChannel.update(0):
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
        parseData = feedparser.parse(rssURL)
        if (parseData['channel'] == {}):
            raise RSSChannelException, 'No RSS Data could be retrieved from specified URL: ' + rssURL
        item = RSSChannel(None,self._container,self._kind)
        item.initAttributes(parseData, rssURL)
        global rssDict
        rssDict[id(item)] = item
        return item
    
class RSSChannelException(exceptions.Exception):
    def __init__(self, args=None):
        self.args = args

class RSSChannel(Item):
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

    def initAttributes(self,parseData, rssURL):
        self.setChannel(parseData,rssURL)
        
    def setChannel(self,parserData,rssURL):
        encoding = parserData.get('encoding','latin_1')
        channel = parserData['channel']
        self.setAttributeValue("creator",
                               unicode(channel.get('creator',''),encoding))
        self.setAttributeValue("description",
                               unicode(channel.get('description','')))
        self.setAttributeValue("link",channel.get('link',''))
        self.setAttributeValue("title",
                               unicode(channel.get('title',''),encoding))
        self.setAttributeValue("category",
                               unicode(channel.get('category',''),encoding))
        self.setAttributeValue("language",channel.get('language','en-us'))
        self.setAttributeValue("encoding",channel.get('encoding',''))
        self.setAttributeValue("etag",parserData.get('etag',''))
        self.setModifiedDate(parserData)
        self.setAttributeValue("rssURL",rssURL)
        items = self.getItemsFromParseData(parserData)
        self.updateItems(items)
        self.setAttributeValue('isUnread',len(items) > 0)         
    
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
        if etag: self.setAttributeValue('etag',etag)
            
        for (key, value) in parseData['channel'].items():
            if (key == 'creator' or key == 'description' or
                key == 'link' or key == 'title' or
                key == 'category' or key == 'language' or
                key == 'encoding'):
                    self.setAttributeValue(key,value)

    def getItemsFromParseData(self,parseData):
        encoding = parseData.get('encoding', 'latin_1')
        items = [RSSItemFactory(app.repository).newItem(itemData, encoding)
                 for itemData in parseData['items']]
        return items
    
    def hasNewItems(self):
        return self.isUnread
    
    def setHasNewItems(self, hasItems, doSave=1):
       changed = self.isUnread != hasItems
       if changed:
           self.setAttributeValue('isUnread',hasItems)
           feedsChangedNotification = Notification(FEED_CHANGED_NOTIFICATION,
                                                   "RSSChannel",'zaobaoDaemon')
           feedsChangedNotification.SetData(self)
           app.model.notificationManager.PostNotification(feedsChangedNotification)
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
        return self.getAttributeValue('lastModified',default=None)
    
    def setModifiedDate(self, parseData):
        try:
            date = parseData['channel']['date']
            lastModified = mx.DateTime.DateTimeFrom(date)
        except KeyError:
            modifiedDate = parseData.get('modified')
            if modifiedDate and len(modifiedDate) > 5:
                lastModified = apply(mx.DateTime.DateTime,modifiedDate[0:3]) #@@@ FIXME, need to store the whole date
            else:
                self.removeAttributeValue('lastModified')
        self.setAttributeValue('lastModified',lastModified)
        
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
        
        if (len(newItems) > 0 and 
            len(diffItems(self.items, newItems)) > 0):
            for item in self.items:
                item.delete()
            self.updateChannel(newData)
            self.updateItems(newItems)
            self.setHasNewItems(1,doSave)
            if doSave: app.repository.commit()
            return 1
        return None
    
class RSSItemFactory:
    def __init__(self,rep):
        self._container = rep.find('//ZaoBao/Items')
        self._kind = rep.find('//Schema/RSSSchema/RSSItem')
        
    def newItem(self, itemData, encoding):
        item = RSSItem(None,self._container,self._kind)
        item.initAttributes(itemData, encoding)
        return item
    
class RSSItem(Item):
    def initAttributes(self, itemData, encoding):
        self.setAttributeValue('creator',
                               unicode(itemData.get('creator',''),encoding))
        self.setAttributeValue('description',
                               unicode(itemData.get('description',''),encoding))
        self.setAttributeValue('link', itemData.get('link',''))
        self.setAttributeValue('title',
                               unicode(itemData.get('title',''),encoding))
        self.setAttributeValue('category',
                               unicode(itemData.get('category',''),encoding))
        try:
            date = itemData['date']
            self.setAttributeValue('lastModified',mx.DateTime.DateTimeFrom(date))
        except KeyError:
            self.removeAttributeValue('lastModified')
        
