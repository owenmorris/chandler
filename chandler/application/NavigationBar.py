__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from wxPython.wx import *
from wxPython.xrc import *
from application.Application import app
from model.schema.AutoItem import AutoItem

class NavigationBar(AutoItem):
    """
      NavigationBar is the navigation bar in the ChandlerWindow and is the
    model counterpart to the wxNavigationBar view object (see below)..
    """
    def __init__(self, **args):
        """
          The model part of the navigation bar simply tracks the history
        and future of visited url's.
        """
        super (NavigationBar, self).__init__ (**args)
        self.newAttribute ("history", [])
        self.newAttribute ("future", [])

        
    def SynchronizeView(self):
        """
          Notifies the window's wxPython counterpart that they need to
        synchronize themselves to match their persistent model counterpart.
        Whenever the url is changed, the navigation bar is notified with 
        the SynchronizeView to update the data to reflect changes.
        """
        if not app.association.has_key(id(self)):
            wxWindow = wxNavigationBar()
            app.association[id(self)] = wxWindow
        else:
            wxWindow = app.association[id(self)]
            
        if len(self.history) > 0:
            wxWindow.SetURL(self.history[-1])
            
    def AddURLToHistory(self, url):
        """
          Adds the specified url to the history list and clears the future
        list.
        """
        del self.future[:]
        urlWithCase = app.model.URLTree.GetProperCaseOfURL(url)
        # FIXME:  There is a problem where, when parcels can 
        # redirect urls (within ChandlerWindow) we do not properly
        # find their url within the sidebar (since the url leaves
        # its displayed hierarchy).
        if urlWithCase == None:
            urlWithCase = url
        self.history.append(urlWithCase)
        
    def GetCurrentURL(self):
        """
          Returns the current url.  Returns None if there is no current url
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
        if not create it. Finally add it to the association.
        """
        if not app.model.mainFrame.hasAttributeValue('NavigationBar'):
            app.model.mainFrame.newAttribute ("NavigationBar", NavigationBar())
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
        EVT_TEXT_ENTER(self, XRCID("urlBox"), self.URLEntered)
        
    def URLEntered(self, event):
        """When the user enters a location in the url text box of the toolbar,
        we navigate to that url.  If switching to that url fails (because of
        a typo or because that url does not exist), then we simply reset the
        text box to the current url."""
        if not hasattr(self, 'urlBox'):
            self.urlBox = self.FindWindowByName('urlBox')
        oldURL = self.model.history[-1]
        newURL = self.urlBox.GetValue()
        
        if not app.wxMainFrame.GoToURL(newURL):
            print "Failed to navigate to " + newURL
            print "setting to " + oldURL
            self.urlBox.SetValue(oldURL)
        
    def SetURL(self, url):
        """Sets the text of the url text field in the navigation bar to reflect
        the current view."""
        if not hasattr(self, 'urlBox'):
            self.urlBox = self.FindWindowByName('urlBox')
        self.urlBox.SetValue(url)

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
            newURL = self.model.history[-1]
            app.wxMainFrame.GoToURL(newURL, false)

    def GoNext(self, event):
        """Change to the next view in your future list.  The Next button
        will only have an effect if the last navigation you did was to 
        use the Prev button.  If so, then the last item added to the future
        list will be popped off, added to the history list, and you will
        navigate to that view."""
        if len(self.model.future) > 0:
            newURL = self.model.future.pop()
            self.model.history.append(newURL)
            app.wxMainFrame.GoToURL(newURL, false)

    def DoStop(self, event):
        """
          Pass the stop command to the active parcel.
        """
        app.wxMainFrame.activeParcel.OnStop()
    
    def DoReload(self, event):
        """
          Pass the reload command to the active parcel.
        """
        app.wxMainFrame.activeParcel.OnReload()
    
    def GoHome(self, event):
        pass
    
    def OnDestroy(self, event):
        """
          Remove from the association when the navigation bar is destroyed.
        """
        del app.association[id(self.model)]
    
    