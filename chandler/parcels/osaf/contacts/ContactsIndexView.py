#!bin/env python

"""
The indexView class for the contacts parcel manages a list of all the items
in the view
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *

import OSAF.contacts.ContactsListView
import OSAF.contacts.MiniContactCardView

class ContactsIndexView(wxPanel):
    def __init__(self, parent, contactsView):
        self.contactsView = contactsView
        
        wxPanel.__init__(self, parent, -1, style = wxNO_FULL_REPAINT_ON_RESIZE|wxNO_BORDER)
        #self.SetBackgroundColour(wxWHITE)

        self.currentView = None
                
        self.indexViewList = []
        
        # allocate the table view
        tableView = OSAF.contacts.ContactsListView.ContactsListPanel(self, contactsView)
        tableView.Hide()
        self.indexViewList.append(tableView)

        # allocate the minicard view
        miniCardView = OSAF.contacts.MiniContactCardView.MiniContactCardView(self, contactsView)
        miniCardView.Hide()
        self.indexViewList.append(miniCardView)

        # install the default view
        self.container = wxBoxSizer(wxVERTICAL)
        self.SetUpActiveView()
        self.SetSizerAndFit(self.container)
                
    def GetContactsCount(self):
        return self.contactsView.GetContactsCount()
    
    def SetSelectedContact(self, selectedContact):
        self.currentView.SetSelectedContact(selectedContact)
            
    # install the active view, as specified by the currentViewTypeIndex, maintaining the
    # selected contact
    def SetUpActiveView(self):
        if self.currentView != None:
            selectedContact = self.currentView.GetSelectedContact()
            self.currentView.Hide()
            self.container.Remove(self.currentView)
        else:
            selectedContact = None
        
        viewIndex = self.contactsView.model.currentViewTypeIndex
        self.currentView = self.indexViewList[viewIndex]
        self.container.Add(self.currentView, 1, wxEXPAND)

        self.currentView.SetSelectedContact(selectedContact)
        self.currentView.Show()

        self.Layout()
                
    def SetZoomIndex(self, zoomIndex, zoomLabel):
       currentZoomIndex = self.contactsView.model.currentZoomIndex
       if currentZoomIndex != zoomIndex:
            self.contactsView.model.currentZoomIndex = zoomIndex
            if self.currentView != None:
                self.currentView.SetZoomIndex(zoomIndex, zoomLabel)
                
    def IsZoomVisible(self):
        if self.currentView == None:
            return false

        return self.currentView.IsZoomVisible()
        
    def SelectViewType(self, typeIndex, typeLabel):
       viewIndex = self.contactsView.model.currentViewTypeIndex
       if viewIndex != typeIndex:
            self.contactsView.model.currentViewTypeIndex = typeIndex
            self.SetUpActiveView()
    
    # delete the selected contact, and update the display
    def DeleteContact(self):
        selectionList = self.currentView.GetSelectionList()
        selectedContacts = self.currentView.GetSelectedContacts()
        if len(selectedContacts) == 0:
            return true
        
        firstContact = selectedContacts[0]
        # FIXME: for now, we can't delete remote contacts.  Later, you will be able to
        # if you have the right permissions
        if firstContact.IsRemote():
            wxMessageBox(_("Sorry, but you don't have permission to delete this contact."))
            return false
        
        # use the lowest index in the selection list
        count = self.GetContactsCount()
        selectedIndex = count
        for index in selectionList:
            if index < selectedIndex:
                selectedIndex = index
                
        if selectedIndex >= count:
            selectedIndex = count - 1
         
        for contact in selectedContacts:
            self.contactsView.DeleteContact(contact)

        self.contactsView.ContactsChanged()
        self.currentView.SetSelectedIndex(selectedIndex)

        return true
    
    # Resort the contacts and update everything
    # FIXME: do this incrementally, by removing and reinserting the contact that changed
    # instead of redoing everything
    def ResortContacts(self, contact):
        selectedContact = self.currentView.GetSelectedContact()
        
        # get the position of the contact before and after the sorting
        contactList = self.contactsView.GetSortedContacts()
        oldIndex = contactList.index(contact)
        self.contactsView.SortContacts()
        newIndex = contactList.index(contact)
        
        # only update the view if the contact's position changed
        if oldIndex != newIndex:
            self.ContactsChanged()
            self.currentView.SetSelectedContact(selectedContact)
        else:
            self.UpdateContact(contact)
            
    # resize the constituent widgets so they display everything inside them
    # FIXME: there must be a better way to do this...
    def ResizeWidgets(self):
        clientSize = self.GetClientSize()
        self.SetClientSize(clientSize)
        
    # UpdateContact is called when the content view changes an attribute
    # to allow the index view to reflect it.  Just pass it along to the
    # current view
    def UpdateContact(self, contact):
        if self.currentView != None:
            self.currentView.UpdateContact(contact)
                
    # tell all the views that the contacts changed, starting with the current one
    def ContactsChanged(self):
        self.currentView.ContactsChanged()

        for view in self.indexViewList:
            if view != self.currentView:
                view.ContactsChanged()
                                
