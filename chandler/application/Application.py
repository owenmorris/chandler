__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import gettext, os, sys, threading, time

from new import classobj
import wx
import Globals
import application.Parcel
from repository.persistence.DBRepository import DBRepository
from repository.persistence.RepositoryError \
     import VersionConflictError, MergeError
from crypto import Crypto
import logging as logging
import cStringIO
import CPIAScript

logger = logging.getLogger('App')
logger.setLevel(logging.INFO)

#@@@Temporary testing tool written by Morgen -- DJA
import util.timing

# Increment this constant whenever you change the schema:
SCHEMA_VERSION = "14"

"""
  Event used to post callbacks on the UI thread
"""
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
        assert len(parts) >= 2, "Delegate %s isn't a module and class" % myMixinClassImportPath
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


class MainFrame(wx.Frame):
    def __init__(self, *arguments, **keywords):
        super (MainFrame, self).__init__(*arguments, **keywords)

        # useful in debugging Mac background drawing problems
        # self.MacSetMetalAppearance(True)

        self.SetBackgroundColour (wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)

    def OnClose(self, event):
        """
          For some strange reason when there's an idle handler on the
        application the mainFrame windows doesn't get destroyed, so
        we'll remove the handler
        """
        wx.GetApp().Bind(wx.EVT_IDLE, None)
        """
          When we quit, as each wxWidget window is torn down our handlers that
        track changes to the selection are called, and we don't want to count
        these changes, since they weren't caused by user actions.
        """
        wx.GetApp().ignoreSynchronizeWidget = True
        wx.GetApp().frame = None
        Globals.mainViewRoot.frame = None
        self.Destroy()

    def OnSize(self, event):
        """
          Calling Skip causes wxWindows to continue processing the event, 
        which will cause the parent class to get a crack at the event.
        """
        if not wx.GetApp().ignoreSynchronizeWidget:
            Globals.mainViewRoot.size.width = self.GetSize().x
            Globals.mainViewRoot.size.height = self.GetSize().y
            Globals.mainViewRoot.setDirty(Globals.mainViewRoot.VDIRTY, 'size', Globals.mainViewRoot._values)   # Temporary repository hack -- DJA
        event.Skip()

    def OnMove(self, event):
        """
          Calling Skip causes wxWindows to continue processing the event, 
        which will cause the parent class to get a crack at the event.
        """
        if not wx.GetApp().ignoreSynchronizeWidget:
            Globals.mainViewRoot.position.x = self.GetPosition().x
            Globals.mainViewRoot.position.y = self.GetPosition().y
            Globals.mainViewRoot.setDirty(Globals.mainViewRoot.VDIRTY, 'position', Globals.mainViewRoot._values)   # Temporary repository hack -- DJA
        event.Skip()


class wxApplication (wx.App):
    """
      PARCEL_IMPORT defines the import directory containing parcels
    relative to chandlerDirectory where os separators are replaced
    with "." just as in the syntax of the import statement.
    """
    PARCEL_IMPORT = 'parcels'

    def OnInit(self):
        util.timing.begin("wxApplication OnInit") #@@@Temporary testing tool written by Morgen -- DJA
        """
          Main application initialization.
        """
        self.needsUpdateUI = True
        self.ignoreSynchronizeWidget = True
        self.focus = None

        wx.InitAllImageHandlers()
        """
          Disable automatic calling of UpdateUIEvents. We will call them
        manually when blocks get rendered, change visibility, etc.
        """
        wx.UpdateUIEvent.SetUpdateInterval (-1)
        """
          Install a custom displayhook to keep Python from setting the global
        _ (underscore) to the value of the last evaluated expression.  If 
        we don't do this, our mapping of _ to gettext can get overwritten.
        This is useful in interactive debugging with PyCrust.
        """
        def _displayHook(obj):
            sys.stdout.write(str(obj))

        sys.displayhook = _displayHook

        assert Globals.wxApplication == None, "We can have only one application"
        Globals.wxApplication = self
        """
          Load the parcels which are contained in the PARCEL_IMPORT directory.
        It's necessary to add the "parcels" directory to sys.path in order
        to import parcels. Making sure we modify the path as early as possible
        in the initialization as possible minimizes the risk of bugs.
        """
        parcelPath = []
        parcelPath.append(os.path.join(Globals.chandlerDirectory,
                          self.PARCEL_IMPORT.replace ('.', os.sep)))

        """
        If PARCELPATH env var is set, append those directories to the
        list of places to look for parcels.
        """
        if Globals.options.parcelPath:
            for directory in Globals.options.parcelPath.split(os.pathsep):
                if os.path.isdir(directory):
                    parcelPath.append(directory)
                else:
                    logger.warning("'%s' not a directory; skipping" % directory)

        insertionPoint = 1
        for directory in parcelPath:
            sys.path.insert(insertionPoint, directory)
            insertionPoint += 1

        logger.info("Using PARCELPATH %s" % parcelPath)

        """
          Splash Screen.

          We don't show the splash screen when nocatchis set, which is typically
        on when running in the debugger. Also, when in the debugger the splash
        screen gets stuck on top of all other windows on some platforms, e.g. Linux,
        so we'll use the nocatch flag to also turn off the splash screen. It didn't
        seem worth adding yet another command line flag for just turning off the
        splash screen.
        """
        splash = None
        if not (__debug__ and application.Globals.options.nocatch):
            splashBitmap = self.GetImage ("splash.png")
            splash=StartupSplash(None, splashBitmap)
            splash.Show()
            wx.Yield() #let the splash screen render itself
        """
          Setup internationalization
        To experiment with a different locale, try 'fr' and wx.LANGUAGE_FRENCH
        """
        os.environ['LANGUAGE'] = 'en'
#        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        """
          @@@ Sets the python locale, used by wx.CalendarCtrl and mxDateTime
        for month and weekday names. When running on Linux, 'en' is not
        understood as a locale, nor is 'fr'. On Windows, you can try 'fr'.
        locale.setlocale(locale.LC_ALL, 'en')
        """
#        wx.Locale_AddCatalogLookupPathPrefix('locale')
#        self.locale.AddCatalog('Chandler.mo')
        gettext.install('chandler', 'locale')
        """
          Crypto initialization
        """
        if splash: splash.updateGauge('crypto')
        Globals.crypto = Crypto.Crypto()
        Globals.crypto.init(Globals.options.profileDir)
        """
          Open the repository.
        Load the Repository after the path has been altered, but before
        the parcels are loaded. 
        """
        if splash: splash.updateGauge('repository')
        if Globals.options.profileDir:
            path = os.sep.join([Globals.options.profileDir, '__repository__'])
        else:
            path = '__repository__'

        options = Globals.options
        kwds = { 'stderr': options.stderr,
                 'ramdb': options.ramdb,
                 'create': True,
                 'recover': options.recover,
                 'exclusive': True,
                 'refcounted': True }

        if Globals.options.repo:
            kwds['fromPath'] = Globals.options.repo
        wx.Yield()
        self.repository = DBRepository(path)

        if Globals.options.create:
            self.repository.create(**kwds)
        else:
            self.repository.open(**kwds)

        wx.Yield()

        self.UIRepositoryView = self.repository.getCurrentView()

        if not self.UIRepositoryView.findPath('//Packs/Schema'):
            """
              Bootstrap an empty repository by loading only the stuff that
            can't be loaded in a data parcel.
            """
            self.UIRepositoryView.loadPack("repository/packs/schema.pack")
            wx.Yield()
            self.UIRepositoryView.loadPack("repository/packs/chandler.pack")
        """
          Load Parcels
        """
        if splash: splash.updateGauge('parcels')
        wx.Yield()

        # Fetch the top-level parcel item to check schema version info
        parcelRoot = self.repository.findPath("//parcels")
        if parcelRoot is not None:
            if (not hasattr(parcelRoot, 'version') or
                parcelRoot.version != SCHEMA_VERSION):
                logger.info("Schema version of repository doesn't match app")
                raise SchemaMismatchError, path

        application.Parcel.Manager.get(self.UIRepositoryView,
                                       path=parcelPath).loadParcels()

        # Record the current schema version into the repository
        parcelRoot = self.repository.findPath("//parcels")
        parcelRoot.version = SCHEMA_VERSION

        EVT_MAIN_THREAD_CALLBACK(self, self.OnMainThreadCallbackEvent)

        """
          The Twisted Reactor should be started before other Managers
          and stopped last.
        """
        if splash: splash.updateGauge('twisted')
        import osaf.framework.twisted.TwistedReactorManager as TwistedReactorManager 
        self.__twistedReactorManager = TwistedReactorManager.TwistedReactorManager()
        self.__twistedReactorManager.startReactor()

        mainViewRoot = self.LoadMainViewRoot(delete=Globals.options.refreshui)
        if (mainViewRoot.position.x == -1 and mainViewRoot.position.y == -1):
            position = wx.DefaultPosition
        else:
            position = (mainViewRoot.position.x, mainViewRoot.position.y)
        self.mainFrame = MainFrame(None,
                                   -1,
                                   "Chandler",
                                   pos=position,
                                   size=(mainViewRoot.size.width, mainViewRoot.size.height),
                                   style=wx.DEFAULT_FRAME_STYLE)
        mainViewRoot.frame = self.mainFrame
        """
          Register to some global events for name lookup.
        """
        if splash: splash.updateGauge('globalevents')
        globalEvents = self.UIRepositoryView.findPath('//parcels/osaf/framework/blocks/GlobalEvents')
        from osaf.framework.blocks.Block import Block
        Block.addToNameToItemUUIDDictionary (globalEvents.eventsForNamedDispatch,
                                             Block.eventNameToItemUUID)

        self.ignoreSynchronizeWidget = False
        if splash: splash.updateGauge('mainview')
        self.RenderMainView ()

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
            
        if splash: splash.Destroy()
        #OnDestroyWindow Binding has to appear after splash.Destroy
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_MENU, self.OnCommand, id=-1)
        self.Bind(wx.EVT_TOOL, self.OnCommand, id=-1)
        self.Bind(wx.EVT_UPDATE_UI, self.OnCommand, id=-1)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroyWindow, id=-1)
        self.Bind(wx.EVT_SHOW, self.OnShow, id=-1)

        self.mainFrame.Show()


        """Start the WakeupCaller Service"""
        from osaf.framework.wakeup.WakeupCaller import WakeupCaller
        Globals.wakeupCaller = WakeupCaller(self.UIRepositoryView.repository)
        Globals.wakeupCaller.startup()

        """Start the Chandler Mail Service"""
        from osaf.mail.mailservice import MailService
        Globals.mailService = MailService(self.UIRepositoryView.repository)
        Globals.mailService.startup()

        util.timing.end("wxApplication OnInit") #@@@Temporary testing tool written by Morgen -- DJA


        return True                     #indicates we succeeded with initialization

    def LoadMainViewRoot (self, delete=False):
        """
          The main view's root is the only item in the soup (e.g. //userdata) with a name
          that isn't it's UUID. We need the name to look it up. If the main view's root
          isn't found then make a copy into the soup with the right name.
        """

        mainViewRoot = self.UIRepositoryView.findPath('//userdata/MainViewRoot')
        if mainViewRoot and delete:
            try:
                frame = mainViewRoot.frame
            except AttributeError:
                pass
            self.UIRepositoryView.refresh()
            mainViewRoot.delete (cloudAlias="default")
            self.UIRepositoryView.commit()
            mainViewRoot = None
        if mainViewRoot is None:
            template = self.UIRepositoryView.findPath ("//parcels/osaf/views/main/MainViewRoot")
            mainViewRoot = template.copy (parent = self.UIRepositoryView.findPath ("//userdata"),
                                          name = "MainViewRoot",
                                          cloudAlias="default")
            try:
                mainViewRoot.frame = frame
            except UnboundLocalError:
                pass
        Globals.mainViewRoot = mainViewRoot
        return mainViewRoot

    def RenderMainView (self):
        mainViewRoot = Globals.mainViewRoot
        mainViewRoot.lastDynamicBlock = False
        assert len (Globals.views) == 0
        mainViewRoot.render()
        """
          We have to wire up the block mainViewRoot, it's widget and sizer to a new
        sizer that we add to the mainFrame.
        """
        sizer = wx.BoxSizer (wx.HORIZONTAL)
        self.mainFrame.SetSizer (sizer)
        from osaf.framework.blocks.Block import wxRectangularChild
        sizer.Add (mainViewRoot.widget,
                   mainViewRoot.stretchFactor, 
                   wxRectangularChild.CalculateWXFlag(mainViewRoot), 
                   wxRectangularChild.CalculateWXBorder(mainViewRoot))
        sizer.Layout()

    def UnRenderMainView (self):
        mainViewRoot = Globals.mainViewRoot.unRender()
        assert len (Globals.views) == 0
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
        root = "application/images/" + root
        try:
            file = open(root + "-" + sys.platform + extension, "rb")
        except IOError:
            try:
                file = open(root + extension, "rb")
            except IOError:
                return None
        stream = cStringIO.StringIO (file.read())
        return wx.ImageFromStream (stream)

    def GetImage (self, name):
        """
          Return None if image isn't found, otherwise loads a bitmap.
        Looks first for platform specific bitmaps.
        """
        rawImage = self.GetRawImage (name)
        if rawImage is None:
            return None
        return wx.BitmapFromImage (rawImage)


    def OnCommand(self, event):
        """
          Catch commands and pass them along to the blocks.
        Our events have ids between MINIMUM_WX_ID and MAXIMUM_WX_ID
        Delay imports to avoid circular references.
        """
        from osaf.framework.blocks.Block import Block

        wxID = event.GetId()

        if wxID >= Block.MINIMUM_WX_ID and wxID <= Block.MAXIMUM_WX_ID:
            block = Block.widgetIDToBlock (wxID)
            updateUIEvent = event.GetEventType() == wx.EVT_UPDATE_UI.evtType[0]
            try:
                blockEvent = block.event
            except AttributeError:
                """
                  Ignore blocks that don't have events.
                """
                assert updateUIEvent
            else:
                arguments = {}
                if updateUIEvent:
                    arguments ['UpdateUI'] = True
                else:
                    try:
                        arguments ['buttonState'] = event.GetEventObject().GetToolState (wxID)
                    except AttributeError: 
                        pass
 
                block.post (blockEvent, arguments)
 
                if updateUIEvent:
                    try:
                        event.Check (arguments ['Check'])
                    except KeyError:
                        pass

                    try:
                        enable = arguments ['Enable']
                    except KeyError:
                        enable = True
                    event.Enable (enable)

                    try:
                        text = arguments ['Text']
                    except KeyError:
                        pass
                    else:
                        event.SetText (text)
                        widget = block.widget
                        """
                          Some widgets, e.g. wxToolbarItems don't properly handle
                        setting the text of buttons, so we'll handle it here by
                        looking for the method OnSetTextEvent to handle it
                        """
                        try:
                            method = widget.OnSetTextEvent
                        except AttributeError:
                            pass
                        else:
                            method (event)
        else:
            event.Skip()

    def OnDestroyWindow(self, event):
        from osaf.framework.blocks.Block import Block
        Block.wxOnDestroyWidget (event.GetWindow())
        event.Skip()

    def OnShow(self, event):
        """
          Giant hack. Calling event.GetEventObject while the object is being created cause the
        object to get the wrong type because of a "feature" of SWIG. So we need to avoid
        OnShows in this case by using ignoreSynchronizeWidget as a flag.
        """
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

    def OnIdle(self, event):
        """
          Adding a handler for catching a set focus event doesn't catch
        every change to the focus. It's difficult to preprocess every event
        so we check for focus changes in OnIdle. Also call UpdateUI when
        focus changes
        """

        def updateOnIdle():
            """
            This function is used to generate notifications of items that were changed
            in the current (repository) view since the last time through the idle loop
            """
            the_view = self.repository.view  # cache the view for performance
            the_view.refresh() # pickup changes from other threads
    
            changes = []
            
            def mapChangesCallable(item, version, status, literals, references):
                """
                closure to be passed to mapChanges that will produce a list of
                changed items in the same format needed by 
                repository.query.Query.queryCallback
                """
                changes.append((item.itsUUID, "changed", {}))
            
            # call mapChanges with flag that prevents seeing changes we've seen before
            the_view.mapChanges(mapChangesCallable, True)
    
            # grab the list of subscribed callbacks and notify them.
            if changes:
                for i in self.repository._notifications: 
                    i(the_view, changes, "changeonly")

        focus = wx.Window_FindFocus()
        if self.focus != focus:
            self.focus = focus
            self.needsUpdateUI = True

        try:
            updateOnIdle()
        except MergeError, e:
            if e.getReasonCode() == MergeError.BUG:
                logger.warning("Changes cancelled due to merge error: %s", e)
                self.repository.view.cancel()
                self.needsUpdateUI = True
            else:
                raise

        if self.needsUpdateUI:
            try:
                self.mainFrame.UpdateWindowUI (wx.UPDATE_UI_FROMIDLE | wx.UPDATE_UI_RECURSE)
            finally:
                self.needsUpdateUI = False

        # Give CPIA Script a chance to execute a script
        CPIAScript.RunScript()

        event.Skip()

    def OnExit(self):
        """
          Main application termination.
        """
        if __debug__:
            wx.GetApp().UIRepositoryView.repository.check()

        Globals.mailService.shutdown()
        Globals.wakeupCaller.shutdown()
        self.__twistedReactorManager.stopReactor()
        """
          Since Chandler doesn't have a save command and commits typically happen
        only when the user completes a command that changes the user's data, we
        need to add a final commit when the application quits to save data the
        state of the user's world, e.g. window location and size.
        """

        try:
            try:
                wx.GetApp().UIRepositoryView.commit()
            except VersionConflictError, e:
                wx.GetApp().UIRepositoryView.logger.warning(str(e))
        finally:
            wx.GetApp().UIRepositoryView.repository.close()

        Globals.crypto.shutdown()

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
        Does a repository refresh to get the changes across from the other thread.
        """
        wx.GetApp().UIRepositoryView.refresh () # bring changes across from the other thread/view

        # unwrap the target item and find the method to call
        item = transportItem.unwrap ()
        try:
            member = getattr (type(item), methodName)
        except AttributeError:
            logger.warning ("CallItemMethodAsync couldn't find method %s on item %s" % (methodName, str (item)))
            return

        # unwrap the transportArgs
        args = []
        for wrapper in transportArgs:
            args.append (wrapper.unwrap())

        # unwrap the keyword args
        for key, wrapper in keyArgs.items():
            keyArgs[key] = wrapper.unwrap()

        # call the member with params
        member (item, *args, **keyArgs)

    def CallItemMethodAsync (self, item, methodName, *args, **keyArgs):
        """
          Post an asynchronous event that will call a method by name in an item.
        Communication between threads is tricky.  This method will convert
        all parameters into UUIDs for transport during the event posting,
        and they will be converted back to items when the event is received.
        However you will have to do a commits in the non-UI thread for the data
        to pass across smoothly.  The UI thread will do a commit to get
        the changes on its side.  
        Also, items that are not simple arguments or keyword arguments will 
        not be converted to/from UUID.
        @param item: an C{Item} whose method we wish to call
        @type item: C{Item}
        @param methodName: the name of the method to call
        @type methodName: C{String}
        All other args are passed across to the other thread.
        """
        # convert the item whose method we're calling
        transportItem = TransportWrapper (item)
        # convert all the arg items
        transportArgs = []
        for anItem in args:
            transportArgs.append (TransportWrapper (anItem))
        # convert all dictionary items
        for key,value in keyArgs.items():
            keyArgs[key] = TransportWrapper (value)
        wx.GetApp().PostAsyncEvent (self._DispatchItemMethod, transportItem, 
                                    methodName, transportArgs, keyArgs)

    def ShowDebuggerWindow(self):
        import wx.py
        rootObjects = {
         "globals" : application.Globals,
         "parcelsRoot" : self.UIRepositoryView.findPath("//parcels"),
         "repository" : self.UIRepositoryView.repository,
         "wxApplication" : self,
        }
        self.crustFrame = wx.py.crust.CrustFrame(rootObject=rootObjects,
         rootLabel="Chandler")
        self.crustFrame.SetSize((700,700))
        self.crustFrame.Show(True)

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
          Construct a TrasportWrapper from an object.
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
            item = Globals.mainViewRoot.findUUID (theUUID)
            return item

class StartupSplash(wx.Frame):
    def __init__(self, parent, bmp):
        height = bmp.GetHeight()
        width = bmp.GetWidth()
        msgHeight = 20
        gaugeHeight = 15
        gaugeBorder = 1
        gaugeWidth = min(300, width - 100)
        padding = 5
        frameSize = wx.Size(width, height + msgHeight + gaugeHeight + 2*padding)
        wx.Frame.__init__(self, size=frameSize, parent=parent, style=wx.SIMPLE_BORDER)
        self.CenterOnScreen()
        self.SetBackgroundColour(wx.WHITE)
        
        #                    name            weight      text
        self.statusTable = {'crypto'      : ( 5,  "Initializing crypto services"),
                            'repository'  : ( 10,  "Opening the repository"),
                            'parcels'     : ( 15, "Loading parcels"),
                            'twisted'     : ( 10,  "Starting Twisted"),
                            'globalevents': ( 15,  "Registering global events"),
                            'mainview'    : ( 10,  "Rendering the main view")}
        
        self.gaugeTicks = reduce(lambda x, y: x + y[0], self.statusTable.values(), 0)
        
        wx.StaticBitmap(self, -1, bmp, wx.Point(0, 0), wx.Size(width, height))
        self.progressText = wx.StaticText(self, -1, "", wx.Point(0, height + padding), 
                                wx.Size(width, msgHeight),
                                wx.ALIGN_CENTRE | wx.ST_NO_AUTORESIZE)
        self.progressText.SetBackgroundColour(wx.WHITE)
        gaugeBox = wx.Window(self, -1, wx.Point((width - gaugeWidth)/2, height + msgHeight + padding), 
                        wx.Size(gaugeWidth, gaugeHeight))
        gaugeBox.SetBackgroundColour(wx.BLACK)
        self.gauge = wx.Gauge(gaugeBox, -1,
                              range = self.gaugeTicks,
                              style = wx.GA_HORIZONTAL,#|wx.GA_SMOOTH,
                              pos   = (gaugeBorder, gaugeBorder),
                              size  = (gaugeWidth - 2 * gaugeBorder,
                                       gaugeHeight - 2 * gaugeBorder))
        self.gauge.SetBackgroundColour(wx.Colour(0x33, 0x33, 0x33))
        self.workingTicks = 0
        self.completedTicks = 0
        self.timerTicks = 0
        
        #Without a lock, spawning a new thread modestly improves the smoothness
        #of the gauge, but then Destroy occasionally raises an exception and the
        #gauge occasionally moves backwards, which is unsettling. Unfortunately,
        #my feeble attempt at using a lock seemed to create a race condition.
        
        #threading._start_new_thread(self.timerLoop, ())
        
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
            self.gauge.SetValue(self.completedTicks + self.timerTicks)
            self.progressText.SetLabel(self.statusTable[type][1])
            self.workingTicks = self.statusTable[type][0]
        wx.Yield()

    def Destroy(self):
        self._startup = False
        self.gauge.SetValue(self.gaugeTicks)
        wx.Yield()
        time.sleep(.25) #give the user a chance to see the gauge reach 100%
        wx.Frame.Destroy(self)

class SchemaMismatchError(Exception):
    """ The schema version in the repository doesn't match the application. """
    def __init__(self, path):
        self.path = path
