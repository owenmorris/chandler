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
import osaf.mail.imap
import osaf.contentmodel.contacts.Contacts as Contacts
import osaf.contentmodel.tests.GenerateItems as GenerateItems
import osaf.framework.sharing.Sharing as Sharing
import repository.query.Query as Query
from repository.item.Query import KindQuery
from repository.item.Item import Item
import osaf.mail.sharing as MailSharing
import osaf.mail.smtp as smtp


class MainView(View):
    """
      Main Chandler view contains event handlers for Chandler
    """
    def displaySMTPSendError (self, mailMessage):
        """
          Called when the SMTP Send generated an error.
        """
        if mailMessage is not None and mailMessage.isOutbound:
            """@@@DLD - Select the message in CPIA"""
    
            errorStrings = []
    
            for error in mailMessage.deliveryExtension.deliveryErrors:
                 errorStrings.append(error.errorString)
   
            if len (errorStrings) == 0:
                errorMessage = _("An unknown error occurred.")
            else:
                if len (errorStrings) == 1:
                    str = _("error")
                else:
                    str = _("errors")
   
                errorMessage = _("The following %s occurred. %s") % (str, ', '.join(errorStrings))
                errorMessage = errorMessage.encode ('utf-8')
            self.setStatusMessage (errorMessage, alert=True)
        
    def displaySMTPSendSuccess (self, mailMessage):
        """
          Called when the SMTP Send was successful.
        """
        if mailMessage is not None and mailMessage.isOutbound:
            self.setStatusMessage (_('Mail "%s" sent.') % mailMessage.about)

    def onAboutEvent(self, notification):
        # The "Help | About Chandler..." menu item
        """
          Show the splash screen in response to the about command
        """
        import version
        pageLocation = os.path.join ('application', 'welcome.html')
        html = ''
        for line in open(pageLocation):
            if line.find('@@buildid@@') >= 0:
                line = "<p>Build identifier: '%s'</p>" % version.build
            html += line
        splash = SplashScreen(None, _("About Chandler"), 
                              None, html, False, False)
        splash.Show(True)

    def onCopyEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onCutEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onDeleteEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onEditAccountPreferencesEvent (self, notification):
        # Triggered from "File | Prefs | Accounts..."
        application.dialogs.AccountPreferences.ShowAccountPreferencesDialog(Globals.wxApplication.mainFrame)

    def onNewEvent (self, notification):
        # Create a new Content Item
        # Triggered from "File | New Item" menu, for any of the item kinds.
        event = notification.event
        newItem = event.kindParameter.newItem (None, None)
        newItem.InitOutgoingAttributes ()
        self.RepositoryCommitWithStatus ()

        # Tell the sidebar we want to go to the All or contacts box
        if newItem.isItemOf (Contacts.ContactsParcel.getContactKind ()):
            itemName = 'ContactsView'
        else:
            itemName = 'AllView'
        self.PostEventByName ('RequestSelectSidebarItem', {'itemName':itemName})

        # Tell the ActiveView to select our new item
        self.PostEventByName ('SelectItemBroadcastInsideActiveView', {'item':newItem})

    def onPasteEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onPreferencesEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onQuitEvent (self, notification):
        Globals.wxApplication.mainFrame.Close ()

    def onRedoEventUpdateUI (self, notification):
        notification.data ['Enable'] = False

    def onUndoEventUpdateUI (self, notification):
        notification.data ['Text'] = _("Can't Undo\tCtrl+Z")
        notification.data ['Enable'] = False

    def onNewEventUpdateUI (self, notification):
        notification.data ['Enable'] = True

    def RepositoryCommitWithStatus (self):
        """
          Do a repository commit with notice posted in the Status bar.
        """
        self.setStatusMessage (_("committing changes to the repository..."))
        Globals.repository.commit()
        self.setStatusMessage ('')

    def selectView(self, view, showInDetailView=False):
        """
          Given a view, select it in the sidebar. 
        Optionally display an item in the detail view.
        @param view: the view to select in the sidebar
        @type view: C{Block}
        @param showInDetailView: the item (or None) for the Detail View; False disables
        @type showInDetailView: C{Item} or None.  False disables notifying the Detail View.
        """

        # Tell the sidebar we want to select this view
        self.PostEventByName('RequestSelectSidebarItem', {'item':view})

        if showInDetailView is not False:
            # Tell the ActiveView to select the item (usually a collection)
            # It will pass the item on to the Detail View.
            self.PostEventByName ('SelectItemBroadcastInsideActiveView', {'item':showInDetailView})

    def setStatusMessage (self, statusMessage, progressPercentage=-1, alert=False):
        """
          Allows you to set the message contained in the status bar.  You can also specify 
        values for the progress bar contained on the right side of the status bar.  If you
        specify a progressPercentage (as a float 0 to 1) the progress bar will appear.  If 
        no percentage is specified the progress bar will disappear.
        """
        Globals.wxApplication.mainFrame.GetStatusBar().blockItem.setStatusMessage (statusMessage, progressPercentage)
        if alert:
            application.dialogs.Util.ok(Globals.wxApplication.mainFrame,
             "", statusMessage)
            self.setStatusMessage ('')

    def onSendMailEvent (self, notification):
        # put a "committing" message into the status bar
        self.setStatusMessage ('Committing changes...')

        # commit changes, since we'll be switching to Twisted thread
        Globals.repository.commit()
    
        # get default SMTP account
        item = notification.data ['item']
        account = item.defaultSMTPAccount ()

        # put a sending message into the status bar
        self.setStatusMessage ('Sending mail...')

        # Now send the mail
        smtp.SMTPSender(account, item).sendMail()

    def onShareItemEvent (self, notification):
        """
          Share an ItemCollection.
        """
        itemCollection = notification.data ['item']

        # commit changes, since we'll be switching to Twisted thread
        self.RepositoryCommitWithStatus()

        # show status
        self.setStatusMessage (_("Sharing collection %s") % itemCollection.displayName)
    
        # check that it's not already shared, and we have the sharing account set up.
        url = self.SharingURL (itemCollection)

        # build list of invitees.
        if len (self.SharingInvitees (itemCollection)) == 0:
            self.setStatusMessage (_("No sharees!"))
            return


        # change the name to include "Shared", but first record the
        # original name in case webdav publishing fails and we need to
        # restore it
        originalName = itemCollection.displayName
        if not "Shared" in itemCollection.displayName:
            itemCollection.displayName = _("%s (Shared)") % itemCollection.displayName
        # @@@ Update the sidebar to display new collection name (hack for 0.4)
        sidebarPath = '//parcels/osaf/views/main/Sidebar'
        sidebar = Globals.repository.findPath (sidebarPath)
        sidebar.synchronizeWidget()

        # Sync the collection with WebDAV
        self.setStatusMessage (_("accessing WebDAV server"))
        try:
            Sharing.putCollection(itemCollection, url)
        except:
            # An error occurred during webdav; restore the collection's name
            itemCollection.displayName = originalName
            raise

        # Send out sharing invites
        inviteeStringsList = self.SharingInvitees (itemCollection)
        self.setStatusMessage (_("inviting %s") % inviteeStringsList)
        self.SendSharingInvitations (itemCollection, url)

        # Done
        self.setStatusMessage (_("Sharing initiated."))

    def SharingInvitees (self, itemCollection):
        # return the list of sharing invitees
        inviteeStringsList = []
        try:
            invitees = itemCollection.sharees
        except AttributeError:
            invitees = []
        for entity in invitees:
            inviteeStringsList.append (entity.emailAddress)
        return inviteeStringsList

    # Test Methods

    def getSidebarSelectedCollection (self):
        """
          Return the sidebar's selected item collection.

          The sidebar is a table, whose contents is a collection.
        The selection is a table (one of the splitters), 
        whose contents is a collection.
        """
        sidebarPath = '//parcels/osaf/views/main/Sidebar'
        sidebar = Globals.repository.findPath (sidebarPath)
        selectedBlock = sidebar.contents [sidebar.widget.GetGridCursorRow ()]
        assert selectedBlock, "No selected block in the Sidebar"
        try:
            selectionContents = selectedBlock.contents
        except AttributeError:
            selectionContents = None
        return selectionContents

    def _logChange(self, item, version, status, values, references):
        logger = item.itsView.logger
        logger.info("%s %d 0x%0.4x\n  values: %s\n  refs: %s",
                    Item.__repr__(item), version, status, values, references)

    def onCheckRepositoryEvent(self, notification):
        # triggered from "Test | Check Repository" Menu
        repository = Globals.repository
        checkingMessage = _('Checking repository...')
        repository.logger.info(checkingMessage)
        self.setStatusMessage (checkingMessage)
        if repository.check():
            successMessage = _('Check completed successfully')
            repository.logger.info (successMessage)
            self.setStatusMessage (successMessage)
        else:
            errorMessage = _('Check completed with errors')
            repository.logger.info (errorMessage)
            self.setStatusMessage (errorMessage)

    def onCommitRepositoryEvent(self, notification):
        # Test menu item
        self.RepositoryCommitWithStatus ()

    def onGenerateCalendarEventItemsEvent(self, notification):
        GenerateItems.generateCalendarEventItems(10, 30)
        Globals.repository.commit()

    def onGenerateContactsEvent(self, notification):
        GenerateItems.GenerateContacts(10)
        Globals.repository.commit()

    def onGenerateContentItemsEvent(self, notification):
        # triggered from "Test | Generate Content Items" Menu
        GenerateItems.GenerateNotes(2) 
        GenerateItems.generateCalendarEventItems(2, 30)
        GenerateItems.GenerateTasks(2)
        GenerateItems.GenerateEventTasks(2)
        # GenerateItems.GenerateContacts(2) 
        Globals.repository.commit() 

    def onGenerateNotesEvent(self, notification):
        GenerateItems.GenerateNotes(10)
        Globals.repository.commit()

    def onGetNewMailEvent (self, notification):
        # Triggered from "Test | Get Mail" menu

        if not Sharing.isMailSetUp():
            if application.dialogs.Util.okCancel( \
             Globals.wxApplication.mainFrame,
             "Account information required",
             "Please set up your accounts."):
                if not application.dialogs.AccountPreferences.ShowAccountPreferencesDialog( \
                 Globals.wxApplication.mainFrame):
                    return
            else:
                return

        account = osaf.mail.imap.getIMAPAccount()

        Globals.repository.commit()
        osaf.mail.imap.IMAPDownloader (account).getMail()
        Globals.repository.refresh()

    def onLogRepositoryHistoryEvent(self, notification):
        # triggered from "Test | Log Repository History" Menu
        repository = Globals.repository
        repository.logger.info("Items changed outside %s since last commit:", repository.view)
        repository.mapHistory(self._logChange)

    def onLogViewChangesEvent(self, notification):
        # triggered from "Test | Log View Changes" Menu
        repository = Globals.repository
        repository.logger.info("Items changed in %s:", repository.view)
        Globals.repository.mapChanges(self._logChange)

    def onReloadParcelsEvent(self, notification):
        # Test menu item
        ParcelManager.getManager().loadParcels()
        # @@@DLD figure out why rerender fails on the new wxWidgets
        # self.rerender ()

    def onResendSharingInvitationsEvent (self, notification):
        """
          Resend the sharing invitations for the selected collection.
        The "Test | Resend Sharing Invitations" menu item
        """
        itemCollection = self.getSidebarSelectedCollection ()
        url = self.SharingURL (itemCollection)
        self.SendSharingInvitations (itemCollection, url)

    def onResendSharingInvitationsEventUpdateUI (self, notification):
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            isShared = Sharing.isShared (collection)
            notification.data ['Enable'] = isShared
        else:
            notification.data ['Enable'] = False

    def onSharingSubscribeToCollectionEvent(self, notification):
        # Triggered from "Tests | Subscribe to collection..."
        Sharing.manualSubscribeToCollection()

    def onShowColumnEventUpdateUI (self, notification):
        notification.data ['Enable'] = False
        notification.data ['Check'] = True

    def onShowPyCrustEvent(self, notification):
        # Test menu item
        Globals.wxApplication.ShowDebuggerWindow()

    def onShareCollectionEvent (self, notification):
        # Triggered from "Test | Share collection..."
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            Sharing.manualPublishCollection(collection)

    def onShareCollectionEventUpdateUI (self, notification):
        """
        Update the menu to reflect the selected collection name
        """
        # Only enable if user has set their webdav account up
        if not self.webDAVAccountIsSetup ():
            notification.data ['Enable'] = False
            return

        collection = self.getSidebarSelectedCollection ()
        notification.data ['Enable'] = collection is not None
        if collection:
            menuTitle = _('Share collection "%s"') \
                    % collection.displayName
        else:
            menuTitle = _('Share a collection')
        notification.data ['Text'] = menuTitle

    def onShareOrManageEvent (self, notification):
        """
          Share the collection selected in the Sidebar. 
        If the current collection is already shared, then manage the collection.
        In either case, the real work here is to tell the summary
        view to deselect, and the detail view that the selection has
        changed to the entire summary view's collection.
        The "Collection | Share collection " menu item
        """
        if not self.webDAVAccountIsSetup():
            # The user hasn't set up webdav, so let's bring up the accounts
            # dialog, with the webdav account selected
            webdavAccount = Globals.repository.findPath('//parcels/osaf/framework/sharing/WebDAVAccount')
            application.dialogs.AccountPreferences.ShowAccountPreferencesDialog(Globals.wxApplication.mainFrame, account=webdavAccount)
            return

        # Tell the ActiveView to select the collection
        # It will pass the collection on to the Detail View.

        self.PostEventByName ('SelectItemBroadcastInsideActiveView', {'item':self.getSidebarSelectedCollection ()})

    def onShareOrManageEventUpdateUI (self, notification):
        """
        Update the menu to reflect the selected collection name
        """
        collection = self.getSidebarSelectedCollection ()
        accountOK = self.webDAVAccountIsSetup ()
        if accountOK and collection is not None:
            # notification.data['Enable'] = True
            if Sharing.isShared (collection):
                menuTitle = _('Manage collection "%s"') % collection.displayName
            else:
                menuTitle = _('Share collection "%s"') % collection.displayName
        else:
            # notification.data['Enable'] = False
            menuTitle = _('Share a collection')
        notification.data ['Text'] = menuTitle

    def onSyncCollectionEvent (self, notification):
        # Triggered from "Test | Sync collection..."
        Globals.repository.commit() 
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            Sharing.syncCollection(collection)

    def onSyncCollectionEventUpdateUI (self, notification):
        """
        Update the menu to reflect the selected collection name
        """
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            menuTitle = _('Sync collection "%s"') % collection.displayName
            if Sharing.isShared(collection):
                notification.data['Enable'] = True
            else:
                notification.data['Enable'] = False
        else:
            notification.data['Enable'] = False
            menuTitle = _('Sync a collection')
        notification.data ['Text'] = menuTitle

    def onSyncWebDAVEvent (self, notification):
        """
          Synchronize WebDAV sharing.
        The "File | Sync | WebDAV" menu item
        """
        # commit repository changes before synch
        self.RepositoryCommitWithStatus()

        # find all the shared collections and sync them.
        self.setStatusMessage (_("checking shared collections"))
        collections = self.sharedWebDAVCollections ()
        if len (collections) == 0:
            self.setStatusMessage (_("No shared collections found"))
            return
        for collection in collections:
            self.setStatusMessage (_("synchronizing %s") % collection)
            Sharing.syncCollection(collection)

        # synch mail
        self.setStatusMessage (_("Sharing synchronized."))

    def onSyncWebDAVEventUpdateUI (self, notification):
        accountOK = self.webDAVAccountIsSetup ()
        sharedCollections = self.sharedWebDAVCollections ()
        enable = accountOK and len (sharedCollections) > 0
        notification.data ['Enable'] = enable
        # @@@DLD set up the help string to let the user know why it's disabled

    def onSyncAllEvent (self, notification):
        """
          Synchronize Mail and all sharing.
        The "File | Sync | All" menu item
        """
        # find all the shared collections and sync them.
        self.onSyncWebDAVEvent (notification)

        if not Sharing.isMailSetUp():
            if application.dialogs.Util.okCancel( \
             Globals.wxApplication.mainFrame,
             "Account information required",
             "Please set up your accounts."):
                if not application.dialogs.AccountPreferences.ShowAccountPreferencesDialog( \
                 Globals.wxApplication.mainFrame):
                    return
            else:
                return

        # synch mail
        self.setStatusMessage (_("Getting new Mail"))
        self.onGetNewMailEvent (notification)

    def SendSharingInvitations (self, itemCollection, url):
        """
          Send Sharing invitations to all invitees.
        """
        inviteeStringsList = self.SharingInvitees (itemCollection)
        MailSharing.sendInvitation(url, itemCollection.displayName, inviteeStringsList)

    def SharingURL (self, itemCollection):
        # Return the url used to share the itemCollection.
        if Sharing.isShared (itemCollection):
            url = str (itemCollection.sharedURL)
        else:
            path = Sharing.getWebDavPath()
            if path:
                url = "%s/%s" % (path, itemCollection.itsUUID)
            else:
                self.setStatusMessage (_("You need to set up the server and path in the account dialog!"),
                                       alert=True)
                return
            url = url.encode ('utf-8')
        return url

    def sharedWebDAVCollections (self):
        # return the list of all the shared collections
        # @@@DLD - use new query, once it can handle method calls, or when our item.isShared
        #  attribute is correctly set.
        UseNewQuery = False
        if UseNewQuery:
            qString = u"for i in '//parcels/osaf/contentmodel/ItemCollection' where len (i.sharedURL) > 0"
            collQuery = Query.Query (Globals.repository, qString)
            collQuery.recursive = False
            collections = []
            for item in collQuery:
                collections.append (item)
        else:
            itemCollectionKind = Globals.repository.findPath("//parcels/osaf/contentmodel/ItemCollection")
            allCollections = KindQuery().run([itemCollectionKind])
            collections = []
            for collection in allCollections:
                if Sharing.isShared (collection):
                    collections.append (collection)
        return collections

    def webDAVAccountIsSetup (self):
        # return True iff the webDAV account is set up
        return Sharing.getWebDavPath() != None
        
