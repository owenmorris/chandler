
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"

from wxPython.wx import *
from wxPython.xrc import *
import application.Application
"""Ideally we'd prefer to do a "from application.Application import app", however,
because Application imports ChandlerWindow (the mutually recursive import problem),
app isn't defined yet. Further attempt postpone the include of ChandlerWindow after
app is setup lead to hairballs
"""
from persistence import Persistent
from persistence.dict import PersistentDict


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
        
    def SynchronizeView(self):
        """
          Notifies the window's wxPython view counterpart that they need to
        synchronize themselves to match their peristent model counterpart.
        """
        app = application.Application.app
        if not app.association.has_key(id(self)):
            wxWindow = app.applicationResources.LoadFrame (None, "ChandlerWindow")
            assert (wxWindow != None)
            # FIXME:  Setting the toolbar to None does not work on Linux.
            # However, removing this line on Windows causes an extra grey 
            # box to be drawn.
            if wxPlatform != '__WXGTK__':
                wxWindow.SetToolBar (None)
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
        
    def OnActivate(self, event):
        """
           The Application keeps a copy of the last persistent window openn
        so that the next time we run the application we can open the same window
        """
        app = application.Application.app
        app.wxMainFrame = self
        app.model.mainFrame = self.model
        event.Skip()

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
        assert (self.menuBar != None)
        self.SetMenuBar (self.menuBar)

        self.sideBar = self.FindWindowByName("SideBar")
        assert (self.sideBar != None)
        # FIXME:  See FIXME note above.  FindWindowByName does not work on
        # Linux, but due to the SetToolBar(None) above on Windows, GetToolBar
        # does not work.
        if wxPlatform == '__WXGTK__':
            self.navigationBar = self.GetToolBar()
        else:
            self.navigationBar = self.FindWindowByName("NavigationBar")
        assert (self.navigationBar != None)

        if __debug__:
            """
              In the debugging version, we add a command key combination that
            toggles a debug menu. We currently default to having it on.
            """
            toggleDebugMenuId = wxNewId()
            aTable = wxAcceleratorTable([(wxACCEL_CTRL | wxACCEL_SHIFT | wxACCEL_ALT,
                                          ord('D'), toggleDebugMenuId)])
            self.SetAcceleratorTable(aTable)
            EVT_MENU (self, toggleDebugMenuId, self.OnToggleDebugMenu)

            # turn on the debug menu if necessary
            debugFlag = application.Application.app.model.preferences.GetPreferenceValue('chandler/debugging/debugmenu')
            if debugFlag == None:
                debugFlag = 0
            self.ShowOrHideDebugMenu(debugFlag)
        
        EVT_MOVE(self, self.OnMove)
        EVT_SIZE(self, self.OnSize)
        EVT_CLOSE(self, self.OnClose)
        EVT_ACTIVATE(self, self.OnActivate)

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
                menuBar.Append(debugMenu, _('Debug'))
                menuBar.Check(XRCID('CreateNewRepository'),
                               hasattr (application.Application.app.model,
                                        'CreateNewRepository'))

        def OnToggleDebugMenu(self, event):
            hasMenu = self.HasDebugMenu()
            self.ShowOrHideDebugMenu(not hasMenu)
            preferences = application.Application.app.model.preferences
            preferences.SetPreferenceValue('chandler/debugging/debugmenu', not hasMenu)
            
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
        application.Application.app.model.URLTree.RemoveSideBar(self.model)
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
            
    def GoToUri(self, uri, doAddToHistory = true):
        """
          Navigates to the specified uri.  Steps for this include:
        1) Adjusting the sidebar to represent the currently selected uri  
        2) Adjusting the navigation bar to have the proper history and 
        synchronize its view  3) Telling the parcel to display the proper
        uri.
        """
        # If the window has already been closed
        if not application.Application.app.association.has_key(id(self.model)):
            return false

        if uri.startswith('/'):
            uri = uri[1:]
        if uri.endswith('/'):
            uri = uri[:-1]
        fields = uri.split('/')
        uriParcelName = fields[0]
        parcel = application.Application.app.model.URLTree.UriExists(uriParcelName)
        if parcel == None:
            return false
        
        self.sideBar.model.SelectUri(uri)
        if doAddToHistory:
            self.navigationBar.model.AddUriToHistory(uri)
        self.navigationBar.model.SynchronizeView()
        return parcel.GoToUri(uri)
