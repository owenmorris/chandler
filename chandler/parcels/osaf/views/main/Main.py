__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from osaf.framework.blocks.Views import View
from datetime import timedelta
from time import time
import wx, os, sys, traceback, logging
import application.dialogs.AccountPreferences
import application.dialogs.Util
import osaf.mail.imap
import osaf.mail.pop
from application.SplashScreen import SplashScreen
import application.Parcel
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.contacts.Contacts as Contacts
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.Notes as Notes
import osaf.contentmodel.photos.Photos as Photos
import osaf.contentmodel.tests.GenerateItems as GenerateItems
import osaf.framework.sharing.Sharing as Sharing
import repository.query.Query as Query
from repository.item.Item import Item
import application.Printing as Printing
import osaf.framework.blocks.calendar.CollectionCanvas as CollectionCanvas
import osaf.mail.sharing as MailSharing
import osaf.mail.smtp as smtp
from osaf.framework.blocks.Block import Block
from osaf.contentmodel.ItemCollection import ItemCollection
import osaf.framework.sharing.ICalendar as ICalendar
import osaf.framework.sharing.PublishCollection
import osaf.framework.sharing.SubscribeDialog
import osaf.framework.scripting.CPIAScript as CPIAScript
import osaf.framework.webserver.Web as Web
from osaf.app import Trash

logger = logging.getLogger("mainview")
logger.setLevel(logging.INFO)

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

    def onEmptyTrashEvent(self, event):
        Trash.EmptyTrash(self.itsView)

    def onEmptyTrashEventUpdateUI(self, event):
        trash = Trash.FindTrashCollection(self.itsView)
        event.arguments['Enable'] = (len(trash) > 0)

    def onEditAccountPreferencesEvent (self, event):
        # Triggered from "File | Prefs | Accounts..."

        # Handy during development:
        reload(application.dialogs.AccountPreferences)

        application.dialogs.AccountPreferences.ShowAccountPreferencesDialog(wx.GetApp().mainFrame, view=self.itsView)

    def onNewEvent (self, event):
        # Create a new Content Item
        # Triggered from "File | New Item" menu, for any of the item kinds.
        try:
            kindParam = event.kindParameter
        except AttributeError:
            kindParam = Notes.Note.getKind(self.itsView) # default kind for "New"
        newItem = kindParam.newItem (None, None)
        newItem.InitOutgoingAttributes ()
        self.RepositoryCommitWithStatus ()

        # Tell the sidebar we want to go to the All collection
        self.postEventByName ('RequestSelectSidebarItem', {'itemName':u"All"})

        # If the event cannot be displayed in this viewer, we need to switch to the all view
        viewFilter = Block.findBlockByName ("Sidebar").filterKind
        if not kindParam.isKindOf(viewFilter):
            self.postEventByName ('ApplicationBarAll', { })

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
        
    def onQuitEvent (self, event):
        wx.GetApp().mainFrame.Close ()

    def onCloseEvent (self, event):
        curWindow = self.widget.FindFocus() #start with the focus
        while not curWindow.IsTopLevel():
            curWindow = curWindow.GetParent()
        curWindow.Close()

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

        # If we have a detail view, let it write pending edits back first.
        detailView = self.findBlockByName("DetailRoot")
        if detailView is not None:
            detailView.finishSelectionChanges()
            
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
            # XXX This is not right, the alert should have a caption
            application.dialogs.Util.ok(wx.GetApp().mainFrame,
             "", statusMessage)
            self.setStatusMessage ('')

    def askTrustSiteCertificate(self, pem, reconnect):
        import M2Crypto.X509 as X509
        import osaf.framework.certstore.certificate as certificate
        x509 = X509.load_cert_string(pem)
        fingerprint = certificate._fingerprint(x509)
        # XXX Need to design real dialog
        dlg = wx.SingleChoiceDialog(wx.GetApp().mainFrame,
                                   'Do you want to trust this certificate?\n' +
                                   'SHA1 fingerprint: ' + fingerprint +
                                   '\n' + x509.as_text(),
                                   'Trust Site Certificate?',
                                   choices=['Trust the authenticity of this certificate until program exit.',
                                            'Trust the authenticity of this certificate permanently.'])
        try:
            if dlg.ShowModal() == wx.ID_OK:
                selection = dlg.GetSelection()
            
                if selection == 0:
                    import crypto.ssl as ssl
                    ssl.trusted_until_shutdown_site_certs += [pem]
                else:
                    certificate._importCertificate(x509, fingerprint, certificate.TRUST_AUTHENTICITY, self.itsView)
    
                reconnect()
        finally:
            dlg.Destroy()

    def onSendShareItemEventUpdateUI(self, event):
        # If we get asked about this, and it hasn't already been set, there's no selected 
        # item in the detail view - disallow sending. Also, make sure the label's set back to "Send"
        event.arguments ['Enable'] = False
        event.arguments ['Text'] = _(u"Send")

    def onSendMailEvent (self, event):
        # commit changes, since we'll be switching to Twisted thread
        self.RepositoryCommitWithStatus()
    
        # get default SMTP account
        item = event.arguments ['item']
        account = Mail.getCurrentSMTPAccount(self.itsView)[0]

        # put a sending message into the status bar
        self.setStatusMessage ('Sending mail...')

        # Now send the mail
        Globals.mailService.getSMTPInstance(account).sendMail(item)

    def onShareItemEvent (self, event):
        """
          Share an ItemCollection.
        """
        itemCollection = event.arguments ['item']

        # Make sure we have all the accounts; returns False if the user cancels
        # out and we don't.
        if not Sharing.ensureAccountSetUp(self.itsView):
            return
        webdavAccount = Sharing.getWebDAVAccount(self.itsView)

        # commit changes, since we'll be switching to Twisted thread
        # @@@DLD bug 1998 - update comment above and use refresh instead?
        self.RepositoryCommitWithStatus()

        # show status
        self.setStatusMessage (_("Sharing collection %s") % itemCollection.displayName)

        # Get or make a share for this item collection
        share = Sharing.getShare(itemCollection)
        isNewShare = share is None
        if isNewShare:
            share = Sharing.newOutboundShare(self.itsView,
                                             itemCollection,
                                             account=webdavAccount)

        # Copy the invitee list into the share's list. As we go, collect the 
        # addresses we'll notify.
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

        # Sync the collection with WebDAV
        self.setStatusMessage (_("accessing WebDAV server"))
        try:
            if not share.exists():
                share.create()
            share.put()

        except Sharing.SharingError, err:
            self.setStatusMessage (_("Sharing failed."))

            msg = "Couldn't share collection:\n%s" % err.message
            application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                        "Error", msg)

            if isNewShare:
                share.conduit.delete()
                share.format.delete()
                share.delete()

            return

        # Send out sharing invites
        self.setStatusMessage (_("inviting %s") % ", ".join(inviteeStringsList))
        MailSharing.sendInvitation(itemCollection.itsView.repository,
                                   share.conduit.getLocation(), itemCollection,
                                   inviteeList)

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
        progressMessage = _('Checking repository...')
        repository.logger.info(progressMessage)
        self.setStatusMessage(progressMessage)
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

    def onBackupRepositoryEvent(self, event):
        # triggered from "Test | Backup Repository" Menu
        repository = self.itsView.repository
        progressMessage = _('Backing up repository...')
        repository.logger.info(progressMessage)
        self.setStatusMessage(progressMessage)
        dbHome = repository.backup()
        successMessage = _('Repository was backed up into %s' %(dbHome))
        repository.logger.info(successMessage)
        self.setStatusMessage(successMessage)

    def onImportIcalendarEvent(self, event):
        # triggered from "File | Import/Export" menu
        wildcard = "iCalendar files|*.ics|All files (*.*)|*.*"
        dlg = wx.FileDialog(wx.GetApp().mainFrame, "Choose a file to import",
                              "", "import.ics", wildcard,
                              wx.OPEN | wx.HIDE_READONLY)
        if dlg.ShowModal() == wx.ID_OK:
            (dir, filename) = os.path.split(dlg.GetPath())
            dlg.Destroy()
        else:
            dlg.Destroy()
            self.setStatusMessage("Import aborted")
            return
            
        self.setStatusMessage ("Importing from %s" % filename)
        try:
            share = Sharing.OneTimeFileSystemShare(dir, filename,
                            ICalendar.ICalendarFormat, view=self.itsView)
            collection = share.get()
            self.postEventByName ("AddToSidebarWithoutCopyingAndSelectFirst", {'items':[collection]})
            self.setStatusMessage ("Import completed")
        except:
            trace = "".join(traceback.format_exception (*sys.exc_info()))
            self.itsView.getLogger().info("Failed importFile:\n%s" % trace)
            self.setStatusMessage("Import failed")

    def onExportIcalendarEvent(self, event):
        # triggered from "File | Import/Export" Menu

        wildcard = "iCalendar files|*.ics|All files (*.*)|*.*"
        dlg = wx.FileDialog(wx.GetApp().mainFrame, "Choose filename to export to",
                              "", "export.ics", wildcard,
                              wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            (dir, filename) = os.path.split(dlg.GetPath())
            dlg.Destroy()
        else:
            dlg.Destroy()
            self.setStatusMessage("Export aborted")
            return

        self.setStatusMessage ("Exporting to %s" % filename)
        try:
            share = Sharing.OneTimeFileSystemShare(dir, filename,
                            ICalendar.ICalendarFormat, view=self.itsView)
            collection = ItemCollection(view=self.itsView)
            for event in Calendar.CalendarEvent.iterItems(self.itsView):
                collection.add(event)
            share.contents = collection
            share.put()
            self.setStatusMessage("Export completed")
        except:
            trace = "".join(traceback.format_exception (*sys.exc_info()))
            self.itsView.getLogger().info("Failed exportFile:\n%s" % trace)
            self.setStatusMessage("Export failed")


    def onImportImageEvent(self, event):
        # triggered from "File | Import/Export" Menu

        wildcard = "Images|*.jpg;*.gif;*.png|All files (*.*)|*.*"
        dlg = wx.FileDialog(wx.GetApp().mainFrame, "Choose image to import",
                              "", "", wildcard,
                              wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = str(dlg.GetPath())
            dlg.Destroy()
        else:
            dlg.Destroy()
            self.setStatusMessage("")
            return

        self.setStatusMessage ("Importing %s" % path)
        photo = Photos.Photo(view=self.itsView)
        (dir, filename) = os.path.split(path)
        photo.displayName = filename
        photo.importFromFile(path)
        self.setStatusMessage("")
        # No longer needed since Photo is a Note
        # self.addItemToAllCollection(photo)

        # Tell the sidebar we want to go to the All collection
        self.postEventByName ('RequestSelectSidebarItem', {'itemName':u"All"})
        self.postEventByName ('ApplicationBarAll', { })
        # Tell the ActiveView to select our new item
        self.postEventByName ('SelectItemBroadcastInsideActiveView',
                              {'item':photo})

    def addItemToAllCollection(self, item):
        for coll in Block.findBlockByName("Sidebar").contents:
            if coll.displayName == "All":
                coll.add(item)
                return

    def onCommitRepositoryEvent(self, event):
        # Test menu item
        self.RepositoryCommitWithStatus ()
        
    def onWxTestHarnessEvent(self, event):
        # Test menu item
        #mainWidget = Globals.views[0].widget
        mainWidget = wx.GetApp().mainFrame
        if isinstance(mainWidget, wx.Window):
            # @@@ ForceRedraw works; the other two fail to induce a window update !!!
            #mainWidget.ForceRedraw()
            #mainWidget.ClearBackground()
            #mainWidget.Refresh( True )
            #mainWidget.Layout()
            statusMsg = "invalidated main view and back buffer"
        else:
            statusMsg = "wxDang"
        self.setStatusMessage(statusMsg)

    def onGenerateContentItemsEvent(self, event):
        # triggered from "Test | Generate Some Content Items" and
        # "Test | Generate Many Content Items" menu items
        count = event.arguments['sender'].blockName == 'GenerateSomeDataItem' and 4 or 100
        sidebarCollection = Block.findBlockByName ("Sidebar").contents
        mainView = Globals.views[0]
        GenerateItems.GenerateAllItems(self.itsView, count, mainView, sidebarCollection)


    def onMimeTestEvent (self, event):
        self.__loadMailTests ("mime_tests")

    def oni18nMailTestEvent (self, event):
        self.__loadMailTests ("i18n_tests")

    def __loadMailTests (self, dir):
        import osaf.mail.utils as utils
        utils.loadMailTests(self.itsView, dir)
        self.itsView.refresh()

    def onGetNewMailEvent (self, event):
        # Make sure we have all the accounts; returns False if the user cancels
        # out and we don't.
        if not Sharing.ensureAccountSetUp(self.itsView):
            return

        view = self.itsView
        # @@@DLD bug 1998 - why do we have to commit here?  Are we pushing our changes
        # over to mail?
        view.commit()

        for account in Mail.IMAPAccount.getActiveAccounts(self.itsView):
            Globals.mailService.getIMAPInstance(account).getMail()

        for account in Mail.POPAccount.getActiveAccounts(self.itsView):
            Globals.mailService.getPOPInstance(account).getMail()

        view.refresh()

    def LogTheException(self, message):
        type, value, stack = sys.exc_info()
        formattedBacktrace = "".join (traceback.format_exception (type, value, stack, 5))
        message += "\nHere are the bottom 5 frames of the stack:\n%s" % formattedBacktrace
        logger.exception( message )

    def ReloadPythonImports(self):
        """
        Try to reload all the modules that are reloadable.
        """
        # scan all the modules in sys.modules
        for aModule in sys.modules.values():
            # filter out ones that have no file (like None)
            try:
                modulePath = aModule.__file__
            except AttributeError:
                pass
            else:
                # filter modules that don't accept reloading
                try:
                    canReload = aModule.AcceptsReload
                except AttributeError:
                    pass
                else:
                    try:
                        if canReload:
                            reload(aModule)
                    except Exception:
                        self.LogTheException("Exception during reload of Python code.")

    def onReloadParcelsEvent(self, event, traceItem = None):
        """
        Reloads the parcels and UI by deleting the UI elements and
        creating a new set.  Often this operation exposes bugs in the
        copying cloud where data items referenced by the UI get
        deleted too.  If this happens, you can get debugging
        help by passing in a traceItem to view how that item
        gets included by the cloud.
        """
        # pass in an Item to trace, or set it here in the debugger
        if traceItem is not None:
            self.TraceMainViewCloud(traceItem)

        theApp = wx.GetApp()
        theApp.UnRenderMainView ()

        # reload the python code now
        self.ReloadPythonImports()

        try:
            application.Parcel.Manager.get(self.itsView).loadParcels()
        except Exception:
            self.LogTheException("Error scanning parcels.")

        theApp.LoadMainViewRoot (delete=True)
        theApp.RenderMainView ()

    def TraceMainViewCloud(self, traceItem):
        # for debugging, trace through the mainViewRoot copy cloud
        def commonName(item, showKind=True):
            if showKind:
                kindLabel = commonName(item.itsKind, False)+':'
            else:
                kindLabel = ''
            if hasattr(item, 'about'): 
                return kindLabel + item.about
            if hasattr(item, 'blockName'): 
                return kindLabel + item.blockName
            if hasattr(item, 'displayName'): 
                return kindLabel + item.displayName
            if hasattr(item, 'itsName') and item.itsName is not None: 
                return kindLabel + item.itsName
            return str(item)

        mainViewRoot = Globals.mainViewRoot
        traceData = {}
        mainViewRoot.getItemCloud(cloudAlias="copying", trace=traceData)
        cloud = mainViewRoot.getKind().getClouds("copying")[0]
        logger.info("MainViewRoot trace information:")
        for item, other, endpoint, policy, indent in cloud.traceItem(traceItem, traceData):
            logger.info( "   "*indent +'\t"'+
                         commonName(item)+'"\t"'+
                         commonName(other)+'"\t'+ 
                         endpoint+'\t'+ policy)

    def onSharingSubscribeToCollectionEvent(self, event):
        # Triggered from "Collection | Subscribe to collection..."

        osaf.framework.sharing.SubscribeDialog.Show(wx.GetApp().mainFrame,
                                                    self.itsView)

    def onSharingImportDemoCalendarEvent(self, event):
        # Triggered from "Tests | Import demo calendar..."

        url="http://www.osafoundation.org/0.5/DemoCalendar.ics"

        osaf.framework.sharing.SubscribeDialog.Show(wx.GetApp().mainFrame,
                                                    self.itsView,
                                                    url=url)


    def onEditCollectionRuleEvent(self, event):
        # Triggered from "Tests | Edit collection rule..."
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            rule = application.dialogs.Util.promptUser(wx.GetApp().mainFrame, "Edit rule", "Enter a rule for this collection", str(collection.getRule()))
            if rule:
                collection.setRule(rule)

    def _SelectedItemScript(self):
        """ Return the poosible script item:
        the item shown in the Detail View, unless
        its body is empty.  
        Otherwise return None.
        """
        item = None
        try:
            item = Block.findBlockByName("DetailRoot").selectedItem()
            body = item.bodyString
        except AttributeError:
            pass
        else:
            if len(body) == 0:
                item = None
        return item

    def onRunScriptEvent(self, event):
        # Triggered from "Tests | Run script..."
        previousScript = CPIAScript.GetDialogScript(self.itsView)
        script = application.dialogs.Util.promptUser(wx.GetApp().mainFrame, "Run Script", "Enter a CPIA script to run.", previousScript)
        if script:
            CPIAScript.RunDialogScript(script, self.itsView)

    def onRunSelectedScriptEvent(self, event):
        # Triggered from "Tests | Run an Item"
        item = self._SelectedItemScript()
        if item:
            # in case the user was just editing the script,
            # ask the focus to finish changes, if it can
            focusedWidget = wx.Window_FindFocus()
            try:
                focusedWidget.blockItem.finishSelectionChanges()
            except AttributeError:
                pass
            # run the script from the item's body
            CPIAScript.RunScript(item.bodyString, self.itsView)

    def onRunSelectedScriptEventUpdateUI(self, event):
        # Triggered from "Tests | Run an Item"
        item = self._SelectedItemScript()
        event.arguments ['Enable'] = item is not None
        if item is not None:
            menuTitle = _('Run "%s"') \
                    % item.about
        else:
            menuTitle = _('Run an Item')
        menuTitle = menuTitle + '\t' + 'Ctrl+S'
        event.arguments ['Text'] = menuTitle

    def onShowPyShellEvent(self, event):
        # Test menu item
        wx.GetApp().ShowPyShell(withFilling=False)

    def onShowPyCrustEvent(self, event):
        # Test menu item
        wx.GetApp().ShowPyShell(withFilling=True)

    def onActivateWebserverEventUpdateUI (self, event):
        for server in Web.Server.iterItems(view=self.itsView):
            if server.isActivated():
                event.arguments['Enable'] = False
                return
        event.arguments['Enable'] = True

    def onActivateWebserverEvent(self, event):
        # Test menu item
        for server in Web.Server.iterItems(view=self.itsView):
            server.startup()

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

        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            reload(osaf.framework.sharing.PublishCollection)
            collection = self.getSidebarSelectedCollection()
            sidebar = Block.findBlockByName("Sidebar")
            if sidebar.filterKind is None:
                filterKindPath = None 
            else:
                filterKindPath = str(sidebar.filterKind.itsPath)
            osaf.framework.sharing.PublishCollection.ShowPublishDialog( \
                wx.GetApp().mainFrame,
                view=self.itsView,
                collection=collection,
                filterKindPath=filterKindPath)

    def onShareSidebarCollectionEventUpdateUI (self, event):
        """
        Update the menu to reflect the selected collection name
        """
        collection = self.getSidebarSelectedCollection ()

        if collection is not None:

            sidebar = Block.findBlockByName("Sidebar")
            if sidebar.filterKind is None:
                filterKindPath = []
            else:
                filterKindPath = [str(sidebar.filterKind.itsPath)]
            collName = Sharing.getFilteredCollectionDisplayName(collection,
                                                                filterKindPath)

            menuTitle = _('Share "%s"...') % collName
        else:
            menuTitle = _('Share a collection...')

        event.arguments ['Text'] = menuTitle
        event.arguments['Enable'] = collection is not None and (not Sharing.isShared(collection))

    def onManageSidebarCollectionEventUpdateUI (self, event):
        collection = self.getSidebarSelectedCollection ()
        event.arguments['Enable'] = collection is not None and (Sharing.isShared(collection))

    def onUnsubscribeSidebarCollectionEvent(self, event):
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            Sharing.unsubscribe(collection)

    def onUnsubscribeSidebarCollectionEventUpdateUI(self, event):
        collection = self.getSidebarSelectedCollection ()
        event.arguments['Enable'] = collection is not None and (Sharing.isShared(collection))

    def onUnpublishSidebarCollectionEvent(self, event):
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            Sharing.unpublish(collection)

    def onUnpublishSidebarCollectionEventUpdateUI(self, event):
        collection = self.getSidebarSelectedCollection ()
        event.arguments['Enable'] = collection is not None and (Sharing.isShared(collection))

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
            for share in collection.shares:
                if share.active:
                    Sharing.syncShare(share)

    def onSyncCollectionEventUpdateUI (self, event):
        """
        Update the menu to reflect the selected collection name
        """
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:

            sidebar = Block.findBlockByName("Sidebar")
            if sidebar.filterKind is None:
                filterKindPath = []
            else:
                filterKindPath = [str(sidebar.filterKind.itsPath)]
            collName = Sharing.getFilteredCollectionDisplayName(collection,
                                                                filterKindPath)

            menuTitle = _('Sync "%s"') % collName
            if Sharing.isShared(collection):
                event.arguments['Enable'] = True
            else:
                event.arguments['Enable'] = False
        else:
            event.arguments['Enable'] = False
            menuTitle = _('Sync a collection')
        event.arguments ['Text'] = menuTitle

    def onCopyCollectionURLEvent(self, event):
        collection = self.getSidebarSelectedCollection()
        if collection is not None:
            share = Sharing.getShare(collection)
            if share is not None:
                url = str(share.getLocation())
                gotClipboard = wx.TheClipboard.Open()        
                if gotClipboard:
                    wx.TheClipboard.SetData(wx.TextDataObject(url))
                    wx.TheClipboard.Close()

    def onCopyCollectionURLEventUpdateUI(self, event):
        enable = False
        collection = self.getSidebarSelectedCollection()
        if collection is not None:
            share = Sharing.getShare(collection)
            if share is not None:
                enable = True
        event.arguments['Enable'] = enable
        
    def onSyncWebDAVEvent (self, event):
        """
          Synchronize WebDAV sharing.
        The "File | Sync | WebDAV" menu item
        """
        # commit repository changes before synch
        # @@@DLD bug 1998 - update comment above and use refresh instead?
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

        # If mail is set up, fetch it:
        if Sharing.isInboundMailSetUp(self.itsView):
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
            collections = list(collQuery)
        else:
            collections = [
                coll for coll in ItemCollection.iterItems(self.itsView)
                     if Sharing.isShared(coll)
            ]
        return collections
        
