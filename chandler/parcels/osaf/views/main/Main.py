#   Copyright (c) 2004-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from datetime import timedelta
from time import time, strftime
import wx, os, sys, traceback, logging, re, webbrowser
import application.dialogs.Util
import pkg_resources

from application import Globals, Printing, schema, Utility
from application.AboutBox import AboutBox
from application.Application import wxBlockFrameWindow
from application.dialogs import ( AccountPreferences, PublishCollection,
                                  SubscribeCollection, RestoreShares, autosyncprefs, TurnOnTimezones,
                                  ActivityViewer, Progress, Invite, Proxies
)

from repository.item.Item import MissingClass
from osaf import (
    pim, sharing, messages, webserver, settings, dumpreload, quickentry
)
from osaf.activity import *

from osaf.pim import Contact, mail, stamp_to_command
from osaf.usercollections import UserCollection

from osaf.mail import constants
import twisted.internet.error

from osaf.framework.blocks.Views import View
from osaf.framework.blocks.Block import Block

from osaf.framework.prompts import promptOk

from i18n import ChandlerMessageFactory as _

from application.Utility import getDesktopDir
from application.dialogs import ImportExport
from application.dialogs.RecurrenceDialog import delayForRecurrenceDialog
logger = logging.getLogger(__name__)

class MainView(View):
    """
    Main Chandler view contains event handlers for Chandler.

    Can't do any kind of edit operation by default.
    Override the ones that you can do.

    The presence of these methods disables the
    associated menu items if the message
    bubbles all the way up to us.  
    """
    def _Method_CantEdit(self, event):
        event.arguments['Enable'] = False

    onCopyEventUpdateUI = _Method_CantEdit
    onCutEventUpdateUI = _Method_CantEdit
    onRemoveEventUpdateUI = _Method_CantEdit
    onPasteEventUpdateUI = _Method_CantEdit
    onUndoEventUpdateUI = _Method_CantEdit
    onRedoEventUpdateUI = _Method_CantEdit
    onSelectAllEventUpdateUI = _Method_CantEdit
    onDuplicateEventUpdateUI = _Method_CantEdit

    def displayMailError (self, message, account):
        application.dialogs.Util.mailAccountError(self.itsView, message, account)

    def displaySMTPSendError(self, mailMessage, account):
        """
        Called when the SMTP Send generated an error.
        """
        if mailMessage is not None:
            item = mailMessage.itsItem

            # sender is the main view
            error = getattr(item, "error", None)
            if error is not None:
                errorMessage = _(u"Message Title: %(title)s\nError: %(translatedErrorStrings)s") % {
                                     'title': item.displayName,
                                     'translatedErrorStrings': error
                                 }
            else:
                errorMessage = _(u"An unknown error has occurred.")

            from application.dialogs import Util
            # add 'errorQuestion' to the bottom of the dialog, above the
            # buttons after the i18n freeze is over (0.7.1).
            errorQuestion = _(u"Would you like to")
            result = Util.promptUserAction(
                u'',
                errorMessage,
                okayTitle = _(u"Send Again"),
                cancelTitle = _(u"Edit Message"))
            if result == wx.ID_OK:
                # User clicked 'send again' button
                eventName =  "SendMail"
            else:
                eventName =  "DisplayMailMessage"
            self.postEventByName(eventName, {'item': item})

            """
            Clear the status message.
            """
            self.setStatusMessage(u'')

    def displaySMTPSendSuccess (self, mailMessage, account):
        """
        Called when the SMTP Send was successful.
        """
        if mailMessage is not None:
            self.setStatusMessage (constants.UPLOAD_SENT % \
                                   {'accountName': account.displayName,
                                    'subject': mailMessage.subject})

    def onAboutEvent(self, event):
        # The "Help | About Chandler..." menu item
        """
        Show the about box in response to the about command.
        """
        about = AboutBox()
        return about

    def onEmptyTrashEvent(self, event):
        trash = schema.ns("osaf.pim", self).trashCollection
        trash.empty()

    def onEmptyTrashEventUpdateUI(self, event):
        trash = schema.ns("osaf.pim", self).trashCollection
        event.arguments['Enable'] = not trash.isEmpty()

    def onEditAccountPreferencesEvent (self, event):
        # Triggered from "File | Prefs | Accounts..."

        AccountPreferences.ShowAccountPreferencesDialog(rv=self.itsView)

    def onLocalePickerEvent (self, event):
        from application.dialogs import LocalePickerDialog

        LocalePickerDialog.showLocalePickerDialog()

    def onConfigureProxiesEvent (self, event):
        Proxies.Show(rv=self.itsView)

    def onProtectPasswordsEvent (self, event):
        # Triggered from "File | Prefs | Protect Passwords..."
        from osaf.framework import MasterPassword
        from osaf.framework.twisted import waitForDeferred
        waitForDeferred(MasterPassword.change(self.itsView))

    def trashCollectionSelected(self):
        trashCollection = schema.ns("osaf.pim", self).trashCollection

        if self.getSidebarSelectedCollection() is trashCollection:
            msg = _(u"New items cannot be created in the Trash.")
            promptOk(msg)
            return True

        return False

    def onNewItemEventUpdateUI(self, event):
        # Change the title of the "New Item" menu depending on the area selected 
        # in the Toolbar.
        # Unfortunately, because of the mnemonics, we can't use the same strings than
        # the ones defined for the rest of the menu (see ItemMenu creation in menus.py)
        if event.arguments['sender'].itsName == 'NewItemItem':
            if Block.findBlockByName("ApplicationBarAllButton").widget.IsToggled():
                # L10N: One of the possible titles for the  Item -> New -> New Item menu.
                # This title changes based on the area selected in the Toolbar.
                # The keyboard mnemonic should be the same for each alternative title.
                event.arguments['Text'] = _(u'Ne&w Note')
            elif Block.findBlockByName("ApplicationBarMailButton").widget.IsToggled():
                # L10N: One of the possible titles for the  Item -> New -> New Item menu.
                # This title changes based on the area selected in the Toolbar.
                # The keyboard mnemonic should be the same for each alternative title.
                event.arguments['Text'] = _(u'Ne&w Message')
            elif Block.findBlockByName("ApplicationBarTaskButton").widget.IsToggled():
                # L10N: One of the possible titles for the  Item -> New -> New Item menu.
                # This title changes based on the area selected in the Toolbar.
                # The keyboard mnemonic should be the same for each alternative title.
                event.arguments['Text'] = _(u'Ne&w Task')
            elif Block.findBlockByName("ApplicationBarEventButton").widget.IsToggled():
                # L10N: One of the possible titles for the  Item -> New -> New Item menu.
                # This title changes based on the area selected in the Toolbar.
                # The keyboard mnemonic should be the same for each alternative title.
                event.arguments['Text'] = _(u'Ne&w Event')

    def onNewItemEvent(self, event):
        # See the declaration of the class NewItemEvent in Block.py for a
        # description of the attributes and values.

        if self.trashCollectionSelected():
            # Items can not be created in the
            # trash collectioon
            return


        allCollection = schema.ns('osaf.pim', self).allCollection
        sidebar = Block.findBlockByName("Sidebar")
        classParameter = event.classParameter

        if classParameter is MissingClass:
            classParameter = sidebar.filterClass

        if issubclass(classParameter, pim.Stamp):
            stampClass = classParameter
        else:
            stampClass = MissingClass

        # First check to see if arguments have an item, then
        # try onNewItem method, finally create an item of type
        # classParameter
        newItem = event.arguments.get ("item", None)

        # no item was passed in, so create a new one
        if newItem is None:
            # onNewItem method takes precedence of classParameter
            onNewItemMethod = getattr(event, "onNewItem", None)
            if onNewItemMethod is not None:
                newItem = onNewItemMethod()
                if newItem is None:
                    return
            else:
                # A classParameter of MissingClass stamps a Note with the sidebar's
                # filterClass

                if classParameter is MissingClass or stampClass is not MissingClass:
                    kindToCreate = pim.Note.getKind(self.itsView)
                else:
                    kindToCreate = classParameter.getKind(self.itsView)

                newItem = kindToCreate.newItem(None, None)

                if stampClass is not MissingClass:
                    stampObject = stampClass(newItem)
                    stampObject.add()
                    stampObject.InitOutgoingAttributes()
                else:
                    newItem.InitOutgoingAttributes ()

        collection = event.collection
        selectedCollection = self.getSidebarSelectedCollection()
        if collection is None:
            # If collection is None use the selected collection
            collection = selectedCollection

        # If we can't add items to the collection use the All collection
        if (collection is None or
            sharing.isReadOnly(collection) or
            not UserCollection(collection).canAdd):
            # Tell the sidebar we want to go to the All collection
            collection = allCollection

        # The stampClass is used to specify the viewer
        sidebar.setPreferredClass(stampClass, keepMissing=True)

        if not collection in sidebar.contents and event.collectionAddEvent is not None:
            Block.post(event.collectionAddEvent, {}, self)

        if collection in sidebar.contents and collection is not selectedCollection:
            sidebar.postEventByName("SelectItemsBroadcast", {'items':[collection]})

        # repository collection implements add to print an error that
        # says add isn't implemented, so we can't just call add if
        # the add method exists.
        try:
            collection.add (newItem)
        except NotImplementedError:
            pass

        self.selectItems([newItem])

        return newItem

    def selectItems(self, itemList):
        # Tell the summary view to select our new item
        sidebarBPB = self.findBlockByName ("SidebarBranchPointBlock")
        sidebarBPB.childBlocks.first().postEventByName (
            'SelectItemsBroadcast',
            {'items':itemList})

        # Put the focus into the Detail View
        detailRoot = self.findBlockByName("DetailRoot")
        if detailRoot:
            detailRoot.focus()

    # Disabling Printing in Chandler as required by bug 8137 - This is a temporary measure
    # Simply delete these functions to enable printing

    def onPrintPreviewEventUpdateUI(self, event):
        # Print Disabled
        event.arguments['Enable'] = False

    def onPageSetupEventUpdateUI(self, event):
        # Print Disabled
        event.arguments['Enable'] = False

    def onPrintEventUpdateUI(self, event):
        # Print Disabled
        event.arguments['Enable'] = False

    # End Disabling Printing

    def onPrintPreviewEvent (self, event):
        self.printEvent(1)

    def onPageSetupEvent (self, event):
        self.printEvent(2)

    def onPrintEvent (self, event):
        self.printEvent(0)

    def onSearchEvent (self, event):
        quickEntryBlock = Block.findBlockByName("ApplicationBarQuickEntry")

        text = getattr (quickEntryBlock, "lastText", None)
        sidebar = Block.findBlockByName ("Sidebar")

        if text is None:
            text = "/" + SearchCommand.command_names[0] + " "

        widget = quickEntryBlock.widget.GetControl()
        widget.SetFocus()
        quickEntryBlock.text = text
        quickEntryBlock.synchronizeWidget()
        end = len(text)
        start = text.find (u' ')
        if start == -1:
            start = end
        else:
            start = start + 1
        widget.SetSelection (start, end)

    def onSwitchToQuickEntryEvent (self, event):
        quickEntryBlock = self.findBlockByName("ApplicationBarQuickEntry")
        widget = quickEntryBlock.widget.GetControl()
        widget.SetFocus()
        quickEntryBlock.synchronizeWidget()

        start = 0
        end = len(quickEntryBlock.text)
        widget.SetSelection(start, end)

    def onQuickEntryEvent (self, event):
        sidebar = self.findBlockByName("Sidebar")
        quickEntryBlock = self.findBlockByName("ApplicationBarQuickEntry")
        quickEntryWidget = quickEntryBlock.widget.GetControl()

        text = quickEntryWidget.GetValue().strip()

        # handle cancel
        if len(text) == 0 or event.arguments.get("cancelClicked", False):
            if sidebar.showSearch:
                # Remember the search string
                if len(text) > 0:
                    quickEntryBlock.lastText = text
                sidebar.setShowSearch(False)

            quickEntryWidget.SetValue("")
            self.setStatusMessage(u'')
            return

        # Process quick entry commands
        qe_commands = []
        end = 0
        # L10N: string to be appended to text when it has unrecognized commands
        error_string = _(u"  ?")
        for match in quick_entry_commands_re.finditer(text):
            command = get_quick_entry(match.group('cmd').lower())

            if command is None:
                quickEntryWidget.SetValue(text + error_string)
                self.setStatusMessage (_(u"Command entered is not valid."))
                if sidebar.showSearch:
                    sidebar.setShowSearch(False)
                quickEntryWidget.SetFocus()
                return

            end = match.end()
            qe_commands.append(command)
            if len(qe_commands) == 1 and command.single_command:
                break

        text = text[end:].strip().rstrip(error_string)

        if len(qe_commands) == 0:
            # use a default stamp command based on the selected filter
            command = stamp_to_command.get(sidebar.filterClass)
            if command is None:
                command = stamp_to_command.get(None)
            qe_commands.append(command)

        state = quickentry.run_commands(self.itsView, text, qe_commands)
        item = state.item
        if item is not None:
            # Add the item to the selected collection if possible, otherwise
            # the Dashboard collection
            collection = self.getSidebarSelectedCollection()
            msg = _(u"'%(title)s' created in %(collection)s")
            if (collection is None or sharing.isReadOnly(collection) or 
                not UserCollection(collection).canAdd):
                collection = schema.ns('osaf.pim', self.itsView).allCollection

            statusMessageDict = {'title' : item.displayName, 
                                 'collection' : collection.displayName}
            collection.add(item)
            self.selectItems([item])
            self.setStatusMessage(msg % statusMessageDict)

        # Stop showing search results if a non-search command was run
        if not getattr(state, 'search', False):
            if sidebar.showSearch:
                sidebar.setShowSearch(False)

            # Clear out the widget when non-search commands run
            quickEntryWidget.SetValue("")

        # bring focus back to quick entry so the next quick item can be created
        quickEntryWidget.SetFocus()


    def printEvent(self, isPreview):
        block = self.findBlockByName ("TimedEvents")
        if block is None:
            wx.MessageBox (_(u"Printing is currently only supported for the calendar view."),
                           u"Chandler",
                           parent=wx.GetApp().mainFrame)
        else:
            printObject = Printing.Printing(wx.GetApp().mainFrame, block.widget)
            if isPreview == 1:
                printObject.OnPrintPreview()
            elif isPreview == 0:
                printObject.OnPrint()
            elif isPreview == 2:
                printObject.OnPageSetup()

    def openURLOrDialog(self, url):
        try:
            webbrowser.open(url)
        except OSError:
            wx.MessageBox (_(u"Chandler could not access a browser to open %(url)s.") % {'url' : url},
                           _(u"Browser Not Found"),
                           parent=wx.GetApp().mainFrame)

    def onHelpEvent(self, event):
        # For now, open the Chandler FAQ page:
        #
        # <http://lists.osafoundation.org/pipermail/design/2006-August/005311.html>
        self.openURLOrDialog(
            'http://chandlerproject.org/faq'
        )

    def onGettingStartedEvent(self, event):
        self.openURLOrDialog(
            'http://chandlerproject.org/guide'
        )

    def onFileBugEvent(self, event):
        self.openURLOrDialog(
            'http://chandlerproject.org/reportabug'
        )

    def onQuitEvent (self, event):
        """
        Close all the windows. Close the mainFrame last since it's the
        place we execute all the quitting Chandler code.
        """
        mainFrame = wx.GetApp().mainFrame
        for window in wx.GetTopLevelWindows():
            if window is not mainFrame:
                window.Close()
        mainFrame.Close()

    def onCloseEvent (self, event):
        curWindow = self.widget.FindFocus() #start with the focus
        while not curWindow.IsTopLevel():
            curWindow = curWindow.GetParent()
        curWindow.Close()

    def onCommitViewEvent(self, event):
        self.RepositoryCommitWithStatus()

    def onBackupRepositoryEvent(self, event):
        self.RepositoryCommitWithStatus()

        from osaf.framework import MasterPassword
        MasterPassword.beforeBackup(self.itsView)

        dlg = wx.DirDialog(wx.GetApp().mainFrame, _(u'Back up Repository'),
                           unicode(Utility.getDesktopDir(), sys.getfilesystemencoding()),
                           wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            path = os.path.join(dlg.GetPath(), '__repository__')
        else:
            path = None
        dlg.Destroy()

        if path is not None:
            repository = self.itsView.repository
            progressMessage = _(u'Backing up repository...')
            repository.logger.info('Backing up repository...')
            self.setStatusMessage(progressMessage)
            dbHome = repository.backup(path)
            dbHome_u = dbHome.decode(sys.getfilesystemencoding())
            successMessage = _(u'Repository was backed up to %(directory)s') % {'directory': (dbHome_u)}
            repository.logger.info('Repository was backed up into %s' % (dbHome))
            self.setStatusMessage(successMessage)

    def onRestoreRepositoryEvent(self, event):

        app = wx.GetApp()

        srcPath = path = Utility.getDesktopDir()
        rev = 1
        while True:
            backupPath = os.path.join(srcPath, "__repository__.%03d" %(rev))
            if os.path.isdir(backupPath):
                path = backupPath
                rev += 1
            else:
                break

        dlg = wx.DirDialog(app.mainFrame, _(u'Restore Repository'),
                           unicode(path, sys.getfilesystemencoding()),
                           wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        else:
            path = None
        dlg.Destroy()

        if path is not None:
            dlg = wx.MessageDialog(app.mainFrame,
                                   _(u"You will overwrite your current repository with %(repoPath)s.") % {'repoPath': path},
                                   _(u"Confirm Restore"),
                                   (wx.YES_NO | wx.NO_DEFAULT |
                                    wx.ICON_EXCLAMATION))
            cmd = dlg.ShowModal()
            dlg.Destroy()
            if cmd == wx.ID_YES:
                app.PostAsyncEvent(app.restart, restore=path)

    def onCreateRepositoryEvent(self, event):
        self.switchRepository(True)

    def onSwitchRepositoryEvent(self, event):
        self.switchRepository(False)

    def switchRepository(self, create=False):

        app = wx.GetApp()
        self.RepositoryCommitWithStatus()

        dlg = wx.DirDialog(wx.GetApp().mainFrame, _(u'Switch Repository'),
                           unicode(Utility.getDesktopDir(), sys.getfilesystemencoding()),
                           wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            repodir = dlg.GetPath()
        else:
            repodir = None
        dlg.Destroy()

        if repodir is not None:
            path = os.path.join(repodir, '__repository__')
            if not os.path.exists(path):
                if not create:  # cloning the current repository
                    repository = self.itsView.repository
                    progressMessage = _(u'Preparing repository...')
                    repository.logger.info('Preparing repository...')
                    self.setStatusMessage(progressMessage)
                    dbHome = repository.backup(path)
                    successMessage = _(u'Repository is ready.')
                    repository.logger.info('Repository is ready')
                    self.setStatusMessage(successMessage)
                    message = _(u"Your current repository was copied to %(filePath)s and Chandler is set up to use it after restart. Your current repository will not be affected.\n\nRestart now?")
                    restore = dbHome
                else:
                    message = _(u"A new repository will be created at %(filePath)s and Chandler is set up to use it after restart. Your current repository will not be affected.\n\nRestart now?")
                    restore = None
            else:
                restore = None
                message = _(u"Chandler is setup to use the repository at %(filePath)s after restart. Your current repository will not be affected.\n\nRestart now?")

            dlg = wx.MessageDialog(app.mainFrame, message % {"filePath": repodir},
                                   _(u"Confirm Restart"),
                                   (wx.YES_NO | wx.YES_DEFAULT |
                                    wx.ICON_EXCLAMATION))
            cmd = dlg.ShowModal()
            dlg.Destroy()

            if cmd == wx.ID_YES:

                prefs = Utility.loadPrefs(Globals.options)
                if 'options' not in prefs:
                    prefs['options'] = {}
                prefs['options']['repodir'] = repodir
                prefs.write()

                if restore:
                    app.PostAsyncEvent(app.restart, restore=restore)
                elif create:
                    app.PostAsyncEvent(app.restart, create=True)
                else:
                    app.PostAsyncEvent(app.restart)

    def RepositoryCommitWithStatus(self):
        """
        Do a repository commit with notice posted in the Status bar.
        """
        self.setStatusMessage(_(u"Saving changes..."))

        Block.finishEdits()
        activity = Activity("Saving...")
        activity.started()

        try:
            self.itsView.commit()
            activity.completed()
        except Exception, e:
            logger.exception("Commit failed")
            self.setStatusMessage(_(u"Changes failed to save. Go to the Tools>>Logging>>Log Window... menu for details."))
            activity.failed(exception=e)
            raise
        else:
            self.setStatusMessage('')

    def setStatusMessage (self, statusMessage, progressPercentage=-1):
        """
        Allows you to set the message contained in the status bar.
        You can also specify values for the progress bar contained
        on the right side of the status bar.  If you specify a
        progressPercentage (as a float 0 to 1) the progress bar will
        appear.  If no percentage is specified the progress bar will
        disappear.
        """

        Block.findBlockByName('StatusBar').setStatusMessage (statusMessage, progressPercentage)

    def alertUser(self, message):
        promptOk(message)

    def onReplyEventUpdateUI(self, event):
        event.arguments['Enable'] = False
    def onReplyAllEventUpdateUI(self, event):
        event.arguments['Enable'] = False
    def onForwardEventUpdateUI(self, event):
        event.arguments['Enable'] = False

    def onSendShareItemEventUpdateUI(self, event):
        # If we get asked about this, and it hasn't already been set, there's no selected 
        # item anywhere - disallow sending. Also, make sure the label's set back to "Send"
        # and the bitmap is set to the send bitmap.
        event.arguments ['Enable'] = False
        event.arguments ['Text'] = messages.SEND
        event.arguments ['Bitmap'] = "ApplicationBarSend.png"

    def onSendMailEvent(self, event):
        Block.finishEdits()
        item = event.arguments['item']
        delayForRecurrenceDialog(item, self._sendMailAction, item)

    def _sendMailAction(self, item):
        # commit changes, since we'll be switching to Twisted thread
        self.RepositoryCommitWithStatus()

        if not sharing.ensureAccountSetUp(self.itsView, outboundMail=True):
            return

        mailToSend = mail.MailStamp(item)

        code, valid, invalid = mailToSend.getSendableState()

        if code == 0:
            # 0 = no valid addresses
            wx.MessageBox (_(u"Message can not be sent. You have not entered any valid email addresses."),
                           _(u"Mail Error"),
                           parent=wx.GetApp().mainFrame)
            return

        elif code == 1:
            # 1 = some valid addresses
            if application.dialogs.Util.mailAddressError():
                # Method returns True when the user selects to fix the bad
                # addresses
                return

        elif code == 2:
            # 2 = No to addresses
            wx.MessageBox (_(u"Message can not be sent. At least one valid To: email address is required."),
                           _(u"Mail Error"),
                           parent=wx.GetApp().mainFrame)
            return


        # determine the account through which we'll send this message;
        # we'll use the first outgoing account associated with the message's
        # sender or the default outgoing account
        sender = mailToSend.getSender()
        assert sender is not None and sender.accounts is not None
        outgoingAccount = sender.accounts.first()
        account = (outgoingAccount is not None and outgoingAccount
                   or mail.getCurrentOutgoingAccount(self.itsView))

        # Now send the mail
        smtpInstance = Globals.mailService.getSMTPInstance(account)
        smtpInstance.sendMail(mailToSend)


    # Test Methods

    def getSidebarSelectedCollection (self, private=False):
        """
        Return the sidebar's selected item collection.
        Will not return private collections (whose "private" attribute
        is True) unless you pass private=True.
        """
        sidebar = Block.findBlockByName ("Sidebar")
        item = sidebar.contents.getFirstSelectedItem()
        if getattr(item, 'private', None) is not None and private == False and item.private:
            return None

        return item

    def allowCutOrPaste(self):
        """
        Don't cut or paste if the sidebar selected collection is read-only, or
        if the trash is selected.
        """
        collection = self.getSidebarSelectedCollection()
        trash = schema.ns("osaf.pim", self).trashCollection
        return not sharing.isReadOnly(collection) and collection is not trash

    def _logChange(self, item, version, status, values, references):
        logger = item.itsView.logger
        logger.info("%s %d 0x%0.4x\n  values: %s\n  refs: %s",
                    schema.Item.__repr__(item), version, status, values, references)

    def onCheckRepositoryEvent(self, event):
        # triggered from "Test | Check Repository" Menu
        view = self.itsView
        repository = view.repository
        progressMessage = _(u'Checking repository...')
        repository.logger.info("Checking repository ...")
        self.setStatusMessage(progressMessage)
        before = time()
        if view.check():
            after = time()
            successMessage = _(u'Repository check completed successfully in %(numSeconds)s.') % \
                              {'numSeconds': timedelta(seconds=after-before)}
            repository.logger.info('Check completed successfully in %s' % (timedelta(seconds=after-before)))
            self.setStatusMessage(successMessage)
        else:
            errorMessage = _(u'Repository check completed with errors.')
            repository.logger.info('Check completed with errors')
            self.setStatusMessage(errorMessage)

    def onCheckAndRepairRepositoryEvent(self, event):
        # triggered from "Test | Check Repository and Repair" Menu
        view = self.itsView
        repository = view.repository
        progressMessage = _(u'Checking repository...')
        repository.logger.info("Checking repository ...")
        self.setStatusMessage(progressMessage)
        before = time()
        if view.check(True):
            after = time()
            successMessage = _(u'Repository check completed successfully in %(numSeconds)s.') % \
                              {'numSeconds': timedelta(seconds=after-before)}
            repository.logger.info('Check completed successfully in %s' % (timedelta(seconds=after-before)))
            self.setStatusMessage(successMessage)
        else:
            errorMessage = _(u'Repository check completed with errors.')
            repository.logger.info('Check completed with errors')
            self.setStatusMessage(errorMessage)

    def onCompactRepositoryEvent(self, event):
        # triggered from "Tools | Repository | Compact" Menu
        schema.ns('osaf.app', self.itsView).compactTask.run_once(True)

    def onIndexRepositoryEvent(self, event):
        # triggered from "Tools | Repository | Index" Menu
        self.RepositoryCommitWithStatus()
        repository = self.itsView.repository
        repository.notifyIndexer()

    def onImportICalendarEvent(self, event):
        # triggered from "File | Import/Export" menu
        self.setStatusMessage(_(u"Import .ics Calendar file."))
        dialog = ImportExport.ImportDialog(_(u"Import .ics Calendar"),
                                           self.itsView)
        ret = dialog.ShowModal()
        if ret == wx.ID_OK:
            self.setStatusMessage(_(u"Import completed."))
        else:
            self.setStatusMessage(_(u"Import cancelled."))

        dialog.Destroy()

    def onExportICalendarEventUpdateUI(self, event):
        collection = self.getSidebarSelectedCollection()
        if collection is None:
            event.arguments['Enable'] = False

    def onExportICalendarEvent(self, event):
        # triggered from "File | Import/Export" Menu
        collection = self.getSidebarSelectedCollection()
        if collection is None:
            return

        for item in collection:
            if (pim.has_stamp(item, pim.EventStamp) or 
                pim.has_stamp(item, pim.TaskStamp)):
                break
        else:
            wx.MessageBox (_(u"This collection contains no events."),
                           _(u"Export Cancelled"),
                           parent=wx.GetApp().mainFrame)
            return

        self.setStatusMessage(_(u"Export to .ics Calendar file."))
        if not TurnOnTimezones.ShowTurnOnTimezonesDialog(
            self.itsView,
            state=TurnOnTimezones.EXPORT,
            modal=True):
            # cancelled in turn on timezone dialog
            self.setStatusMessage(_(u"Export cancelled."))
            return


        name = collection.displayName
        try:
            name.encode('ascii')
            pattern = re.compile('[^A-Za-z0-9]')
            name = re.sub(pattern, "_", name)
        except UnicodeEncodeError:
            name = str(collection.itsUUID)

        if isinstance(name, unicode):
            # Value in name will be ascii so
            # cast name to a str if it is
            # unicode.
            name = str(name)

        options = [dict(name='cid:reminders-filter@osaf.us', checked = True,
                        label = _(u"Export reminders")),
                        dict(name='cid:event-status-filter@osaf.us', checked = True,
                             label = _(u"Export event status"))]

        res = ImportExport.showFileChooserWithOptions(
            _(u"Export .ics Calendar"),
            os.path.join(getDesktopDir(), "%s.ics" % name),
            _(u"iCalendar files|*.ics|All files (*.*)|*.*"),
            wx.SAVE | wx.OVERWRITE_PROMPT, options)

        (ok, fullpath, optionResults) = res

        if not ok:
            self.setStatusMessage(_(u"Export cancelled."))
        else:
            try:
                (dir, filename) = os.path.split(fullpath)
                self.setStatusMessage (_(u"Exporting to %(filename)s...") % {'filename': filename})
                try:
                    os.remove(fullpath)
                except OSError:
                    pass

                sharing.exportFile(self.itsView, fullpath, collection,
                                   filters=set(k for k, v in optionResults.iteritems()
                                               if not v))

                self.setStatusMessage(_(u"Export completed."))
            except:
                trace = "".join(traceback.format_exception (*sys.exc_info()))
                logger.info("Failed exportFile:\n%s" % trace)
                self.setStatusMessage(_(u"Export failed."))


    def TraceMainViewCloud(self, traceItem):
        # for debugging, trace through the mainViewRoot copy cloud
        def commonName(item, showKind=True):
            if showKind:
                kindLabel = commonName(item.itsKind, False)+':'
            else:
                kindLabel = ''
            if hasattr(item, 'displayName'): 
                return kindLabel + item.displayName
            if hasattr(item, 'blockName'): 
                return kindLabel + item.blockName
            if hasattr(item, 'itsName') and item.itsName is not None: 
                return kindLabel + item.itsName
            return str(item)

        mainViewRoot = Block.findBlockByName ('MainViewRoot')
        traceData = {}
        mainViewRoot.getItemCloud(cloudAlias="copying", trace=traceData)
        cloud = mainViewRoot.getKind(mainViewRoot.itsView).getClouds("copying")[0]
        logger.info("MainViewRoot trace information:")
        for item, other, endpoint, policy, indent in cloud.traceItem(traceItem, traceData):
            logger.info( "   "*indent +'\t"'+
                         commonName(item)+'"\t"'+
                         commonName(other)+'"\t'+ 
                         endpoint+'\t'+ policy)

    def onSubscribeToCollectionEvent(self, event):
        # Triggered from "Collection | Subscribe to collection..."

        if schema.ns('osaf.app', self.itsView).prefs.isOnline:
            SubscribeCollection.Show(self.itsView)

    def onSubscribeToCollectionEventUpdateUI(self, event):
        event.arguments['Enable'] = schema.ns('osaf.app',
            self.itsView).prefs.isOnline and sharing.isOnline(self.itsView)

    def _dumpFile(self, obfuscate=False, path=None):
        from osaf.framework import MasterPassword
        MasterPassword.beforeBackup(self.itsView)

        if path is None:
            filename = "%s.chex" % strftime("%Y%m%d%H%M%S")
            wildcard = "%s|*.chex|%s (*.*)|*.*" % (_(u"Chandler export files"), _(u"All files"))
    
            dlg = wx.FileDialog(wx.GetApp().mainFrame,
                                _(u"Export Collections and Settings"), "", filename, wildcard,
                                wx.SAVE|wx.OVERWRITE_PROMPT)

            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
            dlg.Destroy()

        if path:
            activity = Activity("Export to %s" % path)
            Progress.Show(activity)
            activity.started()

            try:
                dumpreload.dump(self.itsView, path, activity=activity,
                                obfuscate=obfuscate)
                activity.completed()
            except Exception, e:
                logger.exception("Failed to export file")
                activity.failed(exception=e)
                raise
            self.setStatusMessage(_(u'Items exported.'))

    def onDumpToFileEvent(self, event):
        self._dumpFile()

    def onObfuscatedDumpToFileEvent(self, event):
        self._dumpFile(obfuscate=True)

    def onReloadFromFileEvent(self, event):
        if wx.MessageBox(_(u"Reloading will remove all data and replace it with data from the export file. Are you sure you want to reload?"),
                         _(u"Reload"),
                         style=wx.YES_NO,
                         parent=wx.GetApp().mainFrame) != wx.YES:
            return

        wildcard = "%s|*.chex|%s|*.dump|%s (*.*)|*.*" % (_(u"Chandler export files"),
                                                         _(u"Chandler dump files"),
                                                         _(u"All files"))

        dlg = wx.FileDialog(wx.GetApp().mainFrame,
                            _(u"Reload Collections and Settings"), "", "", wildcard,
                            wx.OPEN)

        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        if path:
            wx.GetApp().restart(reload=path)

    def onAddSharingLogToSidebarEvent(self, event):
        sidebar = Block.findBlockByName ("Sidebar").contents
        try:
            log = schema.ns('osaf.sharing', self.itsView).activityLog
        except AttributeError:
            sharingParcel = schema.ns('osaf.sharing', self.itsView).parcel
            log = pim.ListCollection.update(sharingParcel, 'activityLog',
                                            displayName="Sharing Activity")
        # if already present, just select it
        if log in sidebar:
            self.postEventByName('RequestSelectSidebarItem', {'item': log})
        else:
            schema.ns("osaf.app", self).sidebarCollection.add(log)

        # go to the All application, so we can view the scripts
        self.postEventByName ('ApplicationBarAll', { })

    def onAddSharingLogToSidebarEventUpdateUI(self, event):
        sidebar = Block.findBlockByName ("Sidebar").contents

        try:
            log = schema.ns('osaf.sharing', self.itsView).activityLog
        except AttributeError:
            log = None

        if log in sidebar:
            menuTitle = _(u'Show Sharing Activity')
        else:
            menuTitle = _(u'Add sharing activity log to Sidebar')
        event.arguments ['Text'] = menuTitle
        event.arguments ['Enable'] = True

    def onResetShareEvent(self, event):
        collection = self.getSidebarSelectedCollection()
        if collection is not None and sharing.isShared(collection):
            share = sharing.getShare(collection)
            share.reset()

    def onResetShareEventUpdateUI(self, event):
        collection = self.getSidebarSelectedCollection()
        event.arguments['Enable'] = (collection is not None and
                                     sharing.isShared(collection))

    def onRecordSetDebuggingEvent(self, event):
        if sharing.logger.level == 10:
            sharing.logger.level = 0
            sharing.WebDAV.ChandlerHTTPClientFactory.logLevel = logging.WARNING
        else:
            sharing.logger.level = 10
            sharing.WebDAV.ChandlerHTTPClientFactory.logLevel = logging.INFO

    def onRecordSetDebuggingEventUpdateUI(self, event):
        if sharing.logger.level == 10:
            menuTitle = _(u'Set S&haring Logging Level to Normal')
        else:
            menuTitle = _(u'Set S&haring Logging Level to Debug')
        event.arguments ['Text'] = menuTitle
        event.arguments ['Enable'] = True

    def onSaveSettingsEvent(self, event):
        # triggered from "Test | Save Settings" Menu

        from osaf.framework import MasterPassword
        MasterPassword.beforeBackup(self.itsView)

        wildcard = "%s|*.ini|%s (*.*)|*.*" % (_(u"Chandler settings files"),
                                              _(u"All files"))

        dlg = wx.FileDialog(wx.GetApp().mainFrame,
                            _(u"Settings saved."), "", "chandler.ini", wildcard,
                            wx.SAVE|wx.OVERWRITE_PROMPT)

        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        if path:
            settings.save(self.itsView, path)
            self.setStatusMessage(_(u'Settings saved'))

    def onRestoreSettingsEvent(self, event):
        # triggered from "Test | Restore Settings" Menu

        wildcard = "%s|*.ini|%s (*.*)|*.*" % (_(u"Chandler settings files"),
                                              _(u"All files"))

        dlg = wx.FileDialog(wx.GetApp().mainFrame,
                            _(u"Restore Settings"), "", "chandler.ini", wildcard, wx.OPEN)

        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        if path:
            try:
                self.itsView.refresh()
                settings.restore(self.itsView, path)
                self.setStatusMessage(_(u'Settings restored.'))
            except Exception, e:
                try:
                    self.itsView.cancel()
                except:
                    pass

                errorText = unicode(e.__str__(), "utf-8", "ignore")

                errorMessage = _(u"An error occurred while restoring settings:\n\n%(error)s") % {
                    'error': errorText}

                self.alertUser(errorMessage)
                logger.exception(e)

    def onActivateWebserverEventUpdateUI (self, event):
        for server in webserver.Server.iterItems(self.itsView):
            if server.isActivated():
                event.arguments['Enable'] = False
                return
        event.arguments['Enable'] = True

    def onActivateWebserverEvent(self, event):
        # Test menu item
        for server in webserver.Server.iterItems(self.itsView):
            server.startup()

    def onShowActivityViewerEvent(self, event):
        ActivityViewer.Show()

    def onShowLogWindowEvent(self, event):
        # Test menu item
        logs = [
            os.path.join(Globals.options.profileDir, 'chandler.log'),
        ]
        application.dialogs.Util.displayLogWindow(logs)
        # import application.dialogs.FileTail
        # logPath = os.path.join(Globals.options.profileDir, 'chandler.log')
        # application.dialogs.FileTail.displayFileTailWindow(
        #     wx.GetApp().mainFrame, logPath)

    def onSetLoggingLevelCriticalEvent(self, event):
        Utility.setLoggingLevel(logging.CRITICAL)

    def onSetLoggingLevelCriticalEventUpdateUI(self, event):
        level = Utility.getLoggingLevel()
        event.arguments['Check'] = (level == logging.CRITICAL)

    def onSetLoggingLevelErrorEvent(self, event):
        Utility.setLoggingLevel(logging.ERROR)

    def onSetLoggingLevelErrorEventUpdateUI(self, event):
        level = Utility.getLoggingLevel()
        event.arguments['Check'] = (level == logging.ERROR)

    def onSetLoggingLevelWarningEvent(self, event):
        Utility.setLoggingLevel(logging.WARNING)

    def onSetLoggingLevelWarningEventUpdateUI(self, event):
        level = Utility.getLoggingLevel()
        event.arguments['Check'] = (level == logging.WARNING)

    def onSetLoggingLevelInfoEvent(self, event):
        Utility.setLoggingLevel(logging.INFO)

    def onSetLoggingLevelInfoEventUpdateUI(self, event):
        level = Utility.getLoggingLevel()
        event.arguments['Check'] = (level == logging.INFO)

    def onSetLoggingLevelDebugEvent(self, event):
        Utility.setLoggingLevel(logging.DEBUG)

    def onSetLoggingLevelDebugEventUpdateUI(self, event):
        level = Utility.getLoggingLevel()
        event.arguments['Check'] = (level == logging.DEBUG)

    def onSyncPrefsEvent(self, event):
        autosyncprefs.Show(self.itsView)

    def onRestoreSharesEvent(self, event):
        if sharing.ensureAccountSetUp(self.itsView, sharing=True):
            RestoreShares.Show(self.itsView)

    def onPublishCollectionEvent(self, event):
        self._onShareOrManageSidebarCollectionEvent(event)

    def onManageSidebarCollectionEvent(self, event):
        self._onShareOrManageSidebarCollectionEvent(event)

    def _onShareOrManageSidebarCollectionEvent(self, event):
        """
        Share the collection selected in the Sidebar.
        If the current collection is already shared, then manage the collection.

        The "Collection | Share collection " menu item.
        """

        collection = self.getSidebarSelectedCollection()
        if (collection is not None and
            schema.ns('osaf.app', self.itsView).prefs.isOnline and
            sharing.isOnline(self.itsView) and
            not UserCollection(collection).outOfTheBoxCollection):

            if (not sharing.isShared(collection) and
                not sharing.ensureAccountSetUp(self.itsView, sharing=True)):
                return

            PublishCollection.ShowPublishDialog(view=self.itsView, collection=collection)

    def onPublishCollectionEventUpdateUI (self, event):
        """
        Update the menu to reflect the selected collection name.
        """
        collection = self.getSidebarSelectedCollection()
        event.arguments['Enable'] = (collection is not None and
             schema.ns('osaf.app', self.itsView).prefs.isOnline and
             sharing.isOnline(self.itsView) and
             not UserCollection(collection).outOfTheBoxCollection and
             not sharing.isShared(collection))

    def onManageSidebarCollectionEventUpdateUI (self, event):
        collection = self.getSidebarSelectedCollection ()
        event.arguments['Enable'] = (collection is not None and
             schema.ns('osaf.app', self.itsView).prefs.isOnline and
             sharing.isOnline(self.itsView) and
             sharing.isShared(collection))

    def _unsubscribeCollection(self):
        # Unsubscribe works for published collections, or collections that
        # have been subscribed to. The collection remains on the server.
        # We have two different menu items enabled for each case. (Bug#9178)
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            sharing.unsubscribe(collection)

    def onUnsubscribePublishedCollectionEvent(self, event):
        self._unsubscribeCollection()

    def onUnsubscribePublishedCollectionEventUpdateUI(self, event):
        # A version of unsubscribe enabled for published collections (Bug#9178)
        collection = self.getSidebarSelectedCollection()
        event.arguments['Enable'] = collection is not None and \
             sharing.isShared(collection) and \
             sharing.isSharedByMe(sharing.getShare(collection))

    def onUnsubscribeCollectionEvent(self, event):
        self._unsubscribeCollection()

    def onUnsubscribeCollectionEventUpdateUI(self, event):
        # Unsubscribe is not enabled for published' collections (Bug#9178)
        collection = self.getSidebarSelectedCollection ()
        event.arguments['Enable'] = collection is not None and \
             sharing.isShared(collection) and \
             not sharing.isSharedByMe(sharing.getShare(collection))

    def onUnpublishCollectionEvent(self, event):
        try:
            collection = self.getSidebarSelectedCollection ()
            if collection is not None:
                share = sharing.getShare(collection)
                if sharing.isSharedByMe(share):
                    dialog = wx.MessageDialog(None,
                                              _(u"Are you sure you want to remove this collection from the server?"),
                                              _(u"Unpublish Confirmation"),
                                              wx.YES_NO | wx.ICON_INFORMATION)
                    response = dialog.ShowModal()
                    dialog.Destroy()
                    if response == wx.ID_YES:
                        msg = _(u"Unpublishing...")
                        self.setStatusMessage(msg)
                        sharing.unpublish(collection)
                        msg = _(u"Collection unpublished.")
                        self.setStatusMessage(msg)

        except (sharing.CouldNotConnect, twisted.internet.error.TimeoutError):
            msg = _(u"Unpublish failed, could not connect to server.")
            self.setStatusMessage(msg)
        except:
            msg = _(u"Unpublish failed, unknown error.")
            self.setStatusMessage(msg)
            raise # figure out what the exception is

    def onUnpublishCollectionEventUpdateUI(self, event):
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            share = sharing.getShare(collection)
            sharedByMe = sharing.isSharedByMe(share)
            event.arguments['Enable'] = (
                schema.ns('osaf.app', self.itsView).prefs.isOnline and
                sharing.isOnline(self.itsView) and
                sharing.isShared(collection) and sharedByMe)

    def _freeBusyShared(self):
        allCollection = schema.ns('osaf.pim', self).allCollection
        return (sharing.getFreeBusyShare(allCollection) is not None)

    def onSharingPublishFreeBusyEvent(self, event):
        if not sharing.ensureAccountSetUp(self.itsView, sharing=True):
            return
        allCollection = schema.ns('osaf.pim', self).allCollection
        PublishCollection.ShowPublishDialog(view=self.itsView,
                                            publishType = 'freebusy',
                                            collection=allCollection)

    def onSharingPublishFreeBusyEventUpdateUI(self, event):
        # Freebusy Disabled
        event.arguments['Enable'] = False
        # event.arguments['Enable'] = not self._freeBusyShared()


    def onSharingUnpublishFreeBusyEventUpdateUI(self, event):
        # Freebusy Disabled
        event.arguments['Enable'] = False
        # event.arguments['Enable'] = self._freeBusyShared()

    onCopyFreeBusyURLEventUpdateUI = onSharingUnpublishFreeBusyEventUpdateUI

    def onCopyFreeBusyURLEvent(self, event):
        allCollection = schema.ns('osaf.pim', self).allCollection
        share = sharing.getFreeBusyShare(allCollection)
        if share is not None:
            urlString = sharing.getUrls(share)[-1]
            gotClipboard = wx.TheClipboard.Open()
            if gotClipboard:
                wx.TheClipboard.SetData(wx.TextDataObject(unicode(urlString)))
                wx.TheClipboard.Close()

    def onSharingUnpublishFreeBusyEvent(self, event):
        try:
            sharing.unpublishFreeBusy(schema.ns('osaf.pim', self).allCollection)
        except sharing.NotFound:
            msg = _(u"Free/Busy URL not found, could not revoke Free/Busy access.")
            self.setStatusMessage(msg)
        except (sharing.CouldNotConnect, twisted.internet.error.TimeoutError):
            msg = _(u"Unpublish failed, could not connect to server.")
            self.setStatusMessage(msg)
        except:
            msg = _(u"Unpublish failed, unknown error.")
            self.setStatusMessage(msg)
            raise # figure out what the exception is
        else:
            msg = _(u"Collection unpublished.")
            self.setStatusMessage(msg)

    def onSyncCollectionEvent (self, event):
        rv = self.itsView
        collection = self.getSidebarSelectedCollection()
        if (collection is not None and
            schema.ns('osaf.app', self.itsView).prefs.isOnline
            and sharing.isOnline(self.itsView)):

            # Ensure changes in attribute editors are saved
            wx.GetApp().mainFrame.SetFocus()

            rv.commit()
            sharing.scheduleNow(rv, collection=collection)

    def onSyncCollectionEventUpdateUI (self, event):
        """
        Update the menu to reflect the selected collection name.
        """
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            collName = collection.displayName
            sender = event.arguments['sender']
            if UserCollection(collection).outOfTheBoxCollection:
                event.arguments['Text'] = sender.title
            elif sender.blockName == 'SidebarSyncCollectionItem':
                event.arguments['Text'] = _(u'%(menuTitle)s %(collectionName)s') % \
                     {'menuTitle' : sender.title,
                      'collectionName': collName}
            else:
                event.arguments ['Text'] = _(u'%(collectionName)s') % \
                     {'collectionName': collName}
        event.arguments['Enable'] = (collection is not None and
             schema.ns('osaf.app', self.itsView).prefs.isOnline and
             sharing.isOnline(self.itsView) and
             sharing.isShared(collection))

    def onCollectionInviteEvent(self, event):
        collection = self.getSidebarSelectedCollection()
        if collection is not None:
            share = sharing.getShare(collection)
            if share is not None:
                Invite.Show(collection=collection)

    def onCollectionInviteEventUpdateUI(self, event):
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
            if sharing.isCollectionOnline(collection):
                sharing.takeCollectionOffline(collection)
            else:
                sharing.takeCollectionOnline(collection)

            # To make changes available to sharing thread
            self.RepositoryCommitWithStatus ()

    def onTakeOnlineOfflineEventUpdateUI(self, event):
        event.arguments['Enable'] = False

        collection = self.getSidebarSelectedCollection()
        if collection is not None:

            collName = collection.displayName
            sender = event.arguments['sender']
            if UserCollection(collection).outOfTheBoxCollection:
                event.arguments['Text'] = sender.title
            elif sender.blockName == 'SidebarTakeOnlineOfflineItem':
                event.arguments['Text'] = u'%(menuTitle)s %(collectionName)s' % \
                     {'menuTitle' : sender.title,
                      'collectionName': collName}
            else:
                event.arguments ['Text'] = u'%(collectionName)s' % \
                     {'collectionName': collName}

            if sharing.isShared(collection):
                event.arguments['Enable'] = True
                event.arguments['Check'] = \
                    not sharing.isCollectionOnline(collection)

    def onTakeAllOnlineOfflineEventUpdateUI(self, event):
        event.arguments['Check'] = \
            not schema.ns('osaf.app', self.itsView).prefs.isOnline

    def onTakeAllOnlineOfflineEvent(self, event):
        prefs = schema.ns('osaf.app', self.itsView).prefs

        if not prefs.isOnline:
            prefs.isOnline = True
            Globals.mailService.takeOnline()
        else:
            prefs.isOnline = False
            Globals.mailService.takeOffline()

        self.RepositoryCommitWithStatus()

    def onTakeMailOnlineOfflineEvent(self, event):
        if Globals.mailService.isOnline():
            Globals.mailService.takeOffline()
        else:
            Globals.mailService.takeOnline()

    def onTakeMailOnlineOfflineEventUpdateUI(self, event):
        prefs = schema.ns('osaf.app', self.itsView).prefs

        if prefs.isOnline:
            event.arguments['Enable'] = True
            event.arguments['Check'] = not Globals.mailService.isOnline()
        else:
            event.arguments['Enable'] = False
            event.arguments['Check'] = True

    def onTakeSharesOnlineOfflineEvent(self, event):
        if sharing.isOnline(self.itsView):
            sharing.takeOffline(self.itsView)
        else:
            sharing.takeOnline(self.itsView)


    def onTakeSharesOnlineOfflineEventUpdateUI(self, event):
        prefs = schema.ns('osaf.app', self.itsView).prefs

        if prefs.isOnline:
            event.arguments['Enable'] = True
            event.arguments['Check'] = not sharing.isOnline(self.itsView)
        else:
            event.arguments['Enable'] = False
            event.arguments['Check'] = True


    def onSyncAllEventUpdateUI(self, event):
        event.arguments['Enable'] = \
            schema.ns('osaf.app', self.itsView).prefs.isOnline

    def onSyncAllEvent (self, event):
        """
        Synchronize Mail and all sharing.
        The "File | Sync | All" menu item, and the Sync All ToolBar button.
        """

        # Commit changes, making them available to other views like mail
        # and sharing
        self.RepositoryCommitWithStatus ()

        if not schema.ns('osaf.app', self.itsView).prefs.isOnline:
            return

        view = self.itsView

        masterPassword = True
        from osaf.framework import password
        # Check account status:
        try:
            sharingReady = sharing.isSharingSetUp(view)
            incomingMailReady = sharing.isIncomingMailSetUp(view)
        except password.NoMasterPassword:
            masterPassword = False
            sharingReady = False
            incomingMailReady = False

        # Any active shares?  (Even if default sharing account not set up,
        # the user could have subscribed with tickets)
        activeShares = sharing.checkForActiveShares(view)

        if not masterPassword:
            if not activeShares:
                # Since the user did not give the master password and there are
                # no ticket subscriptions, we can't sync.
                return
        else:
            if not (sharingReady or activeShares or incomingMailReady):
                # Nothing is set up -- nudge the user to set up a sharing account
                sharing.ensureAccountSetUp(view, inboundMail=True, sharing=True)
                # Either the user has created a sharing account, or they haven't,
                # but it doesn't matter since there's no shares to sync
                return

        # At least one account is setup, or there are active shares

        # find all the shared collections and sync them.
        # Fire off a background syncAll:

        # Ensure changes in attribute editors are saved
        wx.GetApp().mainFrame.SetFocus()
        sharing.scheduleNow(view)

        if incomingMailReady:
            self.onGetNewMailEvent (event)

    def onSyncWebDAVEventUpdateUI (self, event):
        event.arguments['Enable'] = schema.ns('osaf.app',
            self.itsView).prefs.isOnline and sharing.isOnline(self.itsView)

    def onSyncWebDAVEvent (self, event):
        """
        Synchronize WebDAV sharing.

        The "File | Sync | Shares" menu item.
        """

        if not schema.ns('osaf.app', self.itsView).prefs.isOnline:
            return

        view = self.itsView

        activeShares = sharing.checkForActiveShares(view)
        if activeShares:
            # find all the shared collections and sync them.

            # Ensure changes in attribute editors are saved
            wx.GetApp().mainFrame.SetFocus()

            # To make changes available to sharing thread
            self.RepositoryCommitWithStatus ()

            sharing.scheduleNow(view)

        else:
            if not sharing.isSharingSetUp(view):
                # DAV is not set up -- nudge the user to set up sharing account
                sharing.ensureAccountSetUp(view, sharing=True)
                # Either way, we don't care if the user actually created an
                # account or not, we know there's nothing to sync
                return
            self.setStatusMessage (_(u"No shared collections found."))

    def onGetNewMailEventUpdateUI (self, event):
        event.arguments['Enable'] = Globals.mailService.isOnline()

    def onGetNewMailEvent (self, event):
        """
        Fetch Mail.

        The "File | Sync | Mail" menu item.
        """

        if not schema.ns('osaf.app', self.itsView).prefs.isOnline:
            return

        view = self.itsView

        # Make sure we have all the accounts; returns False if the user cancels
        # out and we don't.
        if not sharing.ensureAccountSetUp(view, inboundMail=True):
            return

        for account in mail.IMAPAccount.getActiveAccounts(view):
            Globals.mailService.getIMAPInstance(account).getMail()

        for account in mail.POPAccount.getActiveAccounts(view):
            Globals.mailService.getPOPInstance(account).getMail()

    def onEnableTimezonesEventUpdateUI(self, event):
        tzPrefs = schema.ns('osaf.pim', self.itsView).TimezonePrefs
        event.arguments['Check'] = tzPrefs.showUI

    def onEnableTimezonesEvent(self, event):
        tzPrefs = schema.ns('osaf.pim', self.itsView).TimezonePrefs
        tzPrefs.showUI = not tzPrefs.showUI

    def onVisibleHoursEvent(self, event):
        calendarPrefs = schema.ns('osaf.framework.blocks.calendar',
                                  self.itsView).calendarPrefs
        if event.visibleHours == -1:
            calendarPrefs.hourHeightMode = "auto"
        else:
            calendarPrefs.hourHeightMode = "visibleHours"
            calendarPrefs.visibleHours = event.visibleHours

    def onVisibleHoursEventUpdateUI(self, event):
        calendarPrefs = schema.ns('osaf.framework.blocks.calendar',
                                  self.itsView).calendarPrefs

        if event.visibleHours == -1:
            event.arguments['Check'] = (calendarPrefs.hourHeightMode == "auto")
        else:
            event.arguments['Check'] = \
                 (calendarPrefs.hourHeightMode == "visibleHours" and
                  calendarPrefs.visibleHours == event.visibleHours)

    def onNewBlockWindowEvent(self, event):
        rootBlock = event.treeOfBlocks
        for window in wx.GetTopLevelWindows():
            if (isinstance (window, wxBlockFrameWindow) and
                window.GetChildren()[0].blockItem is rootBlock):
                window.Raise()
                break
        else:
            window = wxBlockFrameWindow (None,
                                         -1, 
                                         rootBlock.windowTitle,
                                         pos=(rootBlock.position.x, rootBlock.position.y),
                                         size=(rootBlock.size.width, rootBlock.size.height),
                                         style = wx.DEFAULT_FRAME_STYLE)
            window.ShowTreeOfBlocks (rootBlock)
            window.Show (True)

    def onNeedsUpdateEvent(self, event):
        pass

    def onNeedsUpdateUpdateUI(self, event):
        pass

# these quickentry commands probably shouldn't live in Main, but I don't know
# what a better place would be...

class SearchCommand(quickentry.QuickEntryCommand):
    # L10N: A comma separated list of names for commands to search
    command_names = _(u"find,search").split(',')

    @classmethod
    def process(cls, state):
        """Configure the UI to display a search."""
        quickEntryBlock = Block.findBlockByName("ApplicationBarQuickEntry")
        sidebar = Block.findBlockByName("Sidebar")

        command = cls.backslash_escape(state.text, '+-&|!(){}[]^~*?:\\')
        quickEntryBlock.lastSearch = command
        sidebar.setShowSearch(True)
        state.search = True

    @classmethod
    def backslash_escape(cls, string, escape_chars):
        return ''.join((r'\\'+c if c in escape_chars else c) for c in string)


class LuceneCommand(SearchCommand):
    # L10N: A comma separated list of names for commands to do a full text
    # search using lucene syntax
    command_names = _(u"lucene").split(',')
    @classmethod
    def backslash_escape(cls, string, escape_chars):
        """Don't escape special lucene characters when searching."""
        return string

# Regular expression for finding quick entry commands 
quick_entry_commands_re = re.compile(r'/(?P<cmd>([A-z]+))')

# create a mapping from command names to QuickEntryCommand objects
quick_entry_objects = {}
for ep in pkg_resources.iter_entry_points('chandler.quick_entry'):
    cls = ep.load()
    for name in cls.command_names:
        quick_entry_objects[name.lower()] = cls

def get_quick_entry(partial_name):
    for name, cls in quick_entry_objects.iteritems():
        if name.startswith(partial_name):
            return cls
