#!bin/env python

"""The main window which represents the Chandler application.  A 
ChandlerWindow contains all of the appropriate navigation elements
along with a main display area representing the current view."""

__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"


from wxPython.wx import *
from wxPython.xrc import *

import sys
import os

from MenuBar import MenuBar
from LocationBar import LocationBar
from ActionsBar import ActionsBar
from SideBar import SideBar

class ChandlerWindow(wxFrame):
    def __init__(self, parent, app, id=-1, title="Chandler", 
                 pos=wxPyDefaultPosition, size=(1000,800), style=wxDEFAULT_FRAME_STYLE):

        wxFrame.__init__(self, parent, id, title, pos, size, style)
        
        self.app = app
        self.CreateStatusBar(1)
        self.SetStatusText("Welcome!")  
        
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
        
        self.components = self.__LoadComponents(self.bodyPanel)
        # Should use a better huristic for which component to select
        try:
            self.displayPanel = self.components[0].GetCurrentView()
            self.locationBar.AddLocationHistory(self.components[0], "Calendar")
        except:
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
        
        EVT_CLOSE(self, self.OnCloseWindow)

    def __LoadComponents(self, parent):
        """Load each of the components for Chandler.  Among other things, this will
        include the email, calendar, and contacts components.  In order for a component
        to be successfully loaded, it must have it's own folder in the components directory
        of Chandler, that folder must contain an __init__.py file, and it must have a file
        that subclasses ComponentLoader and is named 'Foldername'Loader.py."""
        sys.path.append('./components')
        componentDirectory = os.listdir('./components')

        components = []
        for package in componentDirectory:
            try:
                loaderName = string.capwords(package) + 'Loader'
                path = package + '.' + loaderName
                exec('from ' + path + ' import *')
                exec('loader = ' + loaderName + '(parent, self)')
                components.append(loader)
            except:
                # Could output some sort of warning that a module failed to load
                # In the development release, this exception will happen at least
                # once when the CVS directory is encountered.
                pass
        return components
 
    # Must optimize this method
    def SelectComponent(self, component, viewName):
        """Select the view (indicated by viewName) from the supplied component.
        This method first retrieves the proper view, then replaces the current view
        within the display panel of the window with this new view.  It also updates the 
        menubar (if the component being selected is different from the current one - since
        it will have it's own menu) and selects the proper item in the sidebar."""
        newView = component.GetViewNamed(viewName)
        if newView != self.displayPanel:        
            self.bodyPanelSizer.Remove(self.displayPanel)
            self.displayPanel.Hide()
            self.displayPanel = component.GetViewNamed(viewName)
            self.bodyPanelSizer.Add(self.displayPanel, 1, wxEXPAND)
            self.displayPanel.Show()
            self.bodyPanelSizer.Layout()
            self.menuBar.SelectComponent(component.GetName())
        else:
            self.displayPanel.Hide()
            self.displayPanel.Show()
            self.bodyPanelSizer.Layout()
        self.sideBar.navPanel.SelectItem(viewName)

#    def NewViewer(self):
#        self.app.OpenNewViewer(self.GetPosition())
        
    def Quit(self):
        self.app.QuitApp()
        
    def ShowLocationBar(self, doShow):
        """Show or hide the location toolbar.  This will only have an effect if doShow does not
        match the current state of the location toolbar."""
        if self.locationBar.locationBar.IsShown() == doShow: return
        self.locationBar.locationBar.Show(doShow)
        self.Layout()
        
    def ShowActionsBar(self, doShow):
        """Show or hide the actions toolbar.  This will only have an effect if doShow does not
        match the current state of the actions toolbar."""
        if self.actionsBar.IsShown() == doShow: return
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
        """Show or hide the sidebar.  This will only have an effect if doShow does not
        match the current state of the sidebar."""
        if self.sideBar.IsShown() == doShow: return
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
        """Show or hide the statusbar.  This will only have an effect if doShow does not
        match the current state of the statusbar."""
        statusBar = self.GetStatusBar()
        if statusBar.IsShown() == doShow: return
        statusBar.Show(doShow)
        self.Layout()
    
    def OnCloseWindow(self, event):
#        self.app.RemoveWindow(self) # Remove it from the app's list of windows
        self.Destroy()
