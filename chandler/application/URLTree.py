__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from model.schema.AutoItem import AutoItem
import application.Application

class URLTree(AutoItem):
    def __init__(self, **args):
        super (URLTree, self).__init__ (**args)
        """
          Set up the URLTree.
        """
        self.newReferenceCollection ("tree")
        self.newReferenceCollection ("sideBars")
        self.addItemToReferenceCollection ("tree", TreeEntry(None, ''))

    def RegisterSideBar(self, sideBar):
        """
          Whenever a new window is created, with a new sideBar, we
        have to let the URLTree know, so that it can tell that
        sideBar to update itself when changes are made.
        """
        self.addItemToReferenceCollection("sidebars", sideBar)
        
    def GetParcelList(self):
        """
          return a list of all the parcels currently installed in
          the tree.  Since a single parcel can be responsible for
          multiple top-level links, make sure we only add it to
          the list once.
        """
        parcels = []
        for entry in self.tree.first().children:
            parcel = application.Application.app.repository.find (entry.parcelUUID)
            try:
                index = parcels.index(parcel)
            except ValueError:
                parcels.append(parcel)
        return parcels
    
    def URLExists(self, url):
        """
          If the url exists, then this returns the parcel associated
        with that url.  If it does not exist, returns None.
        """
        treeEntry = self.__GetURLEntry(self.__GetURLFields(url), self.tree)
        if treeEntry != None:
            return application.Application.app.repository.find (treeEntry.parcelUUID)
        return None

    def GetURLChildren(self, url):
        """
          Returns a list containing all of the children url's of the supplied
        url.  Returns an empty list if the url has no children.  Returns 
        None if the specified url could not be found.
        """
        entry = self.__GetURLEntry(self.__GetURLFields(url), self.tree)
        if entry != None:
            list = []
            for child in entry.children:
                list.append(child.name)
            return list
        return None
    
    def AddURL(self, parcel, url):
        """
          Adds the given parcel at the given url.  In order for the addition
        to be successful, the parcel must not be None, the path to the url
        must already exist, and the url itself must not already exist.
        """
        fields = self.__GetURLFields(url)
        separator = '/'
        if parcel != None:
            parentURL = separator.join(fields[:-1])
            if self.URLExists(parentURL) or parentURL == '':
                if not self.URLExists(url):
                    parentEntry = self.__GetURLEntry(fields[:-1], self.tree)
                    parentEntry.addItemToReferenceCollection ("children", TreeEntry(parcel, fields[-1]))
                    self.__SynchronizeSideBars()
                    return true
        return false
    
    def RemoveURL(self, url):
        """
          Removes the specified url.  Returns the parcel that was located
        at that url and None if the url could not be removed.  A url that has
        children cannot be removed.
        """
        if self.URLExists(url) and len(self.GetURLChildren(url)) == 0:
            fields = self.__GetURLFields(url)
            parentEntry = self.__GetURLEntry(fields[:-1], self.tree)
            for item in parentEntry.children:
                if item.name == fields[-1]:
                    parcel = application.Application.app.repository.find (item.parcelUUID)
                    
                    parentEntry.children.remove(item)
                    del item
                    self.__SynchronizeSideBars()
                    return parcel
        return None
    
    def RenameURL(self, oldURL, newURL):
        """
          Renames oldURL to be newURL.  oldURL and newURL can only differ in
        their last field.  oldURL must exist and newURL must not exist.  If
        oldURL has any children, they will be affected by the change.  Returns
        the parcel located at the specified url if the renaming is successful,
        None otherwise.  If None is returned, then no changes were made to the
        URLTree.
        """
        if self.URLExists(oldURL) and not self.URLExists(newURL):
            oldFields = self.__GetURLFields(oldURL)
            newFields = self.__GetURLFields(newURL)
            separator = '/'
            if separator.join(oldFields[:-1]) ==\
               separator.join(newFields[:-1]):
                entry = self.__GetURLEntry(oldFields, self.tree)
                entry.name = newFields[-1]
                self.__SynchronizeSideBars()
                return app.repository.find (entry.parcelUUID)
        return None

    def MoveParcel(self, oldURL, newURL):
        """
          Moves the parcel located at oldURL to newURL.  oldURL must exist,
        newURL must not exist, and the path to newURL must exist.  Returns 
        the parcel that was moved if the move is successful, None otherwise.
        If the move is successful, the parcel will be located at newURL and
        nothing will be located at oldURL.  If it is not successful, then no 
        changes were made.
        """
        if self.URLExists(oldURL) and not self.URLExists(newURL):
            oldFields = self.__GetURLFields(oldURL)
            newFields = self.__GetURLFields(newURL)
            separator = '/'
            if self.URLExists(separator.join(newFields[:-1])):
                oldParent = self.__GetURLEntry(oldFields[:-1], self.tree)
                newParent = self.__GetURLEntry(newFields[:-1], self.tree)
                for child in oldParent.children:
                    if child.name == oldFields[-1]:
                        entry = child
                        oldParent.children.remove(child)
                entry.name = newFields[-1]
                newParent.addItemToReferenceCollection ("children", entry)
                self.__SynchronizeSideBars()
                return application.Application.app.repository.find (entry.parcelUUID)
        return None
    
    def SetParcelAtURL(self, url, newParcel):
        """
          Sets the parcel located at url to be newParcel.  Returns
        the parcel that had been located at url if the change is successful,
        returns None if no changes were made.  In order to use this,
        there must already be something located at url.  If you want to
        add a parcel to a new url, use URLTree.AddURL.
        """
        entry = self.__GetURLEntry(self.__GetURLFields(url), self.tree)
        if entry != None:
            oldParcelUUID = entry.parcelUUID
            entry.parcelUUID = newParcel.getUUID()
            self.__SynchronizeSideBars()
            return application.Application.app.repository.find (oldParcelUUID)
        return None
    
    def GetProperCaseOfURL(self, url):
        """
          Takes in a url and returns the proper case for that url.
        """
        return self.__URLCaseHelper(self.__GetURLFields(url), self.tree, '')
    
    def __URLCaseHelper(self, urlFields, URLTreeLevel, urlSoFar):
        """
          Recursively builds up the proper case for the supplied urlFields.
        """
        if len(urlFields) == 0:
            return urlSoFar
        for treeEntry in URLTreeLevel:
            if treeEntry.name.lower() == urlFields[0].lower():
                if len(urlSoFar) > 0:
                    urlSoFar += '/'
                urlSoFar += treeEntry.name
                return self.__URLCaseHelper(urlFields[1:], treeEntry.children, urlSoFar)
        return None

    def __GetURLEntry(self, urlFields, URLTreeLevel):
        """
          Recursively finds the specified url and returns the 
        TreeEntry assocaited with it.
        """
        for treeEntry in URLTreeLevel:
            if treeEntry.name.lower() == urlFields[0].lower():
                if len(urlFields) == 1:
                    return treeEntry
                return self.__GetURLEntry(urlFields[1:], treeEntry.children)
        return None
        
    def __GetURLFields(self, url):
        """
          Extracts the individual items within a url and returns it as a list.
        """
        if not url.startswith('/'):
            url = '/' + url
        if url.endswith('/'):
            url = url[:-1]
        return url.split('/')

    def __SynchronizeSideBars(self):
        """
          Calls SynchronizeView on all of the sideBar's that have been
        registered with the URLTree.
        """
        for sideBar in self.sideBars:
            sideBar.SynchronizeView()
            
class TreeEntry (AutoItem):
    """
      Just a wrapper class to encapsulate a single level of the URLTree.
    """
    def __init__ (self, parcel, treeName, **args):
        super (TreeEntry, self).__init__ (**args)
        parcelUUID = None
        if parcel:
            parcelUUID = parcel.getUUID()
        self.newAttribute ("parcelUUID", parcelUUID)
        self.newAttribute ("name", treeName)
        self.newReferenceCollection ("children")
