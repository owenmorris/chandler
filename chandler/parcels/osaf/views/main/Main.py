__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from OSAF.framework.blocks.Views import View
from OSAF.framework.notifications.Notification import Notification
import wx

import OSAF.framework.utils.imports.OutlookContacts as OutlookContacts
import OSAF.contentmodel.tests.GenerateItems as GenerateItems

class MainView(View):
    """
      Main Chandler view contains event handlers for Chandler
    """
    def OnQuitEvent (self, notification):
        Globals.wxApplication.mainFrame.Close ()
        
    def OnNewTabEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def OnCloseTabEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

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
