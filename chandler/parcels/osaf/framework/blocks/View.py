
from ContainerBlocks import BoxContainer
import application.Globals as Globals
from wxPython.wx import *


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
            callMethod (block, methodName, notification)
            for child in block.childrenBlocks:
                broadcast (child, methodName, event)

        event = notification.data['event']
        """
          Find the block with the focus
        """
        block = self.getFocusBlock()
        """
          Construct method name based upon the name of the event.
        """
        methodName = 'on_' + event.name.replace ('/', '_')

        if notification.data['type'] == 'UpdateUI':
            methodName += '_UpdateUI'

        if event.dispatchEnum == 'SendToBlock':
            callMethod (event.dispatchToBlock, methodName, notification)
        elif event.dispatchEnum == 'Broadcast':
            broadcast (event.dispatchToBlock, methodName, notification)
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
        return Globals.topView

    
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


    def on_block_Quit (self, notification):
        Globals.wxApplication.mainFrame.Close ()
        
    def on_block_Undo_UpdateUI (self, notification):
        notification.data ['Text'] = 'Undo Command\tCtrl+Z'

    def on_block_Cut_UpdateUI (self, notification):
        notification.data ['Enable'] = False

    def on_block_Copy_UpdateUI (self, notification):
        notification.data ['Enable'] = False

    def on_block_Paste_UpdateUI (self, notification):
        notification.data ['Enable'] = False

    def on_block_GetTreeListData (self, notification):
        node = notification.data['node']
        item = node.GetData()
        if item:
            for child in item:
                node.AddChildNode (child, child.getItemName(), child.hasChildren())
        else:
            node.AddRootNode (Globals.repository, '//', True)
