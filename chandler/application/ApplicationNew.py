__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import gettext, os, sys
from wxPython.wx import *
import Globals
import repository.parcel.LoadParcels as LoadParcels
import repository.schema.AutoItem as AutoItem
from repository.persistence.XMLRepository import XMLRepository

"""
  Event used to post callbacks on the UI thread
"""
wxEVT_MAIN_THREAD_CALLBACK = wxNewEventType()

def EVT_MAIN_THREAD_CALLBACK(win, func):
    win.Connect(-1, -1, wxEVT_MAIN_THREAD_CALLBACK, func)


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
        Globals.wxApplication.mainFrame = None
        self.Destroy()

    def OnSize(self, event):
        event.Skip()
        counterpart = Globals.repository.find (self.counterpartUUID)
        counterpart.size.width = self.GetSize().x
        counterpart.size.height = self.GetSize().y
        counterpart.setDirty()   # Temporary repository hack -- DJA


class wxApplicationNew (wxApp):
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
        assert (Globals.wxApplication == None) #We can have only one application
        Globals.wxApplication = self

        assert not Globals.application   #More than one application object doesn't make sense
        Globals.application = self

        wxInitAllImageHandlers()

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
        to import parcels.
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
        -recover argument runs recovery when opening after a crash.
        Load the Repository after the path has been altered, but before
        the parcels are loaded. 
        """
        repositoryPath = os.path.join(Globals.chandlerDirectory,
                                      "__repository__")
        Globals.repository = XMLRepository(repositoryPath)

        if '-create' in sys.argv:
            Globals.repository.create()
        else:
            Globals.repository.open(create=True, recover='-recover' in sys.argv)

        if not Globals.repository.find('//Schema'):
            """
              Bootstrap an empty repository by loading only the stuff that
            can't be loaded in a data parcel.
            """
            Globals.repository.loadPack(os.path.join(Globals.chandlerDirectory,
                                                     "repository",
                                                     "packs",
                                                     "schema.pack"))

        # AutoItem needs to know the repository
        AutoItem.AutoItem.SetRepository (Globals.repository) 

        # Load Parcels
        parcelSearchPath = parcelDir
        if __debug__ and debugParcelDir:
            parcelSearchPath = os.path.join(parcelSearchPath, debugParcelDir)

        LoadParcels.LoadParcels(parcelSearchPath, Globals.repository)

        EVT_MAIN_THREAD_CALLBACK(self, self.OnMainThreadCallbackEvent)
        
        # Create and start the notification manager.
        from OSAF.framework.notifications.NotificationManager import NotificationManager
        Globals.notificationManager = NotificationManager()
        Globals.notificationManager.PrepareSubscribers()

        # Create and start the agent manager.
        from OSAF.framework.agents.AgentManager import AgentManager
        Globals.agentManager = AgentManager()
        """
          Temporarily disable agents to avoid repository bug that prevents
        objects from changing in other threads. This allows me to continue
        working -- DJA
        """
        #Globals.agentManager.Startup()

        EVT_MENU(self, -1, self.OnCommand)
        EVT_UPDATE_UI(self, -1, self.OnCommand)
        self.focus = None
        EVT_IDLE(self, self.OnIdle)

        #allocate the Jabber client, logging in if possible
        #import ChandlerJabber
        # Globals.jabberClient = ChandlerJabber.JabberClient(self)
        
        # Globals.jabberClient.Login()

        from OSAF.framework.blocks.View import View
        
        topView = Globals.repository.find('//parcels/OSAF/templates/top/TopView')

        if topView:
            assert isinstance (topView, View)
            self.mainFrame = MainFrame(None,
                                       -1,
                                       "Chandler",
                                       size=(topView.size.width, topView.size.height),
                                       style=wxDEFAULT_FRAME_STYLE|wxNO_FULL_REPAINT_ON_RESIZE)
            Globals.topView = topView
            self.menuParent = None
            self.mainFrame.counterpartUUID = topView.getUUID()
            EVT_SIZE(self.mainFrame, self.mainFrame.OnSize)

            GlobalEvents = Globals.repository.find('//parcels/OSAF/framework/blocks/Events/GlobalEvents')

            events = []
            for event in GlobalEvents.blockEvents:
                events.append (event)
            for event in topView.blockEvents:
                events.append (event)

            Globals.notificationManager.Subscribe (events,
                                                   Globals.topView.getUUID(),
                                                   Globals.topView.dispatchEvent)

            topView.render (self.mainFrame, self.mainFrame)

            self.mainFrame.Show()
        return true                     #indicates we succeeded with initialization


    def OnCommand(self, event):
        """
          Catch commands and pass them along to the blocks.
        Our events have ids between MINIMUM_WX_ID and MAXIMUM_WX_ID
        """
        from OSAF.framework.blocks.Block import Block, BlockEvent
        from OSAF.framework.notifications.Notification import Notification

        wxID = event.GetId()
        if wxID >= Block.MINIMUM_WX_ID and wxID <= Block.MAXIMUM_WX_ID:
            blockEvent = Block.wxIDToObject (wxID)

            if isinstance (blockEvent, BlockEvent):
                assert isinstance (blockEvent, BlockEvent)
                if event.GetEventType() == wxEVT_UPDATE_UI:
                    data = {'type':'UpdateUI'}
                else:
                    data = {'type':'Normal'}

                notification = Notification(blockEvent, None, None)
                notification.SetData(data)
                Globals.notificationManager.PostNotification (notification)
                if event.GetEventType() == wxEVT_UPDATE_UI:
                    try:
                        event.Check (data ['Check'])
                    except KeyError:
                        pass
                    try:
                        event.Enable (data ['Enable'])
                    except KeyError:
                        pass
                    try:
                        text = data ['Text']
                        eventObject = event.GetEventObject()
                        event.SetText (data ['Text'])
                    except KeyError:
                        pass
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
            Globals.topView.onSetFocus()
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
        def DebugRoutine(self, event):
            i = 1
            pass

        def ShowDebuggerWindow(self, event):
            from wx import py
            self.crustFrame = py.crust.CrustFrame()
            self.crustFrame.SetSize((700,700))
            self.crustFrame.Show(wx.TRUE)
            self.crustFrame.shell.interp.locals['chandler'] = self
            wx.EVT_CLOSE(self.crustFrame, self.onCloseDebuggerWindow)

        def onCloseDebuggerWindow(self, event):
            self.crustFrame.Destroy()
