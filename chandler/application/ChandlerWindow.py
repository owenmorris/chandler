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

DEFAULT_WINDOW_WIDTH = -1
DEFAULT_WINDOW_HEIGHT = -1
STATUS_WELCOME_MESSAGE = "Welcome!"

class ChandlerWindow(wxFrame):
    def __init__(self, parent, app, componentStrings, id = -1, 
                 title = "Chandler", pos = wxPyDefaultPosition, 
                 size = (DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT),
                 style = wxDEFAULT_FRAME_STYLE):
        """Sets up the Chandler Window.  Each window has a location bar, an
        actions bar, a status bar, and a menu bar that must be allocated and
        setup.  There is also a panel where the components get to display 
        themselves (self._displayPanel).  In order to get that display panel 
        setup, we must load each of the components, select a default one, and
        display it."""

        wxFrame.__init__(self, parent, id, title, pos, size, style)
        
        self._app = app
        self.CreateStatusBar()
        self.SetStatusText(STATUS_WELCOME_MESSAGE)  
        
        self._locationBar = LocationBar(self)

        # Main window
        # We have to put the actions toolbar into the main window because
        # multiple toolbars are not supported
        self._actionsBarSizer = wxBoxSizer(wxVERTICAL)
        self._actionsBar = ActionsBar(self)
        self._actionsBarSizer.Add(self._actionsBar, 0, wxEXPAND)
        
        self._bodyPanel = wxPanel(self, -1)
        self._bodyPanelSizer = wxBoxSizer(wxHORIZONTAL)
        self._sideBar = SideBar(self._bodyPanel, self)
        
        self._componentInterface = ComponentInterface(self)
        self._components = self.__LoadComponents(componentStrings, self._bodyPanel)
        
        self._displayPanel = wxPanel(self, -1)
        self._bodyPanelSizer.Add(self._sideBar, 0, wxEXPAND)
        self._bodyPanelSizer.Add(self._displayPanel, 1, wxEXPAND)
        
        self._bodyPanel.SetAutoLayout(true)
        self._bodyPanel.SetSizer(self._bodyPanelSizer)
        self._actionsBarSizer.Add(self._bodyPanel, 1, wxEXPAND)

        orderedComponents = self.__OrderComponents(self._components)

        self._menuBar = MenuBar(self, orderedComponents)
        self._sideBar.PopulateSideBar(orderedComponents)

        self.SetAutoLayout(true)
        self.SetSizer(self._actionsBarSizer)

        if len(orderedComponents) > 0:
            defaultUri = orderedComponents[0].data["DefaultUri"]
            self.GoToUri(defaultUri)

        EVT_CLOSE(self, self.__OnCloseWindow)
        EVT_SIZE(self, self.__OnSizeWindow)

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
                component.Load(parent, self, self._componentInterface)
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
        component = self._components[componentName]
        if doAddToHistory:
            self._locationBar.AddLocationHistory(uri)
        self._locationBar.SetUri(uri) #displays the uri in the location bar
        newView = component.data["View"][viewName]
        self.__ChangeActiveView(newView, component)
        # Make sure that the proper item is selected in the sidebar
        self._sideBar.navPanel.SelectItem(uri)
        
    def __ChangeActiveView(self, newView, component):
        """Changes the window to display the supplied view.  First determines
        if the view simply needs to be updated (if we are navigating to the
        same view that is being displayed) and if so refreshes the view.  If 
        not, it adds changes self._displayPanel to be the proper view."""
        if newView != self._displayPanel:
            self._bodyPanelSizer.Remove(self._displayPanel)
            self._displayPanel.Hide()
            self._displayPanel = newView
            self._bodyPanelSizer.Add(self._displayPanel, 1, wxEXPAND)
            self._displayPanel.Show()
            self._bodyPanelSizer.Layout()
            self._menuBar.SelectComponent(component.data["ComponentName"])
        else:
            self._displayPanel.Hide()
            self._displayPanel.Show()
            self._bodyPanelSizer.Layout()
        
    def NewViewer(self):
        """Create a new Chandler window.  We notify the application that
        a request for a new window as been made."""
        self._app.OpenNewViewer(self.GetPosition())
        
    def Quit(self):
        """Tells the application that the quit menu was selected."""
        self._app.QuitApp()
        
    def ShowLocationBar(self, doShow):
        """Show or hide the location toolbar.  This will only have an effect
        if doShow does not match the current state of the location toolbar."""
        if self._locationBar.locationBar.IsShown() != doShow: 
            self._locationBar.locationBar.Show(doShow)
            self.Layout()
        
    def ShowActionsBar(self, doShow):
        """Show or hide the actions toolbar.  This will only have an effect
        if doShow does not match the current state of the actions toolbar."""
        if self._actionsBar.IsShown() != doShow: 
            self._actionsBar.actionsBar.Show(doShow)
            if doShow:
                self._actionsBarSizer.Remove(self._bodyPanel)
                self._actionsBarSizer.Add(self._actionsBar, 0, wxEXPAND)
                self._actionsBarSizer.Add(self._bodyPanel, 1, wxEXPAND)
            else:
                self._actionsBarSizer.Remove(self._actionsBar)
            self._actionsBarSizer.Layout()
            self.Layout()
 
    def ShowSideBar(self, doShow):
        """Show or hide the sidebar.  This will only have an effect if
        doShow does not match the current state of the sidebar."""
        if self._sideBar.IsShown() != doShow: 
            self._sideBar.Show(doShow)
            if doShow:
                self._bodyPanelSizer.Remove(self._displayPanel)
                self._bodyPanelSizer.Add(self._sideBar, 0, wxEXPAND)
                self._bodyPanelSizer.Add(self._displayPanel, 1, wxEXPAND)
            else:
                self._bodyPanelSizer.Remove(self._sideBar)
            self._bodyPanelSizer.Layout()
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
        self._app.RemoveWindow(self) # Remove it from the app's list of windows
        for key in self._components.keys():
            self._components[key].Unload()
        self.Destroy()
        
    def __OnSizeWindow(self, event):
        size = self.GetSize()
        self._app.SetWindowSize(size)
        event.Skip()
