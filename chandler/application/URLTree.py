__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"


from wxPython.wx import *
from persistence import Persistent 
from persistence.list import PersistentList

class URLTree(Persistent):
    def __init__(self):
        """
          Set up the URLTree.
        """
        Persistent.__init__(self)
        self.tree = PersistentList()
        self.sideBars = PersistentList()
        # FIXME:  Right now there is no class handling the '/'
        # url.  Once there is a default handler for that, it
        # should be used here.
        self.tree.append(TreeEntry(self, '', PersistentList()))

    def RegisterSideBar(self, sideBar):
        """
          Whenever a new window is created, with a new sideBar, we
        have to let the URLTree know, so that it can tell that
        sideBar to update itself when changes are made.
        """
        self.sideBars.append(sideBar)
        
    def RemoveSideBar(self, sideBar):
        """
          When a sideBar is no longer around, we have to let the 
        URLTree know, so that it no longer sends SynchronizeView
        messages.
        """
        for item in self.sideBars:
            if item == sideBar:
                return true
        return false

    # return a list of all the parcels currently installed in the tree
    def GetParcelList(self):
        parcels = []
        for entry in self.tree[0].children:
            parcels.append(entry.parcel)
        return parcels
    
    def UriExists(self, uri):
        """
          If the uri exists, then this returns the parcel associated
        with that uri.  If it does not exist, returns None.
        """
        treeEntry = self.__GetUriEntry(self.__GetUriFields(uri), self.tree)
        if treeEntry != None:
            return treeEntry.parcel
        return None

    def GetUriChildren(self, uri):
        """
          Returns a list containing all of the children uri's of the supplied
        uri.  Returns an empty list if the uri has no children.  Returns 
        None if the specified uri could not be found.
        """
        entry = self.__GetUriEntry(self.__GetUriFields(uri), self.tree)
        if entry != None:
            list = []
            for child in entry.children:
                list.append(child.name)
            return list
        return None
    
    def AddUri(self, parcel, uri):
        """
          Adds the given parcel at the given uri.  In order for the addition
        to be successful, the parcel must not be None, the path to the uri
        must already exist, and the uri itself must not already exist.
        """
        fields = self.__GetUriFields(uri)
        separator = '/'
        if parcel != None and\
           self.UriExists(separator.join(fields[:-1])) and\
           not self.UriExists(uri):
            parentEntry = self.__GetUriEntry(fields[:-1], self.tree)
            newEntry = TreeEntry(parcel, fields[-1], PersistentList())
            parentEntry.children.append(newEntry)
            self.__SynchronizeSideBars()
            return true
        return false
    
    def RemoveUri(self, uri):
        """
          Removes the specified uri.  Returns the parcel that was located
        at that uri and None if the uri could not be removed.  A uri that has
        children cannot be removed.
        """
        if self.UriExists(uri) and len(self.GetUriChildren(uri)) == 0:
            fields = self.__GetUriFields(uri)
            parentEntry = self.__GetUriEntry(fields[:-1], self.tree)
            for item in parentEntry.children:
                if item.name == fields[-1]:
                    parcel = item.parcel
                    
                    parentEntry.children.remove(item)
                    del item
                    self.__SynchronizeSideBars()
                    return parcel
        return None
    
    def RenameUri(self, oldUri, newUri):
        """
          Renames oldUri to be newUri.  oldUri and newUri can only differ in
        their last field.  oldUri must exist and newUri must not exist.  If
        oldUri has any children, they will be affected by the change.  Returns
        the parcel located at the specified uri if the renaming is successful,
        None otherwise.  If None is returned, then no changes were made to the
        URLTree.
        """
        if self.UriExists(oldUri) and not self.UriExists(newUri):
            oldFields = self.__GetUriFields(oldUri)
            newFields = self.__GetUriFields(newUri)
            separator = '/'
            if separator.join(oldFields[:-1]) ==\
               separator.join(newFields[:-1]):
                entry = self.__GetUriEntry(oldFields, self.tree)
                entry.name = newFields[-1]
                self.__SynchronizeSideBars()
                return entry.parcel
        return None

    def MoveParcel(self, oldUri, newUri):
        """
          Moves the parcel located at oldUri to newUri.  oldUri must exist,
        newUri must not exist, and the path to newUri must exist.  Returns 
        the parcel that was moved if the move is successful, None otherwise.
        If the move is successful, the parcel will be located at newUri and
        nothing will be located at oldUri.  If it is not successful, then no 
        changes were made.
        """
        if self.UriExists(oldUri) and not self.UriExists(newUri):
            oldFields = self.__GetUriFields(oldUri)
            newFields = self.__GetUriFields(newUri)
            separator = '/'
            if self.UriExists(separator.join(newFields[:-1])):
                oldParent = self.__GetUriEntry(oldFields[:-1], self.tree)
                newParent = self.__GetUriEntry(newFields[:-1], self.tree)
                for child in oldParent.children:
                    if child.name == oldFields[-1]:
                        entry = child
                        oldParent.children.remove(child)
                entry.name = newFields[-1]
                newParent.children.append(entry)
                self.__SynchronizeSideBars()
                return entry.parcel
        return None
    
    def SetParcelAtUri(self, uri, newParcel):
        """
          Sets the parcel located at uri to be newParcel.  Returns
        the parcel that had been located at uri if the change is successful,
        returns None if no changes were made.  In order to use this,
        there must already be something located at uri.  If you want to
        add a parcel to a new uri, use URLTree.AddUri.
        """
        entry = self.__GetUriEntry(self.__GetUriFields(uri), self.tree)
        if entry != None:
            oldParcel = entry.parcel
            entry.parcel = newParcel
            self.__SynchronizeSideBars()
            return oldParcel
        return None

    def __GetUriEntry(self, uriFields, URLTreeLevel):
        """
          Recursively finds the specified uri and returns the 
        TreeEntry assocaited with it.
        """
        for treeEntry in URLTreeLevel:
            if treeEntry.name == uriFields[0]:
                if len(uriFields) == 1:
                    return treeEntry
                return self.__GetUriEntry(uriFields[1:], treeEntry.children)
        return None
        
    def __GetUriFields(self, uri):
        """
          Extracts the individual items within a uri and returns it as a list.
        """
        if not uri.startswith('/'):
            uri = '/' + uri
        if uri.endswith('/'):
            uri = uri[:-1]
        return uri.split('/')

    def __SynchronizeSideBars(self):
        """
          Calls SynchronizeView on all of the sideBar's that have been
        registered with the URLTree.
        """
        for sideBar in self.sideBars:
            sideBar.SynchronizeView()
            
class TreeEntry(Persistent):
    """
      Just a wrapper class to encapsulate a single level of the URLTree.
    """
    def __init__(self, parcel, name, children):
        Persistent.__init__(self)
        self.parcel = parcel
        self.name = name
        self.children = children