__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"


import os, sys, stat, gettext, locale
from wxPython.wx import *
from wxPython.xrc import *

from application.Preferences import Preferences
from application.SplashScreen import SplashScreen
from application.URLTree import URLTree
from persistence import Persistent 
from persistence.list import PersistentList

import application.ChandlerWindow
import PreferencesDialog
import ChandlerJabber
import PresencePanel

from zodb import db 
from zodb.storage.file import FileStorage

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
	VERSION = 22
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
		self.URLTree             tree of url's
		self.version             see __setstate__
		"""
		self.preferences = Preferences()
		self.mainFrame = application.ChandlerWindow.ChandlerWindow()
		self.URLTree = URLTree()
		self.version = Application.VERSION
	
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
			splash = SplashScreen(_("Welcome to Chandler"), false)
			splash.Show(true)
			
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
	self.parcels                  global list of parcel classes
	self.model                    the persistent counterpart
	self.storage                  ZODB low level database
	self.db                       ZODB high level database (object cache)
	self.connection               connection to ZODB
	self.dbroot                   ZODB root object tree
	self.homeDirectory            path to a folder in the user's home directory
	self.wxMainFrame              active wxChandlerWindow
	self.locale                   locale used for internationalization
	self.jabberClient             state of jabber client including presence dictionary
	
	In the future we may replace ZODB with another database that provides 
	similar functionality
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
		self.presenceWindow = None
		
		global app
		assert app == None     #More than one app object doesn't make sense
		app = self

		wxInitAllImageHandlers()

		self.chandlerDirectory = os.path.dirname (os.path.abspath (sys.argv[0]))
		
		# Setup internationalization
		# To experiment with a different locale, try 'fr' and wxLANGUAGE_FRENCH
		os.environ['LANGUAGE'] = 'en'
		self.locale = wxLocale(wxLANGUAGE_ENGLISH)
		
		# @@@ Sets the python locale, used by wxCalendarCtrl and mxDateTime
		# for month and weekday names. When running on Linux, 'en' is not
		# understood as a locale, nor is 'fr'. On Windows, you can try 'fr'.
		# locale.setlocale(locale.LC_ALL, 'en')
		
		wxLocale_AddCatalogLookupPathPrefix('locale')
		self.locale.AddCatalog('Chandler.mo')
		gettext.install('Chandler', self.chandlerDirectory + os.sep + 'locale')
		
		resourceFile = "application" +\
						os.sep + "application.xrc"

		#Check for the file's existence in debugging code
		assert stat.S_ISREG(os.stat(resourceFile)[stat.ST_MODE])
		self.applicationResources = wxXmlResource(resourceFile)

		#Open the database
		self.storage = FileStorage ('_CHANDLER_')
		self.db = db.DB (self.storage)
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
		EVT_MENU(self, XRCID ("About"), self.OnAbout)
		EVT_MENU(self, XRCID ("Preferences"), self.OnPreferences)
		
		# view menu handlers
		EVT_MENU(self, XRCID("TogglePresenceWindow"), self.TogglePresenceWindow)
		
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
			EVT_MENU(self, XRCID ('CreateNewRepository'), 
						self.OnCreateNewRepository)
			
		EVT_MENU(self, -1, self.OnCommand)
		EVT_UPDATE_UI(self, -1, self.OnCommand)

		# allocate the Jabber client, logging in if possible
		self.jabberClient = ChandlerJabber.JabberClient(self)
		
		self.InCommand = false          #used by OnCommand
		self.OpenStartingUri()

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

	def OpenStartingUri(self):
		"""
			Opens the proper uri when the application first starts.  If
		this is the first time running, then we just take the first item
		in the URLTree.  If we have persisted, then we use the last
		remembered uri.
		"""
		if not hasattr(self, 'wxMainFrame'):
			self.wxMainFrame = app.association[id(self.model.mainFrame)]
		uri = self.wxMainFrame.navigationBar.model.GetCurrentUri()
		if uri != None:
			self.wxMainFrame.GoToUri(uri, false)
		else:
			children = self.model.URLTree.GetUriChildren('')
			if len(children) > 0:
				self.wxMainFrame.GoToUri(children[0], true)
			
	def OnQuit(self, event):
		"""
			Exit the application
		"""
		self.ExitMainLoop ()

	# for now, we show the splash screen for the about command.
	def OnAbout(self, event):
		"""
			Show the splash screen in response to the about command
		"""
		splash = SplashScreen(_("About Chandler"), useTimer=false)
		splash.Show(true)

	# handle the preferences command by showing the preferences dialog
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
			
	def LoadParcels(self):       
		"""
			Load the parcels and call the class method to install them. Packages
		are defined by directories that contain __init__.py. __init__.py must
		define assign the parcel's class name to parcelClass. For example
		"parcelClass = CalendarView.CalendarView", where the first string 
		before the dot is the file, (CalendarView.py) and the second string is
		the class e.g. CalendarView. See calendar/__init__.py for an example.
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

	# return a list of views accessible to the user represented by
	# the passed in jabberID by looping through all the parcels
	# and asking them
	def GetAccessibleViews(self, jabberID):
		parcels = self.model.URLTree.GetParcelList()
		accessibleViews = []
		
		for parcel in parcels:
			parcelViews = parcel.GetAccessibleViews(jabberID)
			for view in parcelViews:
				accessibleViews.append(view)
				
		return accessibleViews
	
	# handler for the Show/Hide Presence Window command
	def TogglePresenceWindow(self, event):
		if self.presenceWindow == None:
			title = _("Presence Panel")
			self.presenceWindow = PresencePanel.PresenceWindow(title, self.jabberClient)
			self.presenceWindow.CentreOnScreen()
			self.presenceWindow.Show()
			EVT_CLOSE(self.presenceWindow, self.PresenceWindowClosed)
		else:
			self.presenceWindow.Close()
			self.presenceWindow = None
	
	# handle the presence window closing by clearing the reference
	def PresenceWindowClosed(self, event):
		self.presenceWindow.Destroy()
		self.presenceWindow = None
		
	# HandleSystemPreferences is called after the preferences
	# changed to handle changing the state for varous
	# system preferences
	def HandleSystemPreferences(self):
		self.LoginIfNecessary()
		if __debug__:
			self.SetupDebugMenu()
		
	# LoginIfNecessary logs in to the jabber server if necessary
	def LoginIfNecessary(self):
		if not self.jabberClient.IsConnected():
			self.jabberClient.ReadAccountFromPreferences()
			self.jabberClient.Login()

	# make the visibility of the debug menu correspond to the
	# preference
	def SetupDebugMenu(self):
		debugFlag = self.model.preferences.GetPreferenceValue('chandler/debugging/debugmenu')
		self.wxMainFrame.ShowOrHideDebugMenu(debugFlag)
