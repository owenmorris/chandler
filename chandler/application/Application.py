__author__ = "John Anderson"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"


import os, sys, stat, gettext
from wxPython.wx import *
from wxPython.xrc import *
from application.Preferences import Preferences
from Persistence import Persistent, PersistentList
import application.ChandlerWindow

from ZODB import DB, FileStorage 
from Persistence import Persistent

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
    VERSION = 7
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

        self.preferences               object containing all application preferences
        self.mainFrame                 ChandlerWindow
        self.URLTree                   tree of parcel views
        self.version                   see __setstate__
        """
        self.preferences = Preferences()
        self.mainFrame = application.ChandlerWindow.ChandlerWindow()
        self.URLTree = PersistentList.PersistentList ()
        self.version = Application.VERSION
    
    def SynchronizeView(self):
        """
          Notifies each of the application's wxPython view counterparts
        that they need to synchronize themselves to match their
        peristent counterpart.
        """
        self.mainFrame.SynchronizeView()
        app.association[id(self.mainFrame)].Show()

    def __setstate__(self, dict):
        """
          Data often lives a long time, even longer than code and we may need to
        update it over time as it's structure changes. A convienent way to do
        this is to check for an old version in __setstate__, which is called
        each time the object is loaded, and update the data as necessary.
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
    needs to be saved across successive application executions. The non-persistent
    object, usually a wxPython object can't be easily be saved because they
    contain data that doesn't pickle.
      We'll use the convention of naming the wxPython view object with a "wx"
    prefix using the same name its persistent model counterpart.
      Here's a description of the data available that the wxApplication makes
    available for the rest of the program:

    self.applicationResources      the main application-wide XRC resources
    self.association               a dictionary mapping persistent object ids to non-persistent
                                   wxPython counterparts
    self.chandlerDirectory         directory containing chandler executable
    self.parcels                   global list of parcel classes
    self.model                     the persistent counterpart
    self.storage                   ZODB low level database
    self.db                        ZODB high level database (object cache)
    self.connection                connection to ZODB
    self.dbroot                    ZODB root object tree
    self.homeDirectory             path to a folder in the user's home directory
    self.wxMainFrame               active wxChandlerWindow

    In the future we may replace ZODB with another database that provides similar
    functionality
    """
    def OnInit(self):       
        """Main application initialization. Open the persistent object
         store, lookup of the application's persitent model counterpart, or
         create it if it doesn't exist.
        """
        self.applicationResources=None
        self.association={}
        self.chandlerDirectory=None
        self.parcels=[]
        self.storage=None
        self.model=None

        global app
        assert app==None                #More than one application object doesn't make any sense
        app = self;

        wxInitAllImageHandlers()
        gettext.install('Chandler')

        self.chandlerDirectory = os.path.dirname (os.path.abspath (sys.argv[0]))
        resourceFile = "application" +\
                       os.sep + "application.xrc"

        #Check for the file's existance in debugging code
        assert stat.S_ISREG(os.stat(resourceFile)[stat.ST_MODE])
        self.applicationResources = wxXmlResource(resourceFile)

        #Open the database
        self.storage = FileStorage.FileStorage ('_CHANDLER_')
        self.db = DB.DB (self.storage)
        self.connection = self.db.open ()
        self.dbroot = self.connection.root ()

        if not self.dbroot.has_key('Application'):
            self.model = Application()
            self.dbroot['Application'] = self.model
        else:
            self.model = self.dbroot['Application']
        """
           The model persists, so it can't store a reference to self, which
        is a wxApp object. We use the association to keep track of the
        wxPython object associated with each persistent object.
        """
        self.association={id(self.model) : self}
        
        self.LoadParcels()
        self.model.SynchronizeView()
        EVT_MENU(self, XRCID ("Quit"), self.OnQuit)
        
        self.homeDirectory = wxGetHomeDir() + os.sep + ".Chandler";
        if not os.path.exists (self.homeDirectory):
            os.makedirs (self.homeDirectory)
        
        if __debug__:
            """
               In the debugging version we have a debug menu with a couple
            commands that are useful for testing code. Currently they call
            OnTest1 and OnTest2. To see how all this works check out
            ChandlerWindow.py and application.xrc.
            """
            EVT_MENU(self, XRCID ('Test1'), self.OnTest1)
            EVT_MENU(self, XRCID ('Test2'), self.OnTest2)
            EVT_MENU(self, XRCID ('Test3'), self.OnTest3)
            EVT_MENU(self, XRCID ('CreateNewRepository'), self.OnCreateNewRepository)

        return true  #indicates we succeeded with initialization

    if __debug__:
        def OnTest1 (self, event):
            for parcel in self.model.URLTree:
                """
                  Each parcel must have an attribute which is the displayName.
                """
                assert (hasattr (parcel, 'displayName'))
                if parcel.displayName == 'Calendar':
                    parcel.SynchronizeView ()
                    return
        
        def OnTest2 (self, event):
            for parcel in self.model.URLTree:
                """
                  Each parcel must have an attribute which is the displayName.
                """
                assert (hasattr (parcel, 'displayName'))
                if parcel.displayName == 'Contacts':
                    parcel.SynchronizeView ()
                    return
        
        def OnTest3 (self, event):
            for parcel in self.model.URLTree:
                """
                  Each parcel must have an attribute which is the displayName.
                """
                assert (hasattr (parcel, 'displayName'))
                if parcel.displayName == 'Test':
                    parcel.SynchronizeView ()
                    return

        def OnCreateNewRepository (self, event):
            if (hasattr (self.model, 'CreateNewRepository')):
                del self.model.CreateNewRepository
            else:
                self.model.CreateNewRepository = true
            menuBar = self.wxMainFrame.GetMenuBar ()
            menuBar.Check (XRCID ('CreateNewRepository'),
                           hasattr (self.model, 'CreateNewRepository'))
        
    def OnQuit(self, event):
        """
          Exit the application
        """
        self.ExitMainLoop ()

    def LoadParcels(self):       
        """
           Load the parcels and call the class method to install them. Packages
        are defined by directories that contain __init__.py. __init__.py must
        define assign the parcel's class name to parcelClass. For example
        "parcelClass = CalendarView.CalendarView", where the first string before the
        dot is the file, (CalendarView.py) and the second string is the class
        e.g. CalendarView. See calendar/__init__.py for an example
        """
        self.parcels=[]
        """
           We've got to have a parcel directory..
         """
        importDirectory = Application.PARCEL_IMPORT
        importDirectory.replace ('.', os.sep)
        
        parcelDirectory = self.chandlerDirectory + os.sep + importDirectory
        assert (os.path.exists (parcelDirectory))

        for directory in os.listdir(parcelDirectory):
            pathToPackage = parcelDirectory + os.sep + directory
            if os.path.isdir (pathToPackage) and \
               os.path.exists (pathToPackage + os.sep + "__init__.py"):
                directory = Application.PARCEL_IMPORT + '.' + directory
                """
                  Import the parcel, which should define parcelClass
                """
                module = __import__(directory, globals, locals, ['*'])
                assert (hasattr (module, 'parcelClass'))
                """
                  Import the parcel's class and append it to our global list
                of parcels and install it.
                """
                parcelClassStrings = module.parcelClass.split ('.')
                directory += '.' + parcelClassStrings[0]
                module = __import__(directory, globals, locals, ['*'])
                """
                  Check to mark sure the class in parcelClass exists.
                """
                assert (hasattr (module, parcelClassStrings[1]))
                theClass = module.__dict__[parcelClassStrings[1]]
                self.parcels.append (theClass)
                theClass.path = pathToPackage
                theClass.Install ()

