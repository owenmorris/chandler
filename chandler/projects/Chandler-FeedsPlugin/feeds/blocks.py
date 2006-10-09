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


import logging
import application
import osaf.views.detail as Detail
import application.Globals as Globals
import osaf.framework.blocks.Block as Block
from channels import FeedChannel, FeedItem
from i18n import MessageFactory
from osaf import messages
from application import schema
from osaf.pim.structs import SizeType, RectType

_ = MessageFactory("Chandler-FeedsPlugin")

logger = logging.getLogger(__name__)

class FeedItemDetail(Detail.HTMLDetailArea):
    """
    This class implements a block for visualizing feed item content.
    """
    def getHTMLText(self, item):
        """
        This method renders the feed item content as HTML.
        """
        # check that we have a valid feed item.
        if item == item.itsView:
            return
        if item is not None:
            displayName = item.getAttributeValue(
                             "displayName", default=u"<" + messages.UNTITLED + u">")
            
            # make the html
            HTMLText = u"<html><body>\n\n"
            
            link = item.getAttributeValue("link", default=None)
            if link:
                HTMLText = HTMLText + u"<a href=\"%s\">" % (link)
            HTMLText = HTMLText + u"<h5>%s</h5>" % (displayName)
            if link:
                HTMLText = HTMLText + u"</a>\n"
                
            content = item.getAttributeValue("content", default=None)
            if content:
                content = content.getReader().read()
            else:
                content = displayName
            #desc = desc.replace("<", "&lt;").replace(">", "&gt;")
            HTMLText = HTMLText + u"<p>" + content + u"</p>\n\n"
            if link:
                HTMLText = HTMLText + u"<br><a href=\"" + unicode(item.link) + u"\">" + _(u"more...") + u"</a>"
                
            HTMLText = HTMLText + "</body></html>\n"
            
            return HTMLText

class AddFeedCollectionEvent(Block.AddToSidebarEvent):
    """
    This class implements an event for adding a new collection to the sidebar.
    """
    
    def onNewItem (self):
        """
        This method is invoked when the user clicks on "New Feed Channel"
        menu item.
        """
        def calledInMainThread(channelUUID, success):
            """
            This callback is invoked once the feed has been processed.  If all
            is okay, success will be True, otherwise False.
            """
            self.itsView.refresh(notify=False)
            channel = self.itsView.findUUID(channelUUID)
            
            if not channel.isEstablished and not success:
                # request a new URL from the user.
                url = application.dialogs.Util.promptUser(
                    _(u"The provided URL seems to be invalid"),
                    _(u"Enter a URL for the RSS Channel"),
                    defaultValue = unicode(channel.url))
                url = str(url)
                if url != None:
                    try:
                        # try to recreate the channel...
                        channel.displayName = url
                        channel.url = channel.getAttributeAspect("url", "type").makeValue(url)
                        channel.isEstablished = False
                        channel.isPreviousUpdateSuccessful = True
                        channel.logItem = None
                        channel.itsView.commit()
                        # ... and then try to update its contents.
                        channel.refresh(callback=calledInTwisted)
                    except:
                        # unable to recreate the feed channel.
                        application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                                    _(u"New Channel Error"),
                                                    _(u"Could not create channel for %(url)s\nCheck the URL and try again.") % {"url": url})
                        
        def calledInTwisted(channelUUID, success):
            """
            This callback is what we really pass to twisted, and it will
            invoke the calledInMainThread method in the main thread.
            """
            wx.GetApp().PostAsyncEvent(calledInMainThread, channelUUID, success)
            
        # get a URL from the user, ...
        import wx
        url = application.dialogs.Util.promptUser(
            _(u"New Channel"),
            _(u"Enter a URL for the RSS Channel"),
            defaultValue = u"http://")
        if url == None:
            return None
        url = str(url)
        
        # ... and then try to create a new channel.
        try:
            # create a new feed channel...
            self.itsView.refresh(notify=False)
            channel = FeedChannel(itsView=self.itsView)
            channel.displayName = url
            channel.url = channel.getAttributeAspect("url", "type").makeValue(url)
            self.itsView.commit()
            # ... and then update its contents.
            channel.refresh(callback=calledInTwisted)
        except:
            # unable to create a new feed channel.
            application.dialogs.Util.ok(wx.GetApp().mainFrame,
                _(u"New Channel Error"),
                _(u"Could not create channel for %(url)s\nCheck the URL and try again.") % {"url": url})
            return None
        
        # return succesfully
        return channel

def installParcel(parcel, oldVersion=None):
    """
    This function defines the feed parcel detail view layout.
    """
    
    detail = schema.ns("osaf.views.detail", parcel)
    blocks = schema.ns("osaf.framework.blocks", parcel)
    main   = schema.ns("osaf.views.main", parcel)
    feeds  = schema.ns("feeds", parcel)
    
    # Create an AddFeedCollectionEvent that adds an RSS collection to the sidebar.
    addFeedCollectionEvent = AddFeedCollectionEvent.update(
        parcel, "addFeedCollectionEvent",
        blockName = "addFeedCollectionEvent")
    
    # Add a separator to the "Collection" menu ...
    blocks.MenuItem.update(parcel, "feedsParcelSeparator",
                           blockName = "feedsParcelSeparator",
                           menuItemKind = "Separator",
                           parentBlock = main.CollectionMenu)
    
    # ... and, below it, a menu item to subscribe to a RSS feed.
    blocks.MenuItem.update(parcel, "newFeedChannel",
        blockName = "newFeedChannel",
        title = _(u"New Feed Channel"),
        event = addFeedCollectionEvent,
        eventsForNamedLookup = [addFeedCollectionEvent],
        parentBlock = main.CollectionMenu,
    )
    
    # The hierarchy of UI elements for the FeedItem detail view
    feedItemRootBlocks = [
        # The markup bar
        detail.MarkupBar,
        detail.makeSpacer(parcel, height=6, position=0.01).install(parcel),
        
        # Author area
        detail.makeArea(parcel, "AuthorArea",
            position=0.19,
            childrenBlocks = [
                detail.makeLabel(parcel, _(u"author"), borderTop=2),
                detail.makeSpacer(parcel, width=8),
                #field("AuthorAttribute", title=u"author"),
                detail.makeEditor(parcel, "author",
                       viewAttribute=u"author",
                       border=RectType(0,2,2,2),
                       readOnly=True),                   
            ]
        ).install(parcel),
        
        # Category
        detail.makeArea(parcel, "CategoryArea",
            position=0.2,
            childrenBlocks = [
                detail.makeLabel(parcel, _(u"category"), borderTop=2),
                detail.makeSpacer(parcel, width=8),
                detail.makeEditor(parcel, "category",
                       viewAttribute=u"category",
                       border=RectType(0,2,2,2),
                       readOnly=True),
            ]
        ).install(parcel),
        
        # URL
        detail.makeArea(parcel, "LinkArea", 
            position=0.3,
            childrenBlocks = [
                detail.makeLabel(parcel, _(u"link"), borderTop=2),
                detail.makeSpacer(parcel, width=8),
                detail.makeEditor(parcel, "link",
                       viewAttribute=u"link",
                       border=RectType(0,2,2,2),
                       readOnly=True),
            ],
        ).install(parcel),
        
        # Date area
        detail.makeArea(parcel, "DateArea",
            position=0.4,
            childrenBlocks = [
                detail.makeLabel(parcel, _(u"date"), borderTop=2),
                detail.makeSpacer(parcel, width=8),
                detail.makeEditor(parcel, "date",
                       viewAttribute=u"date",
                       border=RectType(0,2,2,2),
                       readOnly=True,
                       stretchFactor=0.0,
                       size=SizeType(90, -1)),
            ],
        ).install(parcel),
        
        detail.makeSpacer(parcel, height=7, position=0.8999).install(parcel),
        
        FeedItemDetail.update(parcel, "ItemBodyArea",
            position=0.9,
            blockName="articletext",
            size=SizeType(100,50),
            minimumSize=SizeType(100,50),
        ),
    ]
    
    # The BranchSubtree ties the blocks to our FeedItem"s Kind.
    detail.makeSubtree(parcel, FeedItem, feedItemRootBlocks)

