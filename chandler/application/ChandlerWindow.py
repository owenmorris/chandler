
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.xrc import *

import string

import application.Application
"""Ideally we'd prefer to do a "from application.Application import app", 
however, because Application imports ChandlerWindow (the mutually recursive 
import problem), app isn't defined yet. Further attempt postpone the include
of ChandlerWindow after app is setup lead to hairballs
"""
from persistence import Persistent
from persistence.dict import PersistentDict

import version

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
        self.size = PersistentDict()
        self.size['x'] = -1
        self.size['y'] = -1
        self.size['width'] = -1
        self.size['height'] = -1
        self.sashSize = -1
        self.showNavigationBar = true
        self.showActionsBar = false
        self.showSideBar = true
        self.showStatusBar = true

    def SynchronizeView(self):
        """
          Notifies the window's wxPython view counterpart that they need to
        synchronize themselves to match their peristent model counterpart.
        """
        app = application.Application.app
        if not app.association.has_key(id(self)):
            wxWindow = app.applicationResources.LoadFrame (None, 
                                                           "ChandlerWindow")
            assert (wxWindow != None)
            wxWindow.OnInit (self)
            app.association[id(self)] = wxWindow
        else:
            wxWindow = app.association[id(self)]

        wxWindow.sideBar.model.SynchronizeView()
        wxWindow.navigationBar.model.SynchronizeView()
        wxWindow.MoveOntoScreen()
        
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

        self.isRemote = false
        
    def OnActivate(self, event):
        """
           The Application keeps a copy of the last persistent window open
        so that the next time we run the application we can open the same 
        window.
        """
        app = application.Application.app
        app.wxMainFrame = self
        app.model.mainFrame = self.model
        event.Skip()

    def OnInit(self, model):
        """
          There's a tricky problem here. We need to postpone wiring up OnMove,
        OnSize, etc. after __init__, otherwise OnMove, etc. will get called 
        before we've had a chance to set the windows size using the value in 
        our model.
        """
        self.model = model

        self.CreateStatusBar ()
        statusBar = self.GetStatusBar()
        statusBar.SetFieldsCount(2)
        statusBar.SetStatusWidths([-1, 200])
        self.SetStatusText("Welcome!", 0)
        self.SetStatusText(version.build, 1)

        self.SetBackgroundColour(wxColor(236, 233, 216))

        assert (self.GetToolBar() == None)
        applicationResources = application.Application.app.applicationResources
        self.menuBar = applicationResources.LoadMenuBar ("MainMenuBar")
        assert (self.menuBar != None)
        self.SetMenuBar (self.menuBar)

        self.sideBar = self.FindWindowByName("SideBar")
        assert (self.sideBar != None)
        self.navigationBar = self.FindWindowByName("NavigationBar")
        assert (self.navigationBar != None)
        self.actionsBar = self.FindWindowByName("ActionsBar")
        assert (self.actionsBar != None)
        self.emptyActionsBar = self.actionsBar
        self.splitterWindow = self.FindWindowByName("SplitterWindow")
        assert (self.splitterWindow != None)

        self.ShowOrHideNavigationBar()
        self.ShowOrHideActionsBar()
        self.ShowOrHideSideBar()
        self.ShowOrHideStatusBar()

        if __debug__:
            """
              In the debugging version, we add a command key combination that
            toggles a debug menu. We currently default to having it on.
            """
            toggleDebugMenuId = wxNewId()
            aTable = wxAcceleratorTable([(wxACCEL_CTRL | wxACCEL_SHIFT |\
                                          wxACCEL_ALT,
                                          ord('D'), toggleDebugMenuId)])
            self.SetAcceleratorTable(aTable)
            EVT_MENU (self, toggleDebugMenuId, self.OnToggleDebugMenu)

            # turn on the debug menu if necessary
            debugFlag = application.Application.app.model.preferences.\
                      GetPreferenceValue('chandler/debugging/debugmenu')
            if debugFlag == None:
                debugFlag = 0
            self.ShowOrHideDebugMenu(debugFlag)
        
        EVT_MOVE(self, self.OnMove)
        EVT_SIZE(self, self.OnSize)
        EVT_CLOSE(self, self.OnClose)
        EVT_ACTIVATE(self, self.OnActivate)
        EVT_MENU(self, XRCID("Close"), self.OnClose)
        EVT_UPDATE_UI(self, XRCID("ShowNavigationBar"), 
                      self.UpdateViewMenuDisplay)
        EVT_MENU(self, XRCID("ShowNavigationBar"), self.OnShowNavigationBar)
        EVT_MENU(self, XRCID("ShowActionsBar"), self.OnShowActionsBar)
        EVT_MENU(self, XRCID("ShowSideBar"), self.OnShowSideBar)
        EVT_MENU(self, XRCID("ShowStatusBar"), self.OnShowStatusBar)        
        EVT_SPLITTER_SASH_POS_CHANGED(self, XRCID('SplitterWindow'), 
                                      self.OnSplitterSashChanged)
        EVT_ERASE_BACKGROUND (self, self.OnEraseBackground)

    if __debug__:
        def HasDebugMenu(self):
            menuBar = self.GetMenuBar()
            index = menuBar.FindMenu(_('Debug'))
            return index != wxNOT_FOUND
        
        def ShowOrHideDebugMenu(self, showFlag):
            hasMenu = self.HasDebugMenu()
            if hasMenu == showFlag:
                return
            
            menuBar = self.GetMenuBar()  
            if hasMenu:
                index = menuBar.FindMenu(_('Debug'))
                oldMenu = menuBar.Remove(index)
                del oldMenu
            else:
                applicationResources = application.Application.app.applicationResources
                debugMenu = applicationResources.LoadMenu('DebugMenu')
                index = menuBar.GetMenuCount()
                """
                  On Macintosh the debug menu is owned by the system so you 
                can't add an item after it.
                """
                if wxPlatform == '__WXMAC__':
                    index -= 1
                menuBar.Insert(index, debugMenu, _('Debug'))
                menuBar.Check(XRCID('CreateNewRepository'),
                               hasattr (application.Application.app.model,
                                        'CreateNewRepository'))

        def OnToggleDebugMenu(self, event):
            hasMenu = self.HasDebugMenu()
            self.ShowOrHideDebugMenu(not hasMenu)
            preferences = application.Application.app.model.preferences
            preferences.SetPreferenceValue('chandler/debugging/debugmenu', 
                                           not hasMenu)
            
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
        if hasattr(self, "wasClosed"):
            return
        self.wasClosed = True

        app = application.Application.app

        app.agentManager.Stop()
        app.repository.commit(purge=True)
        app.repository.close()

        del app.association[id(self.model)]
        app.model.URLTree.RemoveSideBar(self.model)
        del app.applicationResources
        if self.activeParcel:
            self.activeParcel.Deactivate()

        del app.wxMainFrame
        self.Destroy()
        
    def UpdateViewMenuDisplay(self, event):
        """
          This method is called when the view menu is displayed.  It sets up
        whether some of the menu items should be checked or not according to
        whether or not their corresponding ui elements are being displayed.
        """
        self.menuBar.Check(XRCID("ShowNavigationBar"), 
                           self.model.showNavigationBar)
        self.menuBar.Check(XRCID("ShowActionsBar"), self.model.showActionsBar)
        self.menuBar.Check(XRCID("ShowSideBar"), self.model.showSideBar)
        self.menuBar.Check(XRCID("ShowStatusBar"), self.model.showStatusBar)
        event.Skip()
            
    def OnShowNavigationBar(self, event):
        """
          Called when the 'Show Navigation Bar' menu item is selected.  It
        toggles the display state of the NavigationBar.
        """
        self.model.showNavigationBar = not self.model.showNavigationBar
        self.ShowOrHideNavigationBar()
        
    def ShowOrHideNavigationBar(self):
        """
          Shows or hides the NavigationBar according to the variable set within
        ChandlerWindow.
        """
        if self.navigationBar.IsShown() != self.model.showNavigationBar:
            self.navigationBar.Show(self.model.showNavigationBar)
            if not hasattr(self, "verticalSizer"):
                self.verticalSizer = self.navigationBar.GetContainingSizer()
            
            if self.model.showNavigationBar:
                self.verticalSizer.Prepend(self.navigationBar, 0, wxEXPAND)
            else:
                self.verticalSizer.Remove(self.navigationBar)
            self.verticalSizer.Layout()
            
    def OnShowActionsBar(self, event):
        """
          Called when the 'Show Actions Bar' menu item is selected.  It
        toggles the display state of the ActionsBar.
        """
        self.model.showActionsBar = not self.model.showActionsBar
        self.ShowOrHideActionsBar()
    
    def ShowOrHideActionsBar(self):
        """
          Shows or hides the ActionsBar according to the variable set within
        ChandlerWindow.
        """
        if self.actionsBar.IsShown() != self.model.showActionsBar:
            self.actionsBar.Show(self.model.showActionsBar)
            if not hasattr(self, "verticalSizer"):
                self.verticalSizer = self.actionsBar.GetContainingSizer()
                
            if self.model.showActionsBar:
                if self.model.showNavigationBar:
                    self.verticalSizer.Remove(self.navigationBar)
                    self.verticalSizer.Prepend(self.actionsBar, 0, wxEXPAND)
                    self.verticalSizer.Prepend(self.navigationBar, 0, wxEXPAND)
                else:
                    self.verticalSizer.Prepend(self.actionsBar, 0, wxEXPAND)
            else:
                self.verticalSizer.Remove(self.actionsBar)
            self.verticalSizer.Layout()
            
    def ReplaceActionsBar(self, newActionsBar):
        """
          Replaces the ActionsBar with the one provided.  This is called
        whenever we change parcels so that the current parcel can display
        its version of the ActionsBar.
        """
        if newActionsBar == None:
            newActionsBar = self.emptyActionsBar
        if self.actionsBar.IsShown():
            if not hasattr(self, 'verticalSizer'):
                self.verticalSizer = self.actionsBar.GetContainingSizer()
       
            if self.model.showNavigationBar:
                self.verticalSizer.Remove(self.navigationBar)
                self.verticalSizer.Remove(self.actionsBar)
                self.actionsBar.Show(False)
                self.actionsBar = newActionsBar
                self.verticalSizer.Prepend(self.actionsBar, 0, wxEXPAND)
                self.actionsBar.Show(True)
                self.verticalSizer.Prepend(self.navigationBar, 0, wxEXPAND)
            else:
                self.verticalSizer.Remove(self.actionsBar)
                self.actionsBar.Show(False)
                self.actionsBar = newActionsBar
                self.verticalSizer.Prepend(self.actionsBar, 0, wxEXPAND)
                self.actionsBar.Show(True)
        else:
            self.actionsBar = newActionsBar
            self.actionsBar.Show(False)
            
    def OnShowSideBar(self, event):
        """
          Called when the 'Show Side Bar' menu item is selected.  It
        toggles the display state of the SideBar.
        """
        self.model.showSideBar = not self.model.showSideBar
        self.ShowOrHideSideBar()
        
    def ShowOrHideSideBar(self):
        """
          Shows or hides the SideBar according to the variable set within
        ChandlerWindow.
        """
        if self.sideBar.IsShown() != self.model.showSideBar:
            self.sideBar.Show(self.model.showSideBar)
            if self.model.showSideBar:
                self.splitterWindow.SplitVertically(self.sideBar, 
                                           self.splitterWindow.GetWindow1())
                self.splitterWindow.SetSashPosition (self.model.sashSize)
            else:
                self.splitterWindow.Unsplit(self.sideBar)

    def OnShowStatusBar(self, event):
        """
          Called when the 'Show Status Bar' menu item is selected.  It
        toggles the display state of the StatusBar.
        """
        self.model.showStatusBar = not self.model.showStatusBar
        self.ShowOrHideStatusBar()

    def ShowOrHideStatusBar(self):
        """
          Shows or hides the StatusBar according to the variable set within
        ChandlerWindow.
        """
        statusBar = self.GetStatusBar()
        if statusBar.IsShown() != self.model.showStatusBar:
            statusBar.Show(self.model.showStatusBar)
            self.Layout()
        
    def OnSplitterSashChanged(self, event):
        self.model.sashSize = event.GetSashPosition ()

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
           self.model.size['y'] + self.model.size['height'] > screenSize[3] or \
           self.model.sashSize < 0:
            preferences = application.Application.app.model.preferences
            self.SetSize ((preferences.windowSize['width'],
                          preferences.windowSize['height']))
            self.CentreOnScreen ()
        else:
            self.SetRect ((self.model.size['x'],
                           self.model.size['y'],
                           self.model.size['width'],
                           self.model.size['height']))
            self.splitterWindow.SetSashPosition (self.model.sashSize)
            
        rect = self.GetRect()
        self.model.size['x'] = rect.GetX()
        self.model.size['y'] = rect.GetY()
        self.model.size['width'] = rect.GetWidth()
        self.model.size['height'] = rect.GetHeight()
        self.model.sashSize = self.splitterWindow.GetSashPosition ()

    # parse a url to extract the remote address and parcel name
    # returns a tuple of (parcelname, remoteaddresss, localurl)
    # FIXME: this shouldn't be part of ChandlerWindow, but for now
    # we don't have a better place for it
    def ParseURL(self, url):
        if url.startswith('/'):
            url = url[1:]
        if url.endswith('/'):
            url = url[:-1] 
        fields = url.split('/')
        
        remoteaddress = None
        parcelname = fields[0]
        localurl = url
        
        if parcelname.find('@') > -1 and len(fields) > 1:
            remoteaddress = fields[0]
            parcelname = fields[1]
            localurl = string.join(fields[1:], '/')
        
        return (parcelname, remoteaddress, localurl)

    def IsRemoteURL(self):
        return self.isRemote
    
    def GoToURL(self, url, doAddToHistory = true):
        """
          Navigates to the specified url.  Steps for this include:
        1) Adjusting the sidebar to represent the currently selected url  
        2) Adjusting the navigation bar to have the proper history and 
        synchronize its view  3) Telling the parcel to display the proper
        url.
        """
        # If the window has already been closed
        if not application.Application.app.association.has_key(id(self.model)):
            return false

        parcelname, remoteaddress, localurl = self.ParseURL(url)
        parcel =\
               application.Application.app.model.URLTree.URLExists(parcelname)
        if parcel == None:
            return false
        
        """
          give the parcel a chance to redirect the url to another parcel.  
        This allows the roster to offer links to other parcels, for example
        """
        mappedURL = parcel.RedirectURL(url)
        if mappedURL != url:
            url = mappedURL
            parcelname, remoteaddress, localurl = self.ParseURL(url)
            parcel =\
              application.Application.app.model.URLTree.URLExists(parcelname)
            if parcel == None:
                return false
        
        self.isRemote = remoteaddress != None
            
        self.sideBar.model.SelectURL(localurl)
        if doAddToHistory:
            self.navigationBar.model.AddURLToHistory(url)
        self.navigationBar.model.SynchronizeView()
        return parcel.GoToURL(remoteaddress, localurl)

    def OnEraseBackground (self, event):
        """
          Override OnEraseBackground to avoid erasing background. Instead
        implement OnDrawBackground to draw/erase the background. This
        design alternative will eliminate flicker
        """
        pass

