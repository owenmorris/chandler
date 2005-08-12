__revision__  = "$Revision$"
__date__      = "$Date$"
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


logger = logging.getLogger(__name__)

class FeedItemDetail(Detail.HTMLDetailArea):
    def getHTMLText(self, item):
        if item == item.itsView:
            return
        if item is not None:
            displayName = item.getAttributeValue('displayName',
                                                 default='<Untitled>')

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
            "New Channel", "Enter a URL for the RSS Channel", "http://")
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
                    "New Channel Error",
                    "Could not create channel for " + url + \
                    "\nCheck the URL and try again.")
                raise
