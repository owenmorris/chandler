__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF License"


from wxPython.wx import *
from application.Application import app
from persistence import Persistent
from persistence.dict import PersistentDict


class SideBar(Persistent):
    """
      SideBar is the side bar in the ChandlerWindow and is the model
    counterpart of the wxSideBar view object (see below)..
    """
    def __init__(self):
        """
          sideBarURLTree is a dict mapping what this instance of SideBar
        has visible to the application's full URLTree.  The dict is a 
        tree of dicts that contain extra data specific to this instance of
        SideBar (like which levels are expanded).
        """
        self.sideBarURLTree = PersistentDict()
        self.uriDictMap = PersistentDict()
        self.ignoreChangeSelect = false
        
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
            app.association[id(self)] = wxWindow
        else:
            wxWindow = app.association[id(self)]
        
        wasEmpty = false
        if not hasattr(wxWindow, 'root'):
            wxWindow.root = wxWindow.AddRoot('Root')
            wasEmpty = true        
        self.sideBarURLTree = PersistentDict()
        self.__UpdateURLTree(self.sideBarURLTree, app.model.URLTree, 
                             wxWindow.root, wasEmpty)

    def __UpdateURLTree(self, sideBarURLTree, appURLTree, parent, wasEmpty):
        """
          Synchronizes the sidebar's URLTree with the application's
        URLTree.  The sidebar only stores a dict mapping visible items
        in the sidebar to their instances in the application.
        """
        wxWindow = app.association[id(self)]
        for item in appURLTree:
            instance = item[0]
            instanceId = id(instance)
            name = item[1]
            children = item[2]
            hasChildren = len(children) > 0

            if not sideBarURLTree.has_key(instanceId):
                itemId = wxWindow.AppendItem(parent, name)
                self.uriDictMap[name] = itemId
                wxWindow.SetItemHasChildren(itemId, hasChildren)
                sideBarURLTree[instanceId] = URLTreeEntry(instance, false,
                                                          itemId, {}, false)
            else:
                if wasEmpty:
                    itemId = wxWindow.AppendItem(parent, name)
                    self.uriDictMap[name] = itemId
                    sideBarURLTree[instanceId].wxId = itemId
                else:
                    itemId = sideBarURLTree[instanceId].wxId
                wxWindow.SetItemHasChildren(itemId, hasChildren)
                if sideBarURLTree[instanceId].isOpen:
                    self.__UpdateURLTree(sideBarURLTree[instanceId].children, 
                                         item[2], itemId)
            sideBarURLTree[instanceId].isMarked = true
        # Now we clean up items that exist in the dict, but not 
        # in the app's URLTree
        for key in sideBarURLTree.keys():
            item = sideBarURLTree[key]
            if not item.isMarked:
                wxWindow.Delete(item.wxId)
                del sideBarURLTree[key]
            else:
                item.isMarked = false
                
    def SelectUri(self, uri):
        """
          Selects the proper uri when we have navigated to a different one
        via some tool other than the sideBar.
        """
        wxWindow = app.association[id(self)]
        self.ignoreChangeSelect = true
        wxWindow.SelectItem(self.uriDictMap[uri])
        self.ignoreChangeSelect = false

class URLTreeEntry:
    """
      URLTreeEntry is just a container class for items inserted into the
    SideBar's URLTree dictionary.
    """
    def __init__(self, instance, isOpen, wxId, children, isMarked):
        self.instance = instance
        self.isOpen = isOpen
        self.wxId = wxId
        self.children = children
        self.isMarked = isMarked        

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
        EVT_TREE_ITEM_EXPANDING(self, self.GetId(), self.OnItemExpanding)
        
    def OnSelChanged(self, event):
        """
          Whenever the selection changes in the sidebar we must update the
        current view to visit the proper uri.  Right now, it only allows you
        to select parcels, and not visit specific uri's, but that is only
        temporary.
        """
        if self.model.ignoreChangeSelect:
            return
        clickedItem = event.GetItem()
        text = self.GetItemText(clickedItem)
        app.wxMainFrame.GoToUri(text)
            
    def OnItemExpanding(self, event):
        """
          Whenever a disclosure box is expanded, we mark it as such in the
        model's dict and call SynchronizeView so we can either get the new
        items that are now visible (from the app) or just display them.
        """
        item = event.GetItem()
        text = self.GetItemText(item)
        for item in app.model.URLTree:
            parcel = item[0]
            """
            Each parcel must have an attribute which is the displayName.
            """
            assert (hasattr (parcel, 'displayName'))
            if parcel.displayName == text:
                instanceId = id(parcel)
                self.model.sideBarURLTree[instanceId][1] = true
        self.model.SynchronizeView()
            
    def OnDestroy(self, event):
        """
          Remove from the association when the sidebar is destroyed.
        """
        del app.association[id(self.model)]
    
     
