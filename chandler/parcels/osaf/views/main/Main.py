__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from osaf.framework.blocks.Views import View
from osaf.framework.notifications.Notification import Notification
import wx
import os
import application.Application
from application.SplashScreen import SplashScreen
from application.Parcel import Manager as ParcelManager
from osaf.mail.imap import IMAPDownloader
import osaf.framework.utils.imports.OutlookContacts as OutlookContacts
import osaf.contentmodel.tests.GenerateItems as GenerateItems
from repository.persistence.RepositoryError import VersionConflictError

class MainView(View):
    """
      Main Chandler view contains event handlers for Chandler
    """
    def onNULLEvent (self, notification):
        """ The NULL Event handler """
        pass

    def onNULLEventUpdateUI (self, notification):
        """ The NULL Event is always disabled """
        notification.data ['Enable'] = False

    def onQuitEvent (self, notification):
        Globals.wxApplication.mainFrame.Close ()

    def onUndoEventUpdateUI (self, notification):
        notification.data ['Text'] = "Can't Undo\tCtrl+Z"
        notification.data ['Enable'] = False

    def onRedoEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onCutEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onCopyEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onPasteEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onPreferencesEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onSharingSubscribeToCollectionEvent(self, notification):
        url =  application.Application.promptUser( \
         Globals.wxApplication.mainFrame, "Subscribe to Collection...", 
         "Collection URL:", "http://webdav.osafoundation.org/")
        if url is not None:
            print "I would be subscribing to %s here" % url


    def onEditMailAccountEvent (self, notification):
        account = \
         Globals.repository.findPath('//parcels/osaf/mail/IMAPAccount One')
        if application.Application.promptForItemValues(
         Globals.wxApplication.mainFrame,
         "IMAP Account",
         account,
         [
           { "attr":"serverName", "label":"IMAP Server" },
           { "attr":"accountName", "label":"Username" },
           { "attr":"password", "label":"Password", "password":True },
         ]
        ):
            try:
                Globals.repository.commit()
            except VersionConflictError, e:
                # A first experiment with resolving conflicts.  Not sure
                # yet where the logic for handling this should live.  Could
                # be here, could be handled by the conflicting item itself(?).

                # Retrieve the conflicting item
                conflict = e.getItem()
                itemPath = conflict.itsPath
                serverName = conflict.serverName
                accountName = conflict.accountName
                password = conflict.password
                print "Got a conflict with item:", itemPath
                # The conflict item has *our* values in it; to see the
                # values that were committed by the other thread, we need
                # to cancel our transaction, commit, and refetch the item.
                Globals.repository.cancel()
                # Get the latest items committed from other threads
                Globals.repository.commit()
                # Refetch item
                account = Globals.repository.findPath(itemPath)
                # To resolve this conflict we're going to simply reapply the 
                # values that were set in the dialog box.
                account.serverName = serverName
                account.accountName = accountName
                account.password = password
                Globals.repository.commit()
                # Note: this commit, too, could get a conflict I suppose, so
                # do we need to put this sort of conflict resolution in a loop?
                print "Conflict resolved"


    def onGetNewMailEvent (self, notification):
        accountList = [Globals.repository.findPath('//parcels/osaf/mail/IMAPAccount One')]
        account = accountList[0]
        IMAPDownloader (account).getMail()

    # Test Methods

    def onGenerateContentItemsEvent(self, notification):
        GenerateItems.GenerateNotes(2)
        GenerateItems.generateCalendarEventItems(2, 30)
        GenerateItems.GenerateContacts(2)
        Globals.repository.commit()

    def onGenerateCalendarEventItemsEvent(self, notification):
        GenerateItems.generateCalendarEventItems(10, 30)
        Globals.repository.commit()

    def onGenerateContactsEvent(self, notification):
        GenerateItems.GenerateContacts(10)
        Globals.repository.commit()

    def onImportContactsEvent(self, notification):
        x=OutlookContacts.OutlookContacts().processFile()

    def onGenerateNotesEvent(self, notification):
        GenerateItems.GenerateNotes(10)
        Globals.repository.commit()

    def onCheckRepositoryEvent(self, notification):

        repository = Globals.repository
        repository.logger.info('Checking repository...')
        if repository.check():
            repository.logger.info('Check completed successfully')
        else:
            repository.logger.info('Check completed with errors')

    def onShowPyCrustEvent(self, notification):
        Globals.wxApplication.ShowDebuggerWindow()

    def onReloadParcelsEvent(self, notification):
        ParcelManager.getManager().loadParcels()

    def onCommitRepositoryEvent(self, notification):
        Globals.repository.commit()

    def onAboutChandlerEvent(self, notification):
        """
          Show the splash screen in response to the about command
        """
        pageLocation = os.path.join ('application', 'welcome.html')
        splash = SplashScreen(None, _("About Chandler"), 
                              pageLocation, False, False)
        splash.Show(True)

