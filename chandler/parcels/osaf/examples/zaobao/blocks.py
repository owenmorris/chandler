import application.Globals as Globals
from repository.item.Query import KindQuery
from OSAF.framework.blocks.ContainerBlocks import TreeList
from OSAF.framework.blocks.Views import wxItemView, ItemView
from OSAF.framework.notifications.Notification import Notification
from OSAF.examples.zaobao.RSSData import ZaoBaoParcel

class ZaoBaoTreeList(TreeList):
    def GetTreeData(self, node):
        item = node.GetData()
        if item:
            itemKind = ZaoBaoParcel.getRSSItemKind()
            chanKind = ZaoBaoParcel.getRSSChannelKind()

            if item == Globals.repository:
                for child in KindQuery().run([chanKind]):
                    names = [child.getItemDisplayName(),
                             str(child.getAttributeValue('date', default=''))]
                    node.AddChildNode(child, names, True)

            elif item.kind == ZaoBaoParcel.getRSSChannelKind():
                for child in item.items:
                    names = [child.getItemDisplayName(),
                             str(child.getAttributeValue('date', default=''))]
                    node.AddChildNode(child, names, False)

        else:
            node.AddRootNode(Globals.repository, ['//'], True)

    def OnGoToURI(self, notification):
        wxTreeListWindow = Globals.association[self.getUUID()]
        wxTreeListWindow.GoToURI(notification.data['URI'])

    def OnEnterPressedEvent(self, notification):
        from OSAF.examples.zaobao.RSSData import RSSChannel
        Globals.repository.commit()

        url = notification.GetData()['text']
        if len(url) == 0:
            return

        chan = RSSChannel()        
        chan.url = url

        import ZaoBaoAgent
        ZaoBaoAgent.UpdateChannel(chan)
        Globals.repository.commit()

        
class wxZaoBaoItemView(wxItemView):
    def OnLinkClicked(self, wx_linkinfo):
        itemURL = wx_linkinfo.GetHref()
        item = Globals.repository.find(itemURL)

        if not item:
            self.LoadPage(itemURL)
            return

        self.OnSelectionChangedEvent (item)

        arguments = {'URI':item, 'type':'Normal'}
        event = Globals.repository.find('//parcels/OSAF/framework/blocks/Events/GoToURI')
        notification = Notification(event, None, None)
        notification.SetData(arguments)
        Globals.notificationManager.PostNotification (notification)

    def OnSelectionChangedEvent(self, item):
        if item:
            displayName = item.getItemDisplayName()

            # make the html
            HTMLText = '<html><body>\n\n'

            link = item.getAttributeValue('link', default=None)
            if link:
                HTMLText = HTMLText + '<a href="%s">' % (link)
            HTMLText = HTMLText + '<h5>%s</h5>' % (displayName)
            if link:
                HTMLText = HTMLText + '</a>\n'

            desc = item.getAttributeValue('description', default=displayName)
            desc = desc.replace("<", "&lt;").replace(">", "&gt;")
            HTMLText = HTMLText + '<p>' + desc + '</p>\n\n'

            HTMLText = HTMLText + '</body></html>\n'

            self.SetPage(HTMLText)

class ZaoBaoItemView(ItemView):
    def renderOneBlock (self, parent, parentWindow):
        from OSAF.framework.blocks.Block import Block
        from wxPython.wx import wxDefaultPosition
        
        htmlWindow = wxZaoBaoItemView(parentWindow,
                                      Block.getwxID(self),
                                      wxDefaultPosition,
                                      (self.minimumSize.width, self.minimumSize.height))
        self.getParentBlock(parentWindow).addToContainer(parent,
                                                         htmlWindow,
                                                         self.stretchFactor,
                                                         self.Calculate_wxFlag(),
                                                         self.Calculate_wxBorder())
        return htmlWindow, None, None
