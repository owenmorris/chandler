__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""The parent class that must be subclassed to create a Chandler
parcel viewer.
"""

import new, types, exceptions, sys, os
from wxPython.wx import *
from wxPython.xrc import *
from application.Parcel import Parcel
from application.Application import app
from persistence.list import PersistentList

class ViewerParcel (Parcel):
    """
      The ViewerParcel set's up the following data for the parcel's use:

    self.path                      the path to the parcel directory
    
      And stores the with the non-persistent counterpart:

    counterpart.model              the persistent counterpart
    counterpart.resources          the model's resources
    
      To create a parcel you'll subclass ViewerParcel, and remember
    to call the superclass's __init__.
    """
    def Install(theClass):
        """
          The class method that is used to install the parcel Viewer. Check
        to see if we've been installed into the URLTree, and if not install.
        Classes may be "old style" (type (theClass) == types.ClassType) or
        "new style". The construction method is different in each case: see
        below.
          Currently we install by appending to the end of the list
        """
        urlList = app.model.URLTree.GetURLChildren('')
        found = false
        for url in urlList:
            parcel = app.model.URLTree.URLExists(url)
            if parcel.__module__ == theClass.__module__:
                found = true
                break
        
        if not found:
            if type (theClass) == types.ClassType:
                instance = new.instance (theClass, {})
            else:
                instance = theClass.__new__ (theClass)
            instance.__init__()
            app.model.URLTree.AddURL(instance, instance.displayName)
        
    Install = classmethod (Install)

    def __init__(self):
        """
          modulePath is the path to the module's .xrc file, which must exist.
        """
        Parcel.__init__(self)
        module = sys.modules[self.__class__.__module__]
        self.modulename = os.path.basename (module.__file__)
        self.modulename = os.path.splitext (self.modulename)[0]
        self.modulePath = self.path + os.sep + self.modulename + ".xrc"
        assert (os.path.exists (self.modulePath))
        """
          Go dig the module name out of the XRC, which requires FindResource.
        """
        assert hasattr (app.applicationResources, 'FindResource')
        resources = wxXmlResource(self.modulePath)
        """
          All parcels must have a resource file. Although they are not
        required to have a resource menu, or have a label defined.
        """
        assert (resources)

        ignoreErrors = wxLogNull ()
        parcelMenuResourceXRC = resources.FindResource ('ViewerParcelMenu','wxMenu')
        del ignoreErrors
        """
          Make sure you call the base class before defining your own displayName.
        """
        assert not hasattr (self, 'displayName')
        self.displayName = _('UnnamedParcel')
        if parcelMenuResourceXRC != None:
            node = parcelMenuResourceXRC.GetChildren()
            while node != None:
                if node.GetName() == 'label':
                    self.displayName = node.GetChildren().GetContent()
                    break
                node = node.GetNext()
        self.description = _('The ' + self.displayName + ' parcel')

    def SynchronizeView (self):
        """
          If it isn't in the association we need to construct it and
        put it in the association.
        """
        container = app.wxMainFrame.FindWindowByName("ViewerParcel_container")
        if not app.association.has_key(id(self)):
            """
              ViewerParcels must have a resource file with the same name as 
            the module with an .xrc extension. We'll freeze the 
            app.wxMainFrame while adding the panel, since it's temporarily 
            owned by app.wxMainFrame and would otherwise cause it to be 
            temporarily displayed on the screen.
            """
            resources = wxXmlResource(self.modulePath)
            assert (resources)
            app.wxMainFrame.Freeze ()
            panel = resources.LoadObject(app.wxMainFrame, self.modulename, "wxPanel")
            panel.Show (FALSE)
            app.wxMainFrame.Thaw ()
            assert (panel != None)
            
            app.association[id(self)] = panel
            panel.Setup(self, resources)

        else:
            panel = app.association[id(self)]
        """
          We'll check to see if we've got a parcel installed in the view, and
        if so we'll remove it from the association and destroy it. Only 
        windows with the attribute "model" are removed from the association 
        since on the Mac there are some extra scrollbars added below the 
        viewer parcel container. Shortcut the case of setting the same 
        window we've already set.
        """
        container = app.wxMainFrame.FindWindowByName("ViewerParcel_container")
        children = container.GetChildren ()
        if len (children) == 0 or children[0] != panel:
            for window in children:
                if hasattr (window, "model"):
                    app.association[id(window.model)].Deactivate()
                    del app.association[id(window.model)]
            container.DestroyChildren ()
            """
              Attach the new parcel to the view. Don't forget to show the 
            panel which was temporarily hidden.
            """
            app.applicationResources.AttachUnknownControl("ViewerParcel", 
                                                          panel)
            panel.Activate()
            panel.Show ()

    def GoToURL(self, remoteaddress, url):
        """
          Override to navigate your parcel to the specified url.
          The remoteaddress specifies the address of a remote repository,
          or 'None' for the local repository
        """
        self.SynchronizeView()
        return true

    def RedirectURL(self, url):
        """
          give the parcel a chance to redirect the url to another parcel.
          By default, we don't do any mapping, but parcels can override
          this if they want to.
        """
        return url
    
    def GetAccessibleViews(self, who):
        """
           By default, no views are remotely accessible.  Real parcels override
           this to make their views public or otherwise accessible
        """
        return []
 
    def GetViewObjects(self, url, jabberID):
        """
           return a list of objects from the view specified by the url
           return the empty list here in the base class; packages override
           this to do the work.  Eventually, when we've developed the
           real query mechanism, there work can be done here
        """
        return []
    
    def AddObjectsToView(self, url, objectList, lastFlag):
        """
          add the objects in the passed-in list to the view.
          We don't do anything here in the base class; parcels
          override this so they can manage their own objectlist.
        """
        pass

    
    def UpdateFromRepository(self):
        """
          UpdateFromRepository is called when new objects are added to the repository
          to give the view a change to update itself. There's nothing to do here in the
          baseclass, but parcels should override this to receive notification of changes
        """
        pass
    
    def HandleErrorResponse(self, jabberID, url, errorMessage):
        """
          handle an error reponse.  Here in the base class, just
          display the error message in a dialog, but parcels
          can override if they need notification
        """
        wxMessageBox(errorMessage)

    def HasPermission(self, jabberID, url):
        """
          determinine if the passed-in jabberID has permission to access the passed-in url
          The base class says everything is OK, parcels subclass to implement real permissions
          FIXME: eventually, we should put the logic here when we have a real framework
        """
        return true
    
class wxViewerParcel(wxPanel):
    def __init__(self):
        """
          There is a little magic incantation provided by Robin Dunn here
        to wire up the wxWindows object behind the wxPython object.
        wxPreFrame creates the wxWindows C++ object, which is stored
        in the this member. _setOORInfo store a back pointer in the C++
        object to the wxPython object.
          If you override __init__ don't forget to call the superclass.
        """
        value = wxPrePanel()
        self.this = value.this
        self._setOORInfo(self)
        app.wxMainFrame.activeParcel = None

    def Setup(self, model, resources):
        """
          Set up model and resources for the convience of the parcel.
        OnInit gives the parcel a chance to wire up their events.
        """
        self.model = model
        self.resources = resources
        """
          OnInit does general initialization, which can only be done after
        __init__ has been called.
        """
        if hasattr (self, 'OnInit'):
            self.OnInit()
        """
          OnInitData is called once per parcel class, the first time a parcel
        is displayed. It's a good place to store global data that can't be
        persisted on a per class basis, e.g. open file handles.
          If you need per instance data you can add a dictionary to the 
        per class data, and if this turns out to be a common need, I'll add it
        to wxPacelViewer -- DJA
        """
        if hasattr (self, 'OnInitData'):
            parcelDictionary = app.parcels[id(self.model.__class__)]
            if parcelDictionary.has_key('data'):
                self.data = parcelDictionary['data']
            else:
                parcelDictionary['data'] = {}
                self.data = parcelDictionary['data']
                self.OnInitData()

        # Only bind erase background on Windows for flicker reasons
        if wxPlatform == '__WXMSW__':
            EVT_ERASE_BACKGROUND (self, self.OnEraseBackground)
                
    def OnEraseBackground (self, event):
        """
          Override OnEraseBackground to avoid erasing background. Instead
        implement OnDrawBackground to draw/erase the background. This
        design alternative will eliminate flicker
        """
        pass

    def Activate(self):
        """
          Override to do tasks that need to happen just before your parcel is
        displayed.
        """
        self.ReplaceViewParcelMenu()
        self.UpdateParcelMenus()
        self.UpdateActionsBar()
        app.wxMainFrame.activeParcel = self
    
    def Deactivate(self):
        """
          Override to do tasks that need to happen just before your parcel is
        replaced with anoter.
        """
        app.wxMainFrame.activeParcel = None
    
    def UpdateParcelMenus(self):
        """
          Updates menus to reflect parcel menu items other than the viewerParcelMenu.
          
          There are a host of unfortunate limitations with wxWindows menus and menuBar
        that makes this code more difficult than necessary. Most notably, the problems
        include:
          
            It isn't possible to search for a menu or menu item by a name that isn't
          subject to language translation.
          
            When searching menus, is it possible to find a menu item by index, and
          unfortunately, the only way to insert, remove or replace is by index.
          
            Given these limitations of menus, it is necessary to use the XRC resources
          directly since only they contain all the necessary information. However,
          the method, FindResource, used to find XRC resources is private. I had to
          make it public for this code to work.

            wxWindows menus don't contain the name of the menu, even though the XRC
          resource contains the name. -- DJA
        """
        def FindNameReturnIndex (menu, name):
            """
              Searches a menu for a name (possibly translated) and returns an index to
            the item.
            """
            index = 0
            translatedName = _(name)
            for item in menu.GetMenuItems():
                if item.GetLabel() == translatedName:
                    return index
                index += 1
            return wxNOT_FOUND

        def CopyMenuItem(source, destination):
            """
              Delete all the items in the destinations, then copy all the source
            items over to the destination. We do this instead of just replacing
            the destination menu with the source menu, because replacing the
            help menu on Macintosh fails (since it's owned by the system and can't
            be deleted). Also avoiding the replace eliminates flicker that is
            seen in the menubar as it's replaced.
            """
            for menuItem in destination.GetMenuItems():
                destination.DestroyItem(menuItem)
            
            for menuItem in source.GetMenuItems():
                destination.AppendItem(source.RemoveItem(menuItem))
                

        mainFrameId = id(app.model.mainFrame)
        """
          We require that there's a mainFrame and that wxWindows exposes FindResource.
        """
        assert app.association.has_key(mainFrameId) and hasattr (app.applicationResources, 'FindResource')
        mainFrame = app.association[mainFrameId]
        menuBar = mainFrame.GetMenuBar()
        
        mainMenuResourceXRC = app.applicationResources.FindResource ('MainMenuBar',
                                                                     'wxMenuBar')
        assert mainMenuResourceXRC != None
        
        mainMenuBar = None
        """
          Search sequentially through each of the top level menus looking for
        matching parcel menus
        """
        menuNode = mainMenuResourceXRC.GetChildren()
        while menuNode != None:
            assert menuNode.GetName() == 'object'
            name = menuNode.GetPropVal ('name', '')
            menuNodeChild = menuNode.GetChildren()
            label = ''
            while menuNodeChild != None:
                if menuNodeChild.GetName() == 'label':
                    label = menuNodeChild.GetChildren().GetContent()
                    break
                menuNodeChild = menuNodeChild.GetNext()

            menuBarIndex = menuBar.FindMenu (_(label))
            if menuBarIndex != wxNOT_FOUND:
                """
                  Found an application menu that matches an actual menu
                """
                if mainMenuBar == None:
                    mainMenuBar = app.applicationResources.LoadMenuBar ("MainMenuBar")

                menuIndex = mainMenuBar.FindMenu (_(label))
                assert menuIndex != wxNOT_FOUND
                """
                  menu is the application menu that needs to have parcel menuitems
                  added to it
                """
                menu = menuBar.GetMenu(menuBarIndex)
                source = mainMenuBar.GetMenu(menuIndex)
                """
                  Delete all the items in the menu, then copy all the source
                items over to the menu. We do this instead of just replacing
                the menu with the source menu, because replacing the help menu
                on Macintosh fails (since it's owned by the system and can't
                be deleted). Also avoiding the replace eliminates flicker that
                is seen in the menubar as it's replaced.
                """
                for menuItem in menu.GetMenuItems():
                    menu.DestroyItem(menuItem)
                
                for menuItem in source.GetMenuItems():
                    menu.AppendItem(source.RemoveItem(menuItem))
                    
                ignoreErrors = wxLogNull ()
                parcelMenuResourceXRC = self.resources.FindResource (name, 'wxMenu')
                del ignoreErrors

                if parcelMenuResourceXRC != None:
                    """
                      Found an parcel menu that matches an actual menu
                    """
                    parcelMenu = self.resources.LoadMenu (name)
                    assert parcelMenu != None
                    parcelMenuItems = parcelMenu.GetMenuItems()

                    menuItemNode = parcelMenuResourceXRC.GetChildren()
                    menuItemIndex = 0
                    """
                      Scan through the parcel's menu inserting items where indicated
                    """
                    while menuItemNode != None:
                        if menuItemNode.GetName() == 'object':
                            menuItemNodeChild = menuItemNode.GetChildren()
                            insertAtIndex = menu.GetMenuItemCount()
                            while menuItemNodeChild != None:
                                nodeName = menuItemNodeChild.GetName()
                                if nodeName == 'insertAfter' or nodeName == 'insertBefore':
                                    insertAtName = menuItemNodeChild.GetChildren().GetContent()
                                    index = FindNameReturnIndex (menu, insertAtName)
                                    if index != wxNOT_FOUND:
                                        insertAtIndex = index
                                        if nodeName == 'insertAfter':
                                            insertAtIndex += 1
                                    break
                                menuItemNodeChild = menuItemNodeChild.GetNext()
                            
                            menu.InsertItem (insertAtIndex, parcelMenuItems [menuItemIndex])
                            menuItemIndex += 1
                        menuItemNode = menuItemNode.GetNext()
                
            menuNode = menuNode.GetNext()
        mainMenuBar.Destroy()

    def ReplaceViewParcelMenu(self):
        """
          Override to customize your parcel menu.
        """
        mainFrameId = id(app.model.mainFrame)
        if app.association.has_key(mainFrameId):
            mainFrame = app.association[mainFrameId]
            menuBar = mainFrame.GetMenuBar ()
            menuIndex = menuBar.FindMenu (_('View')) + 1
            assert (menuIndex != wxNOT_FOUND)
            """
              On Macintosh the Debug menu , if visible, is before the
            Help menu instead of after like other platforms
            """
            noParcelMenu = (menuBar.FindMenu(_('Help')) == menuIndex) or \
                           (menuBar.FindMenu(_('Debug')) == menuIndex)

            ignoreErrors = wxLogNull ()
            viewerParcelMenu = self.resources.LoadMenu ('ViewerParcelMenu')
            del ignoreErrors

            if viewerParcelMenu != None:
                if noParcelMenu:
                    menuBar.Insert (menuIndex,
                                    viewerParcelMenu, 
                                    self.model.displayName)
                else:
                    oldMenu = menuBar.Replace (menuIndex,
                                               viewerParcelMenu, 
                                               self.model.displayName)
                    oldMenu.Destroy()
            else:
                if not noParcelMenu:
                    oldMenu = menuBar.Remove (menuIndex)
                    oldMenu.Destroy()
            
            return viewerParcelMenu     
        
        return None
    
    def UpdateActionsBar(self):
        """
          Updates the ChandlerWindow to display the ActionsBar of this
        parcel.  Override to customize your parcel ActionsBar.
        """
        mainFrameId = id(app.model.mainFrame)
        if app.association.has_key(mainFrameId):
            mainFrame = app.association[mainFrameId]
            ignoreErrors = wxLogNull()
            actionsBar = self.resources.LoadToolBar(mainFrame, 'ActionsBar')
            del ignoreErrors
            mainFrame.ReplaceActionsBar(actionsBar)
            
