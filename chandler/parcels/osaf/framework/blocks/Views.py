
import application.Globals as Globals
from Block import Block
from ContainerBlocks import BoxContainer, HTML
from OSAF.framework.notifications.Notification import Notification
from wxPython.wx import *
from wxPython.html import *


class View(BoxContainer):

    def dispatchEvent (self, notification):
        
        def callMethod (block, methodName, notification):
            """
              Call method named methodName on block
            """
            try:
                member = getattr (block, methodName)
                member (notification)
                return True
            except AttributeError:
                return False
        
        def broadcast (block, methodName, notification):
            """
              Call method named methodName on every block and it's children
            who implements it
            """
            if block:
                callMethod (block, methodName, notification)
                for child in block.childrenBlocks:
                    broadcast (child, methodName, notification)

        event = notification.event
        """
          Find the block with the focus
        """
        block = self.getFocusBlock()
        """
          Construct method name based upon the type of the event.
        """
        methodName = event.methodName

        try:
            if notification.data['type'] == 'UpdateUI':
                methodName += 'UpdateUI'
        except KeyError:
            pass

        if event.dispatchEnum == 'SendToBlock':
            callMethod (event.dispatchToBlock, methodName, notification)
        elif event.dispatchEnum == 'Broadcast':
            while (not block.eventBoundary and block.parentBlock):
                block = block.parentBlock
                
            broadcast (block, methodName, notification)
        elif event.dispatchEnum == 'BubbleUp':
            while (block):
                if callMethod (block, methodName, notification):
                    break
                block = block.parentBlock
        elif __debug__:
            assert (False)


    def getFocusBlock (self):
        focusWindow = wxWindow_FindFocus()
        while (focusWindow):
            try:
                UUID = focusWindow.counterpartUUID
                return Globals.repository.find (UUID)
            except AttributeError:
                focusWindow = focusWindow.GetParent()
        return Globals.mainView

    
    def onSetFocus (self):
        """
          Cruise up the parent hierarchy looking for the parent of the first
        menu or menuItem. If it's not the same as the last time the focus
        changed then we need to rebuild the menus.
        """
        from OSAF.framework.blocks.MenuBlocks import Menu, MenuItem

        block = self.getFocusBlock()
        while (block):
            for child in block.childrenBlocks:
                if isinstance (child, Menu) or isinstance (child, MenuItem):
                    parent = child.parentBlock
                    if parent != Globals.wxApplication.menuParent:
                        Globals.wxApplication.menuParent = parent
                        Menu.rebuildMenus(parent)
                    return
            block = block.parentBlock


    def OnQuitEvent (self, notification):
        Globals.wxApplication.mainFrame.Close ()
        
    def OnUndoEventUpdateUI (self, notification):
        notification.data ['Text'] = 'Undo Command\tCtrl+Z'

    def OnCutEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def OnCopyEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def OnPasteEventUpdateUI (self, notification):
        notification.data ['Enable'] = False


class wxItemView(wxHtmlWindow):
    def OnLinkClicked(self, wx_linkinfo):
        itemURL = wx_linkinfo.GetHref()
        item = Globals.repository.find(itemURL)
        self.OnSelectionChangedEvent (item)

        arguments = {'URI':item, 'type':'Normal'}
        event = Globals.repository.find('//parcels/OSAF/framework/blocks/Events/GoToURI')
        notification = Notification(event, None, None)
        notification.SetData(arguments)
        Globals.notificationManager.PostNotification (notification)

    def OnSelectionChangedEvent(self, item):
        def formatReference(reference):
            """
              Formats the a reference attribute to be clickable, etcetera
            """
            url = reference.getItemPath()
            if reference.hasAttributeValue('kind'):
                kind = reference.kind.getItemName()
            else:
                kind = "(kindless)"
            # Originally I was masking the fallback to itemName here just like in
            # the listview, but that doesn't work for many of the more primitive
            # repository items, so I stopped doing that.
            dn = str(reference.getItemDisplayName())
    
            # Escape < and > for HTML display
            kind = kind.replace("<", "&lt;").replace(">", "&gt;")
            dn = dn.replace("<", "&lt;").replace(">", "&gt;")
    
            return "<a href=\"%(url)s\">%(kind)s: %(dn)s</a>" % locals()

        if item:
            displayName = item.getItemDisplayName()

            try:
                kind = item.kind.getItemName()
            except AttributeError:
                kind = "(kindless)"
            
            HTMLText = "<html><body><h5>%s: %s</h5><ul>" % (kind, displayName)
            HTMLText = HTMLText + "<li><b>Path:</b> %s" % item.getItemPath()
            HTMLText = HTMLText + "<li><b>UUID:</b> %s" % item.getUUID()
            HTMLText = HTMLText + "</ul><h5>Attributes</h5><ul>"
    
            # We build tuples (name, formatted) for all value-only, then
            # all reference-only. Then we concatenate the two lists and sort
            # the result, and append that to the HTMLText.
            valueAttr = []
            for k, v in item.iterAttributes(valuesOnly=True):
                if isinstance(v, dict):
                    tmpList = ["<li><b>%s:</b></li><ul>" % k]
                    for attr in v:
                        attrString = str(attr)
                        attrString = attrString.replace("<", "&lt;")
                        attrString = attrString.replace(">", "&gt;")
                        tmpList.append("<li>%s</li>" % attrString)
                    tmpList.append("</ul>")
                    valueAttr.append((k, "".join(tmpList)))
                else:
                    value = str(v)
                    value = value.replace("<", "&lt;")
                    value = value.replace(">", "&gt;")
                    valueAttr.append((k,"<li><b>%s: </b>%s</li>" % (k, value)))
    
            refAttrs = []
            for k, v in item.iterAttributes(referencesOnly=True):
                if isinstance(v, dict) or isinstance(v, list):
                    tmpList = ["<li><b>%s:</b></li><ul>" % k]
                    for attr in v:
                        tmpList.append("<li>%s</li>" % formatReference(attr))
                    tmpList.append("</ul>")
                    refAttrs.append((k, "".join(tmpList)))
                else:
                    value = formatReference(v)
                    refAttrs.append((k,"<li><b>%s: </b>%s</li>" % (k, value)))
    
            allAttrs = refAttrs + valueAttr
            allAttrs.sort()
            dyn_html = "".join([y for x, y in allAttrs])
    
            HTMLText = "%s%s</ul></body></html>" % (HTMLText, dyn_html)
        else:
            HTMLText = "<html><body><h5>Item Viewer</h5></body></html>"

        self.SetPage(HTMLText)


class ItemView(HTML):
    def renderOneBlock (self, parent, parentWindow):
        htmlWindow = wxItemView(parentWindow,
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
          Display the given Item's details in an HTML window.
        """
        item = notification.data['node'].GetData()
        wxItemViewWindow = Globals.association[self.getUUID()]
        wxItemViewWindow.OnSelectionChangedEvent (item)

