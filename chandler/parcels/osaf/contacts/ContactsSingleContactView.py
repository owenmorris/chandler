
#!bin/env python

"""
 The ContactsSingleContactView class shows the details of an individual contact
"""
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *

from application.Application import app

from parcels.OSAF.contacts.ContactNamePlate import *
from parcels.OSAF.contacts.ContactAddressList import *
from parcels.OSAF.contacts.ContactAttributeList import *
import parcels.OSAF.contacts.ImageCache

class ContactContentView(wxPanel):
    def __init__(self, parent, contactsView, indexView, contact):
        self.contactsView = contactsView
        self.contact = contact
        self.contactList = None
        self.indexView = indexView
        self.frozen = false
        
        # set up maximum number of tabs allowed
        self.tabLimit = 7
        
        wxPanel.__init__(self, parent, -1, style=wxNO_BORDER)
 
        self.LayoutWidgets()
     
    def GetContact(self):
        return self.contact
 
    def GetFrozen(self):
        return self.frozen
    
    def SetFrozen(self, frozenFlag):
        self.frozen = frozenFlag
        
    def SetContact(self, newContact):
        # if we're frozen, ignore SetContact calls
        if self.frozen:
            return
        
        # if there's a list, see if the contact is in it.   
        if self.contactList != None:
            self.contactList = None
            self.contact = newContact
            self.RenderWidgets()
        else:      
            if self.contact != newContact:
                self.contact = newContact
                self.contentView.SetContact(self.contact)
        self.Layout()
 
    def SetContactList(self, contactList):
        # if we're frozen, ignore SetContactList calls, too
        if self.frozen:
            return
        
        self.contactList = contactList
        self.RenderWidgets()

    # FIXME: this routine is a hack and shouldn't be necessary.  It adjusts the size of the passed in
    # panel to fit the container.
    def AdjustSize(self, panel):
        contentSize = self.GetSize()
        parentSize = self.GetParent().GetSize()
        panel.SetSize((parentSize[0], contentSize[1]))

    def RenderWidgets(self):
        self.DestroyChildren()
        self.LayoutWidgets()

    def LayoutWidgets(self):
        self.container = wxBoxSizer(wxVERTICAL)
        if self.contactList != None and len(self.contactList) > 1:
            self.notebook = wxNotebook(self, -1, style=wxNB_BOTTOM)
             
            count = 0
            for contact in self.contactList:
                name = contact.GetFullName()
                view = ContactsSingleContactView(self.notebook, self.contactsView, self.indexView, contact)
                self.notebook.AddPage(view, name)
                
                if count == 0:
                    self.contentView = view
                    self.contact = contact
  
                # break out of the loop if we've exceeded the limit
                count += 1
                if count > self.tabLimit:
                    break
                
            # FIXME: we shouldn't have to set size explicitly, sizer should do it, yet we have to
            self.AdjustSize(self.notebook)
            self.container.Add(self.notebook, 1, wxEXPAND)         
        else:
            self.contentView = ContactsSingleContactView(self, self.contactsView, self.indexView, self.contact)
            self.AdjustSize(self.contentView)
            self.container.Add(self.contentView, 1, wxEXPAND)
            
        self.SetSizerAndFit(self.container)
        self.Layout()

    def ContactsChanged(self):
        self.contentView.ContactsChanged()

    def AddNewAddress(self):
        self.contentView.AddNewAddress()
        
    def ShowAttributesDialog(self):
        self.contentView.ShowAttributesDialog()
    
    def GetAddressList(self):
        return self.contentView.contactAddressList
    
    def GetNamePlate(self):
        return self.contentView.namePlate
 
    def ScrollToBottom(self):
        self.contentView.ScrollToBottom()

    def PresenceChanged(self, who):
        self.contentView.RenderWidgets()
        
    # FIXME: this is a vile hack to force resizing when a new contact method is adding.
    # there has to be a better way to accomplish this
    def ForceResizeAndSelect(self, item, attribute):
        self.contentView.contact = None
        self.contentView.SetContact(self.contact)
        self.Layout()
        
        if item != None:
            self.contentView.contactAddressList.SetEditItem(item, attribute, false)
 
class ContactsSingleContactView(wxScrolledWindow):
    def __init__(self, parent, contactsView, indexView, contact):
        self.contactsView = contactsView
        self.contact = contact
        self.indexView = indexView

        self.contactAddressList = None
        self.contactAttributeList = None
        self.namePlate = None
        
        # keep these here for the subviews, so they can be rerendered
        # without losing this state
        self.editAddressItem = None
        self.editPart = ''
        
        wxScrolledWindow.__init__(self, parent, style=wxNO_BORDER)
                
        self.LayoutWidgets()
        self.SetAutoLayout(true)
        
        # register to receive an event when a child is focused, so
        # we can scroll to make sure it's visible
        # FIXME: disabled for now
        #EVT_CHILD_FOCUS(self, self.OnChildFocus)
        
    def GetContact(self):
        return self.contact

    def SetContact(self, newContact):
        if self.contact != newContact:
            self.contact = newContact
            self.RenderWidgets()
            self.SetVirtualSize(self.GetSize())
    
    def RenderWidgets(self):
        self.DestroyChildren()
        self.LayoutWidgets()
                
    def LayoutWidgets(self):        
        self.container = wxBoxSizer(wxVERTICAL)
        
        # display an empty message if necessary
        if self.contact == None:
           emptyMessage = wxStaticText(self, -1, _('    Use the "New" command to create a New contact'))
           self.container.Add(-1, 24)
           emptyMessage.SetFont(wxFont(14, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial"))
           self.container.Add(emptyMessage, 1, wxEXPAND | wxTOP, 24)
           return
       
        self.namePlate = ContactNamePlate(self, self.contact, self, self.indexView, self.contactsView.images)
        self.container.Add(self.namePlate, 0, wxEXPAND | wxLEFT, 4)
  
        # add some empty space between the name and addresses
        self.container.Add(-1, 16)

        # use a horizontal box to group the addresses and attributes
        hBox = wxBoxSizer(wxHORIZONTAL)
        self.contactAddressList = ContactAddressList(self, self.contact, self, self.indexView, self.contactsView.images)
        hBox.Add(self.contactAddressList, 0)

        # add some empty space between the addresses and attributes, too
        hBox.Add(40, -1)

        self.contactAttributeList = ContactAttributeList(self, self.contact, self, self.indexView, self.contactsView.images)
        hBox.Add(self.contactAttributeList, 1)

        self.container.Add(hBox, 2, wxEXPAND | wxLEFT, 4)

        self.SetSizerAndFit(self.container)
        self.Layout()

        self.EnableScrolling(false, true)
        self.SetScrollRate(0, 20)
 
    # resize the constituent widgets so they display everything inside them
    # FIXME: there must be a better way to do this...
    def ResizeWidgets(self):
        clientSize = self.GetClientSize()
        self.SetClientSize(clientSize)
       
    # get rid of any active edit fields
    def DoneEditing(self):
        if self.namePlate != None:
            self.namePlate.DoneEditing()

        if self.contactAddressList != None:
            self.contactAddressList.DoneEditing()

        if self.contactAttributeList != None:
            self.contactAttributeList.DoneEditing()

    # handle the Add New Address command by passing it along to the address list
    def AddNewAddress(self):
        if self.contact == None:
            return
        
        self.contactAddressList.AddNewAddressDialog(None)

    # show dialog to change the image associated with a contact
    def GetPhotoImage(self, event):
        if self.contact == None:
            return
        
        self.namePlate.GetPhotoImage(event)
    
    # handle the Show Attributes command
    def ShowAttributesDialog(self):
        if self.contact == None:
            return
        
        attributeData = self.contactsView.contactMetaData.GetAttributeDictionary()
        
        # build the choice list and selection state arrays from the attribute data
        # and the current attribute list associated with the contact
        choices = []
        fieldChoices = []
        headerSelectState = []
        bodySelectState = []
        
        for template in attributeData.GetAllAttributeTemplates():
            # FIXME: Hack, filter out a set of attributes we don't want
            # to edit. This should be data driven as well...
            attributeURL = template.GetURL()
            if ((attributeURL != chandler.contactType) and
                (attributeURL != chandler.contactName) and
                (attributeURL != chandler.contactMethod) and
                (attributeURL != chandler.photoURL) and
                (attributeURL != chandler.group) and
                (attributeURL != chandler.headerAttribute) and
                (attributeURL != chandler.bodyAttribute)):
                
                choices.append(template.GetDisplayName())
                fieldChoices.append(attributeURL)
                headerSelectState.append(self.contact.HasHeaderAttribute(attributeURL))
                bodySelectState.append(self.contact.HasBodyAttribute(attributeURL))
                
        # create the dialog
        dialogTitle = _("Select Attributes")
        dialogCaption = _(" Select the attributes to display for %s: ") % (self.contact.GetFullName())
        selectState = (headerSelectState, bodySelectState)
        dialog = ContactCheckboxDialog(app.wxMainFrame, dialogTitle, dialogCaption, choices, selectState)
        
        result = dialog.ShowModal()
        if result == wxID_OK:
            newHeaderSelectState, newBodySelectState = dialog.GetSelectionState()
            
            # update the header attributes
            if newHeaderSelectState != headerSelectState:
                for index in range(len(fieldChoices)):
                    if newHeaderSelectState[index]:
                        self.contact.AddHeaderAttribute(fieldChoices[index])
                    else:
                        self.contact.RemoveHeaderAttribute(fieldChoices[index])
                        
                self.namePlate.RenderWidgets()
                
            # update the body attributes
            if newBodySelectState != bodySelectState:
                for index in range(len(fieldChoices)):
                    if newBodySelectState[index]:
                        self.contact.AddBodyAttribute(fieldChoices[index])
                    else:
                        self.contact.RemoveBodyAttribute(fieldChoices[index])
                        
                self.contactAttributeList.RenderWidgets()
         
        self.ResizeWidgets()        

    # scroll to the bottom of the display area if necessary
    def ScrollToBottom(self):
        virtualSize = self.GetVirtualSize()
        realSize = self.GetSize()
        if virtualSize.y > realSize.y:
            verticalPixelsPerUnit = self.GetScrollPixelsPerUnit()[1]
            self.Scroll(-1, (virtualSize.y - realSize.y) / verticalPixelsPerUnit)
    
    # when a child is focused, scroll to make it visible
    def OnChildFocus(self, event):
        event.Skip()
        childWindow = event.GetWindow()

        verticalPixelsPerUnit = self.GetScrollPixelsPerUnit()[1]
        verticalViewStart = self.GetViewStart()[1]
        childPosition = childWindow.GetPosition()
        childSize  = childWindow.GetSize()
        childBottom = childPosition.y + childSize.height

        # is it above the top?
        if childPosition.y < 0:
            self.Scroll(-1, childPosition.y / verticalPixelsPerUnit)

        # is it below the bottom ?
        if childBottom > self.GetClientSize().height:
            delta = (childBottom - self.GetClientSize().height) / verticalPixelsPerUnit
            self.Scroll(-1, verticalViewStart + delta + 1)
        
    # nothing to do when a contact changes, at least for now       
    def ContactsChanged(self):
            pass
