__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


from wxPython.wx import *

from application.ViewerParcel import *
from application.ClickableText import ClickableText
from application.ClickableImage import ClickableImage
from application.URLTree import URLTree

from persistence import Persistent
from persistence.list import PersistentList

class InstalledParcelsViewer(ViewerParcel):
    def __init__(self):
        ViewerParcel.__init__(self)
        
    def Install(theClass):
        """
          The InstalledParcelsViewer behaves differently than the default
        type of viewer parcel.  Since it is accessed as the root item in the
        URLTree, and shouldn't be displayed in the SideBar, we override
        the default behavior of Install.
        """
        parcel = app.model.URLTree.URLExists('')
        if parcel == None or \
           parcel.__module__ != theClass.__module__:
            if type (theClass) == types.ClassType:
                instance = new.instance (theClass, {})
            else:
                instance = theClass.__new__ (theClass)
            instance.__init__()
            app.model.URLTree.SetParcelAtURL('', instance)
        
    Install = classmethod(Install)
           

class wxInstalledParcelsViewer(wxViewerParcel):
    def OnInit(self):
        # Set up a base id for generated menus
        # @@@ We may run into a problem with collisions with other
        # parcels.
        self.commandID = 900
        self.container = wxBoxSizer(wxVERTICAL)
        self.titleFont = wxFont(18, wxSWISS, wxNORMAL, wxNORMAL, false, 'Arial')
        self.title = wxStaticText(self, -1, _("Installed Parcels"))
        self.title.SetFont(self.titleFont)
        self.container.Add(self.title, 0, wxEXPAND)

        self.displaySizer = wxBoxSizer(wxHORIZONTAL)
        self.displaySizer.Add(40, 0, 0, wxEXPAND)

        self.parcelListSizer = wxBoxSizer(wxVERTICAL)
        self.parcelListSizer.Add(0, 10, 0, wxEXPAND)

        self.displaySizer.Add(self.parcelListSizer, 0, wxEXPAND)
        self.container.Add(self.displaySizer, 1, wxEXPAND)
        
        parcels = app.model.URLTree.GetParcelList()        
        for parcel in parcels:
            self.__AddParcelToView(parcel.displayName, parcel.description, '')
                
        self.SetSizerAndFit(self.container)

    def ReplaceViewParcelMenu(self):
        """
          Override the default behavior of ReplaceViewParcelMenu so that
        we can add menu items for each of the installed parcels.
        """
        self.parcelMenu = wxViewerParcel.ReplaceViewParcelMenu(self)
        self.AddInstalledParcelsToMenu()
        
    def AddInstalledParcelsToMenu(self):
        """
          We add a menu item for each parcel that has been installed, so 
        that we can navigate to that parcel.
        """
        parcels = app.model.URLTree.GetParcelList()

        # Remove the item that was put in the menu (via xrc) in case no
        # parcels got installed.
        if len(parcels) > 0:
            id = self.parcelMenu.FindItem(_('None'))
            self.parcelMenu.Remove(id)
            
        for parcel in parcels:
            self.parcelMenu.Append(self.commandID, parcel.displayName)
            handler = SelectParcelHandler(parcel.displayName)
            EVT_MENU(self, self.commandID, handler.SelectParcel)
            self.commandID += 1
            
    def __AddParcelToView(self, name, desc, icon):
        """
          Add an item to the view for every parcel that has been installed
        into Chandler.
        """
        self.nameFont = wxFont(18, wxSWISS, wxNORMAL, wxNORMAL, true, 'Arial')
        self.descFont = wxFont(10, wxSWISS, wxNORMAL, wxNORMAL, false, 'Arial')

        horizontalSizer = wxBoxSizer(wxHORIZONTAL)

        if icon != '':
            bmp = ClickableImage(self, icon, self.__SelectURL, name)
            horizontalSizer.Add(bmp, 0, wxEXPAND)
            horizontalSizer.Add(20, 0, 0, wxEXPAND)
        
        title = ClickableText(self, name, self.__SelectURL, name)
        w,h,d,e = self.GetFullTextExtent(name, self.nameFont)
        title.SetFont(self.nameFont)
        title.SetSize(wxSize(w, h))
        horizontalSizer.Add(title, 0, wxEXPAND)

        self.parcelListSizer.Add(horizontalSizer, 0, wxEXPAND)

        description = wxStaticText(self, -1, desc)
        w,h,d,e = self.GetFullTextExtent(desc, self.descFont)
        description.SetFont(self.descFont)
        description.SetSize(wxSize(w, h))
        self.parcelListSizer.Add(description, 0, wxEXPAND)

        self.parcelListSizer.Add(0, 20, 0, wxEXPAND)

    def __SelectURL(self, name):
        """This method is passed to the clickable items.  When they
        are clicked, they will call this method, passing the name
        of the viewer parcel that is to be selected.  This method 
        will then select that viewer parcel."""
        app.wxMainFrame.GoToURL(name)


class SelectParcelHandler:
    """
      The handler used by menu items to select the parcel that is chosen.
    """
    def __init__(self, url):
        self.url = url
        
    def SelectParcel(self, event):
        app.wxMainFrame.GoToURL(self.url, true)

