__author__ = "John Anderson"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF License"

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
    
      To create a parcel you'll subclass ViewerParcel, and currently
    it's not necessary to call the superclass's __init__.
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
        found = false
        for item in app.model.URLTree:
            parcel = item[0]
            if parcel.__module__ == theClass.__module__:
                found = true
                break
            
        if not found:
            if type (theClass) == types.ClassType:
                instance = new.instance (theClass, {})
            else:
                instance = theClass.__new__ (theClass)
            instance.__init__()
            itemList = PersistentList()
            itemList.append(instance)
            itemList.append(instance.displayName)
            itemList.append(PersistentList())
            app.model.URLTree.append (itemList)
        
    Install = classmethod (Install)
    
    def SynchronizeView (self):
        """
          If it isn't in the association we need to construct it and
        put it in the association.
        """
        container = app.wxMainFrame.FindWindowByName("ViewerParcel_container")
        if not app.association.has_key(id(self)):
            module = sys.modules[self.__class__.__module__]
            modulename = os.path.basename (module.__file__)
            modulename = os.path.splitext (modulename)[0]
            path = os.sep.join(module.__name__.split("."))
            path = path + ".xrc"

            """
              ViewerParcels must have a resource file with the same name as 
            the module with an .xrc extension. We'll freeze the 
            app.wxMainFrame while adding the panel, since it's temporarily 
            owned by app.wxMainFrame and would otherwise cause it to be 
            temporarily displayed on the screen.
            """
            assert (os.path.exists (path))
            resources = wxXmlResource(path)
            app.wxMainFrame.Freeze ()
            panel = resources.LoadObject(app.wxMainFrame, modulename, "wxPanel")
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
        self.OnInit()
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
        app.wxMainFrame.activeParcel = self
    
    def Deactivate(self):
        """
          Override to do tasks that need to happen just before your parcel is
        replaced with anoter.
        """
        app.wxMainFrame.activeParcel = None
    
    def GetMenuName(self):
        """
          Override to customize your parcel menu name.
        """
        return (self.model.displayName)

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
          resource contains the name.
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

        mainFrameId = id(app.model.mainFrame)
        """
          While we are running a version of wxPython that doesn't have FindResource, we won't
          include code to update parcel menu items.
        """
        if app.association.has_key(mainFrameId) and hasattr (app.applicationResources, 'FindResource'):
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
                    menu = mainMenuBar.GetMenu (menuIndex)
                        
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
                                    if menuItemNodeChild.GetName() == 'insertBefore':
                                        insertAtName = menuItemNodeChild.GetChildren().GetContent()
                                        index = FindNameReturnIndex (menu, insertAtName)
                                        if index != wxNOT_FOUND:
                                            insertAtIndex = index
                                        break
                                    menuItemNodeChild = menuItemNodeChild.GetNext()
                                
                                menu.InsertItem (insertAtIndex, parcelMenuItems [menuItemIndex])
                                menuItemIndex += 1
                            menuItemNode = menuItemNode.GetNext()

                    """
                      Update the menu with the new menu and delete the old menu
                    """
                    oldMenu = menuBar.Replace (menuBarIndex, menu,  _(label))
                    del oldMenu
                menuNode = menuNode.GetNext()

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
            noParcelMenu = menuBar.FindMenu(_('Help')) == menuIndex

            ignoreErrors = wxLogNull ()
            viewerParcelMenu = self.resources.LoadMenu ('ViewerParcelMenu')
            del ignoreErrors

            if viewerParcelMenu != None:
                if noParcelMenu:
                    menuBar.Insert (menuIndex,
                                    viewerParcelMenu, 
                                    self.GetMenuName())
                else:
                    oldMenu = menuBar.Replace (menuIndex,
                                               viewerParcelMenu, 
                                               self.GetMenuName())
                    del oldMenu
            else:
                if not noParcelMenu:
                    oldMenu = menuBar.Remove (menuIndex)
                    del oldMenu
            
            return viewerParcelMenu     
        
        return None
    