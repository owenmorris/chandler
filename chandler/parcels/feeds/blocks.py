__revision__  = "$Revision:6542 $"
__date__      = "$Date:2005-08-13 16:44:24 -0700 (Sat, 13 Aug 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, logging
import application
import osaf.framework.blocks.detail.Detail as Detail
import application.Globals as Globals
import osaf.framework.blocks.Block as Block
from PyICU import ICUtzinfo, DateFormat
import datetime
import channels
from i18n import OSAFMessageFactory as _
from application import schema

logger = logging.getLogger(__name__)

class FeedItemDetail(Detail.HTMLDetailArea):
    def getHTMLText(self, item):
        if item == item.itsView:
            return
        if item is not None:
            displayName = item.getAttributeValue('displayName',
                                                 default=_('<Untitled>'))

            # make the html
            HTMLText = '<html><body>\n\n'

            link = item.getAttributeValue('link', default=None)
            if link:
                HTMLText = HTMLText + '<a href="%s">' % (link)
            HTMLText = HTMLText + '<h5>%s</h5>' % (displayName)
            if link:
                HTMLText = HTMLText + '</a>\n'

            content = item.getAttributeValue('content', default=None)
            if content:
                content = content.getReader().read()
            else:
                content = displayName
            #desc = desc.replace("<", "&lt;").replace(">", "&gt;")
            HTMLText = HTMLText + '<p>' + content + '</p>\n\n'
            #should find a good way to localize "more..."
            HTMLText = HTMLText + '<br><a href="' + str(item.link) + \
                '">more...</a>'

            HTMLText = HTMLText + '</body></html>\n'

            return HTMLText


class LinkDetail(Detail.StaticRedirectAttribute):
    def staticTextLabelValue(self, item):
        theLabel = unicode(item.getAttributeValue(Detail.GetRedirectAttribute(item, self.whichAttribute())))
        return theLabel


class DateDetail(Detail.StaticRedirectAttribute):
    def staticTextLabelValue(self, item):
        try:
            value = item.getAttributeValue(Detail.GetRedirectAttribute(item,
                self.whichAttribute()))
        except AttributeError:
            return ""

        # [@@@] grant: Refactor to use code in AttributeEditors?
        aujourdhui = datetime.date.today() # naive
        userTzinfo = ICUtzinfo.getDefault()
        if value.tzinfo is None:
            value = value.replace(tzinfo=userTzinfo)
        else:
            value = value.astimezone(userTzinfo)

        if aujourdhui == value.date():
            format = DateFormat.createTimeInstance(DateFormat.kShort)
        else:
            format = DateFormat.createDateTimeInstance(DateFormat.kShort)
        return unicode(format.format(value))



class FeedController(Block.Block):
    def onNewFeedChannelEvent(self, event):
        import wx
        url = application.dialogs.Util.promptUser(wx.GetApp().mainFrame,
            _("New Channel"), _("Enter a URL for the RSS Channel"), "http://")
        if url and url != "":
            try:
                # create the feed channel
                channel = channels.NewChannelFromURL(view=self.itsView, url=url,
                                                     update=True)

                # now post the new collection to the sidebar
                mainView = Globals.views[0]
                mainView.postEventByName ('AddToSidebarWithoutCopying',
                    {'items': [channel]})
                return [channel]
            except:
                application.dialogs.Util.ok(wx.GetApp().mainFrame,
                    _("New Channel Error"),
                    _("Could not create channel for %s\nCheck the URL and try again.") % url)
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

    blocks.MenuItem.update(parcel, "NewFeedChannel",
        blockName = "NewFeedChannelItem",
        title = "New Feed Channel",
        event = NewFeedChannelEvent,
        eventsForNamedLookup = [NewFeedChannelEvent],
        parentBlock = main.NewItemMenu,
    )

    # detail view stuff

    # Shortcut for creating a detail-view attribute label
    def label(name, title):
        return detail.StaticRedirectAttributeLabel.update(
            parcel, name, title=title,
            characterStyle = blocks.LabelStyle, stretchFactor = 0.0,
            textAlignmentEnum = "Right", minimumSize = blocks.SizeType(60, 24),
            border = blocks.RectType(0, 0, 0, 5),
        )

    # Shortcut for creating a detail-view attribute editor
    def field(name, title, stretchFactor=0.0):
        return detail.StaticRedirectAttribute.update(
            parcel, name, title=title,
            characterStyle=blocks.LabelStyle, stretchFactor=stretchFactor,
            textAlignmentEnum = "Left",
        )

    # Shortcut for creating a label/field editing area
    def pair(name, **kw):
        return detail.DetailSynchronizedLabeledTextAttributeBlock.update(
            parcel, name, stretchFactor = 0.0,
            border = blocks.RectType(5, 0, 0, 5), **kw
        )

    detail.DetailTrunkSubtree.update(parcel, "ChannelSubtree",

        # This ensures that this detail view gets attached to feed items
        key = feeds.FeedItem.getKind(parcel.itsView),

        # UI Elements for detail view
        rootBlocks = [
            detail.MarkupBar,

            FeedItemDetail.update(parcel, "ItemBodyArea",
                blockName = "articletext",
                size = blocks.SizeType(100,50),
                minimumSize = blocks.SizeType(100,50),
            ),

            # URL
            pair("LinkArea", selectedItemsAttribute="link", position=0.3,
                childrenBlocks = [
                    label("LinkLabel", title="link"),
                    LinkDetail.update(parcel, "LinkAttribute",
                        characterStyle = blocks.CharacterStyle.update(
                            parcel, "LinkStyle",
                            fontFamily = "DefaultUIFont",
                            fontSize = 10, fontStyle = "underline",
                        ),
                        # huh, I only seem to be able to apply this to whole
                        # ContentItemDetail items:
                        #
                        # colorStyle = blocks.ColorStyle.update(
                        #     parcel, "LinkColor",
                        #     foregroundColor = blocks.ColorType(0,0,255,255),
                        # ),
                        stretchFactor = 0.0,
                        textAlignmentEnum = "Left",
                        title = "linkattribute",
                    ),
                ],
            ),

            # Author area
            pair("AuthorArea", selectedItemsAttribute="author", position=0.19,
                childrenBlocks = [
                    label("AuthorLabel", title="author"),
                    field("AuthorAttribute", title="author"),
                ]
            ),

            # Date area
            pair("DateArea", selectedItemsAttribute="date", position=0.4,
                childrenBlocks = [
                    label("DateLabel", title="date"),
                    DateDetail.update(parcel, "DateAttribute",
                        title="date",
                        characterStyle=blocks.LabelStyle,
                        stretchFactor=0.0,
                        textAlignmentEnum="Left",
                    ),
                ],
            ),

            # Category
            pair("CategoryArea", selectedItemsAttribute="category",
                position=0.2,
                childrenBlocks = [
                    label("CategoryLabel", title="category"),
                    field("CategoryAttribute",
                        title="category", stretchFactor=1.0
                    ),
                ]
            ),
        ],
    )

