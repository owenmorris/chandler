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


import os, logging
import application
import osaf.framework.blocks.detail.Detail as Detail
import application.Globals as Globals
import osaf.framework.blocks.Block as Block
import channels
from i18n import OSAFMessageFactory as _
from osaf import messages 
from application import schema
from osaf.pim.structs import SizeType, RectType

logger = logging.getLogger(__name__)

class FeedItemDetail(Detail.HTMLDetailArea):
    def getHTMLText(self, item):
        if item == item.itsView:
            return
        if item is not None:
            displayName = item.getAttributeValue('displayName',
                                                 default=u'<' + messages.UNTITLED + u'>')

            # make the html
            HTMLText = u'<html><body>\n\n'

            link = item.getAttributeValue('link', default=None)
            if link:
                HTMLText = HTMLText + u'<a href="%s">' % (link)
            HTMLText = HTMLText + u'<h5>%s</h5>' % (displayName)
            if link:
                HTMLText = HTMLText + u'</a>\n'

            content = item.getAttributeValue('content', default=None)
            if content:
                content = content.getReader().read()
            else:
                content = displayName
            #desc = desc.replace("<", "&lt;").replace(">", "&gt;")
            HTMLText = HTMLText + u'<p>' + content + u'</p>\n\n'
            if link:
                HTMLText = HTMLText + u'<br><a href="' + unicode(item.link) + u'">' + _(u'more...') + u'</a>'

            HTMLText = HTMLText + '</body></html>\n'

            return HTMLText

class AddFeedCollectionEvent(Block.AddToSidebarEvent):
    def onNewItem (self):
        def calledInMainThread(channelUUID, success):
            # This method is called once the feed has been processed.  If all
            # is okay, success will be True, otherwise False.
            self.itsView.refresh()
            channel = self.itsView.findUUID(channelUUID)
            
            if not channel.isEstablished and not success:
                url = application.dialogs.Util.promptUser(
                    _(u"The provided URL seems to be invalid"),
                    _(u"Enter a URL for the RSS Channel"),
                    defaultValue = unicode(channel.url))
                if url != None:
                    try:
                        url = str(url)
                        channel.displayName = url
                        channel.url = channel.getAttributeAspect('url', 'type').makeValue(url)
                        channel.isEstablished = False
                        channel.isPreviousUpdateSuccessful = True
                        channel.logItem = None
                        channel.itsView.commit()
                        channel.refresh(callback=calledInTwisted) # an async task
                    except:
                        application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                                    _(u"New Channel Error"),
                                                    _(u"Could not create channel for %(url)s\nCheck the URL and try again.") % {'url': url})

        def calledInTwisted(channelUUID, success):
            # This callback is what we really pass to twisted, and it will
            # invoke the calledInMainThread method in -- what else -- the
            # main thread
            wx.GetApp().PostAsyncEvent(calledInMainThread, channelUUID, success)

        # get an URL from the user, ...
        import wx
        url = application.dialogs.Util.promptUser(
            _(u"New Channel"),
            _(u"Enter a URL for the RSS Channel"),
            defaultValue = u"http://")
        if url == None:
            return None
        
        # ... and then try to create a new channel.
        try:
            # create the feed channel
            channel = channels.newChannelFromURL(view=self.itsView, url=url)
            self.itsView.commit() # To make the channel avail to feedsView
            channel.refresh(callback=calledInTwisted) # an async task
        except:
            application.dialogs.Util.ok(wx.GetApp().mainFrame,
                _(u"New Channel Error"),
                _(u"Could not create channel for %(url)s\nCheck the URL and try again.") % {'url': url})
            return None
        
        # return succesfully
        return channel

def installParcel(parcel, oldVersion=None):

    detail = schema.ns('osaf.framework.blocks.detail', parcel)
    blocks = schema.ns('osaf.framework.blocks', parcel)
    main   = schema.ns('osaf.views.main', parcel)
    feeds  = schema.ns('feeds', parcel)

    # Create an AddFeedCollectionEvent that adds an RSS collection to the sidebar.
    addFeedCollectionEvent = AddFeedCollectionEvent.update(
        parcel, 'addFeedCollectionEvent',
        blockName = 'addFeedCollectionEvent')

    # Add a separator to the "Collection" menu ...
    blocks.MenuItem.update(parcel, 'FeedsParcelSeparator',
                           blockName = 'FeedsParcelSeparator',
                           menuItemKind = 'Separator',
                           parentBlock = main.CollectionMenu)

    # ... and, below it, a menu item to subscribe to a RSS feed.
    blocks.MenuItem.update(parcel, "NewFeedChannel",
        blockName = "NewFeedChannelItem",
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
                detail.makeEditor(parcel, 'author',
                       viewAttribute=u'author',
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
                detail.makeEditor(parcel, 'category',
                       viewAttribute=u'category',
                       border=RectType(0,2,2,2),
                       readOnly=True),
            ]
        ).install(parcel),

        # URL
        detail.makeArea(parcel, "LinkArea", 
            position=0.3,
            childrenBlocks = [
                detail.makeLabel(parcel, _(u'link'), borderTop=2),
                detail.makeSpacer(parcel, width=8),
                detail.makeEditor(parcel, 'link',
                       viewAttribute=u'link',
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
                detail.makeEditor(parcel, 'date',
                       viewAttribute=u'date',
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
    
    # The BranchSubtree ties the blocks to our FeedItem's Kind.
    detail.makeSubtree(parcel, feeds.FeedItem, feedItemRootBlocks)
