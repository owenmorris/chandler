__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
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
                member = getattr (type(block), methodName)
            except AttributeError:
                return False

            """
              Comment in this code to see which events are dispatched -- DJA

            print "Calling %s" % methodName
            """

            member (block, notification)
            return True
        
        def bubbleUpCallMethod (block, methodName, notification):
            """
              Call a method on a block or if it doesn't handle it try it's parents
            """
            while (block):
                if  callMethod (block, methodName, notification):
                    break
                block = block.parentBlock
        
        def broadcast (block, methodName, notification, childTest):
            """
              Call method named methodName on every block and it's children
            who pass the childTest except for the block that posted the event,
            to avoid recursive calls.
            """
            if block != notification.data['sender']:
                callMethod (block, methodName, notification)
            for child in block.childrenBlocks:
                if childTest (child):
                    broadcast (child, methodName, notification, childTest)

        event = notification.event
        """
          Construct method name based upon the type of the event.
        """
        try:
            methodName = event.methodName
        except AttributeError:
                methodName = 'on' + event.eventName + 'Event'

        try:
            updateUI = notification.data['UpdateUI']
        except KeyError:
            pass
        else:
            methodName += 'UpdateUI'

        dispatchEnum = event.dispatchEnum
        if dispatchEnum == 'SendToBlock':
            callMethod (event.dispatchToBlock, methodName, notification)

        elif dispatchEnum == 'BroadcastInsideMyEventBoundary':
            block = notification.data['sender']
            while (not block.eventBoundary and block.parentBlock):
                block = block.parentBlock
                
            broadcast (block,
                       methodName,
                       notification,
                       lambda child: (child is not None and
                                      child.isShown and 
                                      not child.eventBoundary))

        elif dispatchEnum == 'BroadcastInsideActiveViewEventBoundary':
            block = Globals.activeView
                
            broadcast (block,
                       methodName,
                       notification,
                       lambda child: (child is not None and
                                      child.isShown and 
                                      not child.eventBoundary))

        elif dispatchEnum == 'BroadcastEverywhere':
            broadcast (Globals.mainView,
                       methodName,
                       notification,
                       lambda child: (child is not None and child.isShown))

        elif dispatchEnum == 'FocusBubbleUp':
            block = self.getFocusBlock()
            bubbleUpCallMethod (block, methodName, notification)

        elif dispatchEnum == 'ActiveViewBubbleUp':
            block = Globals.activeView
            bubbleUpCallMethod (block, methodName, notification)

        elif __debug__:
            assert (False)

    def onSetActiveView (self, block):
        """ 
        Set a new Active View.
        The Active View is the whole right hand side of Chandler, which
        represents a coarse unit of functionality.
        
        @param block: the new active view
        @type block: C{Block}
        @param Globals.mainView.lastDynamicBlock: the last block synched
        @type lastDynamicBlock: C{DynamicBlock}, or C{False} for no previous block,
                    or C{True} for forced resync.

        """
        Globals.activeView = block

        def synchToDynamicBlock (block, isChild):
            """
            Function to set and remember the dynamic Block we synch to.
            If it's a child block, it will be used so we must sync, and 
            remember it for later.
            If it's not a child, we only need to sync if we had a different
            block last time.
            """
            previous = Globals.mainView.lastDynamicBlock
            if isChild:
                Globals.mainView.lastDynamicBlock = block
            elif previous and previous is not block:
                Globals.mainView.lastDynamicBlock = False
            else:
                return

            block.synchronizeDynamicBlocks ()

        """
          Cruise up the parent hierarchy looking for the first
        block that can act as a DynamicChild or DynamicContainer
        (Menu, MenuBar, ToolbarItem, etc). 
        If it's a child, or it's not the same Block found the last time 
        the focus changed (or if we are forcing a rebuild) then we need 
        to rebuild the Dynamic Containers.
        """
        candidate = None
        while (block):
            for child in block.childrenBlocks:
                try:
                    method = getattr (type (child), 'isDynamicChild')
                except AttributeError:
                    pass
                else:
                    if candidate is None:
                        candidate = child
                    isChild = method(child)
                    if isChild:
                        synchToDynamicBlock (child, True)
                        return
            block = block.parentBlock
        # none found, to remove dynamic additions we synch to the Active View
        #assert candidate, "Couldn't find a dynamic child to synchronize with"
        if candidate:
            synchToDynamicBlock (candidate, False)
