__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from ContainerBlocks import BoxContainer
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
        
        def broadcast (block, methodName, notification, stopAtEventBoundary = True):
            """
              Call method named methodName on every block and it's children
            who implements it, except for the block that posted the event,
            to avoid recursive calls.
            """
            if block != notification.data['sender']:
                callMethod (block, methodName, notification)
            for child in block.childrenBlocks:
                if child and not (stopAtEventBoundary and child.eventBoundary):
                    broadcast (child, methodName, notification, stopAtEventBoundary)

        event = notification.event
        """
          Construct method name based upon the type of the event.
        """
        try:
            methodName = event.methodName
        except AttributeError:
            methodName = 'on' + event.itsName + 'Event'

        try:
            updateUI = notification.data['UpdateUI']
        except KeyError:
            pass
        else:
            methodName += 'UpdateUI'

        if event.dispatchEnum == 'SendToBlock':
            callMethod (event.dispatchToBlock, methodName, notification)

        elif event.dispatchEnum == 'BroadcastInsideMyEventBoundary':
            block = notification.data['sender']
            while (not block.eventBoundary and block.parentBlock):
                block = block.parentBlock
                
            broadcast (block, methodName, notification)

        elif event.dispatchEnum == 'BroadcastEverywhere':
            broadcast (Globals.mainView, methodName, notification, stopAtEventBoundary = False)

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
                return focusWindow.blockItem
            except AttributeError:
                focusWindow = focusWindow.GetParent()
        return Globals.mainView


    def onSetActiveView (self, block):
        """ 
        Set a new Active View.
        The Active View is the whole right hand side of Chandler, which
        represents a coarse unit of functionality.
        """
        import DynamicContainerBlocks as DynamicContainerBlocks
        Globals.activeView = block
        # function to set and remember the dynamic Block we synch to
        def synchToDynamicBlock(block):
            if block != Globals.mainView.lastDynamicParent:
                Globals.mainView.lastDynamicParent = block
                if block is None:
                    block = Globals.activeView
                DynamicContainerBlocks.DynamicContainer.\
                                      synchronizeDynamicBlocks(block)
        """
          Cruise up the parent hierarchy looking for the parent of the first
        DynamicChild (Menu, MenuBar, ToolbarItem, etc). 
        If it's not the same as the last time the focus changed then we need 
        to rebuild the Dynamic Containers.
        """
        while (block):
            for child in block.childrenBlocks:
                if isinstance (child, DynamicContainerBlocks.DynamicBlock):
                    synchToDynamicBlock(block)
                    return
            block = block.parentBlock
        # none found, to remove dynamic additions we synch to the Active View
        synchToDynamicBlock(None)
            
