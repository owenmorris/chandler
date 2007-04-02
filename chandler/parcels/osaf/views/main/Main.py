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
from time import time
import wx, os, sys, traceback, logging, re, webbrowser
import PyLucene

from application import Globals, Printing, schema, Utility

from application.AboutBox import AboutBox
from application.Application import wxBlockFrameWindow
import application.Parcel

import application.dialogs.Util
import application.dialogs.FileTail
from application.dialogs import ( AccountPreferences, PublishCollection,
    SubscribeCollection, RestoreShares, autosyncprefs, TurnOnTimezones,
    ActivityViewer
)

from repository.item.Item import MissingClass
from osaf import (
    pim, sharing, messages, webserver, settings, search, dumpreload
)
from osaf.activity import *

from osaf.pim import Contact, ContentCollection, mail, Modification
from osaf.usercollections import UserCollection
import osaf.pim.generate as generate

from osaf.mail import constants
import twisted.internet.error

from util import GenerateItemsFromFile

from osaf.framework.blocks.Views import View
from osaf.framework.blocks.calendar import CalendarCanvas
from osaf.framework.blocks.Block import Block

from osaf.preferences import Preferences

from osaf.framework.prompts import promptOk

import i18n
from i18n import ChandlerMessageFactory as _

from application.Utility import getDesktopDir
from application.dialogs import ImportExport

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

    def displayMailError (self, message, account):
        application.dialogs.Util.mailAccountError(wx.GetApp().mainFrame,
                                                  self.itsView, message, account)

    def displaySMTPSendError(self, mailMessage, account):
        """
        Called when the SMTP Send generated an error.
        """
        if mailMessage is not None:
            if getattr(mailMessage.itsItem, "error", None) is None:
                errorMessage = _(u"An unknown error has occurred")
            else:
                errorMessage = _(u"An error occurred while sending:\n%(translatedErrorStrings)s") % {
                                  'translatedErrorStrings': mailMessage.itsItem.error}

            """
            Clear the status message.
            """
            self.setStatusMessage(u'')
            self.displayMailError (errorMessage, account)

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

        AccountPreferences.ShowAccountPreferencesDialog(wx.GetApp().mainFrame,
                                                        rv=self.itsView)

    def onProtectPasswordsEvent (self, event):
        # Triggered from "File | Prefs | Protect Passwords..."
        from osaf.framework import MasterPassword
        from osaf.framework.twisted import waitForDeferred
        waitForDeferred(MasterPassword.change(self.itsView))

    def trashCollectionSelected(self):
        trashCollection = schema.ns("osaf.pim", self).trashCollection

        if self.getSidebarSelectedCollection() is trashCollection:
            msg = _(u"New items cannot be created in the Trash collection.")

            promptOk(msg)
            return True

        return False

    def onNewItemEvent(self, event):
        # Create a new Content Item

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
        sidebar.setPreferredClass(stampClass)

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
        quickEntryWidget = Block.findBlockByName("ApplicationBarQuickEntry").widget
        quickEntryWidget.SetValue (_(u"/find "))
        quickEntryWidget.SetInsertionPointEnd()
        quickEntryWidget.SetFocus()

    def onQuickEntryEvent (self, event):
        # XXX This needs some refactoring love
        searchKinds = (_(u'search'), _(u's'),
                       _(u'find'), _(u'f'),
                       _(u'lucene'), _(u'l'))

        def processQuickEntry(self, command):
            """
            Parses the text in the quick item entry widget in the
            toolbar. Creates the items depending on the command and adds it
            to the appropriate collection. Also parses the date/time info
            and sets the start/end time or the reminder time.
            """
            if self.trashCollectionSelected():
                # Items can not be created in the
                # trash collectioon
                return
            
            msgFlag = False
            eventFlag = False
            taskFlag = False
            
            # Default kind
            defaultKind = sidebar.filterClass
            
            # Search the text for "/" which indicates it is a quick item entry
            cmd_re = re.compile(r'/(?P<kind>([A-z]+))')
            
            cmd = cmd_re.match(command)
            if cmd is None:
                if defaultKind is not None:
                    if defaultKind == pim.tasks.TaskStamp:
                        taskFlag = True
                    elif defaultKind == pim.mail.MailStamp:
                        msgFlag = True
                    elif defaultKind == pim.calendar.Calendar.EventStamp:
                        eventFlag = True
                    displayName = command
                        
            while cmd is not None:
                kind = (cmd.group('kind')).lower()
                displayName = command[(cmd.end()):].strip()
                command = displayName
                
                # Set flags depending on its kind
                if kind in searchKinds:
                    return False
                
                elif kind in (_(u'task'), _(u't')):
                    taskFlag = True
                    
                elif kind in (_(u'msg'), _(u'message'), _(u'm')):
                     msgFlag = True
                    
                elif kind in (_(u'event'), _(u'e')):
                    eventFlag = True
                    
                elif kind in (_(u'invite'), _(u'i')):
                    eventFlag = True
                    msgFlag = True
                    
                elif kind in (_(u'request'), _(u'r')):
                    taskFlag = True
                    msgFlag = True
                    
                elif kind not in (_(u'note'), _(u'n')):
                    # if command is not 'note' then it is not a valid  command. for eg: '/foo'
                    return False
                    
                cmd = cmd_re.match(displayName)
    
            #Create a Note 
            item = pim.Note(itsView = self.itsView)
            
            # Parse the text for date/time information
            startTime, endTime, countFlag, typeFlag = \
                             pim.calendar.Calendar.parseText(displayName)
             
            # Check whether there is a date/time range
            if startTime != endTime:
                eventFlag = True
            
            #Stamp the note appropriately depending on flags
            if taskFlag:
                pim.tasks.TaskStamp(item).add()
            if eventFlag:
                pim.calendar.Calendar.EventStamp(item).add()
            if msgFlag:
                pim.mail.MailStamp(item).add()
                pim.mail.MailStamp(item).InitOutgoingAttributes()
            else:
                item.InitOutgoingAttributes()
       
            # Set a reminder if the item is not an event but it has time
            if (not eventFlag) and (typeFlag != 0) :
                item.userReminderTime = startTime
     
            if eventFlag:
                # If the item is an event, set the event's start and end date/time
                pim.calendar.Calendar.setEventDateTime(item, startTime, endTime, typeFlag)
            
           # If item is a message, search for contacts and seperate them        
            if msgFlag:
                pattern = {}
                pattern['email'] = r'[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}'
                
                checkContact = re.match(r'\s?((%(email)s)\s?(,|;)?\s?)+\s?:'%pattern,displayName)
                sep = re.search(r':',displayName)
                                       
                if checkContact and sep:
                    contacts = (displayName[:sep.start()]).strip()
                    displayName = (displayName[sep.end():]).strip()
                    
                    contacts_pattern = r"""
                        \s*                      # ignore whitespace
                        (?P<contact> ([^,;\s]*)) # any intervening non-whitespace is the contact
                        \s*                      # ignore whitespace
                        (,|;)?                   # gobble contact separators
                        \s*                      # ignore whitespace
                        """
                    
                    contacts_re = re.compile(contacts_pattern, re.VERBOSE)
                    
                    for match in contacts_re.finditer(contacts):
                        toOne = pim.mail.EmailAddress(itsView=self.itsView)
                        toOne.emailAddress = match.group('contact')
                        pim.mail.MailStamp(item).toAddress.append(toOne)                        
    
                else:
                    pim.mail.MailStamp(item).subject = displayName
        
        
            if item is not None:
                item.displayName = displayName
                
                # Add the item to the appropriate collection
                if defaultKind is not MissingClass:
                    if (defaultKind == pim.tasks.TaskStamp and taskFlag == True) or \
                    (defaultKind == pim.calendar.Calendar.EventStamp and eventFlag == True) or \
                    (defaultKind == pim.mail.MailStamp and msgFlag == True):
                        collection = Block.findBlockByName("MainView").getSidebarSelectedCollection()
                        statusMsg =  _(u"New item created in the selected collection")
                    
                    else:
                        # if item is of a different kind than the default item of current view,
                        # put it in Dashboard 'All' collection
                        collection = schema.ns('osaf.pim',self).allCollection
                        statusMsg =  _(u"New item created in the Dashboard All Collection")
                
                else:
                    # if kind is None, it is 'All' app, so add item to selected collection
                    collection = Block.findBlockByName("MainView").getSidebarSelectedCollection()
                    statusMsg =  _(u"New item created in the selected collection")
                
                if collection is not None:
                    collection.add(item)
                    #Put the status message in the Status bar
                    wx.GetApp().CallItemMethodAsync("MainView", 'setStatusMessage', statusMsg)
            
            # Clear out the command when it finishes without errors
            quickEntryWidget.SetValue("")
            return True
        
        
        sidebar = Block.findBlockByName ("Sidebar")
        quickEntryWidget = event.arguments['sender'].widget
        block = quickEntryWidget.blockItem
        command = quickEntryWidget.GetValue().strip()
        showSearchResults = False
        
        cancelClicked = event.arguments.get ("cancelClicked", False)
        if cancelClicked:
            
            # When cancel is clicked we toggle between search and non search views
            if len (command) == 0:
                lastText = getattr (block, "lastText", None)
                if lastText is not None:
                    quickEntryWidget.SetValue (lastText)
                    showSearchResults = True
            else:
                quickEntryWidget.SetValue ("")
                block.lastText = command
        else:
            # Try to process as a quick entry command
            if len (command) != 0 and not processQuickEntry (self, command):
                
                c = command.lower()[:command.find(' ')]
                
                if c not in [u'/' + k for k in searchKinds]:
                    # command is not valid
                    quickEntryWidget.SetValue (command + ' ?')
                    wx.GetApp().CallItemMethodAsync("MainView", 'setStatusMessage', _(u"Command entered is not valid"))
                else:
                    command = command[len(c) + 1:] # remove '/find '

                    # if /search or /find but not /lucene
                    # quote special lucene query syntax chars except "
                    # http://lucene.apache.org/java/docs/queryparsersyntax.html
                    if not c.startswith('/l'):
                        command = ''.join(('\\'+char if char in '+-&|!(){}[]^~*?:\\' else char)
                                          for char in command)
                                    
                    try:
                        sidebar.setShowSearch (True)
                        showSearchResults = True
        
                        view = self.itsView
            
                        # make sure all changes are searchable
                        view.commit()
                        view.repository.notifyIndexer(True)
                        
                        results = view.searchItems (command)
            
                        searchResults = schema.ns('osaf.pim', view).searchResults
                        searchResults.inclusions.clear()
                        
                        sidebarCollection = schema.ns("osaf.app", self).sidebarCollection
                        for collection in sidebarCollection:
                            UserCollection (collection).searchMatches = 0

                        app = wx.GetApp()
                        for item in search.processResults(results):
                            if item not in searchResults:
                                for collection in sidebarCollection:
                                    if item in collection:
                                        UserCollection (collection).searchMatches += 1
                                        searchResults.add(item)
                                        # Update the display every so often 
                                        if len (searchResults) % 50 == 0:
                                            app.propagateAsynchronousNotifications()
                                            app.Yield()

                        if len(searchResults) == 0:
                            # For now we'll write a message to the status bar because it's easy
                            # When we get more time to work on search, we should write the message
                            # just below the search box in the toolbar.
                            app.CallItemMethodAsync("MainView", 'setStatusMessage', _(u"Search found nothing"))
                    except PyLucene.JavaError, error:
                        message = unicode (error)
                        prefix = u"org.apache.lucene.queryParser.ParseException: "
                        if message.startswith (prefix):
                            message = message [len(prefix):]
                        
                        message = _(u"An error occured during search.\n\nThe search engine reported the following error:\n\n" ) + message
                        
                        application.dialogs.Util.ok (None, _(u"Search Error"), message)
                        showSearchResults = False

        block.text = command
        sidebar.setShowSearch (showSearchResults)
                

    def printEvent(self, isPreview):
        block = self.findBlockByName ("TimedEvents")
        if block is None:
            message = _(u"Chandler")
            title = _(u"Printing is currently only supported when viewing in calendar view.")
            application.dialogs.Util.ok(None, message, title)
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
            title = _(u"Browser not found")
            message = _(u"Chandler couldn't access a browser to open %(url)s.") 
            application.dialogs.Util.ok(None, title, message % {'url' : url})
            
    def onHelpEvent(self, event):
        # For now, open the Chandler FAQ page:
        #
        # <http://lists.osafoundation.org/pipermail/design/2006-August/005311.html>
        self.openURLOrDialog(
           'http://wiki.osafoundation.org/bin/view/Projects/ChandlerProductFAQ'
        )

    def onFileBugEvent(self, event):
        self.openURLOrDialog(
           'http://wiki.osafoundation.org/Projects/ReportingBugs'
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

        dlg = wx.DirDialog(wx.GetApp().mainFrame, _(u'Backup Repository'),
                           unicode(Utility.getDesktopDir()),
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
            successMessage = _(u'Repository was backed up into %(directory)s') % {'directory': (dbHome)}
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
                           unicode(path),
                           wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        else:
            path = None
        dlg.Destroy()

        if path is not None:
            dlg = wx.MessageDialog(app.mainFrame,
                                   _(u"Your current repository will be destructively replaced by the repository backup you're about to restart Chandler with: %s") %(path),
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
                           unicode(Utility.getDesktopDir()),
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
                    successMessage = _(u'Repository is ready')
                    repository.logger.info('Repository is ready')
                    self.setStatusMessage(successMessage)
                    message = _(u"Your current repository was copied to %s and Chandler is setup to use it after restarting. Your current repository will not be affected.\n\nRestart now ?")
                    restore = dbHome
                else:
                    message = _(u"A new repository will be created in %s and Chandler is setup to use it after restart. Your current repository will not be affected.\n\nRestart now ?")
                    restore = None
            else:
                restore = None
                message = _(u"Chandler is setup to use the repository at %s after restarting. Your current repository will not be affected.\n\nRestart now ?")

            dlg = wx.MessageDialog(app.mainFrame, message %(repodir),
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
        self.setStatusMessage(_(u"committing changes to the repository..."))

        Block.finishEdits()
        activity = Activity("Saving...")
        activity.started()

        try:
            self.itsView.commit()
            activity.completed()
        except Exception, e:
            logger.exception("Commit failed")
            self.setStatusMessage(_(u"Commit failed, see log for details"))
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

        app = wx.GetApp()
        Block.findBlockByName('StatusBar').setStatusMessage (statusMessage, progressPercentage)

    def alertUser(self, message):
        promptOk(message)

    def callAnyCallable(self, callable, withView, *args, **kw):
        """
        Call any callable. The idea with this method is that any object
        in any view and any thread can put in a request in the application
        async method list with::

            wxApplication.CallItemMethodAsync("MainView", 
                                              'callAnyCallable',
                                              withView, myMethod, myArg1, ...)

        and get a method of their choice be called back on the main thread with
        the main repository view (if they so like).

        @param withView: Should be true if the first argument for the callable
                         should be the main view, before *args and **kw.
        @param callable: A Python callable
        @param args:     Arguments for callable
        @param kw:       Keyword arguments for callable
        """
        if withView:
            return callable(self.itsView, *args, **kw)
        return callable(*args, **kw)

    def onSendShareItemEventUpdateUI(self, event):
        # If we get asked about this, and it hasn't already been set, there's no selected 
        # item anywhere - disallow sending. Also, make sure the label's set back to "Send"
        event.arguments ['Enable'] = False
        event.arguments ['Text'] = messages.SEND

    def onSendMailEvent(self, event):
        # commit changes, since we'll be switching to Twisted thread
        self.RepositoryCommitWithStatus()

        if not sharing.ensureAccountSetUp(self.itsView, outboundMail=True):
            return

        # get default SMTP account
        item = event.arguments['item']
        if pim.has_stamp(item, pim.EventStamp):
            # for preview, always send the full recurrence set
            item = pim.EventStamp(item).getMaster().itsItem

        mailToSend = mail.MailStamp(item)

        code, valid, invalid = mailToSend.getSendableState()

        if code == 0:
            # 0 = no valid addresses
            err = _(u"Message can not be sent. You have not entered any valid email addresses.")
            application.dialogs.Util.ok(wx.GetApp().mainFrame, _(u"Mail Error"), err)
            return

        elif code == 1:
            # 1 = some valid addresses
            if application.dialogs.Util.mailAddressError(wx.GetApp().mainFrame):
                # Method returns True when the user selects to fix the bad
                # addresses
                return

        elif code == 2:
            # 2 = No to addresses
            err = _(u"Message can not be sent. A to address is required.")
            application.dialogs.Util.ok(wx.GetApp().mainFrame, _(u"Mail Error"), err)
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

    def onShareItemEvent (self, event):
        """
        Share a Collection.
        """
        itemCollection = event.arguments ['item']

        # Make sure we have all the accounts; returns False if the user cancels
        # out and we don't.
        if not sharing.ensureAccountSetUp(self.itsView, sharing=True):
            return
        sharingAccount = schema.ns('osaf.sharing',
                                   self.itsView).currentSharingAccount.item

        # commit changes, since we'll be switching to Twisted thread
        self.RepositoryCommitWithStatus()

        # show status
        self.setStatusMessage (_(u"Sharing collection %(collectionName)s") % {'collectionName': itemCollection.displayName})

        # Get or make a share for this item collection
        share = sharing.getShare(itemCollection)
        isNewShare = share is None

        # When this code is revived, it should use sharing.publish( ) rather
        # than newOutboundShare:
        ## if isNewShare:
        ##     share = sharing.newOutboundShare(self.itsView,
        ##                                      itemCollection,
        ##                                      account=sharingAccount)

        # Copy the invitee list into the share's list. As we go, collect the 
        # addresses we'll notify.
        invitees = mail.CollectionInvitation(itemCollection).invitees
        if len (invitees) == 0:
            self.setStatusMessage (_(u"No invitees!"))
            return
        inviteeList = []
        inviteeStringsList = []

        for invitee in invitees:
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
        sidebar = Block.findBlockByName ("Sidebar")
        item = sidebar.contents.getFirstSelectedItem()
        if getattr(item, 'private', None) is not None and private == False and item.private:
            return None

        return item

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
            successMessage = _(u'Check completed successfully in %(numSeconds)s') % {'numSeconds': timedelta(seconds=after-before)}
            repository.logger.info('Check completed successfully in %s' % (timedelta(seconds=after-before)))
            self.setStatusMessage(successMessage)
        else:
            errorMessage = _(u'Check completed with errors')
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
            successMessage = _(u'Check completed successfully in %(numSeconds)s') % {'numSeconds': timedelta(seconds=after-before)}
            repository.logger.info('Check completed successfully in %s' % (timedelta(seconds=after-before)))
            self.setStatusMessage(successMessage)
        else:
            errorMessage = _(u'Check completed with errors')
            repository.logger.info('Check completed with errors')
            self.setStatusMessage(errorMessage)

    def onCompactRepositoryEvent(self, event):
        # triggered from "Test | Compact Repository" Menu
        self.RepositoryCommitWithStatus()
        repository = self.itsView.repository
        progressMessage = _(u'Compacting repository...')
        repository.logger.info('Compacting repository...')
        self.setStatusMessage(progressMessage)
        counts = repository.compact()

        successMessage = _(u'Reclaimed %(counts)s (items, values, refs, lobs, blocks, names, index entries, lucene documents)') %{ 'counts': counts }
        repository.logger.info(successMessage)
        self.setStatusMessage(successMessage)

    def onIndexRepositoryEvent(self, event):
        # triggered from "Test | Index Repository" Menu
        self.RepositoryCommitWithStatus()
        repository = self.itsView.repository
        repository.notifyIndexer()

    def onImportIcalendarEvent(self, event):
        # triggered from "File | Import/Export" menu
        prefs = schema.ns("osaf.sharing", self.itsView).prefs

        dialog = ImportExport.ImportDialog(wx.GetApp().mainFrame,
                                           _(u"Choose a file to import"),
                                           self.itsView)
        
        ret = dialog.ShowModal()
        if ret == wx.ID_OK:
            self.setStatusMessage(_(u"Import completed"))
        dialog.Destroy()

    def onExportIcalendarEventUpdateUI(self, event):
        collection = self.getSidebarSelectedCollection()
        if collection is None:
            event.arguments['Enable'] = False

    def onExportIcalendarEvent(self, event):
        # triggered from "File | Import/Export" Menu
        collection = self.getSidebarSelectedCollection()
        if collection is None:
            return

        for item in collection:
            if (pim.has_stamp(item, pim.EventStamp) or 
                pim.has_stamp(item, pim.TaskStamp)):
                break
        else:
            message = _(u"This collection contains no events")
            title = _(u"Export cancelled")
            application.dialogs.Util.ok(None, message, title)
            return

        if not TurnOnTimezones.ShowTurnOnTimezonesDialog(
            wx.GetApp().mainFrame,
            self.itsView,
            state=TurnOnTimezones.EXPORT,
            modal=True):
            # cancelled in turn on timezone dialog
            return
            

        name = collection.displayName
        try:
            name.encode('ascii')
            pattern = re.compile('[^A-Za-z0-9]')
            name = re.sub(pattern, "_", name)
        except UnicodeEncodeError:
            name = str(collection.itsUUID)

        options = [dict(name=pim.Remindable.reminders.name, checked = True,
                        label = _(u"Export reminders")),
                   dict(name=pim.EventStamp.transparency.name, checked = True,
                        label = _(u"Export event status"))]
        res = ImportExport.showFileChooserWithOptions(wx.GetApp().mainFrame,
                                       _(u"Choose a filename to export to"),
                                            os.path.join(getDesktopDir(),
                                      u"%s.ics" % (name)),
                            _(u"iCalendar files|*.ics|All files (*.*)|*.*"),
                                              wx.SAVE | wx.OVERWRITE_PROMPT, 
                                                                    options)

        (ok, fullpath, optionResults) = res

        if not ok:
            self.setStatusMessage(_(u"Export aborted"))
        else:
            try:
                (dir, filename) = os.path.split(fullpath)
                self.setStatusMessage (_(u"Exporting to %(filename)s") % {'filename': filename})
                try:
                    os.remove(fullpath)
                except OSError:
                    pass
                
                if sharing.caldav_atop_eim:
                    share = sharing.OneTimeFileSystemShare(
                        itsView=self.itsView,
                        filePath=dir, fileName=filename,
                        translatorClass=sharing.SharingTranslator,
                        serializerClass=sharing.ICSSerializer,
                        contents=collection
                    )
                    # TODO: filters
                else:
                    share = sharing.OneTimeFileSystemShare(
                        itsView=self.itsView,
                        filePath=dir, fileName=filename,
                        formatClass=sharing.ICalendarFormat,
                        contents=collection)
                    if not optionResults[pim.Remindable.reminders.name]:
                        share.filterAttributes.append(
                            pim.Remindable.reminders.name)
                    if not optionResults[pim.EventStamp.transparency.name]:
                        share.filterAttributes.append(
                            pim.EventStamp.transparency.name)


                share.put()
                self.setStatusMessage(_(u"Export completed"))
            except:
                trace = "".join(traceback.format_exception (*sys.exc_info()))
                logger.info("Failed exportFile:\n%s" % trace)
                self.setStatusMessage(_(u"Export failed"))


    def onWxTestHarnessEvent(self, event):
        """
         This method is for testing and does not require translation strings.
        """
        # Test menu item
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
        sidebarCollection = schema.ns("osaf.app", self.itsView).sidebarCollection
        return generate.GenerateAllItems(self.itsView, count, sidebarCollection)

    def onGenerateContentItemsFromFileEvent(self, event):
        # triggered from "File | Import/Export" menu
        res = application.dialogs.Util.showFileDialog(
            wx.GetApp().mainFrame, _(u"Choose a file to import"), "",
            _(u"import.csv"), _(u"CSV files|*.csv"),
            wx.OPEN)

        (cmd, dir, filename) = res

        if cmd != wx.ID_OK:
            self.setStatusMessage(_(u"Import aborted"))
            return

        self.setStatusMessage (_(u"Importing from %(filename)s")  % {'filename': filename})
        return GenerateItemsFromFile.GenerateItems(self.itsView, os.path.join(dir, filename))

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

        mainViewRoot = theApp.LoadMainViewRoot (delete=True)

        # mainViewRoot needs to refer to its frame and the mainFrame needs to
        # refert to the mainViewRoot
        mainViewRoot.frame = theApp.mainFrame
        theApp.mainFrame.mainViewRoot = mainViewRoot

        theApp.RenderMainView ()

    def onReloadStylesEvent(self, event):
        """
        Reloads styles that should be read from a text file.
        """
        import application.styles
        application.styles.loadConfig()

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

        SubscribeCollection.Show(wx.GetApp().mainFrame, self.itsView)

    def onDumpToFileEvent(self, event):
        wildcard = "%s|*.dump|%s (*.*)|*.*" % (_(u"Dump files"),
            _(u"All files"))

        dlg = wx.FileDialog(wx.GetApp().mainFrame,
                            _(u"Dump Items"), "", "chandler.dump", wildcard,
                            wx.SAVE|wx.OVERWRITE_PROMPT)

        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        if path:
            activity = Activity("Dump to %s" % path)
            activity.started()
            try:
                uuids = set()
                for item in schema.Item.iterItems(self.itsView):
                    if (isinstance(item, Preferences) or
                        not str(item.itsPath).startswith("//parcels")):
                        uuids.add(item.itsUUID)
                dumpreload.dump(self.itsView, path, uuids, activity=activity)
                activity.completed()
            except Exception, e:
                logger.exception("Failed to dump file")
                activity.failed(exception=e)
                raise
            self.setStatusMessage(_(u'Items dumped'))

    def onReloadFromFileEvent(self, event):
        wildcard = "%s|*.dump|%s (*.*)|*.*" % (_(u"Dump files"),
            _(u"All files"))

        dlg = wx.FileDialog(wx.GetApp().mainFrame,
                            _(u"Dump Items"), "", "chandler.dump", wildcard,
                            wx.OPEN)

        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        if path:
            activity = Activity("Reload from %s" % path)
            activity.started()
            try:
                dumpreload.reload(self.itsView, path, activity=activity)
                activity.completed()
            except Exception, e:
                logger.exception("Failed to reload file")
                activity.failed(exception=e)
                raise
            self.setStatusMessage(_(u'Items reloaded'))

    def onAddScriptsToSidebarEvent(self, event):
        sidebar = Block.findBlockByName ("Sidebar").contents
        scriptsSet = schema.ns('osaf.framework.scripting',
            self.itsView).scriptsCollection
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
        scriptsSet = schema.ns('osaf.framework.scripting',
            self.itsView).scriptsCollection
        if scriptsSet in sidebar:
            menuTitle = u'Show Scripts'
        else:
            menuTitle = u'Add Scripts to Sidebar'
        event.arguments ['Text'] = menuTitle
        event.arguments ['Enable'] = True

    def onAddSharingLogToSidebarEvent(self, event):
        sidebar = Block.findBlockByName ("Sidebar").contents
        log = schema.ns('osaf.sharing', self.itsView).activityLog
        # if already present, just select it
        if log in sidebar:
            self.postEventByName('RequestSelectSidebarItem', {'item': log})
        else:
            schema.ns("osaf.app", self).sidebarCollection.add(log)

        # go to the All application, so we can view the scripts
        self.postEventByName ('ApplicationBarAll', { })

    def onAddSharingLogToSidebarEventUpdateUI(self, event):
        sidebar = Block.findBlockByName ("Sidebar").contents
        log = schema.ns('osaf.sharing', self.itsView).activityLog
        if log in sidebar:
            menuTitle = u'Show Sharing Activity'
        else:
            menuTitle = u'Add sharing activity log to Sidebar'
        event.arguments ['Text'] = menuTitle
        event.arguments ['Enable'] = True

    def onCalDAVAtopEIMEvent(self, event):
        sharing.caldav_atop_eim = not sharing.caldav_atop_eim

    def onCalDAVAtopEIMEventUpdateUI(self, event):
        if sharing.caldav_atop_eim:
            menuTitle = u'Disable CalDAV-atop-EIM'
        else:
            menuTitle = u'Enable CalDAV-atop-EIM'
        event.arguments ['Text'] = menuTitle
        event.arguments ['Enable'] = True

    def onRecordSetDebuggingEvent(self, event):
        sharing.recordset_conduit.recordset_debugging = \
            not sharing.recordset_conduit.recordset_debugging

    def onRecordSetDebuggingEventUpdateUI(self, event):
        if sharing.recordset_conduit.recordset_debugging:
            menuTitle = u'Disable RecordSet debugging'
        else:
            menuTitle = u'Enable RecordSet debugging'
        event.arguments ['Text'] = menuTitle
        event.arguments ['Enable'] = True

    def onShowPyShellEvent(self, event):
        # Test menu item
        wx.GetApp().ShowPyShell(withFilling=False)

    def onShowPyCrustEvent(self, event):
        # Test menu item
        wx.GetApp().ShowPyShell(withFilling=True)

    def onSaveSettingsEvent(self, event):
        # triggered from "Test | Save Settings" Menu

        from osaf.framework import MasterPassword
        MasterPassword.beforeBackup(self.itsView)

        wildcard = "%s|*.ini|%s (*.*)|*.*" % (_(u"Settings files"),
            _(u"All files"))

        dlg = wx.FileDialog(wx.GetApp().mainFrame,
                            _(u"Save Settings"), "", "chandler.ini", wildcard,
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

        wildcard = "%s|*.ini|%s (*.*)|*.*" % (_(u"Settings files"),
            _(u"All files"))

        dlg = wx.FileDialog(wx.GetApp().mainFrame,
            _(u"Restore Settings"), "", "chandler.ini", wildcard, wx.OPEN)

        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        if path:
            settings.restore(self.itsView, path)
            self.setStatusMessage(_(u'Settings restored'))

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

    def onBackgroundSyncAllEvent(self, event):
        rv = self.itsView
        # Specifically *not* doing a commit here.  This is to simulate
        # a scheduled background sync.  Only manually.
        sharing.scheduleNow(rv)

    def onBackgroundSyncGetOnlyEvent(self, event):
        rv = self.itsView
        collection = self.getSidebarSelectedCollection()
        if collection is not None:

            # Ensure changes in attribute editors are saved
            wx.GetApp().mainFrame.SetFocus()

            rv.commit()
            sharing.scheduleNow(rv, collection=collection, modeOverride='get')

    def onToggleReadOnlyModeEvent(self, event):
        sharing.setReadOnlyMode(not sharing.isReadOnlyMode())

    def onToggleReadOnlyModeEventUpdateUI(self, event):
        event.arguments['Check'] = sharing.isReadOnlyMode()


    def onEditMyNameEvent(self, event):
        rv = self.itsView
        application.dialogs.Util.promptForItemValues(None, "Enter your name",
            schema.ns('osaf.pim', rv).currentContact.item.contactName,
            ( {'attr':'firstName', 'label':'First name' },
              {'attr':'lastName', 'label':'Last name' } )
        )
        rv.commit()

    def onRecalculateMeAddressesEvent(self, event):
        mail._recalculateMeEmailAddresses(self.itsView)

    def onShowMeAddressCollectionDebugWindowEvent(self, event):
        application.dialogs.Util.displayAddressDebugWindow(wx.GetApp().mainFrame, self.itsView, 1)

    def onShowCurrentMeAddressesDebugWindowEvent(self, event):
        application.dialogs.Util.displayAddressDebugWindow(wx.GetApp().mainFrame, self.itsView, 2)

    def onShowCurrentMeAddressDebugWindowEvent(self, event):
        application.dialogs.Util.displayAddressDebugWindow(wx.GetApp().mainFrame, self.itsView, 3)

    def onShowI18nManagerDebugWindowEvent(self, event):
        application.dialogs.Util.displayI18nManagerDebugWindow(wx.GetApp().mainFrame)

    def onShowLogWindowEvent(self, event):
        # Test menu item
        logs = [
            os.path.join(Globals.options.profileDir, 'chandler.log'),
        ]
        application.dialogs.Util.displayLogWindow(wx.GetApp().mainFrame, logs)

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
        if not sharing.ensureAccountSetUp(self.itsView, sharing=True):
            return
        RestoreShares.Show(wx.GetApp().mainFrame, self.itsView)

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
        if collection is not None:

            if (not sharing.isShared(collection) and
                not sharing.ensureAccountSetUp(self.itsView, sharing=True)):
                return

            mainFrame = wx.GetApp().mainFrame
            PublishCollection.ShowPublishDialog(mainFrame,
                view=self.itsView,
                collection=collection)

    def onPublishCollectionEventUpdateUI (self, event):
        """
        Update the menu to reflect the selected collection name.
        """
        collection = self.getSidebarSelectedCollection ()
        event.arguments['Enable'] = collection is not None and (not sharing.isShared(collection))

    def onManageSidebarCollectionEventUpdateUI (self, event):
        collection = self.getSidebarSelectedCollection ()
        event.arguments['Enable'] = collection is not None and (sharing.isShared(collection))

    def onUnshareCollectionEvent(self, event):
        try:
            collection = self.getSidebarSelectedCollection ()
            if collection is not None:
                share = sharing.getShare(collection)
                if sharing.isSharedByMe(share):
                    sharing.unpublish(collection)
                else:
                    sharing.unsubscribe(collection)
        except (sharing.CouldNotConnect, twisted.internet.error.TimeoutError):
            msg = _(u"Unpublish failed, could not connect to server")
            self.setStatusMessage(msg)
        except:
            msg = _(u"Unsubscribe/Unpublish failed, unknown error")
            self.setStatusMessage(msg)
            raise # figure out what the exception is
        else:
            msg = _("Unsubscribe/Unpublish succeeded")
            self.setStatusMessage(msg)

    def onUnshareCollectionEventUpdateUI(self, event):
        event.arguments['Enable'] = False
        collection = self.getSidebarSelectedCollection ()
        if collection is not None:
            share = sharing.getShare(collection)
            if sharing.isShared(collection):
                event.arguments['Enable'] = True
                if sharing.isSharedByMe(share):
                    event.arguments['Text'] = _(u"Unpublish")
                else:
                    event.arguments['Text'] = _(u"Unsubscribe")

    def _freeBusyShared(self):
        allCollection = schema.ns('osaf.pim', self).allCollection
        return (sharing.getFreeBusyShare(allCollection) is not None)

    def onSharingPublishFreeBusyEvent(self, event):
        if not sharing.ensureAccountSetUp(self.itsView, sharing=True):
            return
        mainFrame = wx.GetApp().mainFrame
        allCollection = schema.ns('osaf.pim', self).allCollection
        PublishCollection.ShowPublishDialog(mainFrame, view=self.itsView,
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
            msg = _(u"Freebusy ticket not found, couldn't revoke freebusy access")
            self.setStatusMessage(msg)
        except (sharing.CouldNotConnect, twisted.internet.error.TimeoutError):
            msg = _(u"Unpublish failed, could not connect to server")
            self.setStatusMessage(msg)
        except:
            msg = _(u"Unpublish failed, unknown error")
            self.setStatusMessage(msg)
            raise # figure out what the exception is
        else:
            msg = _("Unpublish succeeded")
            self.setStatusMessage(msg)
            
    def onSyncCollectionEvent (self, event):
        rv = self.itsView
        collection = self.getSidebarSelectedCollection()
        if collection is not None:

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
            event.arguments ['Text'] = _(u'%(collectionName)s') % \
                {'collectionName': collName}
            event.arguments['Enable'] = sharing.isShared(collection)

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

            # To make changes available to sharing thread
            self.RepositoryCommitWithStatus ()

    def onTakeOnlineOfflineEventUpdateUI(self, event):
        event.arguments['Enable'] = False

        collection = self.getSidebarSelectedCollection()
        if collection is not None:
            
            collName = collection.displayName
            event.arguments ['Text'] = _(u'%(collectionName)s') % \
                {'collectionName': collName}

            if sharing.isShared(collection):
                event.arguments['Enable'] = True
                event.arguments['Check'] = not sharing.isOnline(collection)

    def onTakeMailOnlineOfflineEvent(self, event):
        if Globals.mailService.isOnline():
            Globals.mailService.takeOffline()
        else:
            Globals.mailService.takeOnline()


    def onTakeMailOnlineOfflineEventUpdateUI(self, event):
        event.arguments ['Check'] = not Globals.mailService.isOnline()

    def onSyncAllEvent (self, event):
        """
        Synchronize Mail and all sharing.
        The "File | Sync | All" menu item, and the Sync All Toolbar button.
        """

        view = self.itsView

        masterPassword = True
        from osaf.framework import password
        # Check account status:
        try:
            DAVReady = sharing.isWebDAVSetUp(view)
            incomingMailReady = sharing.isIncomingMailSetUp(view)
        except password.NoMasterPassword:
            masterPassword = False
            DAVReady = False
            incomingMailReady = False

        # Any active shares?  (Even if default WebDAV account not set up,
        # the user could have subscribed with tickets)
        activeShares = sharing.checkForActiveShares(view)

        if not masterPassword:
            if not activeShares:
                # Since the user did not give the master password and there are
                # no ticket subscriptions, we can't sync.
                return
        else:
            if not (DAVReady or activeShares or incomingMailReady):
                # Nothing is set up -- nudge the user to set up a sharing account
                sharing.ensureAccountSetUp(view, inboundMail=True, sharing=True)
                # Either the user has created a sharing account, or they haven't,
                # but it doesn't matter since there's no shares to sync
                return

        # At least one account is setup, or there are active shares

        # find all the shared collections and sync them.
        if activeShares:
            # Fire off a background syncAll:

            # Ensure changes in attribute editors are saved
            wx.GetApp().mainFrame.SetFocus()

            # To make changes available to sharing thread
            self.RepositoryCommitWithStatus ()

            sharing.scheduleNow(view)

        else:
            if DAVReady:
                self.setStatusMessage (_(u"No shared collections found"))

        if incomingMailReady:
            self.onGetNewMailEvent (event)

    def onSyncWebDAVEvent (self, event):
        """
        Synchronize WebDAV sharing.

        The "File | Sync | Shares" menu item.
        """

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

        The "File | Sync | Mail" menu item.
        """

        view = self.itsView

        # Make sure we have all the accounts; returns False if the user cancels
        # out and we don't.
        if not sharing.ensureAccountSetUp(view, inboundMail=True):
            return

        view.commit()

        for account in mail.IMAPAccount.getActiveAccounts(view):
            Globals.mailService.getIMAPInstance(account).getMail()

        for account in mail.POPAccount.getActiveAccounts(view):
            Globals.mailService.getPOPInstance(account).getMail()

        view.refresh()

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
