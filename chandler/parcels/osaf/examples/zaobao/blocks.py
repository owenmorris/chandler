""" ZaoBao blocks
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Query import KindQuery
from osaf.framework.blocks.ControlBlocks import Tree, ItemDetail, ListDelegate
import osaf.examples.zaobao.RSSData as RSSData
import osaf.framework.blocks.detail.Detail as Detail

# GetZaoBaoElementValues is shared between both classes
def GetZaoBaoElementValues(element):
    if element == RSSData.RSSChannel.getKind(element.itsView):
        return ['','']

    displayName = element.getAttributeValue('displayName',
                                            default='<Untitled>')
    date = element.getAttributeValue('date', default=None)
    if not date:
        date = element.getAttributeValue('lastModified', default='')
    if date != '':
        date = date.localtime().Format('%B %d, %Y    %I:%M %p')

    return [displayName, str(date)]

class ZaoBaoListDelegate (ListDelegate):
    def GetElementParent(self, element):
        if element.itsKind is RSSData.RSSChannel.getKind(element.itsView):
            return None
        return element.channel

    def GetElementChildren(self, element):
        if element.itsKind is RSSData.RSSChannel.getKind(element.itsView):
            return element.items
        return None

    def GetElementValues(self, element):
        return GetZaoBaoElementValues(element)

    def ElementHasChildren(self, element):
        if element.itsKind is RSSData.RSSChannel.getKind(element.itsView):
            return len(element.getAttributeValue('items', default=[])) != 0
        return False

    def NeedsUpdate(self, event):
        chanUUID = self.blockItem.rootPath.itsUUID
        changedUUID = event.arguments['uuid']
        if chanUUID == changedUUID:
            self.scheduleUpdate = True

class ZaoBaoTreeDelegate (ListDelegate):
    def GetElementParent(self, element):
        chanKind = RSSData.RSSChannel.getKind(element.itsView)
        if element == chanKind:
            return None
        if element.itsKind is chanKind:
            return chanKind
        return element.channel

    def GetElementChildren(self, element):
        chanKind = RSSData.RSSChannel.getKind(element.itsView)

        if element == chanKind:
            return KindQuery().run([chanKind])

        if element.itsKind is chanKind:
            return element.items

        return None

    def GetElementValues(self, element):
        return GetZaoBaoElementValues(element)

    def ElementHasChildren(self, element):
        chanKind = RSSData.RSSChannel.getKind(element.itsView)
        if element == chanKind:
            return True

        if element.itsKind is chanKind:
            return len(element.getAttributeValue('items', default=[])) != 0

        return False

    def NeedsUpdate(self, event):
        view = self.blockItem.itsView
        item = view.findUUID(event.arguments['uuid'])
        if item.itsKind is RSSData.RSSChannel.getKind(view):
            self.scheduleUpdate = True


# XXX need to relocate this somewhere...
def onEnterPressedEvent(self, event):
    url = event.arguments['text']
    if len(url) < 5:
        return

    view = self.itsView

    view.commit()
    chan = RSSData.NewChannelFromURL(view, url, True)
    view.commit()


class ZaoBaoItemDetail(Detail.HTMLDetailArea):

    def getHTMLText(self, item):
        if item == item.itsView:
            return
        if item is not None:
            displayName = item.getAttributeValue('displayName', default='<Untitled>')

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
            HTMLText = HTMLText + '<br><a href="' + item.link + '">more...</a>'

            HTMLText = HTMLText + '</body></html>\n'

            return HTMLText



