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
from PyICU import ICUtzinfo, DateFormat
import datetime
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
            #should find a good way to localize "more..."
            HTMLText = HTMLText + u'<br><a href="' + unicode(item.link) + \
                u'">more...</a>'

            HTMLText = HTMLText + '</body></html>\n'

            return HTMLText

class FeedController(Block.Block):
    def onNewFeedChannelEvent(self, event):
        import wx
        url = application.dialogs.Util.promptUser(
            _(u"New Channel"),
            _(u"Enter a URL for the RSS Channel"),
            defaultValue = "http://")
        if url and url != "":
            try:
                # create the feed channel
                channel = channels.newChannelFromURL(view=self.itsView, url=url)
                schema.ns("osaf.app", self).sidebarCollection.add (channel)
                self.itsView.commit() # To make the channel avail to feedsView
                channel.refresh() # an async task

                return [channel]
            except:
                application.dialogs.Util.ok(wx.GetApp().mainFrame,
                    _(u"New Channel Error"),
                    _(u"Could not create channel for %(url)s\nCheck the URL and try again.") % {'url': url})
                raise

def installParcel(parcel, oldVersion=None):

    detail = schema.ns('osaf.framework.blocks.detail', parcel)
    blocks = schema.ns('osaf.framework.blocks', parcel)
    main   = schema.ns('osaf.views.main', parcel)
    feeds  = schema.ns('feeds', parcel)

    feed_controller = FeedController.update(parcel, "feed_controller")

    NewFeedChannelEvent = blocks.BlockEvent.update(
        parcel, "NewFeedChannelEvent",
        blockName="NewFeedChannel",
        dispatchEnum="SendToBlockByReference",
        destinationBlockReference=feed_controller,
        commitAfterDispatch=True,
    )

    blocks.MenuItem.update(parcel, 'FeedsParcelSeparator',
                           blockName = 'FeedsParcelSeparator',
                           menuItemKind = 'Separator',
                           parentBlock = main.CollectionMenu)

    blocks.MenuItem.update(parcel, "NewFeedChannel",
        blockName = "NewFeedChannelItem",
        title = _(u"New Feed Channel"),
        event = NewFeedChannelEvent,
        eventsForNamedLookup = [NewFeedChannelEvent],
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
