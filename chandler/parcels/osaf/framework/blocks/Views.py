__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from ContainerBlocks import BoxContainer
from MenuBlocks import MenuEntry
from osaf.framework.notifications.Notification import Notification
import wx

class View(BoxContainer):
    def dispatchEvent (self, notification):
        
        def callMethod (block, methodName, notification):
            """
              Call method named methodName on block
            """
            try:
                member = getattr (block, methodName)
            except AttributeError:
                return False

            """
              Comment in this code to see which events are dispatched -- DJA

            print "Calling %s" % methodName
            """

            member (notification)
            return True
        
        def bubleUpCallMethod (block, methodName, notification):
            """
              Call a method on a block or if it doesn't handle it try it's parents
            """
            while (block):
                if  callMethod (block, methodName, notification):
                    break
                block = block.parentBlock
        
        def broadcast (block, methodName, notification):
            """
              Call method named methodName on every block and it's children
            who implements it, except for the block that posted the event,
            to avoid recursive calls.
            """
            sender = notification.data['sender']
            callMethod (block, methodName, notification)
            for child in block.childrenBlocks:
                if child and not child.eventBoundary and child != sender:
                    broadcast (child, methodName, notification)

        event = notification.event
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
            """
              Find the block to dispatch to. If the sender is a menu
            we'll dispatch to the block with the focus, otherwise we'll
            dispatch to whoever 
            """
            block = notification.data['sender']
            if isinstance (block, MenuEntry):
                block = self.getFocusBlock()

            while (not block.eventBoundary and block.parentBlock):
                block = block.parentBlock
                
            broadcast (block, methodName, notification)
        elif event.dispatchEnum == 'FocusBubbleUp':
            block = self.getFocusBlock()
            bubleUpCallMethod (block, methodName, notification)

        elif event.dispatchEnum == 'ActiveViewBubbleUp':
            block = Globals.activeView
            bubleUpCallMethod (block, methodName, notification)

        elif __debug__:
            assert (False)

    def getFocusBlock (self):
        focusWindow = wx.Window_FindFocus()
        while (focusWindow):
            try:
                UUID = focusWindow.blockUUID
                return Globals.repository.find (UUID)
            except AttributeError:
                focusWindow = focusWindow.GetParent()
        return Globals.mainView


    def onSetActiveView (self, block):
        """
          Cruise up the parent hierarchy looking for the parent of the first
        menu or menuItem. If it's not the same as the last time the focus
        changed then we need to rebuild the menus.
        """
        from osaf.framework.blocks.MenuBlocks import Menu, MenuItem

        Globals.activeView = block
        while (block):
            for child in block.childrenBlocks:
                if isinstance (child, Menu) or isinstance (child, MenuItem):
                    parent = child.parentBlock
                    if parent != Globals.wxApplication.menuParent:
                        Globals.wxApplication.menuParent = parent
                        Menu.rebuildMenus(parent)
                    return
            block = block.parentBlock

