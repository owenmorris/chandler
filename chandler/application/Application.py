#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
from i18n import ChandlerMessageFactory as _, getImage, getLocaleSet
import schema, feedback
from version import version

from repository.persistence.RepositoryError import \
    RepositoryVersionError, RepositoryPlatformError, VersionConflictError
from repository.persistence.RepositoryView import otherViewWins


logger = logging.getLogger(__name__)

wxWindow_FindFocus = wx.Window_FindFocus

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

# If you pass -1 for a widget's id during creation you'll get a unique id, which might differ
# from run to run. This makes it impossible to find widgets, not associated with blocks, from
# one run to the next during recorded script playback. So instead, if you use a widget, not
# associated with a block, that you want to be scriptable you should use getIdForString
# ("SomeUniqueString") instead of -1. Debugging code will catch non unique strings.
#
# You should also call deleteIdForString in the destructor of your widget.

idToString = {}
stringToId = {}

def registerStringForId (id, string):
    # Strings must be unique
    assert not stringToId.has_key (string)
    idToString [id] = string
    stringToId [string] = id
    

def unregisterStringForId (name):
    del idToString [stringToId [name]]
    del stringToId [name]
    

class MainThreadCallbackEvent(wx.PyEvent):
    def __init__(self, target, *args, **kwds):
        super (MainThreadCallbackEvent, self).__init__()
        self.SetEventType(wxEVT_MAIN_THREAD_CALLBACK)
        self.target = target
        self.args = args
        self.kwds = kwds
        self.lock = threading.Lock()

class wxBlockFrameWindow (wx.Frame):
    def __init__(self, *arguments, **keywords):
        super (wxBlockFrameWindow, self).__init__(*arguments, **keywords)

        self.SetBackgroundColour (wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.app = wx.GetApp()
 
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

        if not self.app.ignoreSynchronizeWidget:
            from osaf.pim.structs import SizeType
            # Our first child's block is the FrameWindow where we store size and position
            size = self.GetSize()
            self.GetChildren()[0].blockItem.size = SizeType (size.x, size.y)
        event.Skip()

    def OnMove(self, event):
        # Calling Skip causes wxWindows to continue processing the event, 
        # which will cause the parent class to get a crack at the event.
        
        if not self.app.ignoreSynchronizeWidget:
            from osaf.pim.structs import PositionType
            # Our first child's block is the FrameWindow where we store size and position
            position = self.GetPosition()
            self.GetChildren()[0].blockItem.position = PositionType(position.x, position.y)
        event.Skip()


class wxMainFrame (wxBlockFrameWindow):
    def __init__(self, *arguments, **keywords):
        super (wxMainFrame, self).__init__(*arguments, **keywords)

        # useful in debugging Mac background drawing problems
        #self.MacSetMetalAppearance(True)

        self.icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        if wx.Platform == "__WXMSW__":
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
            #
            # Unfortunately, for some XP machines msw.remap of 2 doesn't work, even
            # when wx.GetApp().GetComCtl32Version() >= 600 and wx.DisplayDepth() >= 32
            wx.SystemOptions.SetOptionInt ("msw.remap", 0)

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
            busyInfo = wx.BusyInfo (message, wx.GetApp().mainFrame)
            wx.Yield()
            result = method(*args, **kwds)
            del busyInfo
            return result

        def commit(view):
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

        app.ignoreSynchronizeWidget = True

        if wx.Platform == '__WXMAC__':
            app.Bind(wx.EVT_ACTIVATE_APP, None)

        if __debug__:
            displayInfoWhileProcessing (_("Checking repository..."),
                                        app.UIRepositoryView.check)

        displayInfoWhileProcessing (_("Shutting down mail service..."),
                                    Globals.mailService.shutdown)

        displayInfoWhileProcessing (_("Stopping wakeup service..."),
                                    Utility.stopWakeup)

        from osaf import sharing
        displayInfoWhileProcessing (_("Stopping sharing..."),
                                    sharing.interrupt, graceful=False)

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

        feedback.stopRuntimeLog(Globals.options.profileDir)

        # Exit the main loop instead of deleting ourself so as to avoid events
        # firing when object are being deleted
        app.ExitMainLoop()


# We'll create a singleton item to remember our locale, to detect changes.
class LocaleInfo(schema.Item):
    localeName = schema.One(schema.Text)

class wxApplication (wx.App):

    outputWindowClass = feedback.FeedbackWindow
    
    #List of callables for registering to be called during FilterEvent
    filterEventCallables = set()

    def FilterEvent (self, event):
        for callable in self.filterEventCallables:
            callable (event)
        return -1

    def OnInit(self):
        """
        Main application initialization.
        """

        # Python errors caught by wx are emitted via PyErr_Print() which
        # outputs to Python's sys.stderr (bug 6586).
        #
        # Unless --stderr is used, ensure that all stderr output ends
        # up in the logger output.
        #
        # Unless --nocatch is used, Python's sys.stderr is already overriden
        # by the feedback window setup at this point.

        options = Globals.options

        if not options.stderr:

            class _stderr(object):
                def __init__(self, stderr):
                    self.stderr = stderr
                    self.output = []
                    self.logger = logging.getLogger('stderr')
                def __getattr__(self, name):
                    return getattr(self.stderr, name)
                def write(self, string):
                    self.stderr.write(string)
                    if string.endswith('\n'):
                        self.output.append(string.rstrip())
                        self.flush()
                    else:
                        self.output.append(string)
                def flush(self):
                    self.stderr.flush()
                    self.logger.warning(''.join(self.output))
                    self.output = []

            sys.stderr = _stderr(sys.stderr)


        # Ensure that all of wx's C/C++ stdout/stderr output goes to Python's
        # sys.stderr instead (bugs 6120, 6150)

        class _pyLog(wx.PyLog):
            def DoLogString(self, message, timestamp):

                if isinstance(message, unicode):
                    message = message.encode("utf-8", "replace")

                sys.stderr.write('wx output: ')
                sys.stderr.write(message)
                sys.stderr.write('\n')

        wx.Log.SetActiveTarget(_pyLog())

        self.startenv = os.environ.copy()

        # The initI18n can't be initialized until after the App
        # object has been created since initialization creates a
        # wx.Locale object which requires a path that requires
        # GetTraits, which is a method on the App object.
        #
        # Eventually when we get Python egg based localization
        # implemented, this constraint may change
        Utility.initI18n(options)

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

        assert Globals.wxApplication is None, "We can have only one application"
        Globals.wxApplication = self
        self.updateUIInOnIdle = True
        
        # Check the platform, will stop the program if not compatible
        CheckPlatform()

        # Initialize PARCELPATH and sys.path
        parcelPath = Utility.initParcelEnv(options, Globals.chandlerDirectory)
        pluginEnv, pluginEggs = Utility.initPluginEnv(options,
                                                      options.pluginPath)

        # If a magic metakey is down, run the startup options box; it'll
        # modify options as necessary.
        if options.ask or wx.GetMouseState().ControlDown() \
            or (wx.Platform == '__WXMAC__' and wx.GetMouseState().AltDown()):
            from application.dialogs.StartupOptionsDialog import StartupOptionsDialog            
            StartupOptionsDialog.run()

        # Splash Screen:
        # don't show the splash screen when nosplash is set
        splash = None
        if not options.nosplash:
            splashBitmap = self.GetImage("splash.png")
            splash = StartupSplash(None, splashBitmap)
            splash.Show()
            splash.Update()  # Force the window to refresh right now

        # Crypto initialization
        if splash:
            splash.updateGauge('crypto')
        Utility.initCrypto(options.profileDir)

        # The repository opening code was moved to a method so that it can
        # be called again if there is a schema mismatch and the user chooses
        # to reopen the repository in create mode.
        if splash:
            splash.updateGauge('repository')
        repoDir = Utility.locateRepositoryDirectory(options.profileDir, options)

        # Check if this Chandler is an upgrade, will stop the program if backup needed
        # must be done right before initRepository() so it has a fighting chance of
        # detecting the first run after a new install
        if not options.reload and not options.profileDirWasPassedIn and \
           CheckIfUpgraded(options.profileDir, repoDir, options.create):
            from application.dialogs.UpgradeDialog import UpgradeDialog
            UpgradeDialog.run()

        try:
            from application.dialogs.GetPasswordDialog import getPassword
            options.getPassword = getPassword
            view = Utility.initRepository(repoDir, options)
        except RepositoryVersionError, e:
            if self.ShowSchemaMismatchWindow():
                options.create = True
                view = Utility.initRepository(repoDir, options)
            else:
                raise Utility.SchemaMismatchError, e
        except RepositoryPlatformError, e:
            if self.ShowPlatformMismatchWindow(e.args[0], e.args[1]):
                options.create = True
                view = Utility.initRepository(repoDir, options)
            else:
                raise

        self.repository = view.repository

        # Verify Schema Version
        verify, repoVersion, schemaVersion = Utility.verifySchema(view)
        if not verify:
            if self.ShowSchemaMismatchWindow():
                # Blow away the repository
                self.repository.close()
                options.create = True
                view = Utility.initRepository(repoDir, options)
                self.repository = view.repository
            else:
                raise Utility.SchemaMismatchError, (repoVersion, schemaVersion)

        self.UIRepositoryView = view
        view.setMergeFn(otherViewWins)

        # If the locale changed, force index rebuild. (We'll save the locale
        # below if it changed - we'll need the parcels loaded for that)
        if self.localeChanged():
            view.check(True)
            
        # Load Parcels
        if splash:
            splash.updateGauge('parcels')
        Utility.initParcels(options, view, parcelPath)
        Utility.initPlugins(options, view, pluginEnv, pluginEggs)

        # Now that the parcel world exists, save our locale for next time.
        self.saveLocale()
        
        self.Bind(wx.EVT_MENU, self.OnCommand, id=-1)
        self.Bind(wx.EVT_TOOL, self.OnCommand, id=-1)
        self.Bind(wx.EVT_UPDATE_UI, self.OnCommand, id=-1)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroyWindow, id=-1)
        self.Bind(wx.EVT_SHOW, self.OnShow, id=-1)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

        # The Twisted Reactor should be started before other Managers
        # and stopped last.
        if splash:
            splash.updateGauge('twisted')
        Utility.initTwisted()

        mainViewRoot = schema.ns("osaf.views.main", self.UIRepositoryView).MainViewRoot

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

        self.RenderMainView()

        wx.Yield()
        self.UIRepositoryView.commit()

        # Start the WakeupCaller Service
        Utility.initWakeup(self.UIRepositoryView)

        # Start the Chandler Mail Service

        from osaf.mail.mailservice import MailService

        Globals.mailService = MailService(self.UIRepositoryView)
        Globals.mailService.startup()

        if splash:
            splash.Destroy()

        # data loading script execution
        if options.createData:
            import util.GenerateItemsFromFile as GenerateItemsFromFile
            GenerateItemsFromFile.RunScript(self.UIRepositoryView)

        # delay calling OnIdle until now
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        # resize to intended size. (bug 3411)
        self.mainFrame.SetSize(rememberSize)

        # Call UpdateWindowUI before we show the window. UPDATE_UI_FROMIDLE
        # should be set so we don't update menus, since they are done
        # when the menu is pulled down (mac may handle this slightly differently,
        # except we still want UPDATE_UI_FROMIDLE on mac) -- DJA
        self.mainFrame.UpdateWindowUI (wx.UPDATE_UI_FROMIDLE | wx.UPDATE_UI_RECURSE)
        self.needsUpdateUI = False

        self.mainFrame.Show()

        # Set focus so OnIdle won't trigger an unnecessary UpdateWindowUI the
        # first time through. -- DJA
        self.focus = wxWindow_FindFocus()


        # Register sharing activity to be sent to the status bar
        from osaf import sharing
        setStatusMessage = Block.findBlockByName('StatusBar').setStatusMessage
        def _setStatusMessageCallback(*args, **kwds):
            if kwds.get('msg', None) is not None:
                self.PostAsyncEvent(setStatusMessage, kwds['msg'])
        sharing.register(sharing.UPDATE, _setStatusMessageCallback)

        # Fix for Bugs 3720, 3722, 5046, and 5650.  Sets the focus to
        # the first focusable widget in the frame, and also forces a
        # UpdateUI of the menus so the accelerator table will get built.
        if wx.Platform == '__WXGTK__':
            def afterInit():
                self.mainFrame.GetChildren()[0].SetFocus()
                self.mainFrame.UpdateWindowUI(wx.UPDATE_UI_RECURSE)
            wx.CallAfter(afterInit)
                
        if Globals.options.reload is not None:
            wx.CallAfter(self.reload)

        util.timing.end("wxApplication OnInit") #@@@Temporary testing tool written by Morgen -- DJA

        return True    # indicates we succeeded with initialization

    def reload(self):
        from osaf.activity import Activity
        from osaf import dumpreload
        from osaf.framework.blocks.Block import Block

        activity = Activity(_(u"Reload from %(path)s") % {'path': unicode(Globals.options.reload, sys.getfilesystemencoding())})
        activity.started()

        # Don't show the timezone dialog during reload.
        tzprefs = schema.ns('osaf.pim', self.UIRepositoryView).TimezonePrefs
        oldShowPrompt = tzprefs.showPrompt
        tzprefs.showPrompt = False

        try:
            dumpreload.reload(self.UIRepositoryView, Globals.options.reload, 
                              activity=activity)
            activity.completed()
        except Exception, e:
            tzprefs.showPrompt = oldShowPrompt
            logger.exception("Failed to reload file")
            activity.failed(exception=e)
            if isinstance(e, TypeError):
                msg = _(u"Incompatible dump file. Unable to reload.")
            elif isinstance(e, EOFError):
                msg = _(u"Incomplete dump file. Unable to reload.")
            else:
                msg = _(u"Unable to reload file.  See chandler.log for details.")
            dialog = wx.MessageDialog(None, msg,
                _(u"Chandler"), wx.OK | wx.ICON_INFORMATION)
            dialog.ShowModal()
            dialog.Destroy()
            raise

        setStatusMessage = Block.findBlockByName('StatusBar').setStatusMessage
        self.PostAsyncEvent(setStatusMessage, _(u'Items reloaded'))

    def localeChanged(self):
        """
        See if the locale changed since the last time we ran Chandler.
        (Called at startup to see if we need to blow away any locale-sensitive
        repository indexes. Only checks once, then caches the result in a non-
        persistent attribute)
        """
        itChanged = getattr(self, '_localeChanged', None)
        if itChanged is not None:
            return itChanged
        
        localeInfo = self.UIRepositoryView.findPath('//parcels/localeInfo')
        if localeInfo is None:
            return False # we've never recorded a locale, so it can't have changed.
        
        import i18n
        itChanged = localeInfo.localeName != i18n.getLocale()
        self._localeChanged = itChanged
        return itChanged
    
    def saveLocale(self):
        """ Save our locale, if it changed or we hadn't saved it yet """
        # Don't bother saving unless it changed.
        if not getattr(self, '_localeChanged', True):
            return
        import i18n
        localeInfo = self.UIRepositoryView.findPath('//parcels/localeInfo')
        localeName = i18n.getLocale()
        if localeInfo is None:
            localeInfo = LocaleInfo.update(self.UIRepositoryView.getRoot('parcels'),
                                           'localeInfo',
                                           localeName=localeName)
        else:
            localeInfo.localeName = localeName
        
    def RenderMainView (self):
        from osaf.framework.blocks.Block import Block

        mainViewRoot = self.mainFrame.mainViewRoot
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
        #allow callbacks from other threads
        EVT_MAIN_THREAD_CALLBACK(self, self.OnMainThreadCallbackEvent)


    def UnRenderMainView (self):
        #disable callbacks from other threads since they may depend on blocks
        #(i.e. the StatusBar being rendered
        EVT_MAIN_THREAD_CALLBACK(self, None)
        mainViewRoot = self.mainFrame.mainViewRoot.unRender()
        if __debug__:
            from osaf.framework.blocks.Block import Block
            view = self.UIRepositoryView
            for uWatched, watchers in view._watchers.iteritems():
                watchers = watchers.get(view.SUBSCRIBERS)
                if watchers:
                    for watcher in watchers:
                        item = view.findUUID(watcher.watchingItem)
                        assert not isinstance(item, Block)
            
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

    imageCache = {}

    def GetRawImage (self, name):
        """
        Return None if image isn't found, otherwise return the raw image.
        Also look first for platform specific images.
        """
        entry = wxApplication.imageCache.get(name)
        if entry is not None:
            return entry[0]

        root, extension = os.path.splitext (name)

        file = getImage(root + "-" + sys.platform + extension)

        if file is None:
            file = getImage(name)

            if file is None:
                wxApplication.imageCache[name] = [None]
                return None

        image = wx.ImageFromStream (cStringIO.StringIO(file.read()))
        wxApplication.imageCache[name] = [image]
        
        return image

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

            # Similar to below, when the Backspace key is used an as
            # accelerator on wxMac and the currently focused widget is
            # a textctrl then we *must* Skip the event otherwise the
            # text control will either do nothing, or will treat it as
            # a Delete key instead.
            if wx.Platform == '__WXMAC__' and \
                   event.GetEventType() == wx.EVT_MENU.evtType[0] and \
                   getattr(block, 'accel', None) == "Back" and \
                   isinstance(wxWindow_FindFocus(), (wx.TextCtrl, wx.ComboBox)):
                event.Skip()
                return

            #An interesting problem occurs on Mac (see Bug #219). If a dialog is
            #the topmost windw, standard events like cut/copy/paste get processed
            #by this handler instead of the dialog, causing cut/copy/paste to stop
            #working in dialogs. So, instead, if the dialog handles the event we
            #don't want to dispatch it through our CPIA event mechanism.
            #
            #Unfortunately, it's not possible to know if the dialog can process
            #the event. So instead, when the dialog is frontmost, we'll only send
            #events belonging to blocks which have ids in the range we generate
            #with getWidgetID through our commands processing, otherwise we'll send
            #it to the dialog. This can be accomplished by not handling the event
            #here and, instead, calling Skip so it will be passed along to the dialog.
            #
            #Telling if a dialog is the topmost windows is also a bit tricky since
            #wx.GetActiveWindow is implemented only on windows, so wet get the top
            #level parent of whatever window has the focus
    
            if ((0 < wxID < wx.ID_LOWEST) or
                not isinstance (wx.GetTopLevelParent(wxWindow_FindFocus()), wx.Dialog)):

                updateUIEvent = event.GetEventType() == wx.EVT_UPDATE_UI.evtType[0]
                blockEvent = getattr (block, 'event', None)
                # If a block doesn't have an event, it should be an updateUI event
                assert (blockEvent != None or updateUIEvent)

                if blockEvent is not None:
                    arguments = {"wxEvent": event}
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

                        widget = getattr(block, 'widget', None)

                        text = arguments.get ('Text', None)
                        if text is not None and widget is not None:
                            event.SetText (text)
                            # menu items can get here, so check for toolbar item method
                            method = getattr (widget, "OnSetTextEvent", None)
                            if method is not None:
                                # Some widgets, e.g. wxToolBarItems don't properly handle
                                # setting the text of buttons, so we'll handle it here by
                                # calling OnSetTextEvent
                                method (event)

                        bitmap = arguments.get ('Bitmap', None)
                        if bitmap is not None and widget is not None:
                            # menu items can get here, so check for toolbar item method
                            method = getattr (widget, "SetToolBarItemBitmap", None)
                            if method is not None:
                                # The UI requires the bitmap to change; there is no SetBitmap()
                                # method for wx UpdateUIEvents, so just pass the name of the
                                # bitmap as a second parameter to OnSetBitmapEvent()
                                method (bitmap)
                    return
        event.Skip()

    def OnContextMenu(self, event):
        window = wx.FindWindowAtPointer()
        while window is not None:
            blockItem = getattr (window, "blockItem", None)
            if blockItem is not None:
                if hasattr (blockItem, "contextMenu"):
                    blockItem.widget.displayContextMenu(event)
                    return
            window = window.GetParent()
        event.Skip()


    def OnDestroyWindow(self, event):
        from osaf.framework.blocks.Block import Block
        Block.wxOnDestroyWidget (event.GetWindow())
        event.Skip()

    def OnShow(self, event):
        # Giant hack. Calling event.GetEventObject while the object is being created cause the
        # object to get the wrong type because of a "feature" of SWIG. So we need to avoid
        # OnShows in this case by using ignoreSynchronizeWidget as a flag.
        
        if not self.ignoreSynchronizeWidget:
            widget = event.GetEventObject()
            try:
                block = widget.blockItem
            except AttributeError:
                pass
            else:
                if widget.IsShown() != event.GetShow():
                    self.needsUpdateUI = True

        event.Skip()

    def propagateAsynchronousNotifications(self):
        view = self.UIRepositoryView
        view.dispatchQueuedNotifications()

        # synchronize dirtied blocks to reflect changes to the data
        from osaf.framework.blocks.Block import Block
        # make the list first in case it gets tweaked during synchronizeWidget
        dirtyBlocks = [view[theUUID] for theUUID in Block.dirtyBlocks]

        # synchronize affected widgets
        for block in dirtyBlocks:
            if block is not None:
                block.synchronizeWidget()

        Block.dirtyBlocks = set()


    def OnIdle(self, event):
        if self.updateUIInOnIdle:
            self.UIRepositoryView.refresh()
            self.propagateAsynchronousNotifications()
        
        # Adding a handler for catching a set focus event doesn't catch
        # every change to the focus. It's difficult to preprocess every event
        # so we check for focus changes in OnIdle. Also call UpdateUI when
        # focus changes.

        focus = wxWindow_FindFocus()
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

        from osaf.framework import MasterPassword
        from osaf.framework.twisted import waitForDeferred
        waitForDeferred(MasterPassword.clear())

    def restart(self, *args, **kwds):
        """
        Restart the application.

        The application is restarted using the same command it was started
        with.

        Optional arguments passed in via C{args} are appended to the command 
        first.

        Optional named arguments passed in via C{kwds} are appended to the 
        command next - in no particular order - by pre-pending '--' to their
        name which must be a valid command line argument for the application. 

        Argument values may be of any type that can be represented as a
        string. Unicode values are encoded using the system's file system
        encoding. On Windows, values containing space characters are wrapped
        with C{\"} if there are not already. If a keyword argument's value is
        C{True}, only its name is appended to the command.

        For example: app.restart('--backup', restore=path, mvcc=True) would
                     produce a command line containing:
                     C{'--backup --restore=path --mvcc'}
        """

        windows = os.name == 'nt'
        mac = sys.platform == 'darwin'
        linux = sys.platform.startswith('linux')

        encoding = sys.getfilesystemencoding()
        argv = []

        if not __debug__:
            argv.append('-O')

        skip = False
        for arg in sys.argv:
            if skip:
                skip = False
                continue
            if arg in ('-c', '--create'):
                continue
            if arg in ('-r', '--restore'):
                skip = True
                continue
            if arg.startswith('--restore='):
                continue
            if windows and not arg.endswith('"') and ' ' in arg:
                arg = '"%s"' %(arg)
            argv.append(arg)

        for arg in args:
            if isinstance(arg, unicode):
                arg = arg.encode(encoding)
            elif not isinstance(arg, str):
                arg = str(arg)
            if windows and not arg.endswith('"') and ' ' in arg:
                arg = '"%s"' %(arg)
            argv.append(arg)

        for name, value in kwds.iteritems():
            if value is True:
                arg = '--%s' %(name)
            else:
                if isinstance(value, unicode):
                    value = value.encode(encoding)
                elif not isinstance(value, str):
                    value = str(value)
                if windows and not value.endswith('"') and ' ' in value:
                    value = '"%s"' %(value)
                arg = '--%s=%s' %(name, value)
            argv.append(arg)

        if linux:
            for arg in argv:
                if arg in ('-l', '--locale'):
                    break
            else:
                argv.append('--locale=%s' %(getLocaleSet()[0]))

        Utility.stopTwisted()
        self.UIRepositoryView.repository.close()

        try:
            executable = sys.executable
            if windows and ' ' in executable:
                executable = '"%s"' %(executable)

            if mac:
                os.fork()
            argv.append(self.startenv)
            os.execle(sys.executable, executable, *argv)
        except OSError, e:
            from errno import EOPNOTSUPP
            if not mac or e.args[0] != EOPNOTSUPP:
                logger.exception("while restarting")
        except:
            logger.exception("while restarting")
        finally:
            sys.exit(0)

    def OnMainThreadCallbackEvent(self, event):
        """
        Fire off a custom event handler
        """
        event.lock.release()
        event.target(*event.args, **event.kwds)
        event.Skip()

    def PostAsyncEvent(self, callback, *args, **kwds):
        """
        Post an asynchronous event that will call 'callback' with 'data'
        """
        evt = MainThreadCallbackEvent(callback, *args, **kwds)
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

        self.UIRepositoryView.refresh() # bring changes across from the other thread/view

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
        self.PostAsyncEvent (self._DispatchItemMethod, item, 
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

    def ShowSchemaMismatchWindow(self):
        logger.info("Schema version of repository doesn't match app")

        message = \
_(u"""Your repository was created by an older version of Chandler. In the future we will support migrating data between versions, but until then, when the schema changes we need to remove all data from your repository.

Would you like to remove all data from your repository?
""")

        dialog = wx.MessageDialog(None, message, _(u"Cannot open repository"),
            wx.YES_NO | wx.ICON_INFORMATION | wx.NO_DEFAULT)
        response = dialog.ShowModal()
        dialog.Destroy()
        return response == wx.ID_YES

    def ShowPlatformMismatchWindow(self, origName, currentName):
        logger.info("Repository platform mismatch: (orig %s vs now %s)",
                    origName, currentName)

        osNames = { 'darwin-i386': 'Intel Mac OS X',
                    'darwin-ppc': 'Power PC Mac OS X',
                    'linux-i386': 'Linux',
                    'win32-i386': 'Windows XP' }
        origName = osNames.get(origName, origName)
        currentName = osNames.get(currentName, currentName)

        message = _(u"""Your Chandler data was created on %(origName)s and is incompatible with Chandler on %(currentName)s. To transfer your data over to %(currentName)s:

1. On your %(origName)s computer, start up Chandler and go to the File menu to 'Back up' your data.

2. Move the back up file to your %(currentName)s computer.

3. On your %(currentName)s computer, start up Chandler and select the 'Yes' option you see below.

4. Go to the File menu and 'Restore' your data by pointing Chandler to the back up file you transferred over from your %(origName)s computer.

Start Chandler with a fresh data repository ?""") %{'origName': origName, 'currentName': currentName}

        dialog = wx.MessageDialog(None, message,
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
        if isinstance(possibleItem, schema.Annotation):
            self.annotationClass = type(possibleItem)
            possibleItem = possibleItem.itsItem

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

        item = wx.GetApp().UIRepositoryView.findUUID(theUUID)
        try:
            return self.annotationClass(item)
        except (TypeError, AttributeError):
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

        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        self.SetTitle(_(u'Chandler starting...'))
        
        # Progress Text dictionary
        #                    name            weight      text
        self.statusTable = {'crypto'      : ( 5,  _(u"Initializing crypto services")),
                            'repository'  : ( 10, _(u"Opening the repository")),
                            'parcels'     : ( 15, _(u"Loading parcels")),
                            'twisted'     : ( 10, _(u"Starting Twisted")),
                            'globalevents': ( 15, _(u"Registering global events")),
                            'mainview'    : ( 10, _(u"Rendering the main view"))}

        # Font to be used for the progress text
        font = wx.Font(fontsize, wx.SWISS, wx.NORMAL, wx.NORMAL)
        
        # Add title text
        titleText = wx.StaticText(self, -1, _(u"Experimentally Usable Calendar"))
        titleText.SetBackgroundColour(wx.WHITE)
        sizer.Add(titleText, 1, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, padding)
        titleText.SetFont(wx.Font(fontsize, wx.SWISS, wx.NORMAL, wx.NORMAL))

        # Load the splash screen picture.
        # The picture will set the width of the splash screen, 
        # all other elements are horizontally centered on it (except for the progress "%" display)
        bitmap = wx.StaticBitmap(self, -1, bmp)
        sizer.Add(bitmap, 0, wx.ALIGN_CENTER, 0)

        # Add Chandler text
        text1 = wx.StaticText(self, -1, (u"Chandler\u2122"))
        text1.SetBackgroundColour(wx.WHITE)
        sizer.Add(text1, 1,  wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, padding)
        text1.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))

        # Add Version text
        text2 = wx.StaticText(self, -1,
                              _(u"Version %(version)s") % { 'version': version })
        text2.SetBackgroundColour(wx.WHITE)
        sizer.Add(text2, 1,  wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, padding)
        text2.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL))

        # Add OSAF text
        text3 = wx.StaticText(self, -1, (u"Open Source Applications Foundation"))
        text3.SetBackgroundColour(wx.WHITE)
        sizer.Add(text3, 1,  wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, padding)
        text3.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))

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

def CheckPlatform():
    """
    Check that the platforms you're running and the one the code has been compiled for match.
    If they don't, the program stops with sys.exit().
    """
    from Utility import getPlatformName # This is the executing platform name
    try:
        from version import platform # This is the compiled platform name
    except ImportError:
        # If the platform is not specified in version.py, you're running a dev version from
        # code. In that case, we suppose you know what you're doing so 
        # the test will pass and you're on your own...
        platform = getPlatformName()
    if getPlatformName() != platform:
        # Prompt the user that we're going to exit
        wx.MessageBox(_(u'This application has been compiled for another platform. Please download the correct package from OSAF website.'),
                      _(u'Chandler will exit'))
        # Stop the program. Somewhat unclean but since nothing can be done safely
        # or even should be done (could crash anytime), the best is to just exit when
        # we still can...
        sys.exit(0)
    

def CheckIfUpgraded(profileDir, repoDir, createRepo):
    """
    Check to see if Chandler is starting for the first time.
    If it is and we can locate an older Chandler's repository, prompt the user to check
    if they want to backup their previous data
    
    The following will trigger an upgrade warning
        If the profile dir and repository directory exists but --create present
        If the profile dir exists but the repository is not found
        Either of the above and there are more than zero profile version directories present
    """
    import glob

    upgraded    = False
    profileBase = os.path.dirname(os.path.dirname(profileDir))

    dirlist = glob.glob(os.path.join(profileBase, 'Chandler*.dump'))

    if os.path.isdir(profileDir):
        if os.path.isdir(repoDir):
            if len(dirlist) > 0 and createRepo:
                upgraded = True
        else:
            upgraded = True
    else:
        if len(dirlist) > 0:
            upgraded = True

    return upgraded

