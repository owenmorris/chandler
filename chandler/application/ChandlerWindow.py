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

from ComponentInterface import ComponentInterface
from MenuBar import MenuBar
from LocationBar import LocationBar
from ActionsBar import ActionsBar
from SideBar import SideBar

DEFAULT_WINDOW_WIDTH = -1 #1000
DEFAULT_WINDOW_HEIGHT = -1 #800
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
        
        self.componentInterface = ComponentInterface(self)
        self.components = self.__LoadComponents(componentStrings, self.bodyPanel)
        
        self.displayPanel = wxPanel(self, -1)
        self.bodyPanelSizer.Add(self.sideBar, 0, wxEXPAND)
        self.bodyPanelSizer.Add(self.displayPanel, 1, wxEXPAND)
        
        self.bodyPanel.SetAutoLayout(true)
        self.bodyPanel.SetSizer(self.bodyPanelSizer)
        self.actionsBarSizer.Add(self.bodyPanel, 1, wxEXPAND)

        orderedComponents = self.__OrderComponents(self.components)

        self.menuBar = MenuBar(self, orderedComponents)
        self.sideBar.PopulateSideBar(orderedComponents)

        self.SetAutoLayout(true)
        self.SetSizer(self.actionsBarSizer)

        if len(orderedComponents) > 0:
            defaultUri = orderedComponents[0].data["DefaultUri"]
            self.GoToUri(defaultUri)

        EVT_CLOSE(self, self.__OnCloseWindow)

    def __LoadComponents(self, componentStrings, parent):
        """This method takes the list of components that was supplied by the
        application and one-by-one, imports each of them and starts their
        loading.  The components are then returned as a list so that the
        window can access them when needed to switch among components."""
        components = {}
        for componentString in componentStrings:
            try:
                componentName, path = componentString
                exec('from ' + path + ' import *')
                exec('component = ' + componentName + '()')
                component.Load(parent, self, self.componentInterface)
                name = component.data["ComponentName"]
                components[name] = component
            except:
                print "Failed to load component from " + componentName
        return components
    
    def __OrderComponents(self, components):
        """Takes the dictionary of components and gives them some ordering as
        to how they should be displayed both in the sidebar and in the menu.
        Right now, it is just makes sure that the Calendar comes first."""
        orderedList = []
        # This is only to make it so that the Calendar displays first while it
        # is the only real component we have.  Once we actually have real
        # components alongside the Calendar, we can remove this.
        if components.has_key('Calendar'):
            orderedList.append(components['Calendar'])
        for key in components.keys():
            if key != 'Calendar':
                orderedList.append(components[key])
        return orderedList
 
    def GoToUri(self, uri, doAddToHistory = true):
        """Select the view (indicated by the uri) from the proper
        component.  This method first retrieves the proper view, then replaces
        the current view within the display panel of the window with this new
        view.  It also updates the menubar (if the component being selected is
        different from the current one - since it will have it's own menu) and
        selects the proper item in the sidebar."""
        uriFields = uri.split("/")
        componentName = uriFields[0]
        viewName = uriFields.pop()
        component = self.components[componentName]
        if doAddToHistory:
            self.locationBar.AddLocationHistory(uri)
        self.locationBar.SetUri(uri) #displays the uri in the location bar
        newView = component.data["View"][viewName]
        # Actually display the view
        if newView != self.displayPanel:
            self.bodyPanelSizer.Remove(self.displayPanel)
            self.displayPanel.Hide()
            self.displayPanel = newView
            self.bodyPanelSizer.Add(self.displayPanel, 1, wxEXPAND)
            self.displayPanel.Show()
            self.bodyPanelSizer.Layout()
            self.menuBar.SelectComponent(component.data["ComponentName"])
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
    
    def __OnCloseWindow(self, event):
        """Closing a window requires that the window notify the application
        that it is going away.  Once that is done, we may destroy the 
        window."""
        self.app.RemoveWindow(self) # Remove it from the app's list of windows
        self.Destroy()
