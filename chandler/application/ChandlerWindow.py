#!bin/env python

"""The main window which represents the Chandler application.  A 
ChandlerWindow contains all of the appropriate navigation elements
along with a main display area representing the current view."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


from wxPython.wx import *
from wxPython.xrc import *

import sys
import os

from MenuBar import MenuBar
from LocationBar import LocationBar
from ActionsBar import ActionsBar
from SideBar import SideBar

DEFAULT_WINDOW_WIDTH = 1000
DEFAULT_WINDOW_HEIGHT = 800
STATUS_WELCOME_MESSAGE = "Welcome!"

class ChandlerWindow(wxFrame):
    def __init__(self, parent, app, componentStrings, id = -1, 
                 title = "Chandler", pos = wxPyDefaultPosition, 
                 size = (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT),
                 style = wxDEFAULT_FRAME_STYLE):
        """Sets up the Chandler Window.  Each window has a location bar, an
        actions bar, a status bar, and a menu bar that must be allocated and
        setup.  There is also a panel where the components get to display 
        themselves (self.displayPanel).  In order to get that display panel 
        setup, we must load each of the components, select a default one, and
        display it."""

        wxFrame.__init__(self, parent, id, title, pos, size, style)
        
        self.app = app
        self.CreateStatusBar()
        self.SetStatusText(STATUS_WELCOME_MESSAGE)  
        
        self.locationBar = LocationBar(self)

        # Main window
        # We have to put the actions toolbar into the main window because
        # multiple toolbars are not supported
        self.actionsBarSizer = wxBoxSizer(wxVERTICAL)
        self.actionsBar = ActionsBar(self)
        self.actionsBarSizer.Add(self.actionsBar, 0, wxEXPAND)
        
        self.bodyPanel = wxPanel(self, -1)
        self.bodyPanelSizer = wxBoxSizer(wxHORIZONTAL)
        self.sideBar = SideBar(self.bodyPanel, self)
        
        self.components = self.__LoadComponents(componentStrings, self.bodyPanel)
        
        self.displayPanel = wxPanel(self, -1)
        self.bodyPanelSizer.Add(self.sideBar, 0, wxEXPAND)
        self.bodyPanelSizer.Add(self.displayPanel, 1, wxEXPAND)
        
        self.bodyPanel.SetAutoLayout(true)
        self.bodyPanel.SetSizer(self.bodyPanelSizer)
        self.actionsBarSizer.Add(self.bodyPanel, 1, wxEXPAND)

        self.menuBar = MenuBar(self, self.components)
        self.sideBar.PopulateSideBar(self.components)

        self.SetAutoLayout(true)
        self.SetSizer(self.actionsBarSizer)
        
        if len(self.components) > 0:
            defaultComponent = self.components[0]
            self.GoToUri(defaultComponent, defaultComponent.GetDefaultUri())
        
        EVT_CLOSE(self, self.OnCloseWindow)

    def __LoadComponents(self, componentStrings, parent):
        """This method takes the list of components that was supplied by the
        application and one-by-one, imports each of them and allocates their
        corresponding loader.  The loaders are then returned as a list so
        that the window can access them when needed to switch among
        components."""
        components = []
        for componentString in componentStrings:
            try:
                loaderName, path = componentString
                exec('from ' + path + ' import *')
                exec('loader = ' + loaderName + '(parent, self)')
                components.append(loader)
            except:
                print "Failed to load component"
        return components
 
    def GoToUri(self, component, uri, doAddToHistory = true):
        """Select the view (indicated by the uri) from the supplied
        component.  This method first retrieves the proper view, then replaces
        the current view within the display panel of the window with this new
        view.  It also updates the menubar (if the component being selected is
        different from the current one - since it will have it's own menu) and
        selects the proper item in the sidebar."""
        if doAddToHistory:
            self.locationBar.AddLocationHistory(component, uri)
        self.locationBar.SetUri(uri) #displays the uri in the location bar
        newView = component.GetViewFromUri(uri)
        # Actually display the view
        if newView != self.displayPanel:
            self.bodyPanelSizer.Remove(self.displayPanel)
            self.displayPanel.Hide()
            self.displayPanel = component.GetViewFromUri(uri)
            self.bodyPanelSizer.Add(self.displayPanel, 1, wxEXPAND)
            self.displayPanel.Show()
            self.bodyPanelSizer.Layout()
            self.menuBar.SelectComponent(component.GetComponentName())
        else:
            self.displayPanel.Hide()
            self.displayPanel.Show()
            self.bodyPanelSizer.Layout()
        # Make sure that the proper item is selected in the sidebar
        self.sideBar.navPanel.SelectItem(uri)

    def NewViewer(self):
        """Create a new Chandler window.  We notify the application that
        a request for a new window as been made."""
        self.app.OpenNewViewer(self.GetPosition())
        
    def Quit(self):
        """Tells the application that the quit menu was selected."""
        self.app.QuitApp()
        
    def ShowLocationBar(self, doShow):
        """Show or hide the location toolbar.  This will only have an effect
        if doShow does not match the current state of the location toolbar."""
        if self.locationBar.locationBar.IsShown() == doShow: 
            return
        self.locationBar.locationBar.Show(doShow)
        self.Layout()
        
    def ShowActionsBar(self, doShow):
        """Show or hide the actions toolbar.  This will only have an effect
        if doShow does not match the current state of the actions toolbar."""
        if self.actionsBar.IsShown() == doShow: 
            return
        self.actionsBar.actionsBar.Show(doShow)
        if doShow:
            self.actionsBarSizer.Remove(self.bodyPanel)
            self.actionsBarSizer.Add(self.actionsBar, 0, wxEXPAND)
            self.actionsBarSizer.Add(self.bodyPanel, 1, wxEXPAND)
        else:
            self.actionsBarSizer.Remove(self.actionsBar)
        self.actionsBarSizer.Layout()
        self.Layout()
 
    def ShowSideBar(self, doShow):
        """Show or hide the sidebar.  This will only have an effect if
        doShow does not match the current state of the sidebar."""
        if self.sideBar.IsShown() == doShow: 
            return
        self.sideBar.Show(doShow)
        if doShow:
            self.bodyPanelSizer.Remove(self.displayPanel)
            self.bodyPanelSizer.Add(self.sideBar, 0, wxEXPAND)
            self.bodyPanelSizer.Add(self.displayPanel, 1, wxEXPAND)
        else:
            self.bodyPanelSizer.Remove(self.sideBar)
        self.bodyPanelSizer.Layout()
        self.Layout()
    
    def ShowStatus(self, doShow):
        """Show or hide the statusbar.  This will only have an effect if 
        doShow does not match the current state of the statusbar."""
        statusBar = self.GetStatusBar()
        if statusBar.IsShown() != doShow: 
            statusBar.Show(doShow)
            self.Layout()
    
    def OnCloseWindow(self, event):
        """Closing a window requires that the window notify the application
        that it is going away.  Once that is done, we may destroy the 
        window."""
        self.app.RemoveWindow(self) # Remove it from the app's list of windows
        self.Destroy()
