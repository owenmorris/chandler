import application.Globals as Globals
from repository.item.Query import KindQuery
from OSAF.framework.blocks.ControlBlocks import Tree
from OSAF.framework.blocks.RepositoryBlocks import wxItemDetail, ItemDetail
from OSAF.framework.notifications.Notification import Notification
from OSAF.examples.zaobao.RSSData import ZaoBaoParcel

class ZaoBaoList(Tree):
    def _addChildNode(self, node, child, hasKids):
        displayName = child.getAttributeValue('displayName',
                                              default='<Untitled>')
        date = child.getAttributeValue('date', default='')

        names = [displayName, str(date)]
        node.AddChildNode(child, names, hasKids)

    def GetTreeData(self, node):
        item = node.GetData()

        # handle the root node case
        if item == None:
            node.AddRootNode(Globals.repository, ['//'], True)
            return

        # add all the children to the list
        repository = self.getRepository()
        try:
            cs = self.contentSpec.data.split('.')
            channel = repository.find(str(cs[0]))
            items = channel.getAttributeValue(str(cs[1]), default=[])
        except:
            print 'error getting items'
            return

        for item in items:
            self._addChildNode(node, item, False)


    def OnGoToURI(self, notification):
        wxTreeWindow = Globals.association[self.getUUID()]
        wxTreeWindow.GoToURI(notification.data['URI'])

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


class ZaoBaoTree(Tree):
    def _addChildNode(self, node, child, hasKids):
        displayName = child.getAttributeValue('displayName',
                                              default='<Untitled>')
        date = child.getAttributeValue('date', default='')

        names = [displayName, str(date)]
        node.AddChildNode(child, names, hasKids)

    def GetTreeData(self, node):
        item = node.GetData()
        if item:
            chanKind = ZaoBaoParcel.getRSSChannelKind()

            if item.getUUID() == Globals.repository.getUUID():
                for child in KindQuery().run([chanKind]):
                    self._addChildNode(node, child, child.hasAttributeValue('items'))

            elif item.kind == chanKind:
                for child in item.items:
                    self._addChildNode(node, child, False)

        else:
            node.AddRootNode(Globals.repository, ['//'], True)

    def OnGoToURI(self, notification):
        wxTreeWindow = Globals.association[self.getUUID()]
        wxTreeWindow.GoToURI(notification.data['URI'])

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

        
class wxZaoBaoItemDetail(wxItemDetail):
    def OnLinkClicked(self, wx_linkinfo):
        itemURL = wx_linkinfo.GetHref()
        item = Globals.repository.find(itemURL)

        if not item:
            self.LoadPage(itemURL)
            return

        event = Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged')
        notification = Notification(event, None, None)
        notification.SetData({'item':item, 'type':'Normal'})

        Globals.notificationManager.PostNotification (notification)

    def On_wxSelectionChanged(self, item):
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

