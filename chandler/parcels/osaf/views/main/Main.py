__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from osaf.framework.blocks.Views import View
from osaf.framework.notifications.Notification import Notification
import wx
import os
import application.dialogs.AccountPreferences
import application.dialogs.Util
import osaf.contentmodel.mail.Mail as Mail
from application.SplashScreen import SplashScreen
from application.Parcel import Manager as ParcelManager
from osaf.mail.imap import IMAPDownloader
import osaf.framework.utils.imports.OutlookContacts as OutlookContacts
import osaf.contentmodel.tests.GenerateItems as GenerateItems
from repository.persistence.RepositoryError import VersionConflictError
import repository.util.UUID as UUID
import osaf.framework.sharing.Sharing



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
        # Triggered from "Tests | Subscribe to collection..."
        osaf.framework.sharing.Sharing.manualSubscribeToCollection()

    def onEditAccountPreferencesEvent (self, notification):
        # Triggered from "File | Prefs | Accounts..."
        application.dialogs.AccountPreferences.ShowAccountPreferencesDialog(Globals.wxApplication.mainFrame)

    def onEditMailAccountEvent (self, notification):
        # @@@ Deprecated, replaced by onEditAccountPreferencesEvent, above

        account = \
         Globals.repository.findPath('//parcels/osaf/mail/IMAPAccountOne')
        if application.dialogs.Util.promptForItemValues(
         Globals.wxApplication.mainFrame,
         "IMAP Account",
         account,
         [
           { "attr":"host", "label":"IMAP Server" },
           { "attr":"username", "label":"Username" },
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
                host = conflict.host
                username = conflict.username
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
                account.host = host
                account.username = username
                account.password = password
                Globals.repository.commit()
                # Note: this commit, too, could get a conflict I suppose, so
                # do we need to put this sort of conflict resolution in a loop?
                print "Conflict resolved"


    def onGetNewMailEvent (self, notification):
        accountList = [Globals.repository.findPath('//parcels/osaf/mail/IMAPAccountOne')]
        account = accountList[0]
        IMAPDownloader (account).getMail()

    def onNewEvent (self, notification):
        # create a new content item
        event = notification.event
        itemName = 'Anonymous'+str(UUID.UUID())
        newItem = event.kindParameter.newItem (itemName, self)
        newItem.InitOutgoingAttributes ()
        Globals.repository.commit()

        # lookup our selectionChangedEvents
        rootPath = '//parcels/osaf/framework/blocks/Events/'
        sidebarSelectionChanged = Globals.repository.findPath \
                                (rootPath + 'SelectionChangedSentToSidebar')
        activeViewSelectionChanged = Globals.repository.findPath \
                                   (rootPath + 'SelectionChangedBroadcastEverywhere')

        # Tell the sidebar we want to go to the 'All' box
        args = {}
        args['itemName'] = 'AllTableView'
        self.Post(sidebarSelectionChanged, args)

        # Tell the ActiveView to select our new item
        args = {}
        args['item'] = newItem
        self.Post(activeViewSelectionChanged, args)

    def onNewEventUpdateUI (self, notification):
        notification.data ['Enable'] = True

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
        self.rerender ()

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

    def getSidebarSelectedCollection (self):
        """
          Return the sidebar's selected item collection.

          The sidebar is a table, whose contents is a collection.
        The selection is a table (one of the splitters), 
        whose contents is a collection.
        """
        sidebarPath = '//parcels/osaf/views/main/Sidebar'
        sidebar = Globals.repository.findPath (sidebarPath)
        selectedBlock = sidebar.selection
        assert selectedBlock, "No selected block in the Sidebar"
        try:
            selectionContents = selectedBlock.contents
        except AttributeError:
            selectionContents = None
        return selectionContents

    def onShareCollectionEvent (self, notification):
        # Triggered from "Test | Share collection..."
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            osaf.framework.sharing.Sharing.manualPublishCollection(collection)

    def onShareCollectionEventUpdateUI (self, notification):
        """
        Update the menu to reflect the selected collection name
        """
        collection = self.getSidebarSelectedCollection ()
        notification.data ['Enable'] = collection is not None
        if collection:
            menuTitle = 'Share collection "%s"' \
                    % collection.displayName
        else:
            menuTitle = 'Share a collection'
        notification.data ['Text'] = menuTitle

    def onSyncCollectionEvent (self, notification):
        # Triggered from "Test | Sync collection..."
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            osaf.framework.sharing.Sharing.syncCollection(collection)

    def onSyncCollectionEventUpdateUI (self, notification):
        """
        Update the menu to reflect the selected collection name
        """
        collection = self.getSidebarSelectedCollection ()
        if collection is not None and collection.hasAttributeValue('sharedURL'):
            notification.data ['Enable'] = True
        else:
            notification.data ['Enable'] = False
        if collection:
            menuTitle = 'Sync collection "%s"' \
                    % collection.displayName
        else:
            menuTitle = 'Sync a collection'
        notification.data ['Text'] = menuTitle

