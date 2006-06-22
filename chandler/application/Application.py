#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


import os, sys, threading, time, logging, cStringIO
import wx, Globals, Utility

from new import classobj
from i18n import OSAFMessageFactory as _, getImage
import schema
from version import version

from repository.persistence.RepositoryError import \
    MergeError, RepositoryVersionError, VersionConflictError

logger = logging.getLogger(__name__)

# SCHEMA_VERSION has moved to Utility.py


#@@@Temporary testing tool written by Morgen -- DJA
import util.timing

# Event used to post callbacks on the UI thread

wxEVT_MAIN_THREAD_CALLBACK = wx.NewEventType()
EVT_MAIN_THREAD_CALLBACK = wx.PyEventBinder(wxEVT_MAIN_THREAD_CALLBACK, 0)

def mixinAClass (self, myMixinClassImportPath):
    """
    Given an object, self, and the path as a string to a mixin class,
    myMixinClassImportPath, create a new subclass derived from base class
    of self and the mixin class and makes self's class this new class.

    This is useful to dynamicly (at runtime) mixin new behavior.
    """
    if not self.__class__.__dict__.get ("_alreadyMixedIn"):
        try:
            _classesByName = self.__class__._classesByName
        except AttributeError:
            self.__class__._classesByName = {}
            _classesByName = self.__class__._classesByName

        parts = myMixinClassImportPath.split (".")
        assert len(parts) >= 2, "Delegate %s isn't a module name plus a class name" % myMixinClassImportPath
        
        delegateClassName = parts.pop ()
        newClassName = delegateClassName + '_' + self.__class__.__name__
        try:
            theClass = _classesByName [newClassName]
        except KeyError:
            module = __import__ ('.'.join(parts), globals(), locals(), delegateClassName)
            assert module.__dict__.get (delegateClassName), "Class %s doesn't exist" % myMixinClassImportPath
            theClass = classobj (str(newClassName),
                                 (module.__dict__[delegateClassName], self.__class__,),
                                 {})
            theClass._alreadyMixedIn = True
            _classesByName [newClassName] = theClass
        self.__class__ = theClass


class MainThreadCallbackEvent(wx.PyEvent):
    def __init__(self, target, *args):
        super (MainThreadCallbackEvent, self).__init__()
        self.SetEventType(wxEVT_MAIN_THREAD_CALLBACK)
        self.target = target
        self.args = args
        self.lock = threading.Lock()

class wxBlockFrameWindow (wx.Frame):
    def __init__(self, *arguments, **keywords):
        super (wxBlockFrameWindow, self).__init__(*arguments, **keywords)

        self.SetBackgroundColour (wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)
 
    def ShowTreeOfBlocks (self, treeOfBlocks):
        if hasattr (self, "treeOfBlocks"):
            self.treeOfBlocks.unRender()
            self.SetSizer (None)

        self.treeOfBlocks = treeOfBlocks
        self.treeOfBlocks.frame = self
        self.treeOfBlocks.render()

        sizer = wx.BoxSizer (wx.HORIZONTAL)
        self.SetSizer (sizer)
        from osaf.framework.blocks.Block import wxRectangularChild
        sizer.Add (self.treeOfBlocks.widget,
                   self.treeOfBlocks.stretchFactor, 
                   wxRectangularChild.CalculateWXFlag(self.treeOfBlocks), 
                   wxRectangularChild.CalculateWXBorder(self.treeOfBlocks))
        sizer.Layout()

    def OnClose (self, event):
        if hasattr (self, "treeOfBlocks"):
            self.treeOfBlocks.unRender()
            self.SetSizer (None)
            event.Skip()

    def OnSize(self, event):
        # Calling Skip causes wxWindows to continue processing the event, 
        # which will cause the parent class to get a crack at the event.

        if not wx.GetApp().ignoreSynchronizeWidget:
            from osaf.pim.structs import SizeType
            # Our first child's block is the FrameWindow where we store size and position
            self.GetChildren()[0].blockItem.size = SizeType (self.GetSize().x, self.GetSize().y)
        event.Skip()

    def OnMove(self, event):
        # Calling Skip causes wxWindows to continue processing the event, 
        # which will cause the parent class to get a crack at the event.
        
        if not wx.GetApp().ignoreSynchronizeWidget:
            from osaf.pim.structs import PositionType
            # Our first child's block is the FrameWindow where we store size and position
            self.GetChildren()[0].blockItem.position = PositionType(self.GetPosition().x, self.GetPosition().y)
        event.Skip()


class wxMainFrame (wxBlockFrameWindow):
    def __init__(self, *arguments, **keywords):
        super (wxMainFrame, self).__init__(*arguments, **keywords)

        # useful in debugging Mac background drawing problems
        #self.MacSetMetalAppearance(True)

        self.icon = wx.Icon("resources/images/Chandler_32.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        if '__WXMSW__' in wx.PlatformInfo:
            # From the wxWidgets documentation:
            # wxToolBar95: Note that this toolbar paints tools to reflect system-wide colours.
            # If you use more than 16 colours in your tool bitmaps, you may wish to suppress
            # this behaviour, otherwise system colours in your bitmaps will inadvertently be
            # mapped to system colours. To do this, set the msw.remap system option before
            # creating the toolbar:

            # wxSystemOptions::SetOption(wxT("msw.remap"), 0);

            # If you wish to use 32-bit images (which include an alpha channel for
            # transparency) use:

            #   wxSystemOptions::SetOption(wxT("msw.remap"), 2);

            # then colour remapping is switched off, and a transparent background used. But
            # only use this option under Windows XP with true colour:

            #   (wxTheApp->GetComCtl32Version() >= 600 && ::wxDisplayDepth() >= 32)
            if wx.GetApp().GetComCtl32Version() >= 600 and wx.DisplayDepth() >= 32:
                value = 2
            else:
                value = 0
            wx.SystemOptions.SetOptionInt ("msw.remap", value)

        if wx.Platform == '__WXMAC__':
            # Fix for Bug 4156: On the Mac, when the app activates,
            # un-minimize the main window if necessary
            wx.GetApp().Bind(wx.EVT_ACTIVATE_APP, self.OnAppActivate)

    def OnAppActivate(self, event):
        if event.GetActive() and self.IsIconized():
            self.Iconize(False)

    def OnClose(self, event):
        """
        Main window is about to be closed when the application is quitting.
        """
        def displayInfoWhileProcessing (message, method, *args, **kwds):
            busyInfo = wx.BusyInfo (message)
            wx.Yield()
            result = method(*args, **kwds)
            del busyInfo
            return result

        def commit (view):
            try:
                view.commit()
            except VersionConflictError, e:
                logger.exception(e)

        # Finish any edits in progress.
        from osaf.framework.blocks.Block import Block
        Block.finishEdits()

        # For some strange reason when there's an idle handler on the
        # application the mainFrame windows doesn't get destroyed, so
        # we'll remove the handler

        app = wx.GetApp()
        app.Bind(wx.EVT_IDLE, None)
        app.Bind(wx.EVT_MENU, None, id=-1)

        if wx.Platform == '__WXMAC__':
            wx.GetApp().Bind(wx.EVT_ACTIVATE_APP, None)

        if __debug__:
            displayInfoWhileProcessing (_("Checking repository..."),
                                        app.UIRepositoryView.check)

        # Preliminary tests point to stopCrypto as the cause for Chandler being slow
        # to quit besides the debug only checking of the repository

        displayInfoWhileProcessing (_("Shutting down mail service..."),
                                    Globals.mailService.shutdown)

        displayInfoWhileProcessing (_("Stopping wakeup service..."),
                                    Utility.stopWakeup)

        displayInfoWhileProcessing (_("Stopping twisted..."),
                                    Utility.stopTwisted)

        # Since Chandler doesn't have a save command and commits typically happen
        # only when the user completes a command that changes the user's data, we
        # need to add a final commit when the application quits to save data the
        # state of the user's world, e.g. window location and size.

        displayInfoWhileProcessing (_("Committing repository..."),
                                    commit, app.UIRepositoryView)

        displayInfoWhileProcessing (_("Stopping crypto..."),
                                    Utility.stopCrypto, Globals.options.profileDir)

        displayInfoWhileProcessing (_("Checkpointing repository..."),
                                    app.UIRepositoryView.repository.checkpoint)

        # When we quit, as each wxWidget window is torn down our handlers that
        # track changes to the selection are called, and we don't want to count
        # these changes, since they weren't caused by user actions.

        app.ignoreSynchronizeWidget = True

        self.Destroy()

class wxApplication (wx.App):

    __CHANDLER_STARTED_UP = False # workaround for bug 4362

    def OnInit(self):
        """
        Main application initialization.
        """

        # The initI18n can't be initialized until after the App
        # object has been created since initialization creates a
        # wx.Locale object which requires a path that requires
        # GetTraits, which is a method on the App object.
        #
        # Eventually when we get Python egg based localization
        # implemented, this constraint may change
        Utility.initI18n(Globals.options) 

        util.timing.begin("wxApplication OnInit") #@@@Temporary testing tool written by Morgen -- DJA

        self.ignoreSynchronizeWidget = True
        self.focus = None

        wx.InitAllImageHandlers()

        # Disable automatic calling of UpdateUIEvents. We will call them
        # manually when blocks get rendered, change visibility, etc.
        
        wx.UpdateUIEvent.SetUpdateInterval (-1)

        # Install a custom displayhook to keep Python from setting the global
        # _ (underscore) to the value of the last evaluated expression.  If 
        # we don't do this, our mapping of _ to gettext can get overwritten.
        # This is useful in interactive debugging with PyShell.

        def _displayHook(obj):
            if obj is not None:
                print repr(obj)

        sys.displayhook = _displayHook

        assert Globals.wxApplication == None, "We can have only one application"
        Globals.wxApplication = self
        self.ignoreIdle = False

        # Initialize PARCELPATH and sys.path
        parcelPath = Utility.initParcelEnv(Globals.chandlerDirectory,
                                           Globals.options.parcelPath)

        # If the magic metakey is down, run the startup options box; it'll
        # modify Globals.options as necessary.
        if Globals.options.ask or wx.GetMouseState().ControlDown():
            from application.dialogs.StartupOptionsDialog import StartupOptionsDialog            
            StartupOptionsDialog.run()

        # Splash Screen:
        # don't show the splash screen when nosplash is set
        splash = None
        if not Globals.options.nosplash:
            splashBitmap = self.GetImage("splash.png")
            splash = StartupSplash(None, splashBitmap)
            splash.Show()
            splash.Update()  # Force the window to refresh right now

        # Crypto initialization
        if splash:
            splash.updateGauge('crypto')
        Utility.initCrypto(Globals.options.profileDir)

        # The repository opening code was moved to a method so that it can
        # be called again if there is a schema mismatch and the user chooses
        # to reopen the repository in create mode.
        if splash:
            splash.updateGauge('repository')
        repoDir = Utility.locateRepositoryDirectory(Globals.options.profileDir)
            
        try:
            view = Utility.initRepository(repoDir, Globals.options)
        except RepositoryVersionError:
            if self.ShowSchemaMismatchWindow():
                Globals.options.create = True
                view = Utility.initRepository(repoDir, Globals.options)
            else:
                raise Utility.SchemaMismatchError

        self.repository = view.repository

        # Verify Schema Version
        if not Utility.verifySchema(view):
            if self.ShowSchemaMismatchWindow():
                # Blow away the repository
                self.repository.close()
                Globals.options.create = True
                view = Utility.initRepository(repoDir, Globals.options)
                self.repository = view.repository
            else:
                raise Utility.SchemaMismatchError

        self.UIRepositoryView = view

        # Load Parcels
        if splash:
            splash.updateGauge('parcels')
        Utility.initParcels(view, parcelPath)

        EVT_MAIN_THREAD_CALLBACK(self, self.OnMainThreadCallbackEvent)

        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_MENU, self.OnCommand, id=-1)
        self.Bind(wx.EVT_TOOL, self.OnCommand, id=-1)
        self.Bind(wx.EVT_UPDATE_UI, self.OnCommand, id=-1)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroyWindow, id=-1)
        self.Bind(wx.EVT_SHOW, self.OnShow, id=-1)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

        # The Twisted Reactor should be started before other Managers
        # and stopped last.
        if splash:
            splash.updateGauge('twisted')
        Utility.initTwisted()

        mainViewRoot = self.LoadMainViewRoot(delete=Globals.options.refreshui)

        # arel: fix for bug involving window size and toolbar on MacOS (bug 3411).
        # The problem is that mainFrame gets resized when it is rendered
        # (particularly when the toolbar gets rendered), increasing the window's
        # height by the height of the toolbar.  We fix by remembering the
        # (correct) size before rendering and resizing. 
        rememberSize = (mainViewRoot.size.width, mainViewRoot.size.height)

        self.mainFrame = wxMainFrame(None,
                                     -1,
                                     mainViewRoot.windowTitle,
                                     pos=(mainViewRoot.position.x, mainViewRoot.position.y),
                                     size=(mainViewRoot.size.width, mainViewRoot.size.height),
                                     style=wx.DEFAULT_FRAME_STYLE)

        # mainViewRoot needs to refer to its frame and the mainFrame needs to
        # refert to the mainViewRoot
        mainViewRoot.frame = self.mainFrame
        self.mainFrame.mainViewRoot = mainViewRoot

        # Register to some global events for name lookup.
        if splash:
            splash.updateGauge('globalevents')
        globalEvents = self.UIRepositoryView.findPath('//parcels/osaf/framework/blocks/GlobalEvents')

        from osaf.framework.blocks.Block import Block

        Block.addToNameToItemUUIDDictionary (globalEvents.eventsForNamedLookup,
                                             Block.eventNameToItemUUID)

        self.ignoreSynchronizeWidget = False

        if splash:
            splash.updateGauge('mainview')

        #import hotshot
        self.RenderMainView()
        #prof = hotshot.Profile('4117.prof')
        #prof.runcall(self.RenderMainView)
        #prof.close()

        if Globals.options.profile:
            import hotshot, hotshot.stats

            prof = hotshot.Profile(os.path.join(Globals.options.profileDir, 'commit.log'))
            prof.runcall(self.UIRepositoryView.commit)
            prof.close()

            stats = hotshot.stats.load(os.path.join(Globals.options.profileDir, 'commit.log'))
            stats.strip_dirs()
            stats.sort_stats('time', 'calls')
            stats.print_stats(125)
        else:
            wx.Yield()
            self.UIRepositoryView.commit()
            
        # Start the WakeupCaller Service
        Utility.initWakeup(self.UIRepositoryView)

        # Start the Chandler Mail Service

        from osaf.mail import MailService

        Globals.mailService = MailService(self.UIRepositoryView)
        Globals.mailService.startup()

        if splash:
            splash.Destroy()

        # data loading script execution
        if Globals.options.createData:
            import util.GenerateItemsFromFile as GenerateItemsFromFile
            GenerateItemsFromFile.RunScript(self.UIRepositoryView)
        
        self.__CHANDLER_STARTED_UP = True # workaround for bug 4362

        # resize to intended size. (bug 3411)
        self.mainFrame.SetSize(rememberSize)

        # Call UpdateWindowUI before we show the window. UPDATE_UI_FROMIDLE
        # should be set so we don't update menus, since they are done
        # when the menu is pulled down (mac may handle this slightly differently,
        # except we still want UPDATE_UI_FROMIDLE on mac) -- DJA
        self.mainFrame.UpdateWindowUI (wx.UPDATE_UI_FROMIDLE | wx.UPDATE_UI_RECURSE)
        self.needsUpdateUI = False

        self.mainFrame.Show()

        # Set focs so OnIdle won't trigger an unnecessary UpdateWindowUI the
        # first time through. -- DJA
        self.focus = wx.Window_FindFocus()


        # Register sharing activity to be sent to the status bar
        from osaf import sharing
        setStatusMessage = Block.findBlockByName('StatusBar').setStatusMessage
        def _setStatusMessageCallback(*args, **kwds):
            if kwds.get('msg', None) is not None:
                self.PostAsyncEvent(setStatusMessage, kwds['msg'])
        sharing.register(_setStatusMessageCallback)

    
        util.timing.end("wxApplication OnInit") #@@@Temporary testing tool written by Morgen -- DJA

        return True    # indicates we succeeded with initialization

    def LoadMainViewRoot (self, delete=False):
        frame = None
        mainViewRoot = self.UIRepositoryView.findPath('//userdata/MainViewRoot')

        if mainViewRoot and delete:
            # We need to delete the mainViewRoot. Ideally we'd have automatic
            # garbage colleciton so that all the garbage resulting from the
            # deletion of the mainViewRoot would be cleaned up automatically.
            # However, I haven't been able to convince OSAF of the importance
            # of automatic garbage collection, so the deletion is going to
            # be problematic until we implement a garbage collector.
            #
            # Currently, I'm going to try deleting all BranchPoint block
            # delegate's caches, then all the Blocks in the userdata.
            # Chances are this will leave some lingering garbage, but it's
            # too difficult to track it down for now, and isn't worth it yet
            # since this code is used mostly for debugging. And in any event,
            # it would be easier to implement a garbage collector.
            def deleteAllBranchCaches (block):
                for child in block.childrenBlocks:
                    deleteAllBranchCaches (child)
                import osaf.framework.blocks.BranchPoint as BranchPoint
                if isinstance (block, BranchPoint.BranchPointBlock):
                    block.delegate.deleteCache()

            self.UIRepositoryView.refresh()
            frame = getattr (mainViewRoot, 'frame', None)
            
            deleteAllBranchCaches(mainViewRoot)

            from osaf.framework.blocks import Block

            for item in self.UIRepositoryView['userdata'].iterChildren():
                if isinstance (item, Block.Block):
                    item.delete()

            self.UIRepositoryView.commit()
            assert self.UIRepositoryView.findPath('//userdata/MainViewRoot') == None
            mainViewRoot = None
        if mainViewRoot is None:
            template = self.UIRepositoryView.findPath ("//parcels/osaf/views/main/MainViewRoot")
            mainViewRoot = template.copy (parent = schema.Item.getDefaultParent (self.UIRepositoryView),
                                          name = "MainViewRoot",
                                          cloudAlias="copying")
            if frame is not None:
                mainViewRoot.frame = frame
        return mainViewRoot

    def RenderMainView (self):
        mainViewRoot = self.mainFrame.mainViewRoot
        mainViewRoot.lastDynamicBlock = False
        mainViewRoot.render()

        # We have to wire up the block mainViewRoot, it's widget and sizer to a new
        # sizer that we add to the mainFrame.
        
        sizer = wx.BoxSizer (wx.HORIZONTAL)
        self.mainFrame.SetSizer (sizer)
        from osaf.framework.blocks.Block import wxRectangularChild
        sizer.Add (mainViewRoot.widget,
                   mainViewRoot.stretchFactor, 
                   wxRectangularChild.CalculateWXFlag(mainViewRoot), 
                   wxRectangularChild.CalculateWXBorder(mainViewRoot))
        sizer.Layout()

    def UnRenderMainView (self):
        mainViewRoot = self.mainFrame.mainViewRoot.unRender()
        if __debug__:
            from osaf.framework.blocks.Block import Block
            for value in self.UIRepositoryView._subscribers.itervalues():
                for uuid in value:
                    item = self.UIRepositoryView.findUUID(uuid)
                    assert not isinstance (item, Block)
            
        self.mainFrame.SetSizer (None)

    if __debug__:
        def PrintTree (self, widget, indent):
            sizer = widget.GetSizer()
            if sizer:
                for sizerItem in sizer.GetChildren():
                    if sizerItem.IsWindow():
                        window = sizerItem.GetWindow()
                        try:
                            name = window.blockItem.blockName
                        except AttributeError:
                            name = window.blockItem
                        print indent, name
                        self.PrintTree (window, indent + "  ")

    def GetRawImage (self, name):
        """
        Return None if image isn't found, otherwise return the raw image.
        Also look first for platform specific images.
        """

        root, extension = os.path.splitext (name)

        file = getImage(root + "-" + sys.platform + extension)

        if file is None:
            file = getImage(name)

            if file is None:
                return None

        return wx.ImageFromStream (cStringIO.StringIO(file.read()))

    def GetImage (self, name):
        """
        Return None if image isn't found, otherwise loads a bitmap.
        Looks first for platform specific bitmaps.
        """
        rawImage = self.GetRawImage(name)

        if rawImage is not None:
            return wx.BitmapFromImage (rawImage)

        return None

    def OnCommand(self, event):
        """
        Catch commands and pass them along to the blocks.
        Our events have ids greater than wx.ID_HIGHEST
        Delay imports to avoid circular references.
        """
        from osaf.framework.blocks.Block import Block

        wxID = event.GetId()

        block = Block.idToBlock.get (wxID, None)
        if block is not None:

            #An interesting problem occurs on Mac (see Bug #219). If a dialog is
            #the topmost windw, standard events like cut/copy/paste get processed
            #by this handler instead of the dialog, causing cut/copy/paste to stop
            #working in dialogs. So, instead, if the dialog handles the event we
            # don't want to dispatch it through our CPIA event mechanism.
            #
            #Unfortunately, it's not possible to know if the dialog can process
            #the event. So instead we'll just send all events with "standard wx
            #ids" (e.g. that have an associated block whose wxId is non-zero) to
            #the dialog. This can be accomplished by not handling the event
            #here and, instead, calling Skip so it will be passed along to the dialog.
            #
            #Telling if a dialog is the topmost windows is also a bit tricky since
            #dialogs have by default a top level window that is our MainFrame
            #window. So a dialog is on top when the second window in
            #wx.TopLevelWindows is a dialog.

            topWindows = wx.GetTopLevelWindows()
            if not (len (topWindows) > 1 and isinstance (topWindows[1], wx.Dialog)):
                updateUIEvent = event.GetEventType() == wx.EVT_UPDATE_UI.evtType[0]
                blockEvent = getattr (block, 'event', None)
                # If a block doesn't have an event, it should be an updateUI event
                assert (blockEvent != None or updateUIEvent)
    
                if blockEvent is not None:
                    arguments = {}
                    if updateUIEvent:
                        arguments ['UpdateUI'] = True
                    else:
                        eventObject = event.GetEventObject()
                        if eventObject is not None:
                            method = getattr (eventObject, "GetToolState", None)
                            if method is not None:
                                arguments ['buttonState'] = method (wxID)
     
                    Block.post (blockEvent, arguments, block)
     
                    if updateUIEvent:
                        check = arguments.get ('Check', None)
                        if check is not None:
                            event.Check (check)
                        event.Enable (arguments.get ('Enable', True))
                        text = arguments.get ('Text', None)
                        if text != None:
                            event.SetText (text)
                            # Some widgets, e.g. wxToolbarItems don't properly handle
                            # setting the text of buttons, so we'll handle it here by
                            # looking for the method OnSetTextEvent to handle it
                            widget = block.widget
                            method = getattr (widget, "OnSetTextEvent", None)
                            if method is not None:
                                method (event)
                    return
        event.Skip()

    def OnDestroyWindow(self, event):
        from osaf.framework.blocks.Block import Block
        Block.wxOnDestroyWidget (event.GetWindow())
        event.Skip()

    def OnShow(self, event):
        # Giant hack. Calling event.GetEventObject while the object is being created cause the
        # object to get the wrong type because of a "feature" of SWIG. So we need to avoid
        # OnShows in this case by using ignoreSynchronizeWidget as a flag.
        
        if not wx.GetApp().ignoreSynchronizeWidget:
            widget = event.GetEventObject()
            try:
                block = widget.blockItem
            except AttributeError:
                pass
            else:
                if widget.IsShown() != event.GetShow():
                    self.needsUpdateUI = True

        event.Skip()

    def yieldNoIdle(self):
        self.ignoreIdle = True
        try:
            wx.Yield()
        finally:
            self.ignoreIdle = False

    def propagateAsynchronousNotifications (self):
        def mergeFunction(code, item, attribute, value):
            # You can choose which view wins by uncommenting the appropriate
            # return statement:

            return getattr(item, attribute)             # Let changes from
                                                        # other views win

            # return value                              # Let changes from the
                                                        # main view win

        # Fire set notifications that require mapChanges
        self.repository.view.refresh (mergeFunction) # pickup changes from other threads

        # synchronize dirtied blocks to reflect changes to the data
        from osaf.framework.blocks.Block import Block
        # make the list first in case it gets tweaked during synchronizeWidget
        dirtyBlocks = [self.UIRepositoryView.findUUID(theUUID)
                       for theUUID in Block.dirtyBlocks]

        # synchronize affected widgets
        for block in dirtyBlocks:
            block.synchronizeWidget(useHints=True)

        Block.dirtyBlocks = set()


    def OnIdle(self, event):
        # Adding a handler for catching a set focus event doesn't catch
        # every change to the focus. It's difficult to preprocess every event
        # so we check for focus changes in OnIdle. Also call UpdateUI when
        # focus changes.

        if not self.__CHANDLER_STARTED_UP: return # workaround for bug 4362
        if self.ignoreIdle: return                # workaround for bug 4732

        self.propagateAsynchronousNotifications()

        focus = wx.Window_FindFocus()
        if self.focus != focus:
            self.focus = focus
            self.needsUpdateUI = True

        if self.needsUpdateUI:
            try:
                self.mainFrame.UpdateWindowUI(wx.UPDATE_UI_FROMIDLE |
                                              wx.UPDATE_UI_RECURSE)
            finally:
                self.needsUpdateUI = False

        # Give CPIA Script a chance to execute a script
        if not self.StartupScriptDone:
            self.StartupScriptDone = True
            import osaf.framework.scripting as Scripting
            wx.CallAfter(Scripting.run_startup_script, self.UIRepositoryView)

        event.Skip()

    StartupScriptDone = False

    def OnKeyDown(self, event):
        import osaf.framework.scripting as Scripting
        if Scripting.hotkey_script(event, self.UIRepositoryView):
            pass # consume the keystroke (the script is now running)
        else:
            event.Skip() # pass the key along to another widget

    def OnExit(self):
        """
        Main application termination. Called after the window is torn down.
        """
        self.UIRepositoryView.repository.close()

    def OnMainThreadCallbackEvent(self, event):
        """
        Fire off a custom event handler
        """
        event.target(*event.args)
        event.lock.release()
        event.Skip()

    def PostAsyncEvent(self, callback, *args):
        """
        Post an asynchronous event that will call 'callback' with 'data'
        """
        evt = MainThreadCallbackEvent(callback, *args)
        evt.lock.acquire()
        wx.PostEvent(self, evt)
        return evt.lock

    def _DispatchItemMethod (self, transportItem, methodName, transportArgs, keyArgs):
        """
        Private dispatcher for a method call on an item done between threads.
        
        See CallItemMethodAsync() below for calling details.
        
        Do a repository refresh to get the changes across from the other thread.
        """
        from osaf.framework.blocks.Block import Block

        wx.GetApp().UIRepositoryView.refresh () # bring changes across from the other thread/view

        # unwrap the target item and find the method to call

        if isinstance (transportItem, TransportWrapper):
            item = transportItem.unwrap ()
        else:
            item = Block.findBlockByName (transportItem)
            assert item is not None

        method = getattr (type(item), methodName, None)
        if method is None:
            logger.warning ("CallItemMethodAsync couldn't find method %s on item %s" % (methodName, str (item)))
        else:
            # unwrap the transportArgs
            args = []
            for wrapper in transportArgs:
                args.append (wrapper.unwrap())
    
            # unwrap the keyword args
            for key, wrapper in keyArgs.items():
                keyArgs[key] = wrapper.unwrap()
    
            # call the member with params
            method (item, *args, **keyArgs)

    def CallItemMethodAsync (self, item, methodName, *args, **keyArgs):
        """
        Post an asynchronous event that will call a method by name in an item.
        If item is a string then the block of that name will be used as the
        item.
        
        Communication between threads is tricky.  This method will convert
        all parameters into UUIDs for transport during the event posting,
        and they will be converted back to items when the event is received.
        However you will have to do a commits in the non-UI thread for the data
        to pass across smoothly.  The UI thread will do a commit to get
        the changes on its side.  
        
        Also, items that are not simple arguments or keyword arguments will 
        not be converted to/from UUID.

        All other args are passed across to the other thread.
        
        @param item: an C{Item} whose method we wish to call
        @type item: C{Item} or C{String}
        @param methodName: the name of the method to call
        @type methodName: C{String}
        """
        # convert the item whose method we're calling
        if isinstance (item, schema.Item):
            item = TransportWrapper (item)
        # convert all the arg items
        transportArgs = []
        for anItem in args:
            transportArgs.append (TransportWrapper (anItem))
        # convert all dictionary items
        for key,value in keyArgs.items():
            keyArgs[key] = TransportWrapper (value)
        wx.GetApp().PostAsyncEvent (self._DispatchItemMethod, item, 
                                    methodName, transportArgs, keyArgs)


    def ShowPyShell(self, withFilling=False):
        """
        A window with a python interpreter
        """
        import wx.py
        import tools.headless as headless

        headless.view = view = self.UIRepositoryView

        def run(scriptText):
            import osaf.framework.scripting as Scripting
            Scripting.run_script(scriptText, headless.view)

        # Import helper methods/variables from headless, and also add
        # whatever other methods we want to the mix (such as the run method,
        # above).  locals will be passed to PyCrust/Shell to make those
        # symbols available to the developer
        locals = headless.getExports(run=run,
                                     view=view,
                                     schema=schema,
                                     app_ns=schema.ns('osaf.app', view),
                                     pim_ns=schema.ns('osaf.pim', view),
                                    )

        browseableObjects = {
         "globals" : Globals,
         "parcelsRoot" : self.UIRepositoryView.findPath("//parcels"),
         "repository" : self.UIRepositoryView.repository,
         "wxApplication" : self,
        }

        if withFilling:
            self.pyFrame = wx.py.crust.CrustFrame(rootObject=browseableObjects,
                                                  rootLabel="Chandler",
                                                  locals=locals)
        else:
            self.pyFrame = wx.py.shell.ShellFrame(locals=locals)

        self.pyFrame.SetSize((700,700))
        self.pyFrame.Show(True)

    def ChooseLogConfig(self):
        wildcard = u"Config files|*.conf|All files (*.*)|*.*"
        dlg = wx.FileDialog(wx.GetApp().mainFrame,
                            "Choose logging configuration file",
                            "", "", wildcard, wx.OPEN)

        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        if path:
            logger.warning("Loading logging configuration: %s" % path)
            Utility.fileConfig(path)


    def ShowSchemaMismatchWindow(self):
        logger.info("Schema version of repository doesn't match app")

        message = \
_(u"""Your repository was created by an older version of Chandler.  In the future we will support migrating data between versions, but until then, when the schema changes we need to remove all data from your repository.

Would you like to remove all data from your repository?
""")

        dialog = wx.MessageDialog(None,
                                  message,
                                  _(u"Cannot open repository"),
                                  wx.YES_NO | wx.ICON_INFORMATION)
        response = dialog.ShowModal()
        dialog.Destroy()
        return response == wx.ID_YES


class TransportWrapper (object):
    """
    Wrapper class for items sent between threads by
    CallItemMethodAsync() in wxApplication.
    
    Simply wraps any object with this class.  If the 
    object was an Item, we remember its UUID and
    use that to get back the right item on in the
    other thread/view.
    """
    def __init__ (self, possibleItem):
        """
        Construct a TransportWrapper from an object.
        """
        try:
            self.itemUUID = possibleItem.itsUUID
        except AttributeError:
            self.nonItem = possibleItem

    def unwrap (self):
        """
        Unwrap the original object, using the UUID
        if the original was an Item.
        """
        try:
            theUUID = self.itemUUID
        except AttributeError:
            return self.nonItem
        else:
            item = wx.GetApp().UIRepositoryView.findUUID (theUUID)
            return item

class StartupSplash(wx.Frame):
    def __init__(self, parent, bmp):
        padding = 7     # padding under and right of the progress percent text (in pixels)
        fontsize = 12   # font size of the progress text (in pixels)
        
        super(StartupSplash, self).__init__(parent=parent, style=wx.SIMPLE_BORDER)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.CenterOnScreen()
        self.SetBackgroundColour(wx.WHITE)

        # Progress Text dictionary
        #                    name            weight      text
        self.statusTable = {'crypto'      : ( 5,  _(u"Initializing crypto services")),
                            'repository'  : ( 10, _(u"Opening the repository")),
                            'parcels'     : ( 15, _(u"Loading parcels")),
                            'twisted'     : ( 10, _(u"Starting Twisted")),
                            'globalevents': ( 15, _(u"Registering global events")),
                            'mainview'    : ( 10, _(u"Rendering the main view"))}

        # Font to be used for the progress text
        font = wx.Font(fontsize, wx.NORMAL, wx.NORMAL, wx.NORMAL)
        
        # Add title text
        titleText = wx.StaticText(self, -1, _(u"Experimentally Usable Calendar"))
        titleText.SetBackgroundColour(wx.WHITE)
        sizer.Add(titleText, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, padding)
        titleText.SetFont(wx.Font(fontsize, wx.NORMAL, wx.NORMAL, wx.NORMAL))

        # Load the splash screen picture.
        # The picture will set the width of the splash screen, 
        # all other elements are horizontally centered on it (except for the progress "%" display)
        bitmap = wx.StaticBitmap(self, -1, bmp)
        sizer.Add(bitmap, 0, wx.ALIGN_CENTER, 0)

        # Add Chandler text
        text1 = wx.StaticText(self, -1, _(u"Chandler"))
        text1.SetBackgroundColour(wx.WHITE)
        sizer.Add(text1, 1,  wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, padding)
        text1.SetFont(wx.Font(16, wx.NORMAL, wx.NORMAL, wx.BOLD))

        # Add Version text
        text2 = wx.StaticText(self, -1,
                              _(u"Version %(version)s") % { 'version': version })
        text2.SetBackgroundColour(wx.WHITE)
        sizer.Add(text2, 1,  wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, padding)
        text2.SetFont(wx.Font(16, wx.NORMAL, wx.NORMAL, wx.NORMAL))

        # Add OSAF text
        text3 = wx.StaticText(self, -1, _(u"Open Source Applications Foundation"))
        text3.SetBackgroundColour(wx.WHITE)
        sizer.Add(text3, 1,  wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, padding)
        text3.SetFont(wx.Font(10, wx.NORMAL, wx.NORMAL, wx.NORMAL))

        # The progress text is in 2 parts: a text indicating the section being initialized
        # and a percent number indicating an approximate value of the total being done
        # Create the text box for the section initialized text
        self.progressText = wx.StaticText(self, -1)
        self.progressText.SetBackgroundColour(wx.WHITE)

        progressSizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(progressSizer, 1, wx.EXPAND)
        # In order to center the progress text, we need to add a dummy item on the left
        # that has the same weight as the progress percent on the right
        progressSizer.Add((padding, padding), 1)
        progressSizer.Add(self.progressText, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        self.progressText.SetFont(font)

        # Create the text box for the "%" display
        self.progressPercent = wx.StaticText(self, -1, style=wx.ALIGN_RIGHT)
        self.progressPercent.SetBackgroundColour(wx.WHITE)
        progressSizer.Add(self.progressPercent, 1, wx.ALIGN_RIGHT | wx.RIGHT, padding)
        self.progressPercent.SetFont(font)
        
        self.workingTicks = 0
        self.completedTicks = 0
        self.timerTicks = 0
        
        #Without a lock, spawning a new thread modestly improves the smoothness
        #of the gauge, but then Destroy occasionally raises an exception and the
        #gauge occasionally moves backwards, which is unsettling. Unfortunately,
        #my feeble attempt at using a lock seemed to create a race condition.
        
        #threading._start_new_thread(self.timerLoop, ())
        sizer.SetSizeHints(self)
        self.Layout()
        
    def timerLoop(self):#currently unused
        self._startup = True
        while self and self._startup:
            self.updateGauge('timer')
            time.sleep(1.5)

    def updateGauge(self, type):
        if type == 'timer': #currently unused
            if self.timerTicks < self.workingTicks:
                self.timerTicks += 1
                self.gauge.SetValue(self.completedTicks + self.timerTicks)
        else:
            self.timerTicks = 0
            self.completedTicks += self.workingTicks
            self.workingTicks = self.statusTable[type][0]
            self.progressText.SetLabel(self.statusTable[type][1])
            percentString = _(u"%(percent)d%%") % {'percent' : self.completedTicks + self.timerTicks}
            self.progressPercent.SetLabel(percentString)
        self.Layout()
        self.Update()
        wx.Yield()

    def Destroy(self):
        self._startup = False
        wx.Yield()
        time.sleep(.25) #give the user a chance to see the gauge reach 100%
        wx.Frame.Destroy(self)
