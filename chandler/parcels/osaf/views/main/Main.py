__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from application import schema
from osaf.framework.blocks.Views import View
from datetime import timedelta
from time import time
import wx, os, sys, traceback, logging
from application.dialogs import ( AccountPreferences, PublishCollection,
    SubscribeCollection, ShareTool
)
import application.dialogs.Util
from  application.dialogs import ImportExport
import osaf.mail.constants as constants
from application.SplashScreen import SplashScreen
import application.Parcel
import osaf.pim.mail as Mail
from osaf.pim import Contact
from osaf import pim, sharing
from photos import Photo
import osaf.pim.tests.GenerateItems as GenerateItems
import util.GenerateItemsFromFile as GenerateItemsFromFile
from repository.item.Item import Item
import application.Printing as Printing
import osaf.framework.blocks.calendar.CollectionCanvas as CollectionCanvas
import osaf.mail.sharing as MailSharing
from osaf.framework.blocks.Block import Block
from osaf.pim import AbstractCollection
import osaf.sharing.ICalendar as ICalendar
from osaf import webserver
from i18n import OSAFMessageFactory as _
import i18n
from osaf import messages

logger = logging.getLogger(__name__)

class MainView(View):
    """
      Main Chandler view contains event handlers for Chandler
    """
    def displayMailError (self, message, account):
        application.dialogs.Util.mailError(wx.GetApp().mainFrame, self.itsView, message, account)

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
                errorMessage = constants.UNKNOWN_ERROR
            else:
                errorMessage = constants.UPLOAD_ERROR % (', '.join(errorStrings))

            """Clear the status message"""
            self.setStatusMessage(u'')
            self.displayMailError (errorMessage, mailMessage.parentAccount)

    def displaySMTPSendSuccess (self, mailMessage):
        """
          Called when the SMTP Send was successful.
        """
        if mailMessage is not None and mailMessage.isOutbound:
            self.setStatusMessage (_(u'Mail "%(subject)s" sent.') % {'subject': mailMessage.about})

        # If this was a sharing invitation, find its collection and remove the
        # successfully-notified addressees from the invites list.
        try:
            (url, collectionName) = MailSharing.getSharingHeaderInfo(mailMessage)
        except KeyError:
            pass
        else:
            share = sharing.findMatchingShare(self.itsView, url)
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
        html = ''
        for line in i18n.getHTML('welcome.html'):
            if line.find('@@buildid@@') >= 0:
                line = "<p>Version: %s (rev %s build %s)</p>" % \
                        (version.release, version.buildRevision, version.build)
            html += line
        splash = SplashScreen(None, _(u"About Chandler"),
                                   None, html, True, False)
        splash.Show(True)
        return splash

    def onCopyEventUpdateUI (self, event):
        event.arguments ['Enable'] = False

    def onCutEventUpdateUI (self, event):
        event.arguments ['Enable'] = False

    def onRemoveEventUpdateUI (self, event):
        event.arguments ['Enable'] = False

    def onEmptyTrashEvent(self, event):
        trash = schema.ns("osaf.app", self).TrashCollection
        trash.empty()

    def onEmptyTrashEventUpdateUI(self, event):
        trash = schema.ns("osaf.app", self).TrashCollection
        event.arguments['Enable'] = not trash.isEmpty()

    def onEditAccountPreferencesEvent (self, event):
        # Triggered from "File | Prefs | Accounts..."

        AccountPreferences.ShowAccountPreferencesDialog(wx.GetApp().mainFrame,
                                                        view=self.itsView)

    def onNewEvent (self, event):
        # Create a new Content Item
        # Triggered from "File | New Item" menu, for any of the item kinds.
        try:
            kindParam = event.kindParameter
        except AttributeError:
            kindParam = pim.Note.getKind(self.itsView) # default kind for "New"
        newItem = kindParam.newItem (None, None)
        newItem.InitOutgoingAttributes ()
        self.RepositoryCommitWithStatus ()

        sidebar = Block.findBlockByName("Sidebar")

        # if the sidebaritem is read-only, then jump to the
        # all collection
        sidebaritem = sidebar.selectedItemToView
        isReadOnly = getattr(sidebaritem, 'isReadOnly', None)
        if isReadOnly and isReadOnly():
            # Tell the sidebar we want to go to the All collection
            allCollection = schema.ns('osaf.app', self).allCollection
            self.postEventByName ('RequestSelectSidebarItem',
                                  {'item': allCollection})
        elif hasattr(sidebaritem, 'add'):
            sidebaritem.add(newItem)

        # If the event cannot be displayed in this viewer,
        # we need to switch to the all view
        viewFilter = sidebar.filterKind
        if not kindParam.isKindOf(viewFilter):
            self.postEventByName ('ApplicationBarAll', { })

        # Tell the ActiveView to select our new item
        self.postEventByName ('SelectItemsBroadcastInsideActiveView',
                              {'items':[newItem]})
        return [newItem]

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
        message = _(u"Printing is currently only supported when viewing week or \
                    day view of the calendar.")

        title = _(u"chandler")
        application.dialogs.Util.ok(None, message, title)

    def onQuitEvent (self, event):
        self.finishDetailViewChanges()
        mainFrame = wx.GetApp().mainFrame
        mainFrame.Close()
        windows = wx.GetTopLevelWindows()
        for window in windows:
            window.Close()

    def onCloseEvent (self, event):
        curWindow = self.widget.FindFocus() #start with the focus
        while not curWindow.IsTopLevel():
            curWindow = curWindow.GetParent()
        curWindow.Close()

    def onRedoEventUpdateUI (self, event):
        event.arguments ['Enable'] = False

    def onUndoEventUpdateUI (self, event):
        # BJS: commented out - see rant in Block.py, 
        # RectangularChild.onUndoEventUpdateUI
        #event.arguments ['Text'] = _(u"Can't Undo\tCtrl+Z")
        event.arguments ['Enable'] = False

    def RepositoryCommitWithStatus (self):
        """
          Do a repository commit with notice posted in the Status bar.
        """
        self.setStatusMessage (_(u"committing changes to the repository..."))

        self.finishDetailViewChanges()
        self.itsView.commit()
        self.setStatusMessage ('')

    def finishDetailViewChanges(self):
        # If we have a detail view, let it write pending edits back.
        detailView = self.findBlockByName("DetailRoot")
        if detailView is not None:
            detailView.finishSelectionChanges()

    def setStatusMessage (self, statusMessage, progressPercentage=-1, alert=False):
        """
          Allows you to set the message contained in the status bar.  You can also specify 
        values for the progress bar contained on the right side of the status bar.  If you
        specify a progressPercentage (as a float 0 to 1) the progress bar will appear.  If 
        no percentage is specified the progress bar will disappear.
        """

        app = wx.GetApp()
        app.mainFrame.GetStatusBar().blockItem.setStatusMessage (statusMessage, progressPercentage)
        if alert:
            # XXX This is not right, the alert should have a caption
            application.dialogs.Util.ok(app.mainFrame,
             "", statusMessage)
            self.setStatusMessage ('')

    def askTrustSiteCertificate(self, pem, reconnect):
        # XXX It's wrong for the MainView to depend on certstore
        import M2Crypto.X509 as X509
        from osaf.framework.certstore import dialogs, certificate
        x509 = X509.load_cert_string(pem)
        untrustedCertificate = certificate.findCertificate(self.itsView, pem)
        dlg = dialogs.TrustSiteCertificateDialog(wx.GetApp().mainFrame,
                                                 x509,
                                                 untrustedCertificate)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                selection = dlg.GetSelection()

                if selection == 0:
                    from osaf.framework.certstore import ssl
                    ssl.trusted_until_shutdown_site_certs += [pem]
                else:
                    from osaf.framework.certstore import constants
                    if untrustedCertificate is not None:
                        untrustedCertificate.trust |= constants.TRUST_AUTHENTICITY
                    else:
                        from osaf.framework.certstore import utils
                        fingerprint = utils.fingerprint(x509)
                        certificate.importCertificate(x509, fingerprint, 
                                                      constants.TRUST_AUTHENTICITY,
                                                      self.itsView)

                reconnect()
        finally:
            dlg.Destroy()

    def askIgnoreSSLError(self, pem, err, reconnect):
        # XXX It's wrong for the MainView to depend on certstore
        import M2Crypto.X509 as X509
        from osaf.framework.certstore import dialogs
        x509 = X509.load_cert_string(pem)
        dlg = dialogs.IgnoreSSLErrorDialog(wx.GetApp().mainFrame,
                                           x509,
                                           err)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                from osaf.framework.certstore import ssl
                acceptedErrList = ssl.trusted_until_shutdown_invalid_site_certs.get(pem)
                if acceptedErrList is None:
                    ssl.trusted_until_shutdown_invalid_site_certs[pem] = [err]
                else:
                    ssl.trusted_until_shutdown_invalid_site_certs[pem].append(err)
                reconnect()
        finally:
            dlg.Destroy()

    def onSendShareItemEventUpdateUI(self, event):
        # If we get asked about this, and it hasn't already been set, there's no selected 
        # item anywhere - disallow sending. Also, make sure the label's set back to "Send"
        event.arguments ['Enable'] = False
        event.arguments ['Text'] = messages.SEND

    def onSendMailEvent (self, event):
        # commit changes, since we'll be switching to Twisted thread
        self.RepositoryCommitWithStatus()
    
        # get default SMTP account
        item = event.arguments ['item']
        account = Mail.getCurrentSMTPAccount(self.itsView)[0]

        # put a sending message into the status bar
        self.setStatusMessage (_(u'Sending mail...'))

        # Now send the mail
        Globals.mailService.getSMTPInstance(account).sendMail(item)

    def onShareItemEvent (self, event):
        """
          Share a Collection.
        """
        itemCollection = event.arguments ['item']

        # Make sure we have all the accounts; returns False if the user cancels
        # out and we don't.
        if not sharing.ensureAccountSetUp(self.itsView, sharing=True):
            return
        webdavAccount = sharing.getWebDAVAccount(self.itsView)

        # commit changes, since we'll be switching to Twisted thread
        # @@@DLD bug 1998 - update comment above and use refresh instead?
        self.RepositoryCommitWithStatus()

        # show status
        self.setStatusMessage (_(u"Sharing collection %(collectionName)s") % {'collectionName': itemCollection.displayName})

        # Get or make a share for this item collection
        share = sharing.getShare(itemCollection)
        isNewShare = share is None
        if isNewShare:
            share = sharing.newOutboundShare(self.itsView,
                                             itemCollection,
                                             account=webdavAccount)

        # Copy the invitee list into the share's list. As we go, collect the 
        # addresses we'll notify.
        if len (itemCollection.invitees) == 0:
            self.setStatusMessage (_(u"No invitees!"))
            return
        inviteeList = []
        inviteeStringsList = []

        for invitee in itemCollection.invitees:
            inviteeList.append(invitee)
            inviteeStringsList.append(invitee.emailAddress)
            inviteeContact = Contact.getContactForEmailAddress(self.itsView, invitee.emailAddress)

            if not inviteeContact in share.sharees:
                share.sharees.append(inviteeContact)

        # Sync the collection with WebDAV
        self.setStatusMessage (_(u"accessing WebDAV server"))
        try:
            if not share.exists():
                share.create()
            share.put()

        except sharing.SharingError, err:
            self.setStatusMessage (_(u"Sharing failed."))

            msg = _(u"Couldn't share collection:\n%(errorMessage)s") % {'errorMessage': err.message}

            application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                        _(u"Error"), msg)

            if isNewShare:
                share.conduit.delete()
                share.format.delete()
                share.delete()

            return

        # Send out sharing invites
        self.setStatusMessage (_(u"inviting %(inviteList)s") % {'inviteList': ", ".join(inviteeStringsList)})
        MailSharing.sendInvitation(itemCollection.itsView.repository,
                                   share.conduit.getLocation(), itemCollection,
                                   inviteeList)

        # Done
        self.setStatusMessage (_(u"Sharing initiated."))

    def onStartProfilerEvent(self, event):
        Block.profileEvents = True


    def onStopProfilerEvent(self, event):
        Block.profileEvents = False
    # Test Methods

    def getSidebarSelectedCollection (self, private=False):
        """
          Return the sidebar's selected item collection.
        Will not return private collections (whose "private" attribute
        is True) unless you pass private=True.
        """
        item = Block.findBlockByName ("Sidebar").selectedItemToView
        if not isinstance (item, AbstractCollection):
            item = None
        elif private == False and item.private:
            item = None
        return item

    def _logChange(self, item, version, status, values, references):
        logger = item.itsView.logger
        logger.info("%s %d 0x%0.4x\n  values: %s\n  refs: %s",
                    Item.__repr__(item), version, status, values, references)

    def onCheckRepositoryEvent(self, event):
        # triggered from "Test | Check Repository" Menu
        repository = self.itsView.repository
        progressMessage = _(u'Checking repository...')
        repository.logger.info("Checking repository ...")
        self.setStatusMessage(progressMessage)
        before = time()
        if repository.check():
            after = time()
            successMessage = _(u'Check completed successfully in %(numSeconds)s') % {'numSeconds': timedelta(seconds=after-before)}
            repository.logger.info('Check completed successfully in %s' % (timedelta(seconds=after-before)))
            self.setStatusMessage(successMessage)
        else:
            errorMessage = _(u'Check completed with errors')
            repository.logger.info('Check completed with errors')
            self.setStatusMessage(errorMessage)

    def onBackupRepositoryEvent(self, event):
        # triggered from "Test | Backup Repository" Menu
        self.RepositoryCommitWithStatus()
        repository = self.itsView.repository
        progressMessage = _(u'Backing up repository...')
        repository.logger.info('Backing up repository...')
        self.setStatusMessage(progressMessage)
        dbHome = repository.backup()
        successMessage = _(u'Repository was backed up into %(directory)s') % {'directory': (dbHome)}
        repository.logger.info('Repository was backed up into %s' % (dbHome))
        self.setStatusMessage(successMessage)

    def onImportIcalendarEvent(self, event):
        # triggered from "File | Import/Export" menu
        #XXX: need to migrate this to application dialogs utilsA

        res = ImportExport.showFileDialog(wx.GetApp().mainFrame, _(u"Choose a file to import"), "",
                                          "import.ics", _(u"iCalendar files|*.ics|All files (*.*)|*.*"),
                                          wx.OPEN | wx.HIDE_READONLY)

        (cmd, dir, filename) = res

        if cmd  != wx.ID_OK:
            self.setStatusMessage(_(u"Import aborted"))
            return

        self.setStatusMessage (_(u"Importing from %(filename)s") % {'filename': filename})
        try:
            share = sharing.OneTimeFileSystemShare(dir, filename,
                            ICalendar.ICalendarFormat, view=self.itsView)
            collection = share.get()
            assert (hasattr (collection, 'color'))
            schema.ns("osaf.app", self).sidebarCollection.add (collection)
            # Need to SelectFirstItem -- DJA
            self.setStatusMessage (_(u"Import completed"))
        except:
            logger.exception("Failed importFile %s" % \
                os.path.join(dir, filename))
            self.setStatusMessage(_(u"Import failed"))

    def onExportIcalendarEvent(self, event):
        # triggered from "File | Import/Export" Menu
        collection = Block.findBlockByName("Sidebar").selectedItemToView

        res = ImportExport.showFileDialog(
                wx.GetApp().mainFrame,
                _("Choose a filename to export to"),
                "",
                u"%s.ics" % (collection.displayName),
                _("iCalendar files|*.ics|All files (*.*)|*.*"),
                wx.SAVE | wx.OVERWRITE_PROMPT)

        (cmd, dir, filename) = res

        if cmd != wx.ID_OK:
            self.setStatusMessage(_(u"Export aborted"))
            return

        self.setStatusMessage (_(u"Exporting to %(filename)s") % {'filename': filename})
        try:
            share = sharing.OneTimeFileSystemShare(dir, filename,
                            ICalendar.ICalendarFormat, view=self.itsView)
            share.contents = collection
            share.put()
            self.setStatusMessage(_(u"Export completed"))
        except:
            trace = "".join(traceback.format_exception (*sys.exc_info()))
            logger.info("Failed exportFile:\n%s" % trace)
            self.setStatusMessage(_(u"Export failed"))


    def onImportImageEvent(self, event):
        # triggered from "File | Import/Export" Menu
        res = ImportExport.showFileDialog(wx.GetApp().mainFrame, _(u"Choose an image to import"), "",
                                          "", _(u"Images|*.jpg;*.gif;*.png|All files (*.*)|*.*"),
                                          wx.OPEN)

        (cmd, dir, filename) = res

        if cmd != wx.ID_OK:
            self.setStatusMessage("")
            return

        path = os.path.join(dir, filename)

        self.setStatusMessage (_(u"Importing %(filePath)s") % {'filePath': path})
        photo = Photo(view=self.itsView)
        photo.displayName = filename
        photo.importFromFile(path)
        self.setStatusMessage(u"")

        # Tell the sidebar we want to go to the All collection
        self.postEventByName ('RequestSelectSidebarItem', {'item':schema.ns('osaf.app', self).allCollection})
        self.postEventByName ('ApplicationBarAll', { })
        # Tell the ActiveView to select our new item
        self.postEventByName ('SelectItemsBroadcastInsideActiveView',
                              {'items':[photo]})

    def onCommitRepositoryEvent(self, event):
        # Test menu item
        self.RepositoryCommitWithStatus ()

    def onWxTestHarnessEvent(self, event):
        """
           This method is for testing and 
           does not require translation strings
        """
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
        count = event.arguments['sender'].blockName == 'GenerateMuchDataItem' and 100 or 4
        sidebarCollection = schema.ns("osaf.app").sidebarCollection
        mainView = Globals.views[0]
        return GenerateItems.GenerateAllItems(self.itsView, count, mainView, sidebarCollection)

    def onGenerateContentItemsFromFileEvent(self, event):
        # triggered from "File | Import/Export" menu
        res = ImportExport.showFileDialog(wx.GetApp().mainFrame, _(u"Choose a file to import"), "",
                                          "import.csv", _(u"CSV files|*.csv"),
                                          wx.OPEN | wx.HIDE_READONLY)

        (cmd, dir, filename) = res

        if cmd != wx.ID_OK:
            self.setStatusMessage(_(u"Import aborted"))
            return

        self.setStatusMessage (_(u"Importing from %(filename)s")  % {'filename': filename})
        mainView = Globals.views[0]
        return GenerateItemsFromFile.GenerateItems(self.itsView, mainView, os.path.join(dir, filename))

    def onMimeTestEvent (self, event):
        self.__loadMailTests ("mime_tests")

    def oni18nMailTestEvent (self, event):
        self.__loadMailTests ("i18n_tests")

    def __loadMailTests (self, dir):
        import osaf.mail.utils as utils
        utils.loadMailTests(self.itsView, dir)
        self.itsView.refresh()


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

        application.Parcel.Manager.get(self.itsView).loadParcels()

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
        cloud = mainViewRoot.getKind(mainViewRoot.itsView).getClouds("copying")[0]
        logger.info("MainViewRoot trace information:")
        for item, other, endpoint, policy, indent in cloud.traceItem(traceItem, traceData):
            logger.info( "   "*indent +'\t"'+
                         commonName(item)+'"\t"'+
                         commonName(other)+'"\t'+ 
                         endpoint+'\t'+ policy)

    def onSharingSubscribeToCollectionEvent(self, event):
        # Triggered from "Collection | Subscribe to collection..."

        SubscribeCollection.Show(wx.GetApp().mainFrame, self.itsView)

    def onSharingImportDemoCalendarEvent(self, event):
        # Triggered from "Tests | Import demo calendar..."

        url="http://www.osafoundation.org/0.5/DemoCalendar.ics"

        SubscribeCollection.Show(wx.GetApp().mainFrame, self.itsView, url=url)

    def onAddScriptsToSidebarEvent(self, event):
        sidebar = Block.findBlockByName ("Sidebar").contents
        scriptsSet = schema.ns('osaf.app', self.itsView).scriptsCollection
        # if already present, just select it
        if scriptsSet in sidebar:
            self.postEventByName('RequestSelectSidebarItem', {'item': scriptsSet})
        else:
            schema.ns("osaf.app", self).sidebarCollection.add (scriptsSet)
            # Need to SelectFirstItem -- DJA

        # go to the All application, so we can view the scripts
        self.postEventByName ('ApplicationBarAll', { })

    def onAddScriptsToSidebarEventUpdateUI(self, event):
        # Triggered from "Tests | Add Scripts to Sidebar"
        sidebar = Block.findBlockByName ("Sidebar").contents
        scriptsSet = schema.ns('osaf.app', self.itsView).scriptsCollection
        if scriptsSet in sidebar:
            menuTitle = _(u'Show Scripts')
        else:
            menuTitle = _(u'Add Scripts to Sidebar')
        event.arguments ['Text'] = menuTitle
        event.arguments ['Enable'] = True

    def onShowPyShellEvent(self, event):
        # Test menu item
        wx.GetApp().ShowPyShell(withFilling=False)

    def onShowPyCrustEvent(self, event):
        # Test menu item
        wx.GetApp().ShowPyShell(withFilling=True)

    def onActivateWebserverEventUpdateUI (self, event):
        for server in webserver.Server.iterItems(view=self.itsView):
            if server.isActivated():
                event.arguments['Enable'] = False
                return
        event.arguments['Enable'] = True

    def onActivateWebserverEvent(self, event):
        # Test menu item
        for server in webserver.Server.iterItems(view=self.itsView):
            server.startup()

    def onLoadLoggingConfigEvent(self, event):
        # Test menu item
        wx.GetApp().ChooseLogConfig()

    def onRestoreSharesEvent(self, event):
        # Test menu item
        account = schema.ns("osaf.app", self).currentWebDAVAccount.item
        if account is not None:
            self.setStatusMessage (_(u"Restoring published shares..."))
            (collections, failures) = sharing.restoreFromAccount(account)
            for collection in collections:
                assert (hasattr (collection, 'color'))
                schema.ns("osaf.app", self).sidebarCollection.add (collection)

            self.setStatusMessage (_(u"Restoring shares completed"))
        else:
            self.setStatusMessage (_(u"No default sharing account"))

    def onShareSidebarCollectionEvent(self, event):
        self._onShareOrManageSidebarCollectionEvent(event)
        
    def onManageSidebarCollectionEvent(self, event):
        self._onShareOrManageSidebarCollectionEvent(event)
        
    def _onShareOrManageSidebarCollectionEvent(self, event):
        """
          Share the collection selected in the Sidebar. 
        If the current collection is already shared, then manage the collection.

        The "Collection | Share collection " menu item
        """

        if not sharing.ensureAccountSetUp(self.itsView, sharing=True):
            return

        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            sidebar = Block.findBlockByName("Sidebar")
            if sidebar.filterKind is None:
                filterClassName = None
            else:
                klass = sidebar.filterKind.classes['python']
                filterClassName = "%s.%s" % (klass.__module__, klass.__name__)

            mainFrame = wx.GetApp().mainFrame
            PublishCollection.ShowPublishDialog(mainFrame,
                view=self.itsView,
                collection=collection,
                filterClassName=filterClassName)

    def onShareSidebarCollectionEventUpdateUI (self, event):
        """
        Update the menu to reflect the selected collection name
        """
        collection = self.getSidebarSelectedCollection ()

        if collection is not None:

            sidebar = Block.findBlockByName("Sidebar")
            filterClasses = []
            if sidebar.filterKind is not None:
                klass = sidebar.filterKind.classes['python']
                className = "%s.%s" % (klass.__module__, klass.__name__)
                filterClasses.append(className)

            collName = sharing.getFilteredCollectionDisplayName(collection,
                                                                filterClasses)

            menuTitle = _(u'Share "%(collectionName)s"...') % {'collectionName': collName}
        else:
            menuTitle = _(u'Share a collection...')

        event.arguments ['Text'] = menuTitle
        event.arguments['Enable'] = collection is not None and (not sharing.isShared(collection))

    def onManageSidebarCollectionEventUpdateUI (self, event):
        collection = self.getSidebarSelectedCollection ()
        event.arguments['Enable'] = collection is not None and (sharing.isShared(collection))

    def onUnsubscribeSidebarCollectionEvent(self, event):
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            sharing.unsubscribe(collection)

    def onUnsubscribeSidebarCollectionEventUpdateUI(self, event):
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            share = sharing.getShare(collection)
            sharedByMe = sharing.isSharedByMe(share)
        event.arguments['Enable'] = collection is not None and sharing.isShared(collection) and not sharedByMe

    def onUnpublishSidebarCollectionEvent(self, event):
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            sharing.unpublish(collection)

    def onUnpublishSidebarCollectionEventUpdateUI(self, event):
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            share = sharing.getShare(collection)
            sharedByMe = sharing.isSharedByMe(share)
        event.arguments['Enable'] = collection is not None and sharing.isShared(collection) and sharedByMe

    def onShareToolEvent(self, event):
        # Triggered from "Test | Share tool..."
        ShareTool.ShowShareToolDialog(wx.GetApp().mainFrame, view=self.itsView)


    def onSyncCollectionEvent (self, event):
        # Triggered from "Test | Sync collection..."
        self.itsView.commit() 
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            sharing.syncCollection(collection)

    def onSyncCollectionEventUpdateUI (self, event):
        """
        Update the menu to reflect the selected collection name
        """
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:

            sidebar = Block.findBlockByName("Sidebar")
            filterClasses = []
            if sidebar.filterKind is not None:
                klass = sidebar.filterKind.classes['python']
                className = "%s.%s" % (klass.__module__, klass.__name__)
                filterClasses.append(className)

            collName = sharing.getFilteredCollectionDisplayName(collection,
                                                                filterClasses)

            menuTitle = _(u'Sync "%(collectionName)s"') % {'collectionName': collName}
            if sharing.isShared(collection):
                event.arguments['Enable'] = True
            else:
                event.arguments['Enable'] = False
        else:
            event.arguments['Enable'] = False
            menuTitle = _(u'Sync a collection')
        event.arguments ['Text'] = menuTitle

    def onCopyCollectionURLEvent(self, event):
        collection = self.getSidebarSelectedCollection()
        if collection is not None:
            share = sharing.getShare(collection)
            if share is not None:
                urls = sharing.getUrls(share)
                if len(urls) == 1:
                    urlString = urls[0]
                else:
                    urlString = "Read-write: %s\nRead-only: %s\n" % (urls[0], urls[1])

                gotClipboard = wx.TheClipboard.Open()
                if gotClipboard:
                    wx.TheClipboard.SetData(wx.TextDataObject(unicode(urlString)))
                    wx.TheClipboard.Close()

    def onCopyCollectionURLEventUpdateUI(self, event):
        enable = False
        collection = self.getSidebarSelectedCollection()
        if collection is not None:
            share = sharing.getShare(collection)
            if share is not None:
                enable = True
        event.arguments['Enable'] = enable

    def onTakeOnlineOfflineEvent(self, event):
        collection = self.getSidebarSelectedCollection()
        if collection is not None:
            if sharing.isOnline(collection):
                sharing.takeOffline(collection)
            else:
                sharing.takeOnline(collection)

    def onTakeOnlineOfflineEventUpdateUI(self, event):
        enable = False
        menuTitle = "Toggle online/offline"

        collection = self.getSidebarSelectedCollection()
        if collection is not None:
            if sharing.isShared(collection):
                enable = True
                if sharing.isOnline(collection):
                    menuTitle = "Take offline"
                else:
                    menuTitle = "Take online"

        event.arguments['Enable'] = enable
        event.arguments ['Text'] = menuTitle




    def onSyncAllEvent (self, event):
        """
        Synchronize Mail and all sharing.
        The "File | Sync | All" menu item, and the Sync All Toolbar button
        """

        view = self.itsView

        # Check account status:
        DAVReady = sharing.isWebDAVSetUp(view)
        inboundMailReady = sharing.isInboundMailSetUp(view)

        # Any active shares?  (Even if default WebDAV account not set up,
        # the user could have subscribed with tickets)
        activeShares = sharing.checkForActiveShares(view)

        if not (DAVReady or activeShares or inboundMailReady):
            # Nothing is set up -- nudge the user to set up a sharing account
            sharing.ensureAccountSetUp(view, sharing=True)
            # Either the user has created a sharing account, or they haven't,
            # but it doesn't matter since there's no shares to sync
            return

        # At least one account is setup, or there are active shares

        # find all the shared collections and sync them.
        if activeShares:
            self.setStatusMessage (_(u"Synchronizing shared collections..."))
            sharing.syncAll(view)
            self.setStatusMessage (_(u"Shared collections synchronized"))
        else:
            if DAVReady:
                self.setStatusMessage (_(u"No shared collections found"))

        # If mail is set up, fetch it:
        if inboundMailReady:
            self.setStatusMessage (_(u"Getting new Mail"))
            self.onGetNewMailEvent (event)

    def onSyncWebDAVEvent (self, event):
        """
        Synchronize WebDAV sharing.
        The "File | Sync | Shares" menu item
        """

        view = self.itsView

        activeShares = sharing.checkForActiveShares(view)
        if activeShares:
            # find all the shared collections and sync them.
            self.setStatusMessage (_(u"Synchronizing shared collections..."))
            sharing.syncAll(view)
            self.setStatusMessage (_(u"Shared collections synchronized"))

        else:
            if not sharing.isWebDAVSetUp(view):
                # DAV is not set up -- nudge the user to set up sharing account
                sharing.ensureAccountSetUp(view, sharing=True)
                # Either way, we don't care if the user actually created an
                # account or not, we know there's nothing to sync
                return
            self.setStatusMessage (_(u"No shared collections found"))



    def onGetNewMailEvent (self, event):
        """
        Fetch Mail.
        The "File | Sync | Mail" menu item
        """

        view = self.itsView

        # Make sure we have all the accounts; returns False if the user cancels
        # out and we don't.
        if not sharing.ensureAccountSetUp(view, inboundMail=True):
            return

        # @@@DLD bug 1998 - why do we have to commit here?  Are we pushing our changes
        # over to mail?
        view.commit()

        for account in Mail.IMAPAccount.getActiveAccounts(view):
            Globals.mailService.getIMAPInstance(account).getMail()

        for account in Mail.POPAccount.getActiveAccounts(view):
            Globals.mailService.getPOPInstance(account).getMail()

        view.refresh()
