""" ZaoBao blocks
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from repository.item.Query import KindQuery
from OSAF.framework.blocks.ControlBlocks import Tree, ItemDetail
import OSAF.examples.zaobao.RSSData as RSSData

class ZaoBaoListDelegate:
    def ElementParent(self, element):
        if element.kind == RSSData.ZaoBaoParcel.getRSSChannelKind():
            return None
        return element.channel

    def ElementChildren(self, element):
        if element.kind == RSSData.ZaoBaoParcel.getRSSChannelKind():
            return element.items
        return None

    def ElementCellValues(self, element):
        if element.kind == RSSData.ZaoBaoParcel.getRSSChannelKind():
            return ['','']
        
        displayName = element.getAttributeValue('displayName',
                                                default='<Untitled>')
        date = element.getAttributeValue('date', default='')
        if date != '':
            date = date.Format('%B %d, %Y    %I:%M %p')

        return [displayName, str(date)]

    def ElementHasChildren(self, element):
        if element.kind == RSSData.ZaoBaoParcel.getRSSChannelKind():
            return len(element.getAttributeValue('items', default=[])) != 0
        return False

    def NeedsUpdate(self, notification):
        return True


class ZaoBaoTreeDelegate:
    def ElementParent(self, element):
        chanKind = RSSData.ZaoBaoParcel.getRSSChannelKind()
        if element == chanKind:
            return None
        if element.kind == chanKind:
            return chanKind
        return element.channel

    def ElementChildren(self, element):
        chanKind = RSSData.ZaoBaoParcel.getRSSChannelKind()

        if element == chanKind:
            return KindQuery().run([chanKind])

        if element.kind == chanKind:
            return element.items

        return None

    def ElementCellValues(self, element):
        if element == RSSData.ZaoBaoParcel.getRSSChannelKind():
            return ['','']

        displayName = element.getAttributeValue('displayName',
                                                default='<Untitled>')
        date = element.getAttributeValue('date', default='')
        if date != '':
            date = date.Format('%B %d, %Y    %I:%M %p')

        return [displayName, str(date)]

    def ElementHasChildren(self, element):
        chanKind = RSSData.ZaoBaoParcel.getRSSChannelKind()
        if element == chanKind:
            return True

        if element.kind == chanKind:
            return len(element.getAttributeValue('items', default=[])) != 0

        return False

    def NeedsUpdate(self, notification):
        return True


# XXX need to relocate this somewhere...
def OnEnterPressedEvent(self, notification):
    url = notification.GetData()['text']
    if len(url) < 5:
        return

    Globals.repository.commit()
    chan = RSSData.NewChannelFromURL(url, True)
    Globals.repository.commit()

class ZaoBaoItemDetail(ItemDetail):

    def getHTMLText(self, item):
        if item == Globals.repository.view:
            return
        if item:
            displayName = item.getAttributeValue('displayName', default='<Untitled>')

            # make the html
            HTMLText = '<html><body>\n\n'

            link = item.getAttributeValue('link', default=None)
            if link:
                HTMLText = HTMLText + '<a href="%s">' % (link)
            HTMLText = HTMLText + '<h5>%s</h5>' % (displayName)
            if link:
                HTMLText = HTMLText + '</a>\n'

            desc = item.getAttributeValue('description', default=displayName)
            #desc = desc.replace("<", "&lt;").replace(">", "&gt;")
            HTMLText = HTMLText + '<p>' + desc + '</p>\n\n'

            HTMLText = HTMLText + '</body></html>\n'

            return HTMLText



