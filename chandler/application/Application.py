__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


import os, sys, stat, gettext, locale
from wxPython.wx import *
from wxPython.xrc import *

from application.Preferences import Preferences
from application.SplashScreen import SplashScreen
from application.URLTree import URLTree

from application.agents.Notifications.NotificationManager import NotificationManager

from persistence import Persistent 
from persistence.list import PersistentList

import application.ChandlerWindow
import PreferencesDialog
import ChandlerJabber
import PresencePanel

from zodb import db
from zodb.storage.file import FileStorage
from application.repository.Repository import Repository
from application.ImportExport import ImportExport

from model.persistence.FileRepository import FileRepository

"""
  The application module makes available the following global data to
other parts of the program
"""

app=None                   #the single instance of wxApplication

class Application(Persistent):
    """
      The main application class. It's view counterpart is the wxPython class
    wxApplication (see below). Notice that we derive it from Perisistent
    so that it is automatically saved across successive application executions
    """
    VERSION = 40
    """
      PARCEL_IMPORT defines the import directory containing parcels
    relative to chandlerDirectory where os separators are replaced
    with "." just as in the syntax of the import statement.
    """
    PARCEL_IMPORT = 'parcels'

    def __init__(self):
        """
          Create instances of other objects that belong to the application.
        Here are all the public attributes:

        self.preferences         object containing all application preferences
        self.mainFrame           ChandlerWindow
        self.URLTree             tree of URL's
        self.version             see __setstate__
        self.notificationManager notification manager
        """
        self.preferences = Preferences()
        self.mainFrame = application.ChandlerWindow.ChandlerWindow()
        self.URLTree = URLTree()
        self.version = Application.VERSION
        
        self.notificationManager = NotificationManager()
   
    def SynchronizeView(self):
        """
          Notifies each of the application's wxPython view counterparts
        that they need to synchronize themselves to match their
        peristent counterpart.
        """
        self.DisplayChandlerDialog()
        self.mainFrame.SynchronizeView()
        app.association[id(self.mainFrame)].Show()

    def DisplayChandlerDialog(self):
        """
          We want to set expectations for the first release.  The first two
        times the user runs Chandler, that user will be presented with a 
        dialog explaining the current field of play.  Once Chandler has
        grown past this initial stage, this dialog will be removed.
        """
        if hasattr(self, 'splashWasShown'):
            self.splashWasShown += 1
        else:
            self.splashWasShown = 0
        if self.splashWasShown < 2:
            pageLocation = os.path.join ('application', 'welcome.html')
            splash = SplashScreen(None, _("Welcome to Chandler"),
                                  pageLocation, false)
            splash.ShowModal()
            splash.Destroy()
            
    def __setstate__(self, dict):
        """
          Data often lives a long time, even longer than code and we may need
        to update it over time as it's structure changes. A convienent way to 
        do this is to check for an old version in __setstate__, which is 
        called each time the object is loaded, and update the data as necessary.
          Until the schema of the data settles down, I'm going to always create
        a completely new application each time the data changes. Don't forget
        to call the base class, since it initializes the objects data
        """
        Persistent.__setstate__(self, dict)
        if __debug__:
            createNewRepository = hasattr (self, 'CreateNewRepository')
        else:
            createNewRepository = 0
        if self.version != Application.VERSION or createNewRepository:
            self.__dict__.clear  ()
            self.__init__ ()
            if __debug__ and createNewRepository:
                self.CreateNewRepository = 1
                
                
class wxApplication (wxApp):
    """
      Many wxPython objects, for example wxApplication have corresponding
    persistent model counterparts. The persistent object stores data that
    needs to be saved across successive application executions. The 
    non-persistent object, usually a wxPython object can't be easily be saved
    because they contain data that doesn't pickle.
      We'll use the convention of naming the wxPython view object with a "wx"
    prefix using the same name its persistent model counterpart.
      Here's a description of the data available that the wxApplication makes
    available for the rest of the program:

    self.applicationResources     the main application-wide XRC resources
    self.association              a dictionary mapping persistent object ids
                                  to non-persistent wxPython counterparts
    self.chandlerDirectory        directory containing chandler executable
    self.parcels                  global dictionary of parcel classes
    self.model                    the persistent counterpart
    self.storage                  ZODB low level database
    self.db                       ZODB high level database (object cache)
    self.connection               connection to ZODB
    self.dbroot                   ZODB root object tree
    self.wxMainFrame              active wxChandlerWindow
    self.locale                   locale used for internationalization
    self.jabberClient             state of jabber client including presence dictionary
    self.repository               the model.persistence.FileRepository instance
    
    In the future we may replace ZODB with another database that provides 
    similar functionality
    """

    def __init__(self):
        """
          Overriding the __init__() method for wxApp so that we can check
        to see if the user wants stdio redirected to a window or left 
        to the console.  Setting WXREDIRECT=0 will tell wxApp to let
        stdio go to the console; setting WXREDIRECT=1 will redirect to 
        a popup window; not setting WXREDIRECT at all will let wxApp
        decide what to do.
        """
        if os.environ.has_key('WXREDIRECT'):
            if os.environ['WXREDIRECT'] != '0':
                redirect = True
            else:
                redirect = False
            wxApp.__init__(self, redirect)
        else:
            wxApp.__init__(self)

    def OnInit(self):       
        """
          Main application initialization. Open the persistent object
        tore, lookup of the application's persitent model counterpart, or
        create it if it doesn't exist.
        """
        self.applicationResources=None
        self.association={}
        self.chandlerDirectory=None
        self.parcels={}
        self.storage=None
        self.model=None
        
        self.jabberClient = None
        self.presenceWindow = None

        self.chandlerDirectory = os.path.dirname (os.path.abspath (sys.argv[0]))

        self.initInProgress = true
        
        global app
        assert app == None     #More than one app object doesn't make sense
        app = self

        wxInitAllImageHandlers()

        """
          Setup internationalization
        To experiment with a different locale, try 'fr' and wxLANGUAGE_FRENCH
        """
        os.environ['LANGUAGE'] = 'en'
        self.locale = wxLocale(wxLANGUAGE_ENGLISH)
        
        # @@@ Sets the python locale, used by wxCalendarCtrl and mxDateTime
        # for month and weekday names. When running on Linux, 'en' is not
        # understood as a locale, nor is 'fr'. On Windows, you can try 'fr'.
        # locale.setlocale(locale.LC_ALL, 'en')
        
        wxLocale_AddCatalogLookupPathPrefix('locale')
        self.locale.AddCatalog('Chandler.mo')
        gettext.install('Chandler', os.path.join (self.chandlerDirectory, 'locale'))
        
        resourceFile = os.path.join ("application", "application.xrc")
        """
          Check for the file's existence in debugging code
        """
        assert stat.S_ISREG(os.stat(resourceFile)[stat.ST_MODE])
        self.applicationResources = wxXmlResource(resourceFile)
        """
          Open the database
        """
        self.storage = FileStorage ('_CHANDLER_')
        self.db = db.DB (self.storage)
        self.connection = self.db.open ()
        self.dbroot = self.connection.root ()

        if self.dbroot.has_key('Application'):
            self.model = self.dbroot['Application']
        else:
            self.model = Application()
            self.dbroot['Application'] = self.model
        """
          The model persists, so it can't store a reference to self, which
        is a wxApp object. We use the association to keep track of the
        wxPython object associated with each persistent object.
        """
        self.association={id(self.model) : self}

        """
          Load the parcels which are contained in the PARCEL_IMPORT directory.
          It's necessary to add the "parcels" directory to sys.path in order
          to import parcels.
        """
        parcelDir = os.path.join(self.chandlerDirectory,
                                 Application.PARCEL_IMPORT.replace ('.', os.sep))
        sys.path.insert (1, parcelDir)

        if __debug__:
            """
            In the debugging version, if PARCELDIR env var is set, put that
            directory into sys.path because zodb might be loading objects
            based on modules in that directory.  This must be done prior to
            loading the system parcels
            """
            debugParcelDir = None
            if os.environ.has_key('PARCELDIR'):
                path = os.environ['PARCELDIR']
                if path and os.path.exists(path):
                    debugParcelDir = path
                    sys.path.insert (2, debugParcelDir)

        """
        Load the Repository after the path has been altered, but before
        the parcels are loaded. Only load packs if they have not yet been loaded.
        """
        self.repository = FileRepository(os.path.join(self.chandlerDirectory,
         "__database__"))
        self.repository.open()
        if not self.repository.find('//Schema'):
            self.repository.loadPack(os.path.join(self.chandlerDirectory, "model",
                                                  "packs", "schema.pack"))
        if not self.repository.find('//Calendar'):
            self.repository.loadPack(os.path.join(self.chandlerDirectory, "parcels", 
                                                  "OSAF", "calendar", "model", 
                                                  "calendar.pack"))

        """ Load the parcels """
        self.LoadParcelsInDirectory(parcelDir)

        """ Load the debugging parcels """
        if __debug__ and debugParcelDir:
            self.LoadParcelsInDirectory(debugParcelDir)

        self.model.SynchronizeView()
        EVT_MENU(self, XRCID ("Quit"), self.OnQuit)
        EVT_MENU(self, XRCID ("About"), self.OnAbout)
        EVT_MENU(self, XRCID ("Preferences"), self.OnPreferences)
        EVT_MENU(self, XRCID("TogglePresenceWindow"), self.TogglePresenceWindow)
        
        if __debug__:
            """
              In the debugging version we have a debug menu with a couple
            commands that are useful for testing code. Currently they call
            OnTest1 and OnTest2. To see how all this works check out
            ChandlerWindow.py and application.xrc.
            """
            EVT_MENU(self, XRCID ('CreateNewRepository'), self.OnCreateNewRepository)
            EVT_MENU(self, XRCID("DebugRoutine"), self.DebugRoutine)
            EVT_MENU(self, XRCID("ImportItems"), self.OnImportItems)
            EVT_MENU(self, XRCID("ExportItems"), self.OnExportItems)

        EVT_MENU(self, -1, self.OnCommand)
        EVT_UPDATE_UI(self, -1, self.OnCommand)
        
        """
        initialize the non-persistent part of the NotificationManager
        """
        self.model.notificationManager.PrepareSubscribers()
        
        """
          allocate the Jabber client, logging in if possible
        """
        self.jabberClient = ChandlerJabber.JabberClient(self)
        
        self.InCommand = false          #used by OnCommand
        self.jabberClient.Login()

        self.OpenStartingURL()
        
        self.initInProgress = false
        return true                     #indicates we succeeded with initialization

    if __debug__:
        def OnCreateNewRepository (self, event):
            if (hasattr (self.model, 'CreateNewRepository')):
                del self.model.CreateNewRepository
            else:
                self.model.CreateNewRepository = true
            menuBar = self.wxMainFrame.GetMenuBar ()
            menuBar.Check (XRCID ('CreateNewRepository'),
                            hasattr (self.model, 'CreateNewRepository'))

    def OpenStartingURL(self):
        """
          Opens the proper url when the application first starts.  If
        this is the first time running, then we just take the first item
        in the URLTree.  If we have persisted, then we use the last
        remembered url.
        """
        if not hasattr(self, 'wxMainFrame'):
            self.wxMainFrame = app.association[id(self.model.mainFrame)]
        url = self.wxMainFrame.navigationBar.model.GetCurrentURL()
        if url != None:
            url = app.jabberClient.StripRemoteIfNecessary(url)
            self.wxMainFrame.GoToURL(url, false)
        else:
            children = self.model.URLTree.GetURLChildren('')
            if len(children) > 0:
                self.wxMainFrame.GoToURL(children[0], true)
            
    def OnQuit(self, event):
        """
            Exit the application
        """
        # FIXME:  This will not fully quit the app if a stdout window has been
        # opened by a print statement.  We should also close that stdout window.
        self.wxMainFrame.Close()

    def OnAbout(self, event):
        """
          Show the splash screen in response to the about command
        """
        pageLocation = os.path.join ('application', 'welcome.html')
        splash = SplashScreen(app.wxMainFrame, _("About Chandler"), 
                              pageLocation, useTimer=false)
        splash.ShowModal()
        splash.Destroy()

    def OnPreferences(self, event):
        """
          Show the preferences dialog
        """
        title = _("Chandler Preferences")
        dialog = PreferencesDialog.PreferencesDialog(app.wxMainFrame, title, self.model.preferences)

        result = dialog.ShowModal()
        if result == wxID_OK:
            dialog.SavePreferences()
            self.HandleSystemPreferences()
        dialog.Destroy()

    def LoadParcelsInDirectory (self, baseDir, relDir=""):
        """
          Load the parcels and call the class method to install them. Parcels
        are Python Packages and are defined by directories that contain
        __init__.py (or __init__.pyc). __init__.py must assign the parcel's
        class name to parcelClass. For example:
            
            parcelClass = "CalendarFile.CalendarClass"

        CalendarFile is the python file (without the .py extension) that
        contains the class CalendarClass contained in the file which is
        the parcel class.

        For examples, look in the parcel directory.

        The method now takes two directory arguments, baseDir and relDir.
        baseDir should be a directory containing parcel subdirectories,
        while relDir is only used when recursing through directories below
        baseDir.
        """
        path = os.path.join(baseDir, relDir)
        assert (os.path.exists (path) and os.path.isdir(path))

        if (relDir and \
            (os.path.exists(os.path.join (path, "__init__.py"))  or \
             os.path.exists(os.path.join (path, "__init__.pyc")) or \
             os.path.exists(os.path.join (path, "__init__.pyo")))   \
            ):
            importArgument = relDir.replace (os.sep, '.')
            """
              Import the parcel, which should define parcelClass.
              
              If you get an error like "Import can't find module,
            or can't find name in module: No module named XYZ.XYZ
            on the following statement, you probably forgot to
            add a __init__.py file in some directory of the
            importArgument -- Currently, each directory must have
            an __init__.py
            """
            module = __import__(importArgument, globals(), locals(), [])
            importArgumentStrings = importArgument.split('.')
            del importArgumentStrings[0]
            for element in importArgumentStrings:
                if hasattr (module, element):
                    module = module.__dict__[element]
                else:
                    module = None
                    break
            if hasattr (module, 'parcelClass'):
                """
                  Import the parcel's class and append it to our global list
                of parcels and install it.
                """
                parcelFile, parcelClass = module.parcelClass.split('.')
                moduleClass = __import__(importArgument + '.' + parcelFile,
                                         globals(),
                                         locals(),
                                         parcelClass)
                """
                  Check to make sure the class in parcelClass exists.
                """
                assert (hasattr (moduleClass, parcelClass))
                theClass = moduleClass.__dict__[parcelClass]
                """
                  parcels is a dictionary that is indexed by class. For viewer
                parcels, we add a data dictionary when one is first loaded.
                """
                self.parcels[id(theClass)] = {}
                theClass.path = path
                theClass.Install ()
        """
          Recurse through all the subdirectories for more parcels.
        """
        for pathComponent in os.listdir(path):
            if os.path.isdir (os.path.join (path, pathComponent)):
                self.LoadParcelsInDirectory (baseDir,
                                             os.path.join(relDir, pathComponent))

    def OnCommand(self, event):
        """
          Catch commands and pass them along to the viewerParcels.
        If the event the viewerParcel doesn't handle the event we'll get
        recursively called, so we use InCommand to ignore recursive calls.
        """
        applicationCommand = true

        if not self.InCommand:
            self.InCommand = true
            if hasattr(self.wxMainFrame, 'activeParcel'):
                activeParcel = self.wxMainFrame.activeParcel
                if activeParcel != None:
                    activeParcel.GetEventHandler().ProcessEvent(event)
                    applicationCommand = false
            self.InCommand = false

        # This gives a chance for the app to respond to the events as well
        if applicationCommand:
            event.Skip()
    
    # handle the export command
    def OnExportItems(self, event):
        fileDialog = wxFileDialog(self.wxMainFrame, _("Select file to export to:"), "", "SavedItems", "*.*", wxSAVE|wxOVERWRITE_PROMPT )
        if fileDialog.ShowModal() == wxID_OK:
            filePath = fileDialog.GetPath()
            try:
                ImportExport().Export(filepath=filePath)
            except:
                message = _("Couldn't export repository to %s") % (filePath)
                wxMessageBox(message)
        fileDialog.Destroy()

    def OnImportItems(self, event):
        fileDialog = wxFileDialog(self.wxMainFrame, _("Select file to import from:"), "", "", "*.*", wxOPEN)
        if fileDialog.ShowModal() == wxID_OK:
            filePath = fileDialog.GetPath()
        fileDialog.Destroy()
        try:
            ImportExport().Import(filepath=filePath)
            # tell the current view to redraw
            self.wxMainFrame.activeParcel.UpdateFromRepository()
        except:
            message = _("Couldn't import Chandler items from \n%s") % (filePath)
            wxMessageBox(message)

    def GetAccessibleViews(self, jabberID):
        """
          Return a list of views accessible to the user represented by
        the passed in jabberID by looping through all the parcels
        and asking them.
        """
        parcels = self.model.URLTree.GetParcelList()
        accessibleViews = []
        
        for parcel in parcels:
            parcelViews = parcel.GetAccessibleViews(jabberID)
            for view in parcelViews:
                accessibleViews.append(view)
                
        return accessibleViews
    
    def HasPermission(self, jabberID, url):
        """
          Determine if the passed-in jabberID has permission to access the passed-in URL
        implement by asking the relevant parcel.
        """
        parcel = self.GetParcelFromURL(url)
        if parcel != None:
            return parcel.HasPermission(jabberID, url)
        return false

    def GetParcelFromURL(self, url):
        """
          Utility to return the parcel associated with a URL,
        or None if it doesn't exist.
        """
        urlPieces = url.split('/')
        return application.Application.app.model.URLTree.URLExists(urlPieces[0])
        
    def GetViewObjects(self, url, jabberID):
        """
          Request a list of objects from the view specified by a URL.
        Figure out the appropriate parcel, and let it do the work.
        """
        parcel = self.GetParcelFromURL(url)
        if parcel != None:
            return parcel.GetViewObjects(url, jabberID)
        
        # FIXME: should return an error here
        return []
    
    def AddObjectsToView(self, url, objectList, lastFlag):
        """
          Add the passed in objects to the view specified by the URL.
        Figure out the appropriate parcel, and let it do the work
        It must be the active parcel, or don't deliver the objects.
        """
        parcel = self.GetParcelFromURL(url)
        if self.wxMainFrame.activeParcel.model != parcel:
            # FIXME: we should at least log the error here
            return

        if parcel != None:
            parcel.AddObjectsToView(url, objectList, lastFlag)
        else:
            # FIXME: should return an error here
            pass

    def HandleErrorResponse(self, jabberID, url, errorMessage):
        """
          Handle error responses by passing them to the parcel.
        """
        parcel = self.GetParcelFromURL(url)
        if parcel != None:
            parcel.HandleErrorResponse(jabberID, url, errorMessage)
        else:
            wxMessageBox(errorMessage)
        
    def TogglePresenceWindow(self, event):
        """
          Handler for the Show/Hide Presence Window command.
        """
        if self.presenceWindow == None:
            title = _("Presence Panel")
            self.presenceWindow = PresencePanel.PresenceWindow(title, self.jabberClient)
            self.presenceWindow.CentreOnScreen()
            self.presenceWindow.Show()
            EVT_CLOSE(self.presenceWindow, self.PresenceWindowClosed)
        else:
            self.presenceWindow.Close()
            self.presenceWindow = None
    
    def LookupInRepository(self, jabberID):
        """
          Lookup the name of a contact associated with the passed-in
        jabberID.
          FIXME:  this routine is temporary scaffolding - we'll use the
        real database stuff with indexing when it's developed.
        """
        repository = Repository()
        for item in repository.thingList:
            if item.__class__.__name__ == 'Contact':
                if item.HasContactMethod('jabberID', jabberID):
                    return item.GetFullName()
        return None
    
    def PresenceWindowClosed(self, event):
        """
          Handle the presence window closing by clearing the reference.
        """
        self.presenceWindow.Destroy()
        self.presenceWindow = None
        
    def HandleSystemPreferences(self):
        """
          HandleSystemPreferences is called after the preferences
        changed to handle changing the state for varous system preferences.
        """
        self.LoginIfNecessary()
        if __debug__:
            self.SetupDebugMenu()
        
    def LoginIfNecessary(self):
        """
          LoginIfNecessary logs in to the jabber server if necessary.
        """
        if self.jabberClient.IsConnected() and self.jabberClient.HasLoginInfo():
            self.jabberClient.Logout()
            
        if not self.jabberClient.IsConnected():
            self.jabberClient.ReadAccountFromPreferences()
            self.jabberClient.Login()

    def SetupDebugMenu(self):
        """
          Make the visibility of the debug menu correspond to the
        preference.
        """
        debugFlag = self.model.preferences.GetPreferenceValue('chandler/debugging/debugmenu')
        self.wxMainFrame.ShowOrHideDebugMenu(debugFlag)

    if __debug__:
        def DebugRoutine(self, event):
            i = 1
            pass
    
