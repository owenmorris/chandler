__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"

from wxPython.wx import *
import application.Application
"""Ideally we'd prefer to do a "from application.Application import app", however,
because Application imports ChandlerWindow (the mutually recursive import problem),
app isn't defined yet. Further attempt postpone the include of ChandlerWindow after
app is setup lead to hairballs
"""
from Persistence import Persistent, PersistentDict


class ChandlerWindow(Persistent):
    """
      ChandlerWindow is the main window in Chandler and is the model
    counterpart wxChandlerWindow view object (see below). A ChandlerWindow
    contains all of the appropriate navigation elements along with the
    current viewer parcel.
    """
    def __init__(self):
        """
          The initial size (x, y, width, height) is set to (-1, -1, -1, -1) to
        indicate that the window should be tiled to fit the screen, rather than
        being brought up in it's last location and size.
        """
        self.size = PersistentDict.PersistentDict()
        self.size['x'] = -1
        self.size['y'] = -1
        self.size['width'] = -1
        self.size['height'] = -1        
        
    def SynchronizeView(self):
        """
          Notifies the window's wxPython view counterpart that they need to
        synchronize themselves to match their peristent model counterpart.
        """
        app = application.Application.app
        if not app.association.has_key(id(self)):
            wxWindow = app.applicationResources.LoadFrame (None, "ChandlerWindow")
            wxWindow.SetToolBar (None)
            wxWindow.OnInit (self)
            app.association[id(self)] = wxWindow
        else:
            wxWindow = app.association[id(self)]
        
        wxWindow.MoveOntoScreen()

    """
      The following code is under construction.
    """
    #def MenuNewEvent(self):
        #"""Called when the new window menu item has been selected.  Tells the
        #window manager to create a new window."""
        #self._windowManager.NewWindow()
        
    #def MenuQuitEvent(self):
        #"""Called when the quit menu item has been selected.  Tells the
        #window manager to quit the application by closing all open 
        #windows."""
        #self._windowManager.QuitApp()

    #def OnClose(self, event):
        #"""Called whenever this window is to be closed.  First, we remove
        #ourself from the list of open windows, then we send a close message
        #to the wxChandlerWindow so that the wx objects can be cleaned."""
        #self._windowManager.RemoveWindow(self)
        #self._wxWindow.OnClose()
        #self._wxWindow = None
        
    #def OnQuit(self):
        #"""Called whenever the app is quiting.  We send a close message to 
        #the wxChandlerWindow so that the wx objects can be cleaned up and
        #we erase our reference to it, since the wx layer will not be 
        #persisted."""
        #self._wxWindow.OnClose()
        #self._wxWindow = None
        
    #def GoToUri(self, uri, doAddToHistory = true):
        #"""Navigates this window to the supplied uri.  If doAddToHistory
        #is true, then we add the uri to the history list (we won't want
        #to add it if GoToUri is a result of the back button having been
        #pressed)."""
        #self._wxWindow.GoToUri(uri, doAddToHistory)


class wxChandlerWindow(wxFrame):

    def __init__(self):
        """
          wxChandlerWindow is the view counterpart to ChandlerWindow.
        There is a little magic incantation provided by Robin Dunn here
        to wire up the wxWindows object behind the wxPython object.
        wxPreFrame creates the wxWindows C++ object, which is stored
        in the this member. _setOORInfo store a back pointer in the C++
        object to the wxPython object.
        """
        value = wxPreFrame ()
        self.this = value.this
        self._setOORInfo (self)
        
    def OnActivate(self, event):
        """
           The Application keeps a copy of the last persistent window openn
        so that the next time we run the application we can open the same window
        """
        application.Application.app.model.mainFrame = self.model;

    def OnInit(self, model):
        """
          There's a tricky problem here. We need to postpone wiring up OnMove,
        OnSize, etc. after __init__, otherwise OnMove, etc. will get called before
        we've had a chance to set the windows size using the value in our model.
        """
        self.model = model

        self.CreateStatusBar ()
        self.SetStatusText ("Welcome!")

        applicationResources = application.Application.app.applicationResources
        self.menuBar = applicationResources.LoadMenuBar ("MainMenuBar")
        self.SetMenuBar (self.menuBar)

        EVT_MOVE(self, self.OnMove)
        EVT_SIZE(self, self.OnSize)
        EVT_CLOSE(self, self.OnClose)
        EVT_ACTIVATE(self, self.OnActivate)

    def OnMove(self, event):
        """
          Calling Skip causes wxWindows to continue processing the event, which
        will cause the parent class to get a crack at the event.
        """
        event.Skip()
        self.model.size['x'] = self.GetPosition().x
        self.model.size['y'] = self.GetPosition().y

    def OnSize(self, event):
        """
          Calling Skip causes wxWindows to continue processing the event, which
        will cause the parent class to get a crack at the event.
        """
        event.Skip()
        self.model.size['width'] = self.GetSize().x
        self.model.size['height'] = self.GetSize().y

    def OnClose(self, event):
        """
          Closing the last window causes the application to quit.
        """
        del application.Application.app.association[id(self.model)]
        self.Destroy()
        
    def MoveOntoScreen(self):
        """
          Check to see if the window location is off screen and moves it onto
        screen. The code below is currently a place holder. It will change
        depending on how we handle multiple windows (e.g. tiling), multiple
        monitors and various error conditions, like changing monitor size and
        windows off the screen.
        """
        screenSize = wxClientDisplayRect ()
        """
          If the window isn't on the screen, set it to the default size and
        position.
        """
        if self.model.size['x'] < screenSize[0] or \
           self.model.size['y'] < screenSize[1] or \
           self.model.size['x'] + self.model.size['width'] > screenSize[2] or \
           self.model.size['y'] + self.model.size['height'] > screenSize[3]:
            preferences = application.Application.app.model.preferences
            self.SetSize ((preferences.windowSize['width'],
                          preferences.windowSize['height']))
            self.CentreOnScreen ()
        else:
            self.SetRect ((self.model.size['x'],
                           self.model.size['y'],
                           self.model.size['width'],
                           self.model.size['height']))
        rect = self.GetRect()
        self.model.size['x'] = rect.GetX()
        self.model.size['y'] = rect.GetY()
        self.model.size['width'] = rect.GetWidth()
        self.model.size['height'] = rect.GetHeight()
            
    """
      The following code is under construction.
    """
    #def __OrderComponents(self, components):
        #"""Takes the dictionary of components and gives them some ordering as
        #to how they should be displayed both in the sidebar and in the menu.
        #Right now, it is just makes sure that the Calendar comes first."""
        #orderedList = []
        ## This is only to make it so that the Calendar displays first while it
        ## is the only real component we have.  Once we actually have real
        ## components alongside the Calendar, we can remove this.
        #if components.has_key('Calendar'):
            #orderedList.append(components['Calendar'])
        #for key in components.keys():
            #if key != 'Calendar':
                #orderedList.append(components[key])
        #return orderedList
 
    #def GoToUri(self, uri, doAddToHistory = true):
        #"""Select the view (indicated by the uri) from the proper
        #component.  This method first retrieves the proper view, then replaces
        #the current view within the display panel of the window with this new
        #view.  It also updates the menubar (if the component being selected is
        #different from the current one - since it will have it's own menu) and
        #selects the proper item in the sidebar."""
        #uriFields = uri.split("/")
        #componentName = uriFields[1]
        #component = self.__componentRoots[componentName]
        #if doAddToHistory:
            #self._locationBar.AddLocationHistory(uri)
        #self._locationBar.SetUri(uri) #displays the uri in the location bar
        #newView = component.GetViewFromUri(uri)
        #self.__ChangeActiveView(newView, component)
        ## Make sure that the proper item is selected in the sidebar
        #self._sideBar.navPanel.SelectItem(uri)
        
    #def __ChangeActiveView(self, newView, component):
        #"""Changes the window to display the supplied view.  First determines
        #if the view simply needs to be updated (if we are navigating to the
        #same view that is being displayed) and if so refreshes the view.  If 
        #not, it adds changes self._displayPanel to be the proper view."""
        #self._currentComponent = component
        #if newView != self._displayPanel:
            #self._bodyPanelSizer.Remove(self._displayPanel)
            #self._displayPanel.Hide()
            #self._displayPanel = newView
            #self._bodyPanelSizer.Add(self._displayPanel, 1, wxEXPAND)
            #self._displayPanel.Show()
            #self._bodyPanelSizer.Layout()
            #self._menuBar.SelectComponent(component.data["ComponentName"])] = 
        #else:
            #self._displayPanel.Hide()
            #self._displayPanel.Show()
            #self._bodyPanelSizer.Layout()
        
    #def MenuNewEvent(self):
        #"""Called when a new menu event has been generated.  We notify the
        #data layer that the event has been generated."""
        #self._windowData.MenuNewEvent()
        
    #def MenuQuitEvent(self):
        #"""Called when a quit menu event has been generated.  We notify the
        #data layer that the event has been generated."""
        #self._windowData.MenuQuitEvent()
        
    #def ShowLocationBar(self, doShow):
        #"""Show or hide the location toolbar.  This will only have an effect
        #if doShow does not match the current state of the location toolbar."""
        #if self._locationBar.locationBar.IsShown() != doShow: 
            #self._locationBar.locationBar.Show(doShow)
            #self.Layout()
        
    #def ShowActionsBar(self, doShow):
        #"""Show or hide the actions toolbar.  This will only have an effect
        #if doShow does not match the current state of the actions toolbar."""
        #if self._actionsBar.IsShown() != doShow: 
            #self._actionsBar.actionsBar.Show(doShow)
            #if doShow:
                #self._actionsBarSizer.Remove(self._bodyPanel)  
                #self._actionsBarSizer.Add(self._actionsBar, 0, wxEXPAND)
                #self._actionsBarSizer.Add(self._bodyPanel, 1, wxEXPAND)
            #else:
                #self._actionsBarSizer.Remove(self._actionsBar)
            #self._actionsBarSizer.Layout()
            #self.Layout()
 
    #def ShowSideBar(self, doShow):
        #"""Show or hide the sidebar.  This will only have an effect if
        #doShow does not match the current state of the sidebar."""
        #if self._sideBar.IsShown() != doShow: 
            #self._sideBar.Show(doShow)
            #if doShow:
                #self._bodyPanelSizer.Remove(self._displayPanel)
                #self._bodyPanelSizer.Add(self._sideBar, 0, wxEXPAND)
                #self._bodyPanelSizer.Add(self._displayPanel, 1, wxEXPAND)
            #else:
                #self._bodyPanelSizer.Remove(self._sideBar)
            #self._bodyPanelSizer.Layout()
            #self.Layout()
    
    #def ShowStatus(self, doShow):
        #"""Show or hide the statusbar.  This will only have an effect if 
        #doShow does not match the current state of the statusbar."""
        #statusBar = self.GetStatusBar()
        #if statusBar.IsShown() != doShow: 
            #statusBar.Show(doShow)
            #self.Layout()
