import application.Globals as Globals
from repository.item.Query import KindQuery
from OSAF.framework.blocks.ControlBlocks import Tree
from OSAF.framework.blocks.RepositoryBlocks import wxItemDetail, ItemDetail
from OSAF.framework.notifications.Notification import Notification
import OSAF.examples.zaobao.RSSData as RSSData

import webbrowser # for opening external links

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


class wxZaoBaoItemDetail(wxItemDetail):
    def OnLinkClicked(self, wx_linkinfo):
        itemURL = wx_linkinfo.GetHref()
        item = Globals.repository.find(itemURL)

        if not item:
            webbrowser.open(itemURL)
            return

        event = Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged')
        notification = Notification(event, None, None)
        notification.SetData({'item':item, 'type':'Normal'})

        Globals.notificationManager.PostNotification (notification)

    def On_wxSelectionChanged(self, item):
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

            try:
                self.SetPage(HTMLText)
            except TypeError:
                self.SetPage('<body><html><h1>Error displaying the item</h1></body></html>')

class ZaoBaoItemDetail(ItemDetail):
    def renderOneBlock (self, parent, parentWindow):
        from OSAF.framework.blocks.Block import Block
        from wxPython.wx import wxDefaultPosition
        
        htmlWindow = wxZaoBaoItemDetail(parentWindow,
                                      Block.getwxID(self),
                                      wxDefaultPosition,
                                      (self.minimumSize.width, self.minimumSize.height))
        self.getParentBlock(parentWindow).addToContainer(parent,
                                                         htmlWindow,
                                                         self.stretchFactor,
                                                         self.Calculate_wxFlag(),
                                                         self.Calculate_wxBorder())
        return htmlWindow, None, None

    def OnSelectionChangedEvent (self, notification):
        """
          Display the item in the wxWindow counterpart.
        """
        wxWindow = Globals.association[self.getUUID()]
        wxWindow.On_wxSelectionChanged (notification.data['item'])

