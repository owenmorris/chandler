__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import gettext, os, sys, threading
from new import classobj
from wxPython.wx import *
import Globals
from repository.util.UUID import UUID
import repository.parcel.LoadParcels as LoadParcels
from repository.persistence.XMLRepository import XMLRepository

"""
  Event used to post callbacks on the UI thread
"""
wxEVT_MAIN_THREAD_CALLBACK = wxNewEventType()

def EVT_MAIN_THREAD_CALLBACK(win, func):
    win.Connect(-1, -1, wxEVT_MAIN_THREAD_CALLBACK, func)


def repositoryCallback(uuid, notification, reason, **kwds):
    if notification == 'History':
        eventPath = '//parcels/OSAF/framework/item_' + reason
    else:
        return

    event = Globals.repository.find(eventPath)

    # Postpone import to avoid circular imports
    from OSAF.framework.notifications.Notification import Notification
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
        assert len(parts) >= 2, "Delegate %s isn't a module and class" % counterpart.elementDelegate
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


class MainThreadCallbackEvent(wxPyEvent):
    def __init__(self, target, *args):
        wxPyEvent.__init__(self)
        self.SetEventType(wxEVT_MAIN_THREAD_CALLBACK)
        self.target = target
        self.args = args
        self.lock = threading.Lock()


class MainFrame(wxFrame):
    def __init__(self, *arguments, **keywords):
        wxFrame.__init__ (self, *arguments, **keywords)
        self.SetBackgroundColour (wxSystemSettings_GetSystemColour(wxSYS_COLOUR_3DFACE))
        EVT_CLOSE(self, self.OnClose)

    def OnClose(self, event):
        """
          For some strange reason when there's an idle handler on the
        application the mainFrame windows doesn't get destroyed, so
        we'll remove the handler
        """
        EVT_IDLE(Globals.wxApplication, None)
        """
          When we quit, as each wxWidget window is torn down our handlers that
        track changes to the selection are called, and we don't want to count
        these changes, since they weren't caused by user actions.
        """
        Globals.wxApplication.insideSynchronizeFramework = True
        Globals.wxApplication.mainFrame = None
        self.Destroy()

    def OnSize(self, event):
        if not Globals.wxApplication.insideSynchronizeFramework:
            event.Skip()
            counterpart = Globals.repository.find (self.counterpartUUID)
            counterpart.size.width = self.GetSize().x
            counterpart.size.height = self.GetSize().y
            """
              size is a repository type that I defined. They seem harder
            to define than necessary and they don't automatically dirty
            themselves when modified. We need to improve this feature
            of the repository -- DJA
            """
            counterpart.setDirty()   # Temporary repository hack -- DJA


class wxApplication (wxApp):
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
        assert Globals.wxApplication == None, "We can have only one application"
        Globals.wxApplication = self
        self.insideSynchronizeFramework = False

        wxInitAllImageHandlers()
        """
          Splash Screen
        """
        splashFile = os.path.join(Globals.chandlerDirectory, 
                                  "application", "images", "splash.png")
        splashBitmap = wxImage(splashFile, wxBITMAP_TYPE_PNG).ConvertToBitmap()
        splash = wxSplashScreen(splashBitmap, 
                                wxSPLASH_CENTRE_ON_SCREEN|wxSPLASH_TIMEOUT, 
                                6000, None, -1, wxDefaultPosition, wxDefaultSize,
                                wxSIMPLE_BORDER|wxFRAME_NO_TASKBAR|wxSTAY_ON_TOP)
        splash.Show()
        """
          Setup internationalization
        To experiment with a different locale, try 'fr' and wxLANGUAGE_FRENCH
        """
        os.environ['LANGUAGE'] = 'en'
        self.locale = wxLocale(wxLANGUAGE_ENGLISH)
        """
          @@@ Sets the python locale, used by wxCalendarCtrl and mxDateTime
        for month and weekday names. When running on Linux, 'en' is not
        understood as a locale, nor is 'fr'. On Windows, you can try 'fr'.
        locale.setlocale(locale.LC_ALL, 'en')
        """
        wxLocale_AddCatalogLookupPathPrefix('locale')
        self.locale.AddCatalog('Chandler.mo')
        gettext.install('Chandler', os.path.join (Globals.chandlerDirectory, 'locale'))
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
        repositoryPath = os.path.join(Globals.chandlerDirectory,
                                      "__repository__")
        Globals.repository = XMLRepository(repositoryPath)

        if '-create' in sys.argv:
            Globals.repository.create()
        else:
            Globals.repository.open(create=True, recover=True)

        if not Globals.repository.find('//Packs/Schema'):
            """
              Bootstrap an empty repository by loading only the stuff that
            can't be loaded in a data parcel.
            """
            Globals.repository.loadPack(os.path.join(Globals.chandlerDirectory,
                                                     "repository", "packs",
                                                     "schema.pack"))

        # Load Parcels
        parcelSearchPath = parcelDir
        if __debug__ and debugParcelDir:
            parcelSearchPath = parcelSearchPath + os.pathsep + debugParcelDir

        LoadParcels.LoadParcels(parcelSearchPath, Globals.repository)

        Globals.repository.commit()

        EVT_MAIN_THREAD_CALLBACK(self, self.OnMainThreadCallbackEvent)
        """
          Create and start the notification manager. Delay imports to avoid
        circular references.
        """
        from OSAF.framework.notifications.NotificationManager import NotificationManager
        Globals.notificationManager = NotificationManager()
        Globals.notificationManager.PrepareSubscribers()

        # Set it up so that repository changes generate notifications
        Globals.repository.addNotificationCallback(repositoryCallback)
        """
          Create and start the agent manager. Delay imports to avoid
        circular references.
        """
        from OSAF.framework.agents.AgentManager import AgentManager
        Globals.agentManager = AgentManager()
        Globals.agentManager.Startup()

        EVT_MENU(self, -1, self.OnCommand)
        EVT_UPDATE_UI(self, -1, self.OnCommand)
        self.focus = None
        EVT_IDLE(self, self.OnIdle)

        from OSAF.framework.blocks.Views import View
        """
          Load and display the main chandler view.
        """
        mainView = Globals.repository.find('//parcels/OSAF/views/main/MainView')

        if mainView:
            assert isinstance (mainView, View)
            self.mainFrame = MainFrame(None,
                                       -1,
                                       "Chandler",
                                       size=(mainView.size.width, mainView.size.height),
                                       style=wxDEFAULT_FRAME_STYLE|wxNO_FULL_REPAINT_ON_RESIZE)
            Globals.mainView = mainView
            self.menuParent = None
            self.mainFrame.counterpartUUID = mainView.getUUID()
            EVT_SIZE(self.mainFrame, self.mainFrame.OnSize)

            GlobalEvents = Globals.repository.find('//parcels/OSAF/framework/blocks/Events/GlobalEvents')
            """
              Subscribe to some global events and those belonging to the mainView.
            """
            Globals.notificationManager.Subscribe (GlobalEvents.blockEvents,
                                                   UUID(),
                                                   Globals.mainView.dispatchEvent)
            try:
                events = mainView.blockEvents
            except AttributeError:
                pass
            else:
                Globals.notificationManager.Subscribe (events,
                                                       UUID(),
                                                       Globals.mainView.dispatchEvent)

            mainView.render (self.mainFrame, self.mainFrame)

            self.mainFrame.Show()
            """
              Menus on the Mac were not appearing on startup (you needed to switch
            to another app to get them to appear).  Adding this call to onSetFocus
            is a temporary workaround for this bug (Bug#1204).  Once we are on top
            of wxWindows 2.5 we should revisit whether or not this is still a 
            problem and fix it properly if so.
            """
            Globals.mainView.onSetFocus()
            return True                     #indicates we succeeded with initialization
        return False                        #or failed.

    def OnCommand(self, event):
        """
          Catch commands and pass them along to the blocks.
        Our events have ids between MINIMUM_WX_ID and MAXIMUM_WX_ID
        Delay imports to avoid circular references.
        """
        from OSAF.framework.blocks.Block import Block, BlockEvent
        from OSAF.framework.notifications.Notification import Notification

        wxID = event.GetId()
        if wxID >= Block.MINIMUM_WX_ID and wxID <= Block.MAXIMUM_WX_ID:
            block = Block.wxIDToObject (wxID)

            args = {}
            if event.GetEventType() == wxEVT_UPDATE_UI:
                args['UpdateUI'] = True

            try:
                blockEvent = block.event
            except AttributeError:
                """
                  If we have an event and it's not an update event
                then we'd better have a block event for it, otherwise
                we can't post the event.
                """
                assert event.GetEventType() == wxEVT_UPDATE_UI
                pass
            else:
                block.Post (blockEvent, args)
                if event.GetEventType() == wxEVT_UPDATE_UI:
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

    def OnIdle(self, event):
        """
          Adding a handler for catching a set focus event doesn't catch
        every change to the focus. It's difficult to preprocess every event
        so we check for focus changes in OnIdle
        """
        focus = wxWindow_FindFocus()
        if self.focus != focus:
            self.focus = focus
            Globals.mainView.onSetFocus()
        event.Skip()

    def OnExit(self):
        """
          Main application termination.
        """
        Globals.agentManager.Shutdown()
        """
          Since Chandler doesn't have a save command and commits typically happen
        only when the user completes a command that changes the user's data, we
        need to add a final commit when the application quits to save data the
        state of the user's world, e.g. window location and size.
        """
        Globals.repository.commit(purge=True)
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
        wxPostEvent(self, evt)
        return evt.lock

    if __debug__:
        def ShowDebuggerWindow(self, event):
            from wx import py
            self.crustFrame = py.crust.CrustFrame()
            self.crustFrame.SetSize((700,700))
            self.crustFrame.Show(wx.TRUE)
            self.crustFrame.shell.interp.locals['chandler'] = self
            wx.EVT_CLOSE(self.crustFrame, self.onCloseDebuggerWindow)

        def onCloseDebuggerWindow(self, event):
            self.crustFrame.Destroy()
