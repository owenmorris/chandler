__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from Block import *
from ContainerBlocks import *
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
            callMethod (block, methodName, notification)
            for child in block.childrenBlocks:
                if child and not child.eventBoundary:
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
            updateUI = notification.data['UpdateUI']
        except KeyError:
            pass
        else:
            methodName += 'UpdateUI'

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


