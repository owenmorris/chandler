__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF License"


from wxPython.wx import *
from application.Application import app
from persistence import Persistent
from persistence.dict import PersistentDict
import application.Application

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
        self.ignoreChangeSelect = false
        application.Application.app.model.URLTree.RegisterSideBar(self)
                
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
        self.__UpdateURLTree(self.sideBarURLTree, '',
                             wxWindow.root, wasEmpty)

    def __UpdateURLTree(self, sideBarLevel, parentUri,
                        parentItem, wasEmpty=false):
        """
          Synchronizes the sideBar's URLTree with the application's
        URLTree.  The sideBar only stores a dict mapping visible
        items in the sideBar to their instances in the application.
        """
        
        wxWindow = app.association[id(self)]
        uriList = app.model.URLTree.GetUriChildren(parentUri)
        for name in uriList:
            uri = parentUri + name
            parcel = app.model.URLTree.UriExists(uri)
            children = app.model.URLTree.GetUriChildren(uri)
            hasChildren = len(children) > 0            

            if not sideBarLevel.has_key(name):
                itemId = wxWindow.AppendItem(parentItem, name)
                wxWindow.uriDictMap[uri] = itemId
                wxWindow.SetItemHasChildren(itemId, hasChildren)
                sideBarLevel[name] = URLTreeEntry(parcel, false,
                                                          itemId, {}, false)
            else:
                if wasEmpty:
                    itemId = wxWindow.AppendItem(parentItem, name)
                    wxWindow.uriDictMap[uri] = itemId
                    sideBarLevel[name].wxId = itemId
                else:
                    itemId = sideBarLevel[name].wxId
                wxWindow.SetItemHasChildren(itemId, hasChildren)
                if sideBarLevel[name].isOpen:
                    self.__UpdateURLTree(sideBarLevel[name].children, 
                                         uri + '/', itemId, wasEmpty)
#                    if wasEmpty:
#                        wxWindow.Expand(itemId)
            sideBarLevel[name].isMarked = true
        # Now we clean up items that exist in the dict, but not 
        # in the app's URLTree
        for key in sideBarLevel.keys():
            item = sideBarLevel[key]
            if not item.isMarked:
          #      del wxWindow.uriDictMap[uri]
                wxWindow.Delete(item.wxId)
                del sideBarLevel[key]
            else:
                item.isMarked = false
    
    def SelectUri(self, uri):
        """
          Selects the proper uri when we have navigated to a different one
        via some tool other than the sideBar.
        """
        wxWindow = app.association[id(self)]
        self.ignoreChangeSelect = true
        # FIXME:  If the user types a valid uri of an item that has never been
        # displayed in the SideBar (because one of it's ancestors is collapsed)
        # then that item will not yet be in the dict.  We have to recurse
        # through the appURLTree to find the proper item and expand its
        # ancestors if necessary.
        try:
            wxWindow.SelectItem(wxWindow.uriDictMap[uri])
        except:
            pass
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
        self.uriDictMap = {}
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
        uri = self.BuildUriFromItem(clickedItem)
        app.wxMainFrame.GoToUri(uri)
        
    def BuildUriFromItem(self, item, uri = ""):
        """
          Given an item in the SideBar hierarchy, builds up that item's uri
        and returns it.
        """
        if self.GetRootItem() == item:
            return uri
        newUri = self.GetItemText(item)
        if len(uri) != 0:
            newUri = newUri + '/' + uri
        return self.BuildUriFromItem(self.GetItemParent(item), newUri)
            
    def OnItemExpanding(self, event):
        """
          Whenever a disclosure box is expanded, we mark it as such in the
        model's dict and call SynchronizeView so we can either get the new\
        items that are now visible (from the app) or just display them.
        """
        item = event.GetItem()
        uri = self.BuildUriFromItem(item)
        fields = uri.split('/')
        entry = self.__GetSideBarURLTreeEntry(fields, self.model.sideBarURLTree)
        entry.isOpen = true
        self.model.SynchronizeView()

    def __GetSideBarURLTreeEntry(self, fields, dict):
        if len(fields) == 1:
            return dict[fields[0]]
        return self.__GetSideBarURLTreeEntry(fields[1:], 
                                             dict[fields[0]].children)
        
    def OnDestroy(self, event):
        """
          Remove from the association when the sidebar is destroyed.
        """
        del app.association[id(self.model)]
            
    
     
