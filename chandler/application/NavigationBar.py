__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from wxPython.wx import *
from wxPython.xrc import *
from application.Application import app
from persistence import Persistent
from persistence.list import PersistentList

class NavigationBar(Persistent):
    """
      NavigationBar is the navigation bar in the ChandlerWindow and is the
    model counterpart to the wxNavigationBar view object (see below)..
    """
    def __init__(self):
        """
          The model part of the navigation bar simply tracks the history
        and future of visited uri's.
        """
        self.history = PersistentList()
        self.future = PersistentList()
        
    def SynchronizeView(self):
        """
          Notifies the window's wxPython counterpart that they need to
        synchronize themselves to match their persistent model counterpart.
        Whenever the uri is changed, the navigation bar is notified with 
        the SynchronizeView to update the data to reflect changes.
        """
        if not app.association.has_key(id(self)):
            wxWindow = wxNavigationBar()
            app.association[id(self)] = wxWindow
        else:
            wxWindow = app.association[id(self)]
            
        if len(self.history) > 0:
            wxWindow.SetUri(self.history[-1])
            
    def AddUriToHistory(self, uri):
        """
          Adds the specified uri to the history list and clears the future
        list.
        """
        self.future = PersistentList()
        uriWithCase = app.model.URLTree.GetProperCaseOfURI(uri)
        self.history.append(uriWithCase)
        
    def GetCurrentUri(self):
        """
          Returns the current uri.  Returns None if there is no current uri
        (when first launching the app).
        """
        if len(self.history) == 0:
            return None
        return self.history[-1]        
    
class wxNavigationBar(wxToolBar):
    def __init__(self):
        """The information for the navigation bar is stored in a resource
        file.  To create the navigation bar we must just load it from the
        resource."""
        value = wxPreToolBar ()
        self.this = value.this
        self._setOORInfo (self)
        
        """
          Check to see if we've already created the persistent counterpart,
        if not create it, otherwise get it. Finally add it to the association.
        """
        if not app.model.mainFrame.__dict__.has_key('NavigationBar'):
            self.model = NavigationBar()
            app.model.mainFrame.NavigationBar = self.model
        else:
            self.model = app.model.mainFrame.NavigationBar
        """
           The model persists, so it can't store a reference to self, which
        is a wxApp object. We use the association to keep track of the
        wxPython object associated with each persistent object.
        """
        app.association[id(self.model)] = self
        """
           There isn't a EVT_DESTROY function, so we'll implement it do
        what the function would have done.
        """
        EVT_WINDOW_DESTROY (self, self.OnDestroy)
        
        EVT_TOOL(self, XRCID("prev"), self.GoPrev)
        EVT_TOOL(self, XRCID("next"), self.GoNext)
        EVT_TOOL(self, XRCID("stop"), self.DoStop)
        EVT_TOOL(self, XRCID("reload"), self.DoReload)
        EVT_TOOL(self, XRCID("home"), self.GoHome)
        EVT_TEXT_ENTER(self, XRCID("uriBox"), self.UriEntered)
        
    def UriEntered(self, event):
        """When the user enters a location in the uri text box of the toolbar,
        we navigate to that uri.  If switching to that uri fails (because of
        a typo or because that uri does not exist), then we simply reset the
        text box to the current uri."""
        if not hasattr(self, 'uriBox'):
            self.uriBox = self.FindWindowByName('uriBox')
        oldUri = self.model.history[-1]
        newUri = self.uriBox.GetValue()
        
        if not app.wxMainFrame.GoToUri(newUri):
            print "Failed to navigate to " + newUri
            print "setting to " + oldUri
            self.uriBox.SetValue(oldUri)
        
    def SetUri(self, uri):
        """Sets the text of the uri text field in the navigation bar to reflect
        the current view."""
        if not hasattr(self, 'uriBox'):
            self.uriBox = self.FindWindowByName('uriBox')
        self.uriBox.SetValue(uri)

    def GoPrev(self, event):
        """Change to the most recent past view.  This moves you back one
        in the history of views that you have visited.  It causes the view
        that you are currently on to be added to the future list (for use
        with the Next button) and moves you to the last remembered view.
        This new view that you move to will now be the last element in the
        history list."""
        # The current view will always be in the history, so we need more
        # than 1 to be able to pop off a new view to visit.
        if len(self.model.history) > 1:
            currentLocation = self.model.history.pop()
            self.model.future.append(currentLocation)
            newUri = self.model.history[-1]
            app.wxMainFrame.GoToUri(newUri, false)

    def GoNext(self, event):
        """Change to the next view in your future list.  The Next button
        will only have an effect if the last navigation you did was to 
        use the Prev button.  If so, then the last item added to the future
        list will be popped off, added to the history list, and you will
        navigate to that view."""
        if len(self.model.future) > 0:
            newUri = self.model.future.pop()
            self.model.history.append(newUri)
            app.wxMainFrame.GoToUri(newUri, false)

    def DoStop(self, event):
        pass
    
    def DoReload(self, event):
        pass
    
    def GoHome(self, event):
        pass
    
    def OnDestroy(self, event):
        """
          Remove from the association when the navigation bar is destroyed.
        """
        del app.association[id(self.model)]
    
    