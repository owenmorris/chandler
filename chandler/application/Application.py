__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import gettext, os, sys, threading
from new import classobj
import wx
import Globals
from repository.util.UUID import UUID
import repository.parcel.LoadParcels as LoadParcels
from repository.persistence.XMLRepository import XMLRepository


"""
  Event used to post callbacks on the UI thread
"""
wxEVT_MAIN_THREAD_CALLBACK = wx.NewEventType()
EVT_MAIN_THREAD_CALLBACK = wx.PyEventBinder(wxEVT_MAIN_THREAD_CALLBACK, 0)

def repositoryCallback(uuid, notification, reason, **kwds):
    if notification == 'History':
        eventPath = '//parcels/osaf/framework/item_' + reason
    else:
        return

    event = Globals.repository.findPath(eventPath)

    # Postpone import to avoid circular imports
    from osaf.framework.notifications.Notification import Notification
    note = Notification(event)
    note.threadid = id(threading.currentThread())
    note.SetData({'uuid' : uuid, 'keywords' : kwds})
    Globals.notificationManager.PostNotification(note)


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
        newClassName = self.__class__.__name__ + '_' + delegateClassName
        try:
            theClass = _classesByName [newClassName]
        except KeyError:
            module = __import__ ('.'.join(parts), globals(), locals(), delegateClassName)
            assert module.__dict__.get (delegateClassName), "Class %s doesn't exist" % myMixinClassImportPath
            theClass = classobj (str(newClassName),
                                 (self.__class__, module.__dict__[delegateClassName]),
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
            Globals.mainView.setDirty()   # Temporary repository hack -- DJA
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
        if __debug__:
            """
              Install a custom displayhook to keep Python from setting the global
            _ (underscore) to the value of the last evaluated expression.  If 
            we don't do this, our mapping of _ to gettext can get overwritten.
            This is useful in interactive debugging with PyCrust.
            """
            def _displayHook(obj):
                sys.stdout.write(str(obj))
            
            sys.displayhook = _displayHook

        Globals.chandlerDirectory = os.path.dirname (os.path.abspath (sys.argv[0]))
        os.chdir (Globals.chandlerDirectory)
        assert Globals.wxApplication == None, "We can have only one application"
        Globals.wxApplication = self
        self.ignoreSynchronizeWidget = True

        wx.InitAllImageHandlers()
        """
          Splash Screen
        """
        splashBitmap = wx.Image("application/images/splash.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        splash = wx.SplashScreen(splashBitmap, 
                                wx.SPLASH_CENTRE_ON_SCREEN|wx.SPLASH_TIMEOUT, 
                                6000, None, -1, wx.DefaultPosition, wx.DefaultSize,
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

        if __debug__:
            """
              In the debugging version, if PARCELDIR env var is set, put that
            directory into sys.path before any modules are imported.
            """
            debugParcelDir = None
            if os.environ.has_key('PARCELDIR'):
                path = os.environ['PARCELDIR']
                if path and os.path.exists(path):
                    debugParcelDir = path
                    sys.path.insert (2, debugParcelDir)
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

        # Load Parcels
        parcelSearchPath = parcelDir
        if __debug__ and debugParcelDir:
            parcelSearchPath = parcelSearchPath + os.pathsep + debugParcelDir

        LoadParcels.LoadParcels(parcelSearchPath, Globals.repository)

        Globals.repository.commit()

        EVT_MAIN_THREAD_CALLBACK(self, self.OnMainThreadCallbackEvent)
        
        """
          The Twisted Reactor should be started before other Managers
          and stopped last. Is this true?
        
        """
        from osaf.framework.twisted.TwistedReactorManager import TwistedReactorManager
        Globals.twistedReactorManager = TwistedReactorManager()
        Globals.twistedReactorManager.startReactor()
        """
          Create and start the notification manager. Delay imports to avoid
          circular references.
        """
        
        from osaf.framework.notifications.NotificationManager import NotificationManager
        Globals.notificationManager = NotificationManager()
        Globals.notificationManager.PrepareSubscribers()

        # Set it up so that repository changes generate notifications
        Globals.repository.addNotificationCallback(repositoryCallback)
        """
          Create and start the agent manager. Delay imports to avoid
        circular references.
        """
        from osaf.framework.agents.AgentManager import AgentManager
        Globals.agentManager = AgentManager()
        Globals.agentManager.Startup()

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
            self.menuParent = None

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
            sizer.Add (mainView.widget,
                       mainView.stretchFactor, 
                       mainView.Calculate_wxFlag(), 
                       mainView.Calculate_wxBorder())

            self.mainFrame.Show()

            return True                     #indicates we succeeded with initialization
        return False                        #or failed.


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

            args = {}
            if event.GetEventType() == wx.EVT_UPDATE_UI.evtType[0]:
                args['UpdateUI'] = True

            try:
                blockEvent = block.event
            except AttributeError:
                """
                  If we have an event and it's not an update event
                then we'd better have a block event for it, otherwise
                we can't post the event.
                """
                assert event.GetEventType() == wx.EVT_UPDATE_UI.evtType[0]
                pass
            else:
                block.Post (blockEvent, args)
                if event.GetEventType() == wx.EVT_UPDATE_UI.evtType[0]:
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
        OnShows in this case.
        """
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            widget = event.GetEventObject()
            try:
                block = widget.blockItem
            except AttributeError:
                pass
            else:
                if block.hasAttributeValue ('subscribeWhenVisibleEvents') and (widget.IsShown() != event.GetShow()):
                    """
                      The state of the new GetShow flag should be the opposite of whether or
                    not we have a subscribeWhenVisibleEventsUUID attribute
                    """
                    assert event.GetShow() ^ widget.hasAttributeValue ('subscribeWhenVisibleEventsUUID')
    
                    if event.GetShow():
                        widget.subscribeWhenVisibleEventsUUID = UUID()
                        Globals.notificationManager.Subscribe (block.subscribeWhenVisibleEvents,
                                                               widget.subscribeWhenVisibleEventsUUID,
                                                               Globals.mainView.dispatchEvent)
                    else:
                        Globals.notificationManager.Unsubscribe (widget.subscribeWhenVisibleEventsUUID)
                        delattr (widget, 'subscribeWhenVisibleEventsUUID')
    
                
        event.Skip()

    def OnIdle(self, event):
        """
          Adding a handler for catching a set focus event doesn't catch
        every change to the focus. It's difficult to preprocess every event
        so we check for focus changes in OnIdle
        """
        focus = wx.Window_FindFocus()
        if self.focus != focus:
            self.focus = focus
        event.Skip()

    def OnExit(self):
        """
          Main application termination.
        """
        Globals.agentManager.Shutdown()
        Globals.taskManager.stop()
        Globals.twistedReactorManager.stopReactor()
        """
          Since Chandler doesn't have a save command and commits typically happen
        only when the user completes a command that changes the user's data, we
        need to add a final commit when the application quits to save data the
        state of the user's world, e.g. window location and size.
        """
        Globals.repository.commit()
        Globals.repository.close()

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

    if __debug__:
        def ShowDebuggerWindow(self, event):
            import wx.py
            self.crustFrame = wx.py.crust.CrustFrame()
            self.crustFrame.SetSize((700,700))
            self.crustFrame.Show(True)
            self.crustFrame.shell.interp.locals['chandler'] = self
            self.crustFrame.Bind(wx.EVT_CLOSE, self.OnCloseDebuggerWindow)

        def onCloseDebuggerWindow(self, event):
            self.crustFrame.Destroy()
