__author__ = "John Anderson"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"


import os, sys, stat
from wxPython.wx import *
from wxPython.xrc import *
from application.Preferences import Preferences
from application.persist import Persist
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
    VERSION = 0
    def __init__(self):
        """
          Create instances of other objects that belong to the application.
        """
        self.preferences = Preferences()
        self.mainFrame = application.ChandlerWindow.ChandlerWindow()
        self.version = 0
    
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
        if self.version != Application.VERSION:
            self.clear  ()
            self.__init__ ()

            
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
    self.parcelDirectory           global directory containing parcels
    self.parcels                   global list of parcels
    self.model                     the persistent counterpart
    self.storage                   ZODB low level database
    self.db                        ZODB high level database (object cache)
    self.connection                connection to ZODB
    self.dbroot                    ZODB root object tree

    In the future we may replace ZODB with another database that provides similar
    functionality
    """
    def OnInit(self):       
        """Main application initialization. Open the persistent object
         store, lookup of the application's persitent model counterpart, or
         create it if it doesn't exist.
        """
        self.applicationResources=None  #the main application-wide XRC resources
        self.association={}             #a dictionary mapping persistent object ids to non-persistent
                                        #wxPython counterparts
        self.parcelDirectory=None       #global directory containing parcels
        self.parcels=[]                 #global list of parcels
        self.storage=None               #global storage object (the local database)
        self.model=None                 #the persistent counterpart

        global app
        assert app==None                #More than one application object doesn't make any sense
        app = self;

        wxInitAllImageHandlers()
        
        chandlerDirectory = os.path.abspath (sys.argv[0])
        resourceFile = os.path.dirname (chandlerDirectory) +\
                       os.sep + "application" +\
                       os.sep + "resources" +\
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
        """
           Append the path contain parcels to the list of paths used to import
         modules and packages. chandlerDirectory is the path to the executable, no
         matter what the current working directory is when we started.
         """
        self.parcelDirectory = os.path.dirname (chandlerDirectory) + os.sep + "parcels"
        sys.path.append (self.parcelDirectory)
        
        self.LoadParcels()
        self.model.SynchronizeView()
        return true  #indicates we succeeded with initialization

    def LoadParcels(self):       
        """
           Load the parcels and call the class method to install them. Packages
        are defined by directories that contain __init__.py. __init__.py must
        define assign the parcel's class name to parcelClassName.
        """
        self.parcels=[]
        for directory in os.listdir(self.parcelDirectory):
            pathToPackage = self.parcelDirectory + os.sep + directory
            if os.path.isdir (pathToPackage) and \
               os.path.exists (pathToPackage + os.sep + "__init__.py"):
                module = __import__(directory, globals, locals, ['*'])
                self.parcels.append (module.parcelClass)
                module.parcelClass.Install()

