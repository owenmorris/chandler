__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from osaf.framework.blocks.Views import View
from datetime import timedelta
from time import time
import wx, os, sys, traceback
import application.dialogs.AccountPreferences
import application.dialogs.Util
import osaf.mail.imap
from application.SplashScreen import SplashScreen
import application.Parcel
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.contacts.Contacts as Contacts
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.tests.GenerateItems as GenerateItems
import osaf.framework.sharing.Sharing as Sharing
import repository.query.Query as Query
from repository.item.Query import KindQuery
from repository.item.Item import Item
import application.Printing as Printing
import osaf.framework.blocks.calendar.CollectionCanvas as CollectionCanvas
from osaf.framework.blocks.ControlBlocks import Timer
import osaf.mail.sharing as MailSharing
import osaf.mail.smtp as smtp
import application.dialogs.ReminderDialog as ReminderDialog
from osaf.framework.blocks.Block import Block
from osaf.contentmodel.ItemCollection import ItemCollection
import osaf.framework.sharing.ICalendar as ICalendar

class MainView(View):
    """
      Main Chandler view contains event handlers for Chandler
    """
    def displaySMTPSendError (self, mailMessage):
        """
          Called when the SMTP Send generated an error.
        """
        if mailMessage is not None and mailMessage.isOutbound:
            """ Maybe we should select the message in CPIA? """
    
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
        
        # If this was a sharing invitation, find its collection and remove the
        # successfully-notified addressees from the invites list.
        try:
            (url, collectionName) = MailSharing.getSharingHeaderInfo(mailMessage)
        except KeyError:
            pass
        else:
            share = Sharing.findMatchingShare(self.itsView, url)
            itemCollection = share.contents
            
            for addresseeContact in mailMessage.toAddress:
                if addresseeContact in itemCollection.invitees:
                    itemCollection.invitees.remove(addresseeContact)

    def onAboutEvent(self, event):
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
                              None, html, True, False)
        splash.Show(True)

    def onCopyEventUpdateUI (self, event):
        event.arguments ['Enable'] = False

    def onCutEventUpdateUI (self, event):
        event.arguments ['Enable'] = False

    def onRemoveEventUpdateUI (self, event):
        event.arguments ['Enable'] = False

    def onEditAccountPreferencesEvent (self, event):
        # Triggered from "File | Prefs | Accounts..."

        # Handy during development:
        reload(application.dialogs.AccountPreferences)

        application.dialogs.AccountPreferences.ShowAccountPreferencesDialog(wx.GetApp().mainFrame, view=self.itsView)

    def onNewEvent (self, event):
        # Create a new Content Item
        # Triggered from "File | New Item" menu, for any of the item kinds.
        newItem = event.kindParameter.newItem (None, None)
        newItem.InitOutgoingAttributes ()
        self.RepositoryCommitWithStatus ()

        # Tell the sidebar we want to go to the All collection
        self.postEventByName ('RequestSelectSidebarItem', {'itemName':u"All"})

        # Tell the ActiveView to select our new item
        self.postEventByName ('SelectItemBroadcastInsideActiveView', {'item':newItem})

    def onPasteEventUpdateUI (self, event):
        event.arguments ['Enable'] = False
        
    def onPrintPreviewEvent (self, event):
        self.printEvent(True)
        
    def onPrintEvent (self, event):
        self.printEvent(False)

    def printEvent(self, isPreview):
        try:
            activeView = Globals.views [1]
        except IndexError:
            pass
        else:
            for canvas in activeView.childrenBlocks:
                if isinstance(canvas, CollectionCanvas.CollectionBlock):
                    printObject = Printing.Printing(wx.GetApp().mainFrame, canvas.widget)
                    if isPreview:
                        printObject.OnPrintPreview()
                    else:
                        printObject.OnPrint()
                    return
        message = "Printing is currently only supported when viewing week or day view of the calendar."
        dialog = wx.MessageDialog(None, message, 'Chandler', wx.OK | wx.ICON_INFORMATION)
        dialog.ShowModal()
        dialog.Destroy()
        

    def onPreferencesEventUpdateUI (self, event):
        event.arguments ['Enable'] = False

    def onQuitEvent (self, event):
        wx.GetApp().mainFrame.Close ()

    def onRedoEventUpdateUI (self, event):
        event.arguments ['Enable'] = False

    def onUndoEventUpdateUI (self, event):
        event.arguments ['Text'] = _("Can't Undo\tCtrl+Z")
        event.arguments ['Enable'] = False

    def onNewEventUpdateUI (self, event):
        event.arguments ['Enable'] = True

    def RepositoryCommitWithStatus (self):
        """
          Do a repository commit with notice posted in the Status bar.
        """
        self.setStatusMessage (_("committing changes to the repository..."))
        self.itsView.commit()
        self.setStatusMessage ('')

    def setStatusMessage (self, statusMessage, progressPercentage=-1, alert=False):
        """
          Allows you to set the message contained in the status bar.  You can also specify 
        values for the progress bar contained on the right side of the status bar.  If you
        specify a progressPercentage (as a float 0 to 1) the progress bar will appear.  If 
        no percentage is specified the progress bar will disappear.
        """
        wx.GetApp().mainFrame.GetStatusBar().blockItem.setStatusMessage (statusMessage, progressPercentage)
        if alert:
            application.dialogs.Util.ok(wx.GetApp().mainFrame,
             "", statusMessage)
            self.setStatusMessage ('')

    def onSendShareItemEventUpdateUI(self, event):
        # If we get asked about this, and it hasn't already been set, there's no selected 
        # item in the detail view - disallow sending. Also, make sure the label's set back to "Send"
        event.arguments ['Enable'] = False
        # @@@BJS Just as in DetailRoot.onSendShareItemEventUpdateUI, it'd be nice to just
        # set the Text in the event to update the label of this toolbaritem, but that doesn't work.
        # Do it the hard way.
        toolbarItem = event.arguments['sender']
        toolbarItem.widget.SetLabel(_("Send"))
        toolbarItem.parentBlock.widget.Realize()

    def onSendMailEvent (self, event):
        # commit changes, since we'll be switching to Twisted thread
        self.RepositoryCommitWithStatus()
    
        # get default SMTP account
        item = event.arguments ['item']
        account = Mail.MailParcel.getSMTPAccount(self.itsView)[0]

        # put a sending message into the status bar
        self.setStatusMessage ('Sending mail...')

        # Now send the mail
        smtp.SMTPSender(self.itsView.repository, account, item).sendMail()

    def onShareItemEvent (self, event):
        """
          Share an ItemCollection.
        """
        itemCollection = event.arguments ['item']

        # Make sure we have all the accounts; returns False if the user cancels out and we don't.
        if not Sharing.ensureAccountSetUp(self.itsView):
            return
        webdavAccount = Sharing.getWebDAVAccount(self.itsView)

        # commit changes, since we'll be switching to Twisted thread
        self.RepositoryCommitWithStatus()

        # show status
        self.setStatusMessage (_("Sharing collection %s") % itemCollection.displayName)
                
        # Get or make a share for this item collection
        share = Sharing.getShare(itemCollection)
        isNewShare = share is None
        if isNewShare:
            share = Sharing.newOutboundShare(self.itsView, itemCollection, account=webdavAccount)
        
        # Copy the invitee list into the share's list. As we go, collect the addresses we'll notify.
        if len (itemCollection.invitees) == 0:
            self.setStatusMessage (_("No invitees!"))
            return
        inviteeList = []
        inviteeStringsList = []

        for invitee in itemCollection.invitees:
            inviteeList.append(invitee)
            inviteeStringsList.append(invitee.emailAddress)
            inviteeContact = Contacts.Contact.getContactForEmailAddress(self.itsView, invitee.emailAddress)

            if not inviteeContact in share.sharees:
                share.sharees.append(inviteeContact)

        # change the name to include "Shared", but first record the
        # original name in case webdav publishing fails and we need to
        # restore it
        originalName = itemCollection.displayName
        if not itemCollection.displayName.endswith(_(" (Shared)")):
            itemCollection.displayName = _("%s (Shared)") % itemCollection.displayName

        # Sync the collection with WebDAV
        self.setStatusMessage (_("accessing WebDAV server"))
        try:
            if isNewShare:
                share.create()
            share.put()
        except:
            # An error occurred during webdav; restore the collection's name
            itemCollection.displayName = originalName
            raise

        # Send out sharing invites
        self.setStatusMessage (_("inviting %s") % ", ".join(inviteeStringsList))
        MailSharing.sendInvitation(itemCollection.itsView.repository, share.conduit.getLocation(), 
                                   itemCollection, inviteeList)
        
        # Done
        self.setStatusMessage (_("Sharing initiated."))

    def onStartProfilerEvent(self, event):
        Block.profileEvents = True
            
        
    def onStopProfilerEvent(self, event):
        Block.profileEvents = False
    # Test Methods

    def getSidebarSelectedCollection (self):
        """
          Return the sidebar's selected item collection.
        """
        item = Block.findBlockByName ("Sidebar").selectedItemToView
        if not isinstance (item, ItemCollection):
            item = None
        return item
        
        return Block.findBlockByName ("Sidebar").selectedItemToView

    def _logChange(self, item, version, status, values, references):
        logger = item.itsView.logger
        logger.info("%s %d 0x%0.4x\n  values: %s\n  refs: %s",
                    Item.__repr__(item), version, status, values, references)

    def onCheckRepositoryEvent(self, event):
        # triggered from "Test | Check Repository" Menu
        repository = self.itsView.repository
        checkingMessage = _('Checking repository...')
        repository.logger.info(checkingMessage)
        self.setStatusMessage(checkingMessage)
        before = time()
        if repository.check():
            after = time()
            successMessage = _('Check completed successfully in %s'
                               %(timedelta(seconds=after-before)))
            repository.logger.info(successMessage)
            self.setStatusMessage(successMessage)
        else:
            errorMessage = _('Check completed with errors')
            repository.logger.info(errorMessage)
            self.setStatusMessage(errorMessage)

    def onImportIcalendarEvent(self, event):
        # triggered from "Test | Import iCalendar" Menu
        self.setStatusMessage ("Importing from import.ics")
        try:
            share = Sharing.OneTimeFileSystemShare('.', 'import.ics',
                            ICalendar.ICalendarFormat, view=self.itsView)
            share.get()
            self.setStatusMessage ("Import completed")
        except:
            trace = "".join(traceback.format_exception (*sys.exc_info()))
            self.itsView.getLogger().info("Failed importFile:\n%s" % trace)
            self.setStatusMessage("Import failed")

    def onExportIcalendarEvent(self, event):
        # triggered from "Test | Export Events as iCalendar" Menu
        eventKind = Calendar.CalendarEvent.getKind(self.itsView)
        self.setStatusMessage ("Exporting to export.ics")
        try:
            share = Sharing.OneTimeFileSystemShare('.', 'export.ics',
                            ICalendar.ICalendarFormat, view=self.itsView)
            collection = ItemCollection(view=self.itsView)
            events = KindQuery().run([eventKind])
            for event in events:
                collection.add(event)
            share.contents = collection
            share.put()
            self.setStatusMessage("Export completed")
        except:
            trace = "".join(traceback.format_exception (*sys.exc_info()))
            self.itsView.getLogger().info("Failed exportFile:\n%s" % trace)
            self.setStatusMessage("Export failed")

    def onCommitRepositoryEvent(self, event):
        # Test menu item
        self.RepositoryCommitWithStatus ()
        
    # temporary until we can add this dynamically
    def onNewZaoBaoChannelEvent(self, event):
        url = application.dialogs.Util.promptUser(wx.GetApp().mainFrame, "New Channel", "Enter a URL for the RSS Channel", "http://")
        if url and url != "":
            try: 
                # create the zaobao channel
                channel = osaf.examples.zaobao.RSSData.NewChannelFromURL(view=self.itsView, url=url, update=True)
                
                # now post the new collection to the sidebar
                mainView = Globals.views[0]
                mainView.postEventByName ('AddToSidebarWithoutCopying', {'items': [channel.items]})
                self.itsView.commit()
            except:
                application.dialogs.Util.ok(wx.GetApp().mainFrame, "New Channel Error", 
                    "Could not create channel for " + url + "\nCheck the URL and try again.")
                raise

    def onGenerateCalendarEventItemsEvent(self, event):
        GenerateItems.generateCalendarEventItems(self.itsView, 10, 30)
        self.itsView.commit()

    def onGenerateContactsEvent(self, event):
        GenerateItems.GenerateContacts(self.itsView, 10)
        self.itsView.commit()

    def onGenerateContentItemsEvent(self, event):
        # triggered from "Test | Generate Content Items" Menu
        view = self.itsView
        GenerateItems.GenerateNotes(view, 2) 
        GenerateItems.generateCalendarEventItems(view, 2, 30)
        GenerateItems.GenerateTasks(view, 2)
        GenerateItems.GenerateEventTasks(view, 2)
        # GenerateItems.GenerateContacts(view, 2)
        view.commit() 

    def onGenerateNotesEvent(self, event):
        GenerateItems.GenerateNotes(self.itsView, 10)
        self.itsView.commit()

    def onMimeTestEvent (self, event):
        self.__loadMailTests ("mime_tests")

    def oni18nMailTestEvent (self, event):
        self.__loadMailTests ("i18n_tests")


    def __loadMailTests (self, dir):
        import osaf.mail.utils as utils
        utils.loadMailTests(self.itsView, dir)
        self.itsView.refresh()

    def onGetNewMailEvent (self, event):
        # Triggered from "Test | Get Mail" menu

        if not Sharing.isMailSetUp(self.itsView):
            if application.dialogs.Util.okCancel( \
             wx.GetApp().mainFrame,
             "Account information required",
             "Please set up your accounts."):
                if not application.dialogs.AccountPreferences.ShowAccountPreferencesDialog( \
                 wx.GetApp().mainFrame, view=self.itsView):
                    return
            else:
                return


        view = self.itsView
        view.commit()
        for account in Mail.MailParcel.getActiveIMAPAccounts(self.itsView):
            osaf.mail.imap.IMAPDownloader(view.repository, account).getMail()
        view.refresh()

    def onLogRepositoryHistoryEvent(self, event):
        # triggered from "Test | Log Repository History" Menu
        repository = self.itsView.repository
        repository.logger.info("Items changed outside %s since last commit:", repository.view)
        repository.mapHistory(self._logChange)

    def onLogViewChangesEvent(self, event):
        # triggered from "Test | Log View Changes" Menu
        repository = self.itsView.repository
        repository.logger.info("Items changed in %s:", repository.view)
        repository.mapChanges(self._logChange)

    def onReloadParcelsEvent(self, event):
        theApp = wx.GetApp()
        theApp.UnRenderMainView ()

        application.Parcel.Manager.get(self.itsView).loadParcels()

        theApp.LoadMainViewRoot (delete=True)
        theApp.RenderMainView ()

    def onSharingSubscribeToCollectionEvent(self, event):
        # Triggered from "Tests | Subscribe to collection..."
        Sharing.manualSubscribeToCollection(self.itsView)

    def onSharingImportDemoCalendarEvent(self, event):
        # Triggered from "Tests | Import demo calendar..."
        Sharing.loadDemoCalendar(self.itsView)

    def onSharingSubscribeToICalendarEvent(self, event):

        # Triggered from "Tests | Subscribe to ICalendar..."
        import osaf.framework.sharing.ICalendarSubscribeDialog

        # @@@MOR Handy during development:
        reload(osaf.framework.sharing.ICalendarSubscribeDialog)

        osaf.framework.sharing.ICalendarSubscribeDialog.Show(wx.GetApp().mainFrame, self.itsView)

    def onEditCollectionRuleEvent(self, event):
        # Triggered from "Tests | Edit collection rule..."
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            rule = application.dialogs.Util.promptUser(wx.GetApp().mainFrame, "Edit rule", "Enter a rule for this collection", str(collection.getRule()))
            if rule:
                collection.setRule(rule)

    def onShowColumnEventUpdateUI (self, event):
        event.arguments ['Enable'] = False
        event.arguments ['Check'] = True

    def onShowPyCrustEvent(self, event):
        # Test menu item
        wx.GetApp().ShowDebuggerWindow()

    def onShareCollectionEvent (self, event):
        # Triggered from "Test | Share collection..."
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            Sharing.manualPublishCollection(self.itsView, collection)

    def onShareCollectionEventUpdateUI (self, event):
        """
        Update the menu to reflect the selected collection name
        """
        # Only enable if user has set their webdav account up
        if not Sharing.isWebDAVSetUp(self.itsView):
            event.arguments ['Enable'] = False
            return

        collection = self.getSidebarSelectedCollection ()
        event.arguments ['Enable'] = collection is not None
        if collection:
            menuTitle = _('Share "%s" collection') \
                    % collection.displayName
        else:
            menuTitle = _('Share a collection')
        event.arguments ['Text'] = menuTitle

    def onShareSidebarCollectionEvent(self, event):
        self._onShareOrManageSidebarCollectionEvent(event)
        
    def onManageSidebarCollectionEvent(self, event):
        self._onShareOrManageSidebarCollectionEvent(event)
        
    def _onShareOrManageSidebarCollectionEvent(self, event):
        """
          Share the collection selected in the Sidebar. 
        If the current collection is already shared, then manage the collection.
        In either case, the real work here is to tell the summary
        view to deselect, and the detail view that the selection has
        changed to the entire summary view's collection.
        The "Collection | Share collection " menu item
        """
        # Make sure we have all the accounts; returns False if the user cancels out and we don't.
        if not Sharing.ensureAccountSetUp(self.itsView):
            return

        # @@@ BJS For 0.5, simplify sharing: if the application filter isn't All, switch it to All now.
        allFilterToolbarItem = Block.findBlockByName('ApplicationBarAllButton')
        if not allFilterToolbarItem.widget.IsToggled():
            # @@@BJS Maybe put up an alert here to let the user know we've pulled the rug out?
            allFilterToolbarItem.dynamicParent.widget.ToggleTool(allFilterToolbarItem.toolID, True)
        
        # Tell the ActiveView to select the collection
        # It will pass the collection on to the Detail View.
        self.postEventByName ('SelectItemBroadcastInsideActiveView', {'item':self.getSidebarSelectedCollection ()})

        
    def onShareSidebarCollectionEventUpdateUI (self, event):
        self._onShareOrManageSidebarCollectionEventUpdateUI(event, False)
        
    def onManageSidebarCollectionEventUpdateUI (self, event):
        self._onShareOrManageSidebarCollectionEventUpdateUI(event, True)
        
    def _onShareOrManageSidebarCollectionEventUpdateUI (self, event, doManage):
        """
        Update the menu to reflect the selected collection name
        """
        collection = self.getSidebarSelectedCollection ()
        verb = (doManage and _('Manage') or _('Share'))
        
        if collection is not None:
            # event.arguments['Enable'] = True
            menuTitle = _('%s "%s" collection') % (verb, collection.displayName)
        else:
            menuTitle = _('%s a collection') % verb
            
        event.arguments ['Text'] = menuTitle
        event.arguments['Enable'] = collection is not None and (doManage == Sharing.isShared(collection))

    def onShareToolEvent(self, event):
        # Triggered from "Test | Share tool..."
        import osaf.framework.sharing.ShareTool
        reload(osaf.framework.sharing.ShareTool)
        osaf.framework.sharing.ShareTool.ShowShareToolDialog(wx.GetApp().mainFrame, view=self.itsView)

    def onSyncCollectionEvent (self, event):
        # Triggered from "Test | Sync collection..."
        self.itsView.commit() 
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            share = Sharing.getShare(collection)
            if share is not None:
                Sharing.syncShare(share)

    def onSyncCollectionEventUpdateUI (self, event):
        """
        Update the menu to reflect the selected collection name
        """
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            menuTitle = _('Sync "%s" collection') % collection.displayName
            if Sharing.isShared(collection):
                event.arguments['Enable'] = True
            else:
                event.arguments['Enable'] = False
        else:
            event.arguments['Enable'] = False
            menuTitle = _('Sync a collection')
        event.arguments ['Text'] = menuTitle

    def onSyncWebDAVEvent (self, event):
        """
          Synchronize WebDAV sharing.
        The "File | Sync | WebDAV" menu item
        """
        # commit repository changes before synch
        self.RepositoryCommitWithStatus()

        # find all the shared collections and sync them.
        self.setStatusMessage (_("Checking shared collections..."))
        if Sharing.checkForActiveShares(self.itsView):
            self.setStatusMessage (_("Synchronizing shared collections..."))
            Sharing.syncAll(self.itsView)
        else:
            self.setStatusMessage (_("No shared collections found"))
            return
        self.setStatusMessage (_("Shared collections synchronized"))

    def onSyncWebDAVEventUpdateUI (self, event):
        accountOK = Sharing.isWebDAVSetUp(self.itsView)
        haveActiveShares = Sharing.checkForActiveShares(self.itsView)
        event.arguments ['Enable'] = accountOK and haveActiveShares
        # @@@DLD set up the help string to let the user know why it's disabled

    def onSyncAllEvent (self, event):
        """
          Synchronize Mail and all sharing.
        The "File | Sync | All" menu item
        """
        # find all the shared collections and sync them.
        self.onSyncWebDAVEvent (event)

        if not Sharing.isMailSetUp(self.itsView):
            if application.dialogs.Util.okCancel( \
             wx.GetApp().mainFrame,
             "Account information required",
             "Please set up your accounts."):
                if not application.dialogs.AccountPreferences.ShowAccountPreferencesDialog( \
                 wx.GetApp().mainFrame, view=self.itsView):
                    return
            else:
                return

        # synch mail
        self.setStatusMessage (_("Getting new Mail"))
        self.onGetNewMailEvent (event)

    def sharedWebDAVCollections (self):
        # return the list of all the shared collections
        # @@@DLD - use new query, once it can handle method calls, or when our item.isShared
        #  attribute is correctly set.
        UseNewQuery = False
        if UseNewQuery:
            qString = u"for i in '//parcels/osaf/contentmodel/ItemCollection' where len (i.sharedURL) > 0"
            collQuery = Query.Query (self.itsView.repository, qString)
            collQuery.recursive = False
            collections = []
            for item in collQuery:
                collections.append (item)
        else:
            itemCollectionKind = self.findPath("//parcels/osaf/contentmodel/ItemCollection")
            allCollections = KindQuery().run([itemCollectionKind])
            collections = []
            for collection in allCollections:
                if Sharing.isShared (collection):
                    collections.append (collection)
        return collections
        
class ReminderTimer(Timer):
    def synchronizeWidget (self):
        # print "*** Synchronizing ReminderTimer widget!"
        super(ReminderTimer, self).synchronizeWidget()
        if not wx.GetApp().ignoreSynchronizeWidget:            
            pending = self.getPendingReminders()
            if len(pending) > 0:
                self.setFiringTime(pending[0].reminderTime)
    
    def getPendingReminders (self):
        # @@@BJS Eventually, the query should be able to do the hasAttribute filtering for us;
        # for now, that doesn't seem to work so we're doing it here.
        # Should be: timesAndReminders = [ (item.reminderTime, item) for item in self.contents.getResults().values() ]
        timesAndReminders = [ (item.reminderTime, item) for item in self.contents.getResults().values() if item.hasLocalAttributeValue("reminderTime")]
        if len(timesAndReminders) == 0:
            return []
        timesAndReminders.sort()
        sortedReminders = [ item[1] for item in timesAndReminders ]
        return sortedReminders
    
    def onCollectionChanged(self, event):
        # print "*** Got reminders collection changed!"
        pending = self.getPendingReminders()
        closeIt = False
        reminderDialog = self.getReminderDialog(False)
        if reminderDialog is not None:
            (nextReminderTime, closeIt) = reminderDialog.UpdateList(pending)
        elif len(pending) > 0:
            nextReminderTime = pending[0].reminderTime
        else:
            nextReminderTime = None
        if closeIt:
            self.closeReminderDialog();
        self.setFiringTime(nextReminderTime)
    
    def onReminderTimeEvent(self, event):
        # Run the reminders dialog and re-queue our timer if necessary
        # print "*** Got reminders time event!"
        pending = self.getPendingReminders()
        reminderDialog = self.getReminderDialog(True)
        assert reminderDialog is not None
        (nextReminderTime, closeIt) = reminderDialog.UpdateList(pending)
        if closeIt:
            # print "*** closing the dialog!"
            self.closeReminderDialog()
        self.setFiringTime(nextReminderTime)

    def getReminderDialog(self, createIt):
        try:
            reminderDialog = self.widget.reminderDialog
        except AttributeError:
            if createIt:
                reminderDialog = ReminderDialog.ReminderDialog(wx.GetApp().mainFrame, -1)
                self.widget.reminderDialog = reminderDialog
            else:
                reminderDialog = None
        return reminderDialog

    def closeReminderDialog(self):
        try:
            reminderDialog = self.widget.reminderDialog
        except AttributeError:
            pass
        else:
            del self.widget.reminderDialog
            reminderDialog.Destroy()

