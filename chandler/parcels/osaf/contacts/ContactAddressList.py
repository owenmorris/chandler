#!bin/env python

"""
 Contact Display List for SingleContactView
"""
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002, 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
import webbrowser

from application.Application import app
from application.repository.Repository import Repository
from application.repository.Namespace import chandler

from parcels.OSAF.contacts.AutoCompleteTextCtrl import *
from parcels.OSAF.contacts.ContactsDialog import *

class ContactAddressList(wxPanel):
    def __init__(self, parent, contact, singleContactView, indexView, images):
        self.contact = contact
        self.singleContactView = singleContactView
        self.indexView = indexView
        self.images = images
        self.commandID = 100
        
        # here's some state to support editing a selected item
        self.editField = None
        self.originalText = ''
        
        wxPanel.__init__(self, parent, -1)
        
        # allocate the fonts used by the address list
        self.labelFont = wxFont(10, wxSWISS, wxNORMAL, wxBOLD, false, "Arial")
        self.valueFont = wxFont(10, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")		
        self.commentFont = wxFont(9, wxSWISS, wxITALIC, wxNORMAL, false, "Arial")		

        # set up a minimum horizontal size
        self.SetSize((220, -1))
        
        # set up the mapping between address locations and their images
        # before rendering the widgets
        self.SetUpLocationProperties()
        self.LayoutWidgets()
        self.SetAutoLayout(true)
        
        # receive an event when the user clicks in us		
        EVT_LEFT_DOWN(self, self.OnLeftClick)
        
    # get the contact associated with the addresslist
    def GetContact(self):
        return self.contact

    # set the contact associated with the addresslist, and regenerate the widgets
    def SetContact(self, newContact):
        if self.contact != newContact:
            self.contact = newContact
            self.RenderWidgets()

    # destroy any exisiting widgets and layout a new set to represent the contact
    def RenderWidgets(self):
        self.DestroyChildren()
        self.LayoutWidgets()
        # FIXME: is this necessary?
        self.singleContactView.Layout()
                
    # FIXME - this should be set up from an xml file or the database instead of
    # being hardwired in code like this.
    def SetUpLocationProperties(self):
        self.locationProperties = {}
        self.locationProperties['Home Phone'] = ('home-phone.gif', 'phone')
        self.locationProperties['Work Phone'] = ('work-phone.gif', 'phone')
        self.locationProperties['Main Phone'] = ('work-phone.gif', 'phone')
        self.locationProperties['Cellphone'] = ('cell-phone.gif', 'phone')
        self.locationProperties['Main Email'] = ('email.gif', 'email')
        self.locationProperties['Work Email'] = ('email.gif', 'email')
        self.locationProperties['Main Email'] = ('email.gif', 'email')
        self.locationProperties['Jabber ID'] = ('badge.gif', 'jabberID')
        self.locationProperties['Home Address'] = ('home-address.gif', 'postal')
        self.locationProperties['Work Address'] = ('work-address.gif', 'postal')
        self.locationProperties['Main Office Address'] = ('work-address.gif', 'postal')
        self.locationProperties['Home Fax'] = ('fax.gif', 'phone')
        self.locationProperties['Work Fax'] = ('fax.gif', 'phone')
        self.locationProperties['Website'] = ('web.gif', 'website')
        self.locationProperties['Note'] = ('note.gif', 'note')

        # finally, set up short descriptions for each type (also should be in xml)
        self.typeDescriptions = {}
        self.typeDescriptions['phone'] = 'phone number'
        self.typeDescriptions['email'] = 'email address'
        self.typeDescriptions['jabberID'] = 'Jabber ID'
        self.typeDescriptions['postal'] = 'postal address'
        self.typeDescriptions['website'] = 'website address'
        self.typeDescriptions['note'] = 'free-form note'

    # return a short description for the passed-in type
    def GetTypeDescription(self, addressType):
        return self.typeDescriptions[addressType]
  
    # return the default value for an attribute of a given type
    def GetDefaultValue(self, item, attribute):
        attributeTemplate = item.GetAttributeTemplate(attribute)
        if (attributeTemplate != None):
            return attributeTemplate.GetDefault()
        return None
     
    def HasDefaultValue(self, item, part, currentValue):
        defaultValue = self.GetDefaultValue(item, part)
        return currentValue == defaultValue
   
    # set the type of the passed-in address ro the one associated with the description
    def SetAddressType(self, addressItem, addressDescription):
        if self.locationProperties.has_key(addressDescription):
            properties = self.locationProperties[addressDescription]
            newType = properties[1]
        else:
            newType = 'phone'

        oldType = addressItem.GetMethodType()
        addressItem.ChangeMethodType(newType)

        if oldType != newType:
            attributes = addressItem.GetAddressAttributes()
            self.SetEditItem(addressItem, attributes[0], false)
        
    # lookup the pathname corresponding to the address location, and use it to load a bitmap
    # if it's a jabberID, use presence and subscription info
    def GetItemBitmap(self, item):
        description = item.GetMethodDescription()
        itemType = item.GetMethodType()
        if itemType == 'jabberID':
            jabberID = item.GetAttribute(chandler.jabberAddress)
            # FIXME: Call IsValid on the item?
            if ((jabberID != None) and (len(jabberID) > 0) and (jabberID != 'jabber id')):
                if app.jabberClient.IsSubscribed(jabberID):
                    if app.jabberClient.IsPresent(jabberID):
                        imageName = 'present.gif'
                    else:
                        imageName = 'absent.gif'
                    return self.images.LoadBitmapFile(imageName)
            
        if self.locationProperties.has_key(description):
            locationData = self.locationProperties[description]
            bitmapName = locationData[0]
            return self.images.LoadBitmapFile(bitmapName)

        # otherwise, use the default address image
        return self.images.LoadBitmapFile('default-address.gif')

    # update the selected address item with the passed-in text.
    def UpdateAttribute(self, text):
        if self.singleContactView.editPart == 'label':
            if text[-1] == ':':
                text = text[0:-1]
            self.singleContactView.editAddressItem.SetMethodDescription(text)
 
            if not self.locationProperties.has_key(text):
                self.locationProperties[text] = ('default-address.gif', 'phone')
            else:
                properties = self.locationProperties[text]
                self.SetAddressType(self.singleContactView.editAddressItem, properties[1])          
        else:
            self.singleContactView.editAddressItem.SetAttribute(self.singleContactView.editPart, text)
                
    # set the selected address item and subpart
    def SetEditItem(self, addressItem, addressPart, acceptFlag):
        if self.singleContactView.editAddressItem != addressItem or self.singleContactView.editPart != addressPart:
            # update the underlying data if necessary
            textGotBigger = false
            if self.singleContactView.editAddressItem != None and len(self.singleContactView.editPart) > 0:
                if acceptFlag and self.editField != None:
                    text = self.editField.GetValue()  
                    self.UpdateAttribute(text)
                    textGotBigger = len(self.originalText) < len(text)
                    # commit the changes
                    repository = Repository()
                    repository.Commit()

                    # tell the index view about it, too
                    self.indexView.UpdateContact(self.contact)

            self.singleContactView.editAddressItem = None
            self.singleContactView.editPart = ''
            self.singleContactView.DoneEditing()

            self.singleContactView.editAddressItem = addressItem
            self.singleContactView.editPart = addressPart
            
            # re-render the whole single contact view if necessary, or
            # just the addresslist
            if textGotBigger:
                self.singleContactView.RenderWidgets()
            else:
                self.RenderWidgets()
                
    # return true if we're being edited
    def isEdited(self):
        return self.singleContactView.editPart != None and len(self.singleContactView.editPart) > 0
        
    # close any fields being edited, accepting changes
    def DoneEditing(self):
        self.SetEditItem(None, '', true)

    # return the choiceList used for auto-completion associated with a part type
    def GetChoiceList(self, partType):
        if partType == 'label':
            choiceList = self.locationProperties.keys()
        else:
            choiceList = None

        return choiceList
                
    # utility routine to render a static text object or a text field, depending on whether the
    # item is selected
    def RenderTextField(self, text, font, item, partType):
        # see if we should use a text control or not
        if self.singleContactView.editAddressItem == item and self.singleContactView.editPart == partType:
            width, height, descent, ascent = self.GetFullTextExtent(text, font)
            if item.GetMethodType() == 'note':
                width = 160
                height = 80
                widget = wxTextCtrl(self, -1, text, size=(width, height), style=wxTE_RICH | wxTE_MULTILINE)      
            else:
                choiceList = self.GetChoiceList(partType)
                widget = AutoCompleteTextCtrl(self, -1, text, choiceList,
                             false, style=wxTE_RICH | wxTE_PROCESS_ENTER)
            
                if width < 160:
                    width = 160
                else:
                    width += 16
               
                if height < 16:
                    height = 16

            self.editField = widget      
            widget.SetSize((width, height + descent + 4))
            widget.SetFont(font)
            
            widget.SetFocus()
            widget.SelectAll()
                        
            EVT_CHAR(widget, self.OnKeystroke)
        else:
            if partType == 'label':
                displayString = text + ':'
            else:
                displayString = text

            # notes are multi-line
            if partType == chandler.note:
                widget = wxStaticText(self, -1, displayString, style=wxTE_MULTILINE)
            else:
                widget = wxStaticText(self, -1, displayString)
            
            widget.SetFont(font)
            actionHandler = AddressActionHandler(self, item, widget, partType)

        self.originalText = text
        return widget
            
    # here's the routine to layout an address item.  An item consists of an icon,
    # a label, and a value.  The label or value could be editable
    def LayoutAddressItem(self, item, container):
        bitmap = self.GetItemBitmap(item)
        if bitmap != None:
            imageWidget = wxStaticBitmap(self, -1, bitmap)
            container.Add(imageWidget, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)
            actionHandler = AddressActionHandler(self, item, imageWidget, 'image')

        vBox = wxBoxSizer(wxVERTICAL)
        locationWidget = self.RenderTextField(item.GetMethodDescription(), self.labelFont, item, 'label')
        vBox.Add(locationWidget, 0)

        # fetch the list of attributes associated with this item, and create widgets for them 
        attributes = item.GetAddressAttributes()
        itemType = item.GetMethodType()
        
        hBox = wxBoxSizer(wxHORIZONTAL)

        for attribute in attributes:	
            if attribute == 'linebreak':
               vBox.Add(hBox, 0)
               hBox = wxBoxSizer(wxHORIZONTAL)		
            else:
                displayString = item.GetFormattedAttribute(attribute)
                if displayString == None:
                    displayString = ''
                
                attributeWidget = self.RenderTextField(displayString, self.valueFont, item, attribute)
                hBox.Add(attributeWidget, 0)
                
            hBox.Add(4, -1)          
          
        vBox.Add(hBox, 0)	
            
        # add the comment field, if necessary
        if item.HasComment():
            comment = item.GetMethodComment()
            widget = self.RenderTextField(comment, self.commentFont, item, chandler.methodComment)
            vBox.Add(widget, 0, wxEXPAND)
            
        container.Add(vBox, 1, wxEXPAND)

        # add some empty space between addresses
        container.Add(-1, 3)
        container.Add(-1, 3)

    # loop through the addresses, laying them out in a table		
    def LayoutWidgets(self):
        if self.contact == None:
            return
        
        self.Hide()
 
        container = wxFlexGridSizer(cols=2, vgap=4, hgap=8)
        container.AddGrowableCol(1)
                
        addressList = self.contact.GetContactMethods()
        count = 0
        for addressItem in addressList:
            self.LayoutAddressItem(addressItem, container)
            count += 1
            
        # if there are no addresses, add an add button
        if count == 0:
            container = wxBoxSizer(wxVERTICAL)
            container.Add(-1, 12)
            button = wxButton(self, self.commandID, _("Add New Address"))
            container.Add(button, flag=wxALIGN_CENTER)
            EVT_BUTTON(self, self.commandID, self.AddNewAddressDialog)
            self.commandID += 1
        
        self.SetSizerAndFit(container)
        self.Layout()
        
        self.Show()
                
    # ActivateNextField is used to handle tabs, by selecting the next field
    # after the active one, or the first one if the last is activated
    def ActivateNextField(self):
        if self.singleContactView.editAddressItem != None:	
            # look up the current item position
            addresses = self.contact.GetAddresses()
            index = addresses.index(self.singleContactView.editAddressItem)
            newIndex = index
            newPart = self.singleContactView.editPart
            
            attributes = self.singleContactView.editAddressItem.GetAddressAttributes()
            
            # see if current attribute is the last one
            if attributes[-1] == self.singleContactView.editPart:
                # it's the last one, so bump the index and wrap it around
                newIndex = index + 1
                if newIndex >= len(addresses):
                    newIndex = 0
                newItem = addresses[newIndex]
                attributes = newItem.GetAddressAttributes()
                newPart = attributes[0]
            elif (self.singleContactView.editPart == chandler.methodComment):
                newPart = ''
            else:	
                # it's not the last one, so bump to the next attribute
                attributeIndex = attributes.index(self.singleContactView.editPart)
                newPart = attributes[attributeIndex + 1]
                # skip over linebreak attribute
                if newPart == 'linebreak':
                    newPart = attributes[attributeIndex + 2]

            self.SetEditItem(addresses[newIndex], newPart, true)

    # add a new address to the current contact with the passed-in label
    def AddNewAddress(self, label, forceResize):
        properties = self.locationProperties[label]
        newType = properties[1]

        # add the address and display it
        newAddressItem = self.contact.AddAddress(newType, label)
        attributes = newAddressItem.GetAddressAttributes()

        # add the address item and commit the changes
        repository = Repository()
        repository.AddThing(newAddressItem)

        self.RenderWidgets()
        
        # FIXME: ugly hack to force sizing and scrolling
        if forceResize:
            contentView = self.singleContactView.GetParent()
            contentView.ForceResizeAndSelect(newAddressItem, attributes[0])
            contentView.ScrollToBottom()
            
    # add a new address to the contact by showing a dialog to allow the
    # user to select an address type
    def AddNewAddressDialog(self, event):
        choiceList = self.locationProperties.keys()
        choiceList.sort()

        title = _("Add a Contact Method:")
        label = _("Select the type of contact method to add:")
        dialog = ContactChoiceDialog(app.wxMainFrame, title, label, _("Contact Method:"), choiceList, None)

        result = dialog.ShowModal()
        if result == wxID_OK:
            addressLabel = dialog.GetSelection()
            self.AddNewAddress(addressLabel, true)
    
    # test if the first part of an address item has its default value
    def HasDefaultValue(self, contactItem):
        attribute = contactItem.GetFirstAttribute()
        currentValue = contactItem.GetAttribute(attribute)
        attributeTemplate = contactItem.GetAttributeTemplate(attribute)
        if attributeTemplate == None:
            defaultValue = ''
        else:
            defaultValue = attributeTemplate.GetDefault()
        return currentValue == defaultValue
 
    # test if the next field after the current one has its default value
    def NextFieldHasDefaultValue(self):
        # see if the current item has more fields
        attributes = self.singleContactView.editAddressItem.GetAddressAttributes()
            
        # see if current attribute is the last one, if not return true (even if not default)
        if attributes[-1] != self.singleContactView.editPart:
            return true
        
        addresses = self.contact.GetAddresses()
        index = addresses.index(self.singleContactView.editAddressItem)
        index += 1
        
        if index < len(addresses):
            nextContactItem = addresses[index]
            return self.HasDefaultValue(nextContactItem)
        return false
    
    # Edit the first contact method if it has its default value
    def ActivateFirstFieldIfDefault(self):
        contactMethods = self.contact.GetContactMethods()
        if len(contactMethods) == 0:
            return
        
        # figure out the current and default values of the first contact method
        firstContactMethod = contactMethods[0]
        if self.HasDefaultValue(firstContactMethod):
            attribute = firstContactMethod.GetFirstAttribute()
            self.SetEditItem(firstContactMethod, attribute, false)
                             
    # handle the enter key
    def OnKeystroke(self, event):
        keycode = event.GetKeyCode()
        # handle return by accepting
        if keycode == 13:
            if self.NextFieldHasDefaultValue():
                self.ActivateNextField()
            else:
                self.DoneEditing()
        # handle tabs
        elif keycode == 9:
            self.ActivateNextField()
        # handle escape by rejecting
        elif keycode == 27:
            self.SetEditItem(None, '', false)			
        else:
            if keycode < 32 or keycode > 255 or self.singleContactView.editAddressItem.GetMethodType() == 'note':
                event.Skip()
            else:
                self.editField.AutoComplete(keycode)
  
    # clear editing if clicked in blank part
    def OnLeftClick(self, event):
        self.SetEditItem(None, None, true)
                
# utility class to handle clicks on the text fields by invoking a menu or editing a field
class AddressActionHandler:
    def __init__(self, addressList, addressItem, widget, part):
        self.addressList = addressList
        self.item = addressItem
        self.widget = widget
        self.part = part
        self.actionMenu = None

        EVT_LEFT_DOWN(widget, self.HandleClick)
        EVT_RIGHT_DOWN(widget, self.HandleRightClick)
        
    # shared routine to actually pop-up the menu
    def PresentMenu(self, menu, event):
        xPos, yPos = self.widget.GetPositionTuple()
        xOffset, yOffset = event.GetPositionTuple()
        position = (xPos + xOffset, yPos + yOffset)
        self.addressList.PopupMenu(menu, position)

    # generate a sub menu containing address label choices
    def MakeLabelMenu(self):
        labelMenu = wxMenu()
        contactsView = self.addressList.singleContactView.contactsView
        
        labels = self.addressList.locationProperties.keys()
        labels.sort()

        for menuLabel in labels:
            labelMenu.Append(contactsView.commandID, menuLabel, menuLabel)
            setLabelHandler = SetLabelMenuHandler(self.addressList, menuLabel)
            wx.EVT_MENU(contactsView, contactsView.commandID, setLabelHandler.SetNewAddressLabel)
            contactsView.commandID += 1
       
        label = _("Add New Contact Method Type")
        labelMenu.AppendSeparator()
        labelMenu.Append(contactsView.commandID, label, label)
        wx.EVT_MENU(contactsView, contactsView.commandID, self.AddNewDescription)
        contactsView.commandID += 1

        return labelMenu
    
    # generate a sub menu containing address label choices
    def MakeAddContactMethodMenu(self):
        contactMethodMenu = wxMenu()
        contactsView = self.addressList.singleContactView.contactsView
        
        contactMethods = self.addressList.locationProperties.keys()
        contactMethods.sort()

        for menuLabel in contactMethods:
            contactMethodMenu.Append(contactsView.commandID, menuLabel, menuLabel)
            handler = AddContactMethodMenuHandler(self.addressList, menuLabel)
            wx.EVT_MENU(contactsView, contactsView.commandID, handler.AddContactMethod)
            contactsView.commandID += 1

        label = _("Add New Contact Method Type")
        contactMethodMenu.AppendSeparator()
        contactMethodMenu.Append(contactsView.commandID, label, label)
        wx.EVT_MENU(contactsView, contactsView.commandID, self.AddNewDescription)
        contactsView.commandID += 1

        return contactMethodMenu
    
    
    # utility routine to add a menu item
    def _AddMenuItem(self, menu, label, handler, enabled):
        contactsView = self.addressList.singleContactView.contactsView
        menu.Append(contactsView.commandID, label, label)
        menu.Enable(contactsView.commandID, enabled)
        wx.EVT_MENU(contactsView, contactsView.commandID, handler)
        contactsView.commandID += 1

    # add type specific actions based on the type of the label
    # FIXME: eventually, we'll have an extensible API for adding scripts that
    # add commands to this menu, but for now it's hardwired
    def AddTypeActions(self, actionMenu):
        methodType = self.item.GetMethodType()
        needsSeparator = true
        
        if methodType == 'email':
            itemLabel = _('Compose email to %s') % (self.item.GetAttribute(chandler.emailAddress))
            self._AddMenuItem(actionMenu, itemLabel, self.ComposeEmail, true)
        elif methodType == 'phone':
            itemLabel = _('Call %s') % (self.item.GetFormattedAttribute(chandler.phonenumber))
            self._AddMenuItem(actionMenu, itemLabel, self.MakePhoneCall, true)        
        elif methodType == 'postal':
            itemLabel = _('Show map of address')
            self._AddMenuItem(actionMenu, itemLabel, self.ShowMap, true)
        elif methodType == 'jabberID':
            contact = self.addressList.contact
            jabberID = self.item.GetAttribute(chandler.jabberAddress)
            isPresent = app.jabberClient.IsPresent(jabberID)
            isSubscribed = app.jabberClient.IsSubscribed(jabberID)

            itemLabel = _('Compose instant message to %s') % (self.item.GetAttribute(chandler.jabberAddress))
            self._AddMenuItem(actionMenu, itemLabel, self.ComposeIM, isPresent)
            
            itemLabel = _("Add %s to roster") % (contact.GetFullName())
            self._AddMenuItem(actionMenu, itemLabel, self.SubscribeToPresence, not isSubscribed)
            
            itemLabel = _("Remove %s from roster") % (contact.GetFullName())
            self._AddMenuItem(actionMenu, itemLabel, self.UnsubscribeToPresence, isSubscribed)

        elif methodType == 'website':
            itemLabel = _('Display webpage %s') % (self.item.GetAttribute(chandler.url))
            self._AddMenuItem(actionMenu, itemLabel, self.DisplayWebsite, true)
        else:
            needsSeparator = false

        return needsSeparator
    
    # generate a pop-up menu containing actions to perform on the address.  All addresses have the
    # delete command; the other ones are type specific
    def PresentActionMenu(self, event):
        actionMenu = wxMenu()
        addressType = self.item.GetMethodType()
        self.addressList.addressLocationItem = self.item			
        
        needsSeparator = self.AddTypeActions(actionMenu)		
        if needsSeparator:
            actionMenu.AppendSeparator()

        # add the edit command
        description = self.addressList.GetTypeDescription(addressType)
        itemLabel = 'Edit %s' % (description)
        self._AddMenuItem(actionMenu, itemLabel, self.EditValue, true)

        # add the add or edit command item
        if self.item.HasComment():
            itemLabel = _("Edit Comment about %s ") % (description)
        else:
            itemLabel = _("Add Comment about %s") % (description)
        self._AddMenuItem(actionMenu, itemLabel, self.AddOrEditComment, true)

        # add the 'change type' submenu
        subMenu = self.MakeLabelMenu()
        subMenuLabel = _('Change "%s" Description') % (self.item.GetMethodDescription())
        contactsView = self.addressList.singleContactView.contactsView
        actionMenu.AppendMenu(contactsView.commandID, subMenuLabel, subMenu)
        contactsView.commandID += 1
       
        actionMenu.AppendSeparator()
        
        # add the 'add contact menu' submenu
        subMenu = self.MakeAddContactMethodMenu()
        contactsView = self.addressList.singleContactView.contactsView
        actionMenu.AppendMenu(contactsView.commandID, 'Add New Contact Method to this Contact', subMenu)
        contactsView.commandID += 1
     
        # add the delete command, independent of type
        deleteLabel = _("Delete %s") % (self.item.GetMethodDescription())
        actionMenu.Append(contactsView.commandID, deleteLabel , deleteLabel)
        wx.EVT_MENU(contactsView, contactsView.commandID, self.DeleteAddressItem)
        contactsView.commandID += 1
                
        self.PresentMenu(actionMenu, event)

    # handlers for the various actions
    def DeleteAddressItem(self, event):
        addressList = self.addressList
        
        addressList.contact.DeleteContactMethod(self.item)
        addressList.RenderWidgets()

        # tell the index view about it, too
        addressList.indexView.UpdateContact(self.addressList.contact)

        # readjust scrolling after delete
        contentView = addressList.singleContactView.GetParent()
        contentView.ForceResizeAndSelect(None, None)

    def EditValue(self, event):
        attributes = self.item.GetAddressAttributes()
        part = attributes[0]
        self.addressList.SetEditItem(self.item, part, true)
 
    def AddOrEditComment(self, event):
        if not self.item.HasComment():
            self.item.SetMethodComment(_('comment goes here'))
        
        self.addressList.SetEditItem(self.item, chandler.methodComment, true)
        
        
    def ComposeEmail(self, event):
        wxMessageBox(_("The Compose Email command isn't implemented yet."))
                
    def MakePhoneCall(self, event):
        wxMessageBox(_("The Make Phone Call command isn't implemented yet."))

    def ComposeIM(self, event):
        name = self.addressList.contact.GetFullName()
        url = "Roster/" + name
        app.wxMainFrame.GoToURL(url)
        
    def SubscribeToPresence(self, event):
        jabberID = self.item.GetAttribute(chandler.jabberAddress)
        app.jabberClient.RequestSubscription(jabberID, true)
   
    def UnsubscribeToPresence(self, event):
        jabberID = self.item.GetAttribute(chandler.jabberAddress)
        app.jabberClient.RequestSubscription(jabberID, false)
   
    def ShowMap(self, event):
        wxMessageBox(_("The Show Map command isn't implemented yet."))

    def DisplayWebsite(self, event):
        url = self.item.GetAttribute(chandler.url)
        if not url.startswith('http://'):
            url = 'http://' + url
        webbrowser.open(url)
                
    def AddNewDescription(self, event):
        self.addressList.SetEditItem(self.item, 'label', true)
                
    # handle clicks by presenting the action menu or editing the clicked object
    def HandleClick(self, event):
        if self.addressList.contact.IsRemote():
            contactsView = self.addressList.singleContactView.contactsView
            contactsView.ShowCantEditDialog(self.addressList.contact)
            return
        
        if self.part == 'image':
            if self.addressList.isEdited():
                self.addressList.DoneEditing()
            else:
                self.PresentActionMenu(event)
        elif self.part == 'label':
            self.PresentActionMenu(event)
        else:   
            self.addressList.SetEditItem(self.item, self.part, true)
 
    def HandleRightClick(self, event):
        if self.addressList.contact.IsRemote():
            contactsView = self.addressList.singleContactView.contactsView
            contactsView.ShowCantEditDialog(self.addressList.contact)
            return

        self.PresentActionMenu(event)
        
# handler to handle set label menu commands
class SetLabelMenuHandler:
    def __init__(self, addressList, newLabel):
        self.addressList = addressList
        self.newLabel = newLabel

    def SetNewAddressLabel(self, event):
        if self.newLabel[-1] == ':':
            self.newLabel = self.newLabel[0:-1]

        item = self.addressList.addressLocationItem
        item.SetMethodDescription(self.newLabel)
        self.addressList.SetAddressType(item, self.newLabel)
        
        self.addressList.RenderWidgets()

# handler to add a contact method
class AddContactMethodMenuHandler:
    def __init__(self, addressList, newLabel):
        self.addressList = addressList
        self.newLabel = newLabel

    def AddContactMethod(self, event):
        if self.newLabel[-1] == ':':
            self.newLabel = self.newLabel[0:-1]

        # add a new contact method of the given type
        self.addressList.AddNewAddress(self.newLabel, true)
