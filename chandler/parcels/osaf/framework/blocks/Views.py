__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import logging
import application.Globals as Globals
from Block import *
from ContainerBlocks import *
from MenuBlocks import MenuEntry
from OSAF.framework.notifications.Notification import Notification
from wxPython.wx import *
from wxPython.html import *

import OSAF.framework.utils.imports.OutlookContacts as OutlookContacts
import OSAF.contentmodel.tests.GenerateItems as GenerateItems

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
            try:
                updateUI = notification.data['UpdateUI']
            except KeyError:
                print "Calling %s" % methodName
            """
            member (notification)
            return True
        
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
        elif event.dispatchEnum == 'BubbleUp':
            block = self.getFocusBlock()
            while (block):
                if  callMethod (block, methodName, notification):
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


    """
      Some placeholders for handling events.
    """
    def OnQuitEvent (self, notification):
        Globals.wxApplication.mainFrame.Close ()
        
    def OnUndoEventUpdateUI (self, notification):
        notification.data ['Text'] = 'Undo Command\tCtrl+Z'
        notification.data ['Enable'] = False

    def OnRedoEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def OnCutEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def OnCopyEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def OnPasteEventUpdateUI (self, notification):
        notification.data ['Enable'] = False
        
    def OnPreferencesEventUpdateUI (self, notification):
        notification.data ['Enable'] = False
        
    # Test Methods

    def OnGenerateContentItems(self, notification):
        GenerateItems.GenerateCalendarEvents(5, 30)
        GenerateItems.GenerateContacts(5)
        Globals.repository.commit()

    def OnGenerateCalendarEvents(self, notification):
        GenerateItems.GenerateCalendarEvents(10, 30)
        Globals.repository.commit()

    def OnGenerateContacts(self, notification):
        GenerateItems.GenerateContacts(10)
        Globals.repository.commit()

    def OnImportContacts(self, notification):
        x=OutlookContacts.OutlookContacts().processFile()

    def OnGenerateNotes(self, notification):
        GenerateItems.GenerateNotes(10)
        Globals.repository.commit()

    def OnCheckRepository(self, notification):

        repository = Globals.repository
        repository.logger.info('Checking repository...')
        if repository.check():
            repository.logger.info('Check completed successfully')
        else:
            repository.logger.info('Check completed with errors')
