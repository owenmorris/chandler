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
        self.ignoreExpand = false
        self.ignoreCollapse = false
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
        
        if not hasattr(wxWindow, 'root'):
            wxWindow.root = wxWindow.AddRoot('Root')
        self.__UpdateURLTree(self.sideBarURLTree, '', wxWindow.root)

    def __UpdateURLTree(self, sideBarLevel, parentUri, parentItem):
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
                                                  PersistentDict(),
                                                  false)
            else:
                if not wxWindow.uriDictMap.has_key(uri):
                    itemId = wxWindow.AppendItem(parentItem, name)
                    wxWindow.uriDictMap[uri] = itemId
                else:
                    itemId = wxWindow.uriDictMap[uri]
                wxWindow.SetItemHasChildren(itemId, hasChildren)
                if sideBarLevel[name].isOpen:
                    self.__UpdateURLTree(sideBarLevel[name].children, 
                                         uri + '/', itemId)
                    self.ignoreExpand = true
                    wxWindow.Expand(itemId)
                    self.ignoreExpand = false
                else:
                    self.ignoreCollapse = true
                    wxWindow.Collapse(itemId)
                    self.ignoreCollapse = false
            sideBarLevel[name].isMarked = true
        # Now we clean up items that exist in the dict, but not 
        # in the app's URLTree
        for key in sideBarLevel.keys():
            uriToDelete = parentUri + key
            item = sideBarLevel[key]
            if not item.isMarked:
                if wxWindow.uriDictMap.has_key(uriToDelete):
                    itemId = wxWindow.uriDictMap[uriToDelete]
                    wxWindow.Delete(itemId)
                    del wxWindow.uriDictMap[uriToDelete]
                del sideBarLevel[key]
            else:
                item.isMarked = false
    
    def SelectUri(self, uri):
        """
          Selects the proper uri when we have navigated to a different one
        via some tool other than the sideBar.
        """
        # if the uri is remote, don't do this
        if app.wxMainFrame.IsRemoteUri():
            return
        
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

    def ExpandUri(self, uri):
        """
          Expands the item representing the given uri.  Will also expand 
        any ancestors of the item representing the supplied uri.  Returns 
        true if the expansion was successful, false otherwise.
        """
        wxWindow = app.association[id(self)]
        return wxWindow.ExpandUri(uri)
        
    def CollapseUri(self, uri):
        """
          Collapses the item representing the given uri.  Returns true if
        the collapse was successful, false otherwise.
        """
        wxWindow = app.association[id(self)]
        return wxWindow.CollapseUri(uri)
    
    def SetUriColor(self, uri, color):
        """
          Changes the color of the item representing the uri.  Will also
        expand any ancestors of the item representing the supplied uri.        
        Returns true if the color was successfully set, false otherwise.
        """
        wxWindow = app.association[id(self)]
        return wxWindow.SetUriColor(uri)

    def SetUriBold(self, uri, isBold=true):
        """
          Sets whether or not the item representing the uri should be bold.
        Will also expand any ancestors of the item representing the supplied
        uri.  Returns true if the bold state of the item was successfully set,
        false otherwise.
        """
        wxWindow = app.association[id(self)]
        return wxWindow.SetUriBold(uri)
    
        
class URLTreeEntry(Persistent):
    """
      URLTreeEntry is just a container class for items inserted into the
    SideBar's URLTree dictionary.
    """
    def __init__(self, instance, isOpen, children, isMarked):
        self.instance = instance
        self.isOpen = isOpen
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
        EVT_TREE_ITEM_COLLAPSING(self, self.GetId(), self.OnItemCollapsing)
        
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
        # If the selection change is generated by a right click, we get events
        # that have items without text.  We don't want to respond to these 
        # selection changes.
        if self.GetItemText(clickedItem) == "":
            return
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
        model's dict and call SynchronizeView so we can either get the new
        items that are now visible (from the app) or just display them.
        """
        if self.model.ignoreExpand:
            return
        item = event.GetItem()
        uri = self.BuildUriFromItem(item)
        fields = uri.split('/')
        entry = self.__GetSideBarURLTreeEntry(fields, self.model.sideBarURLTree)
        entry.isOpen = true
        self.model.SynchronizeView()

    def OnItemCollapsing(self, event):
        """
          Whenever a disclosure box is collapsed, we mark it as such in the
        model's dict.
        """
        item = event.GetItem()
        uri = self.BuildUriFromItem(item)
        fields = uri.split('/')
        entry = self.__GetSideBarURLTreeEntry(fields, self.model.sideBarURLTree)
        entry.isOpen = false
        
    def ExpandUri(self, uri):
        """
          Expands the item representing the given uri.  Will also expand 
        any ancestors of the item representing the supplied uri.  Returns 
        true if the expansion was successful, false otherwise.
        """
        item = self.__GetItemFromUri(uri)
        if item != None:
            fields = uri.split('/')
            entry = self.__GetSideBarURLTreeEntry(fields, self.model.sideBarURLTree)
            entry.isOpen = true
            self.Expand(item)
            return true
        return false

    def CollapseUri(self, uri):
        """
          Collapses the item representing the given uri.  Returns true if
        the collapse was successful, false otherwise.
        """
        item = self.__GetItemFromUri(uri)
        if item != None:
            fields = uri.split('/')
            entry = self.__GetSideBarURLTreeEntry(fields, self.model.sideBarURLTree)
            entry.isOpen = false
            self.Collapse(item)
            return true
        return false
    
    def SetUriColor(self, uri, color):
        """
          Changes the color of the item representing the uri.  Will also
        expand any ancestors of the item representing the supplied uri.        
        Returns true if the color was successfully set, false otherwise.
        """
        item = self.__GetItemFromUri(uri)
        if item != None:
            self.SetItemTextColour(item, color)
            return true
        return false

    def SetUriBold(self, uri, isBold=true):
        """
          Sets whether or not the item representing the uri should be bold.
        Will also expand any ancestors of the item representing the supplied
        uri.  Returns true if the bold state of the item was successfully set,
        false otherwise.
        """
        item = self.__GetItemFromUri(uri)
        if item != None:
            self.SetItemBold(item, isBold)
            return true
        return false

    def __GetSideBarURLTreeEntry(self, fields, dict):
        if len(fields) == 1:
            return dict[fields[0]]
        return self.__GetSideBarURLTreeEntry(fields[1:], 
                                             dict[fields[0]].children)
        
    def __GetItemFromUri(self, uri):
        if not self.uriDictMap.has_key(uri):
            urlTree = app.model.URLTree
            if urlTree.UriExists(uri):
                fields = uri.split('/')
                self.__DoExpandUri(fields, self.model.sideBarURLTree)
            else:
                return None
        return self.uriDictMap[uri]

    def __DoExpandUri(self, fields, dict):
        if not dict[fields[0]].isOpen:
            dict[fields[0]].isOpen = true
            self.model.SynchronizeView()
        if len(fields) > 1:
            self.__DoExpandUri(fields[1:], dict[fields[0]].children)
        
    def OnDestroy(self, event):
        """
          Remove from the association when the sidebar is destroyed.
        """
        del app.association[id(self.model)]
 