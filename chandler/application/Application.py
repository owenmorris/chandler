__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import gettext, os, sys, threading
from new import classobj
import wx
import Globals
from repository.util.UUID import UUID
import application.Parcel
from repository.persistence.XMLRepository import XMLRepository
from crypto import Crypto
import logging as logging

#@@@Temporary testing tool written by Morgen -- DJA
import tools.timing


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
        self.SetBackgroundColour (wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnClose(self, event):
        """
          For some strange reason when there's an idle handler on the
        application the mainFrame windows doesn't get destroyed, so
        we'll remove the handler
        """
        Globals.wxApplication.Bind(wx.EVT_IDLE, None)
        """
          When we quit, as each wxWidget window is torn down our handlers that
        track changes to the selection are called, and we don't want to count
        these changes, since they weren't caused by user actions.
        """
        Globals.wxApplication.ignoreSynchronizeWidget = True
        Globals.wxApplication.mainFrame = None
        self.Destroy()

    def OnSize(self, event):
        """
          Calling Skip causes wxWindows to continue processing the event, 
        which will cause the parent class to get a crack at the event.
        """
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            Globals.mainView.size.width = self.GetSize().x
            Globals.mainView.size.height = self.GetSize().y
            Globals.mainView.setDirty(Globals.mainView.VDIRTY, 'size')   # Temporary repository hack -- DJA
        event.Skip()

class wxApplication (wx.App):
    """
      PARCEL_IMPORT defines the import directory containing parcels
    relative to chandlerDirectory where os separators are replaced
    with "." just as in the syntax of the import statement.
    """
    PARCEL_IMPORT = 'parcels'

    def OnInit(self):
        """
          Main application initialization.
        """
        tools.timing.begin("wxApplication OnInit") #@@@Temporary testing tool written by Morgen -- DJA
        """
          Disable automatic calling of UpdateUIEvents. We will call them
        manually when blocks get rendered, change visibility, etc.
        """
        wx.UpdateUIEvent.SetUpdateInterval (-1)
        self.needsUpdateUI = True
        """
          Install a custom displayhook to keep Python from setting the global
        _ (underscore) to the value of the last evaluated expression.  If 
        we don't do this, our mapping of _ to gettext can get overwritten.
        This is useful in interactive debugging with PyCrust.
        """
        def _displayHook(obj):
            sys.stdout.write(str(obj))

        sys.displayhook = _displayHook
        """
          Find the directory that Chandler lives in by looking up the file that
        the application module lives in.
        """
        pathComponents = sys.modules['application'].__file__.split (os.sep)
        assert len (pathComponents) > 3
        Globals.chandlerDirectory = os.sep.join(pathComponents[0:-2])

        os.chdir (Globals.chandlerDirectory)
        assert Globals.wxApplication == None, "We can have only one application"
        Globals.wxApplication = self
        self.ignoreSynchronizeWidget = True

        wx.InitAllImageHandlers()
        """
          Splash Screen
        """
        splashBitmap = self.GetImage ("splash")
        splash = wx.SplashScreen(splashBitmap,
                                 wx.SPLASH_CENTRE_ON_SCREEN|wx.SPLASH_TIMEOUT,
                                 6000, None, -1, wx.DefaultPosition,
                                 wx.DefaultSize,
                                 wx.SIMPLE_BORDER|wx.FRAME_NO_TASKBAR)
        splash.Show()

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
          Load the parcels which are contained in the PARCEL_IMPORT directory.
        It's necessary to add the "parcels" directory to sys.path in order
        to import parcels. Making sure we modify the path as early as possible
        in the initialization as possible minimizes the risk of bugs.
        """
        parcelDir = os.path.join(Globals.chandlerDirectory,
                                 self.PARCEL_IMPORT.replace ('.', os.sep))
        sys.path.insert (1, parcelDir)

        """
        If PARCELDIR env var is set, put that
        directory into sys.path before any modules are imported.
        """
        debugParcelDir = None
        if os.environ.has_key('PARCELDIR'):
            path = os.environ['PARCELDIR']
            if path and os.path.exists(path):
                print "Using PARCELDIR environment variable (%s)" % path
                debugParcelDir = path
                sys.path.insert (2, debugParcelDir)

        Globals.crypto = Crypto.Crypto()
        Globals.crypto.init()

        """
          Open the repository.
        -create argument forces a new repository.
        Load the Repository after the path has been altered, but before
        the parcels are loaded. 
        """
        Globals.repository = XMLRepository("__repository__")

        kwds = { 'stderr': '-stderr' in sys.argv,
                 'ramdb': '-ramdb' in sys.argv,
                 'create': True,
                 'recover': True }

        if '-repo' in sys.argv:
            for i in range(0, len(sys.argv)):
                if sys.argv[i] == '-repo':
                    path = sys.argv[i+1]
                    kwds['fromPath'] = path

        if '-create' in sys.argv:
            Globals.repository.create(**kwds)
        else:
            Globals.repository.open(**kwds)

        if not Globals.repository.findPath('//Packs/Schema'):
            """
              Bootstrap an empty repository by loading only the stuff that
            can't be loaded in a data parcel.
            """
            Globals.repository.loadPack("repository/packs/schema.pack")

        """
          Create the notification manager. Start later.
        """
        from osaf.framework.notifications.NotificationManager import NotificationManager
        Globals.notificationManager = NotificationManager()
        Globals.notificationManager.PrepareSubscribers()

        # Load Parcels
        parcelSearchPath = [ parcelDir ]
        if debugParcelDir:
            parcelSearchPath.append( debugParcelDir )

        application.Globals.parcelManager = \
         application.Parcel.Manager.getManager(path=parcelSearchPath)
        application.Globals.parcelManager.loadParcels()

        Globals.repository.commit()

        EVT_MAIN_THREAD_CALLBACK(self, self.OnMainThreadCallbackEvent)

        """
          The Twisted Reactor should be started before other Managers
          and stopped last.
        """
        import osaf.framework.twisted.TwistedReactorManager as TwistedReactorManager 
        self.__twistedReactorManager = TwistedReactorManager.TwistedReactorManager()
        self.__twistedReactorManager.startReactor()

        """
          Start the notification manager
        """
        Globals.notificationManager.PrepareSubscribers()

        # It is important to commit before the task manager starts
        Globals.repository.commit()
        from osaf.framework.tasks.TaskManager import TaskManager
        Globals.taskManager = TaskManager()
        Globals.taskManager.start()

        self.focus = None
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_MENU, self.OnCommand, id=-1)
        self.Bind(wx.EVT_UPDATE_UI, self.OnCommand, id=-1)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy, id=-1)
        self.Bind(wx.EVT_SHOW, self.OnShow, id=-1)

        from osaf.framework.blocks.Views import View
        """
          Load and display the main chandler view.
        """
        mainView = Globals.repository.findPath('//parcels/osaf/views/main/MainView')

        if mainView:
            assert isinstance (mainView, View)
            self.mainFrame = MainFrame(None,
                                       -1,
                                       "Chandler",
                                       size=(mainView.size.width, mainView.size.height),
                                       style=wx.DEFAULT_FRAME_STYLE)
            Globals.mainView = mainView
            mainView.lastDynamicBlock = False

            GlobalEvents = Globals.repository.findPath('//parcels/osaf/framework/blocks/Events/GlobalEvents')
            """
              Subscribe to some global events.
            """
            Globals.notificationManager.Subscribe (GlobalEvents.subscribeAlwaysEvents,
                                                   UUID(),
                                                   Globals.mainView.dispatchEvent)
            Globals.mainView.onSetActiveView(mainView)

            self.ignoreSynchronizeWidget = False
            mainView.render()

            """
              We have to wire up the block mainView, it's widget and sizer to a new
            sizer that we add to the mainFrame.
            """
            sizer = wx.BoxSizer (wx.HORIZONTAL)
            self.mainFrame.SetSizer (sizer)
            from osaf.framework.blocks.Block import wxRectangularChild
            sizer.Add (mainView.widget,
                       mainView.stretchFactor, 
                       wxRectangularChild.CalculateWXFlag(mainView), 
                       wxRectangularChild.CalculateWXBorder(mainView))

            self.mainFrame.Show()

            tools.timing.end("wxApplication OnInit") #@@@Temporary testing tool written by Morgen -- DJA

            return True                     #indicates we succeeded with initialization
        return False                        #or failed.


    def GetImage (self, name):
        return wx.Image("application/images/" + name + ".png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()

    def OnCommand(self, event):
        """
          Catch commands and pass them along to the blocks.
        Our events have ids between MINIMUM_WX_ID and MAXIMUM_WX_ID
        Delay imports to avoid circular references.
        """
        from osaf.framework.blocks.Block import Block, BlockEvent
        from osaf.framework.notifications.Notification import Notification

        wxID = event.GetId()
        if wxID >= Block.MINIMUM_WX_ID and wxID <= Block.MAXIMUM_WX_ID:
            block = Block.widgetIDToBlock (wxID)
            updateUIEvent = event.GetEventType() == wx.EVT_UPDATE_UI.evtType[0]
            try:
                blockEvent = block.event
            except AttributeError:
                """
                  If we have an event and it's not an update event
                then we'd better have a block event for it, otherwise
                we can't post the event.
                """
                assert updateUIEvent
            else:
                args = {'wxEvent':event}
                if updateUIEvent:
                    args['UpdateUI'] = True
                else:
                    try:
                        args['buttonState'] = event.GetEventObject().GetToolState (wxID)
                    except AttributeError: 
                        pass
 
                block.Post (blockEvent, args)
 
                if updateUIEvent:
                    try:
                        event.Check (args ['Check'])
                    except KeyError:
                        pass
                    try:
                        event.Enable (args ['Enable'])
                    except KeyError:
                        pass
                    try:
                        text = args ['Text']
                    except KeyError:
                        pass
                    else:
                        eventObject = event.GetEventObject()
                        event.SetText (text)
                    return
        else:
            event.Skip()

    def OnDestroy(self, event):
        widget = event.GetWindow()
        if hasattr (widget, 'blockItem'):
            widget.blockItem.onDestroyWidget()
        event.Skip()

    def OnShow(self, event):
        """
          Giant hack. Calling event.GetEventObject while the object is being created cause the
        object to get the wrong type because of a "feature" of SWIG. So we need to avoid
        OnShows in this case by using ignoreSynchronizeWidget as a flag.
        """
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            widget = event.GetEventObject()
            try:
                block = widget.blockItem
            except AttributeError:
                pass
            else:
                try:
                    subscribeWhenVisibleEvents = block.subscribeWhenVisibleEvents
                except AttributeError:
                    pass
                else:
                    if widget.IsShown() != event.GetShow():
                        """
                          The state of the new GetShow flag should be the opposite of whether or
                        not we have a subscribeWhenVisibleEventsUUID attribute
                        """
                        assert event.GetShow() ^ hasattr (widget, 'subscribeWhenVisibleEventsUUID')
        
                        if event.GetShow():
                            widget.subscribeWhenVisibleEventsUUID = UUID()
                            Globals.notificationManager.Subscribe (subscribeWhenVisibleEvents,
                                                                   widget.subscribeWhenVisibleEventsUUID,
                                                                   Globals.mainView.dispatchEvent)
                        else:
                            Globals.notificationManager.Unsubscribe (widget.subscribeWhenVisibleEventsUUID)
                            delattr (widget, 'subscribeWhenVisibleEventsUUID')
                        self.needsUpdateUI = True
    
                
        event.Skip()

    def OnIdle(self, event):
        """
          Adding a handler for catching a set focus event doesn't catch
        every change to the focus. It's difficult to preprocess every event
        so we check for focus changes in OnIdle. Also call UpdateUI when
        focus changes
        """
        focus = wx.Window_FindFocus()
        if self.focus != focus:
            self.focus = focus
            self.needsUpdateUI = True

        if self.needsUpdateUI:
            try:
                self.mainFrame.UpdateWindowUI (wx.UPDATE_UI_FROMIDLE | wx.UPDATE_UI_RECURSE)
            finally:
                self.needsUpdateUI = False
        event.Skip()

    def OnExit(self):
        """
          Main application termination.
        """

        Globals.taskManager.stop()
        self.__twistedReactorManager.stopReactor()
        """
          Since Chandler doesn't have a save command and commits typically happen
        only when the user completes a command that changes the user's data, we
        need to add a final commit when the application quits to save data the
        state of the user's world, e.g. window location and size.
        """
        Globals.repository.commit()
        Globals.repository.close()

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
        Does a repository commit to get the changes across from the other thread.
        """
        Globals.repository.commit () # bring changes across from the other thread/view

        # unwrap the target item and find the method to call
        item = transportItem.unwrap ()
        try:
            member = getattr (type(item), methodName)
        except AttributeError:
            logging.warning ("CallItemMethodAsync couldn't find method %s on item %s" % (methodName, str (item)))
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
        Globals.wxApplication.PostAsyncEvent (self._DispatchItemMethod, transportItem, 
                                              methodName, transportArgs, keyArgs)

    def ShowDebuggerWindow(self):
        import wx.py
        rootObjects = {
         "globals" : application.Globals,
         "parcelManager" : application.Globals.parcelManager,
         "parcelsRoot" : application.Globals.repository.findPath("//parcels"),
         "repository" : application.Globals.repository,
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
            repView = Globals.mainView
            item = repView.findUUID (theUUID)
            return item
        
