#!bin/env python

"""
This is the ListView class used for Contacts.  It's intended to be thrown away,
to be replaced with a more sophisticated outline/list with editing
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *

from application.repository.Namespace import chandler

class ContactsListControl(wxListCtrl):
 
    def SetListInfo(self, listPanel, contactList):
        self.listPanel = listPanel
        self.contactList = contactList
        self.SetItemCount(len(contactList))
        
    def OnGetItemText(self, item, column):
        contact = self.contactList[item]
        label, attribute = self.listPanel.columnFields[column]
        
        # FIXME: we shouldn't have to special case name here
        # and we really shouldn't need 'label'
        if label == 'Name':
            value = contact.GetSortName()
        else:
            value = contact.GetContactValue(label, attribute) 
        
        if value == None:
            value = ''
        
        return value

    # no images (yet) in contact list view - might want presence image soon
    def OnGetItemImage(self, item):
        return -1
    
class ContactsListPanel(wxPanel):
    def __init__(self, parent, contactView):
        wxPanel.__init__(self, parent, -1, style=wxWANTS_CHARS|wxSUNKEN_BORDER)

        self.contactView = contactView
                
        self.currentIndex = None
        self.needToUpdate = false

        self.columnFields = self.GetColumnFields()
        
        container = wxBoxSizer(wxVERTICAL)

        # populate the list		
        tID = wxNewId()		
        contactList = self.contactView.GetSortedContacts()
        self.list = ContactsListControl(self, tID, style=wxNO_BORDER|wxLC_VIRTUAL|wxLC_REPORT|wxLC_VRULES|wxLC_HRULES)
        self.list.SetListInfo(self, contactList)
 
        listHeight = self.PopulateListFromContacts()
        
        container.Add(self.list, 1, wxEXPAND)
        self.SetSizerAndFit(container)
        
        # set up event handlers
        EVT_IDLE(self, self.OnIdle)
        EVT_LIST_ITEM_FOCUSED(self.list, tID, self.OnSelectionChanged)
         
    # get a list containing the fields to display for each column.
    # FIXME: For now, this is hard-wired, but soon we'll fetch it from
    # the underlying view
    def GetColumnFields(self):
        return [(_('Name'), chandler.sortname), (_('Home Phone'), chandler.phonenumber), (_('Main Email'), chandler.emailAddress)]
        
    # populate the contacts list from the data in the table. First, loop through
    # the field list and make a column for each field
    def PopulateListFromContacts(self):
        fieldList = self.GetColumnFields()
        self.columnCount = len(fieldList)
        column = 0

        for fieldInfo in fieldList:
            fieldName, attributeName = fieldInfo
            self.list.InsertColumn(column, fieldName)
            column += 1

        self.ResizeColumns()
    
    # resize the columns to fit, including the header size
    # FIXME: need better sizing of columns, for now we just use a fixed size
    def ResizeColumns(self):
        for columnIndex in range(self.columnCount):
            self.list.SetColumnWidth(columnIndex, 180)        
                    
    # update the contacts by refetching the list and redrawing
    def UpdateContacts(self, fieldList):
        contactList = self.contactView.GetSortedContacts()
        self.list.SetListInfo(self, contactList)
        self.list.Refresh()
        
    # the list view doesnt support zooming for now.  We might use this for controlling
    # the font size in the future.
    def IsZoomVisible(self):
        return false

    # routines to map between an index and a contact
    def GetContactFromRowIndex(self, index):
        contactList = self.contactView.GetSortedContacts()
        return contactList[index]
    
    def GetRowIndexFromContact(self, contact):
        contactList = self.contactView.GetSortedContacts()
        try:
            index = contactList.index(contact)
            return index
        except ValueError:
            return None
  
    # here's a set of routines to manage the selection
    
    # return the selected index
    def GetSelectedIndex(self):
        return self.currentIndex
    
    # use the row to contact index to return the currently selected contact, if any	
    def GetSelectedContact(self):
        if self.currentIndex != None:
            return self.GetContactFromRowIndex(self.currentIndex)
        return None

    # set the currently selected contact
    def SetSelectedContact(self, newContact):
        rowIndex = self.GetRowIndexFromContact(newContact)
        if rowIndex != None:
            self.SetSelectedItem(rowIndex)
            self.contactView.SetContact(newContact)

    def SetSelectedIndex(self, rowIndex):
        self.SetSelectedItem(rowIndex)
        newContact = self.GetContactFromRowIndex(rowIndex)
        self.contactView.SetContact(newContact)
                
    def SetSelectedItem(self, newIndex):
        if self.currentIndex != None:
            self.list.SetItemState(self.currentIndex, 0, wxLIST_STATE_SELECTED)

        self.list.SetItemState(newIndex, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED)
        self.currentIndex = newIndex
 
    # compute the list of selected item numbers by iterating through the list control
    def GetSelectionList(self):
        selectedList = []
        item = -1
        while true:
            item = self.list.GetNextItem(item, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
            if item == -1:
                break;
            selectedList.append(item)
        return selectedList
    
    # get the list of contacts, instead of indexes, by fetching the indexes and dereferencing
    def GetSelectedContacts(self):
        resultList = []
        contactList = self.contactView.GetSortedContacts()
        itemList = self.GetSelectionList()
        
        for itemIndex in itemList:
            resultList.append(contactList[itemIndex])
            
        return resultList
    
    # UpdateContact is called when the content view changes an attribute
    # so the index view can reflect the change.
    def UpdateContact(self, contact):
        self.list.Refresh()
        
    def ContactsChanged(self):
        fieldList = self.GetColumnFields()
        self.UpdateContacts(fieldList)
        
    # here are the event handlers for the ContactsListView
    def OnSelectionChanged(self, event):
        self.currentIndex = event.m_itemIndex
        self.needToUpdate = true
        self.UpdateContactView()
        
    def UpdateContactView(self):
        if self.needToUpdate:
            self.needToUpdate = false
            
            contact = self.GetContactFromRowIndex(self.currentIndex)
            contactList = self.GetSelectedContacts()
            
            if len(contactList) > 1:
                self.contactView.SetContactList(contactList)
            else:
                self.contactView.SetContact(contact)
        
    # update the contact view on idle if necessary
    def OnIdle(self, event):
         #self.UpdateContactView()
         pass