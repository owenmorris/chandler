__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF License"


from wxPython.wx import *
from application.Application import app
from Persistence import Persistent, PersistentDict


class SideBar(Persistent):
    """
      SideBar is the side bar in the ChandlerWindow and is the model
    counterpart of the wxSideBar view object (see below)..
    """
    def __init__(self):
        """
          sideBarURLTree is the subset of the app.model.URLTree visible in
          ChandlerWindow with some added information as to whether or not
          each node is expanded.
        """
        self.sideBarURLTree = PersistentDict.PersistentDict()
        
    def SynchronizeView(self):
        """
          Notifies the window's wxPython counterpart that they need to
        synchronize themselves to match their peristent model counterpart.
        Whenever the application's URLTree is changed, the sidebar is
        notified with the SynchronizeView to update the sideBarURLTree
        to reflect changes
        """
        if not app.association.has_key(id(self)):
            wxWindow = wxSideBar ()
            app.association[id(self)] = wxSideBar ()
            wxWindow.OnInit (self)
        else:
            wxWindow = app.association[id(self)]
            
        self.__UpdateURLTree(self.sideBarURLTree, app.model.URLTree)

    def __UpdateURLTree(self, sideBarURLTree, appURLTree):
        """
          Synchronizes the sidebar's URLTree with the application's
        URLTree.  The sidebar only stores a dict mapping visible items
        in the sidebar to their instances in the application.
        """
        for item in appURLTree:
            instance = item[0]
            name = item[1]
            childrenList = item[2]
            instanceId = id(instance)
            
            if not sideBarURLTree.has_key(id(instance)):
                childrenDict = {}
                for child in childrenList:
                    childrenDict[id(child)] = child
                sideBarURLTree[instanceId] = [instance, false, 0, 
                                              childrenDict, false]
            else:
                # Do ceck to see if items are the same
                ## Not yet implemented
                if sideBarURLTree[instanceId][1]: # If it is open
                    # Repeat recursively
                    self.UpdateURLTree(sideBarURLTree[instanceId][3], children)
            # Mark the item as existing in the app's URLTree
            sideBarURLTree[instanceId][4] = true
        # Now we clean up items that exist in the dict, but not 
        # in the app's URLTree
        for key in sideBarURLTree.keys():
            item = sideBarURLTree[key]
            # If it was not marked, delete it
            if not item[4]:
                del sideBarURLTree[key]
            else:
                # Clear the visited flag
                item[4] = false
        app.association[id(self)].UpdateView()
        

class wxSideBar(wxTreeCtrl):
    def __init__(self):
        """
          wxSideBar is the view counterpart to SideBar. Wire up the wxWindows
        object behind the wxPython object. wxPreFrame creates the wxWindows
        C++ object, which is stored in the this member. _setOORInfo store a
        back pointer in the C++ object to the wxPython object.
        """
        value = wxPreTreeCtrl ()
        self.this = value.this
        self._setOORInfo (self)
        """
          Check to see if we've already created the persistent counterpart,
        if not create it, otherwise get it. Finally add it to the association.
        """
        if not app.model.mainFrame.__dict__.has_key('SideBar'):
            self.model = SideBar()
            app.model.mainFrame.SideBar = self.model
        else:
            self.model = app.model.mainFrame.SideBar
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
        EVT_TREE_SEL_CHANGED(self, self.GetId(), self.OnSelChanged)
        
    def UpdateView(self):
        """
          Updates the wxTreeCtrl to match the model's version of the Sidebar.
        Right now, it only displays the first level parcel names, but it
        should recursively display all of the available uri's.
        """
        if not hasattr(self, 'root'):
            self.root = self.AddRoot("Root")
            
        for item in app.model.URLTree:
            instance = item[0]
            name = item[1]
            children = item[2]
            hasChildren = len(children) > 0
            modelItem = self.model.sideBarURLTree[id(instance)]            

            itemId = self.AppendItem(self.root, name)
            self.SetItemHasChildren(itemId, hasChildren)
            
            isOpen = modelItem[1]
            if hasChildren and isOpen:
                # Recursively visit the children
                ## Not yet implemented
                pass
                
    def OnSelChanged(self, event):
        """
          Whenever the selection changes in the sidebar we must update the
        current view to visit the proper uri.  Right now, it only allows you
        to select parcels, and not visit specific uri's, but that is only
        temporary.
        """
        clickedItem = event.GetItem()
        text = self.GetItemText(clickedItem)
        for item in app.model.URLTree:
            parcel = item[0]
            """
            Each parcel must have an attribute which is the displayName.
            """
            assert (hasattr (parcel, 'displayName'))
            if parcel.displayName == text:
                parcel.SynchronizeView ()
                return

    def OnDestroy(self, event):
        """
          Remove from the association when the sidebar is destroyed.
        """
        del app.association[id(self.model)]
    
     