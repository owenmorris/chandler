#!bin/env python

"""
 Name Area for SingleContactView
"""
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002, 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.lib.imagebrowser import *

from application.Application import app

from application.repository.Namespace import chandler
from application.repository.Repository import Repository

import urllib
from copy import copy
import parcels.OSAF.contacts.ImageCache
from parcels.OSAF.contacts.AutoCompleteTextCtrl import *

# here's the ContactNamePlate class, which displays the name and other
# attributes of the associated contact, as well as an optional photo
class ContactNamePlate(wxPanel):
    def __init__(self, parent, contact, singleContactView, indexView, images):
        self.contact = contact
        self.singleContactView = singleContactView
        self.parent = parent
        self.indexView = indexView
        self.images = images
        self.commandID = 100
        
        self.editAttribute = None
        self.editField = None
                
        self.genericPhotoImage = self.images.LoadBitmapFile('genericphoto.jpg')
                
        wxPanel.__init__(self, parent, -1)
        
        self.nameFont = wxFont(20, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
        self.itemFont = wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")		

        self.LayOutWidgets()
                
        EVT_LEFT_DOWN(self, self.OnNamePlateLeftDown)
        
    # return the contact associated with the nameplate
    def GetContact(self):
        return self.contact

    # set a new contact
    def SetContact(self, newContact):
        if self.contact != newContact:
            self.contact = newContact
            self.RenderWidgets()

    # read the preference to determine if we're using one name field or not
    def UseOneNameField(self):
        return self.singleContactView.contactsView.model.useOneNameField
          
    # get a list of attributes to display in the header
    def GetNamePlateAttributes(self):
        fieldList = copy(self.contact.GetHeaderAttributes())
        if self.UseOneNameField():
            fieldList.insert(0, chandler.fullname)           
        else:
            fieldList.insert(0, chandler.lastname)
            fieldList.insert(0, chandler.firstname)
        return fieldList
    
    def GetAttributeDictionary(self):
        return self.singleContactView.contactsView.contactMetaData
    
    # add a new value to an enumerated type, if necessary
    def UpdateEnumeration(self, newValue):
        attributeDictionary = self.GetAttributeDictionary()
        attributeType = attributeDictionary.GetAttributeType(self.editAttribute)
        if attributeType == 'enumeration':
            choiceList = attributeDictionary.GetAttributeData(self.editAttribute)
            try:
                index = choiceList.index(newValue)
            except ValueError:
                choiceList.append(newValue)
   
    # change the edit attribute, render as necessary
    def SetEditAttribute(self, newAttribute, acceptFlag):
        if self.editAttribute != newAttribute:
            # update the old attribute, if any
            if self.editField != None and self.editAttribute != None and len(self.editAttribute) > 0:
                if acceptFlag:
                    text = self.editField.GetValue()
                    self.contact.SetAttribute(self.editAttribute, text)
                    self.UpdateEnumeration(text)

                    # commit the changes
                    repository = Repository()
                    repository.Commit()
                    
                    # if the last name changed, resort the contacts
                    if self.editAttribute == chandler.lastname or self.editAttribute == chandler.fullname:
                        # since ResortContacts can make a new contentView which would destroy
                        # this object, we freeze the content view before calling it so that can't happen
                        contentView = self.indexView.contactsView.contentView
                        wasFrozen = contentView.GetFrozen()
                        contentView.SetFrozen(true) 
                        self.indexView.ResortContacts(self.contact)
                        contentView.SetFrozen(wasFrozen)
                    else:   
                        self.indexView.UpdateContact(self.contact)
                                
            self.editAttribute = ''
            self.singleContactView.DoneEditing()
                        
            # render for the new attribute
            self.editAttribute = newAttribute
            self.RenderWidgets()
    
    # terminate editing, if any, by accepting changes
    def DoneEditing(self):
        self.SetEditAttribute('', true)
                
    # add an image if there's one specified by the photourl attribute;
    # otherwise, use a generic image
    def AddPhoto(self, container):
        photoURL = self.contact.GetPhotoURL()
        if photoURL != None:
            try:
                photoBitmap = self.images.LoadBitmapURL(photoURL, maxWidth=80, maxHeight=80)
            except:
                photoBitmap = self.genericPhotoImage  
        else:
            photoBitmap = self.genericPhotoImage

        if photoBitmap == None:
            photoBitmap = self.genericPhotoImage
            
        photoWidget = wxStaticBitmap(self, -1, photoBitmap)

        container.Add(photoWidget, 0, wxTOP, 4)
        EVT_LEFT_DOWN(photoWidget, self.GetPhotoImage)

    # return the choiceList used for auto-completion associated with a part type
    def GetChoiceList(self, attribute):
        dictionary = self.GetAttributeDictionary()
        return dictionary.GetAttributeChoices(attribute)
        
    # utility routine to render a text field as either a static text object, or
    # a text control, if its attribute is the edit attribute
    def RenderTextField(self, text, attribute, font):
        if self.editAttribute == attribute:
            isFullName = attribute == chandler.fullname
            if isFullName:
                choiceList = {}
                choiceList['firstname'] = self.GetChoiceList(chandler.firstname)
                choiceList['lastname'] = self.GetChoiceList(chandler.lastname)
            else:
                choiceList = self.GetChoiceList(attribute)
               
            widget = AutoCompleteTextCtrl(self, -1, text, choiceList, isFullName, style=wxTE_RICH | wxTE_PROCESS_ENTER)
            self.editField = widget
                        
            width, height, descent, ascent = self.GetFullTextExtent(text, font)
            widget.SetSize((width + 32, height + descent + 4))
            widget.SetFont(font)
            widget.SetFocus()
            widget.SelectAll()
                        
            EVT_CHAR(widget, self.OnKeystroke)
        else:
            attributeDictionary = self.GetAttributeDictionary()
            widget = wxStaticText(self, -1, text)
            handler = AttributeMenuHandler(widget, self, attributeDictionary, attribute)
            widget.SetFont(font)

        return widget

    # destroy any exisiting widgets and layout a new set to represent the contact
    def RenderWidgets(self):
        self.DestroyChildren()
        self.LayOutWidgets()
        
    # allocate and layout the widgets to represent the contact	
    # for now, we're keeping two different approaches around: a single, parsed field for the name,
    # or two seperate fields, selectable by a boolean
    def LayOutWidgets(self):
        if self.contact == None:
            return
        
        hBox = wxBoxSizer(wxHORIZONTAL)
        vBox = wxBoxSizer(wxVERTICAL)
        
        # indent a little vertically, then add the photo or placeholder image
        vBox.Add(-1, 2)
        self.AddPhoto(hBox)
        hBox.Add(6, -1)
        
        # render the name parts
        nameBox = wxBoxSizer(wxHORIZONTAL)
        
        # at least for now, we support two different ways of entering the name, determined by a preference.
        # We use a single, parsed field, or separate first and lastname fields
        
        if self.UseOneNameField():
            fullName = self.contact.GetFullName()
            widget = self.RenderTextField(fullName, chandler.fullname, self.nameFont)	
            nameBox.Add(widget, 0)            
        else:
            firstName = self.contact.GetNameAttribute(chandler.firstname)
            widget = self.RenderTextField(firstName, chandler.firstname, self.nameFont)	
            nameBox.Add(widget, 0)

            nameBox.Add(8, -1)

            lastName = self.contact.GetNameAttribute(chandler.lastname)
            widget = self.RenderTextField(lastName, chandler.lastname, self.nameFont)	
            nameBox.Add(widget, 1)

        vBox.Add(nameBox, 0)

        # display the revelant attributes below the name
        attributes = self.contact.GetHeaderAttributes()
        for attribute in attributes:
            value = self.contact.GetAttribute(attribute)
            if value == None:
                attributeDictionary = self.GetAttributeDictionary()
                value = attributeDictionary.GetAttributeDefaultValue(attribute)
                
            newWidget = self.RenderTextField(value, attribute, self.itemFont)
            vBox.Add(newWidget, 0, wxEXPAND)


        hBox.Add(vBox, false)				        
        self.SetSizerAndFit(hBox)
        self.Layout()
                
    # GetNextFieldIndex returns the index of the next field
    def GetNextFieldIndex(self, currentAttribute):
        if currentAttribute == None or len(currentAttribute) == 0:
            return 0
        
        fieldList = self.GetNamePlateAttributes()
        
        # look up the current position
        index = fieldList.index(currentAttribute)
                        
        # bump the index and wrap it around
        newIndex = index + 1
        if newIndex >= len(fieldList):
            newIndex = 0
            
        return newIndex
     
    # Activate the next editable field
    def ActivateNextField(self):
        foundField = false
        attributeDictionary = self.GetAttributeDictionary()
        fieldList = self.GetNamePlateAttributes()
        editAttribute = self.editAttribute
        
        # loop until we find one that's not an enumeration
        while not foundField:
            newIndex = self.GetNextFieldIndex(editAttribute)
            attributeType = attributeDictionary.GetAttributeType(fieldList[newIndex])
            foundField = attributeType != 'enumeration'
            editAttribute = fieldList[newIndex]
            
        self.SetEditAttribute(fieldList[newIndex], true)

    # determine if the next field after the passed in one has it's default value
    def NextFieldHasDefaultValue(self):
        nextFieldIndex = self.GetNextFieldIndex(self.editAttribute)
        fieldList = self.GetNamePlateAttributes()
        
        # if there's only one field, don't endlessly wrap
        if len(fieldList) == 1:
            return false
        
        attribute = fieldList[nextFieldIndex]
        
        attributeDictionary = self.GetAttributeDictionary()
        attributeType = attributeDictionary.GetAttributeType(attribute)
        defaultValue = attributeDictionary.GetAttributeDefaultValue(attribute)
        currentValue = self.contact.GetAttribute(attribute)
        return attributeType != 'enumeration' and (currentValue == None or defaultValue == currentValue)
    
    # some event handlers
    def OnKeystroke(self, event):
        keycode = event.GetKeyCode()
        # handle return by accepting whatever's in the field
        if keycode == 13:
            if self.NextFieldHasDefaultValue():
                 self.ActivateNextField()
            else:
               nextFieldIndex = self.GetNextFieldIndex(self.editAttribute)
               self.DoneEditing()
               # if it was the last field, pass the torch to the address list
               if nextFieldIndex == 0:
                   addressList = self.singleContactView.contactAddressList
                   addressList.ActivateFirstFieldIfDefault()
                   
         # handle tabs
        elif keycode == 9:
            self.ActivateNextField()
        # handle escape by cancelling whatever's in the field
        elif keycode == 27:
            self.SetEditAttribute('', false)	
        else:
            if keycode < 32:
                event.Skip()
            else:
                self.editField.AutoComplete(keycode)

    # select a photo for this address card
    def GetPhotoImage(self, event):
        contactsView = self.indexView.contactsView
        if self.contact.IsRemote():
            contactsView.ShowCantEditDialog(self.contact)
            return

        if contactsView.model.lastImageDirectory == None:
            contactsView.model.lastImageDirectory = wxGetHomeDir()
 
        dialog = ImageDialog(app.wxMainFrame, contactsView.model.lastImageDirectory)
        dialog.Centre()
        
        if dialog.ShowModal() == wxID_OK:
            path = dialog.GetFile()
            fileURL = urllib.pathname2url(path)
            self.contact.SetPhotoURL(fileURL)
            self.RenderWidgets()
            self.singleContactView.Layout()
 
        contactsView.model.lastImageDirectory = dialog.GetDirectory()
        dialog.Destroy()
                
    # handle clicks on the background by closing down any editing
    def OnNamePlateLeftDown(self, event):
        self.DoneEditing()
        
# here's a utility class to handle the menu commands
class AttributeMenuHandler:
    def __init__(self, widget, namePlate, attributeDictionary, attribute):
        self.widget = widget
        self.namePlate = namePlate
        self.attributeDictionary = attributeDictionary
        self.attribute = attribute

        EVT_LEFT_DOWN(widget, self.OnLeftDown)

    def PresentMenu(self, menu, event):
        xPos, yPos = self.widget.GetPositionTuple()
        xOffset, yOffset = event.GetPositionTuple()
        position = (xPos + xOffset, yPos + yOffset)
        self.namePlate.PopupMenu(menu, position)
        
    # handle clicks on attribute text by presenting a pop-up menu
    def OnLeftDown(self, event):
        contactsView = self.namePlate.singleContactView.contactsView

        if self.namePlate.contact.IsRemote():
            contactsView.ShowCantEditDialog(self.namePlate.contact)
            return
        
        attributeType = self.attributeDictionary.GetAttributeType(self.attribute)
        attributeData = self.attributeDictionary.GetAttributeData(self.attribute)
       
        if attributeType == 'enumeration':
            attributeMenu = wxMenu()
            choiceList = attributeData
            
            if len(choiceList) == 0:
                self.namePlate.SetEditAttribute(self.attribute, true)
                return
            
            choiceList.sort()
            
            currentAttribute = self.namePlate.contact.GetAttribute(self.attribute)
            for itemLabel in choiceList:
                attributeMenu.Append(contactsView.commandID, itemLabel, itemLabel, wxITEM_RADIO)
                if itemLabel == currentAttribute:
                    attributeMenu.Check(contactsView.commandID, true)
                    
                handler = SetAttributeHandler(self, itemLabel)
                wx.EVT_MENU(contactsView, contactsView.commandID, handler.SetAttributeCommand) 
                contactsView.commandID += 1
                 
            label = _("Add New Value")
            attributeMenu.AppendSeparator()
            attributeMenu.Append(contactsView.commandID, label, label)
            wx.EVT_MENU(contactsView, contactsView.commandID, self.AddNewAttributeValue)
            contactsView.commandID += 1
            
            self.PresentMenu(attributeMenu, event)
        elif attributeType == 'string' or attributeType == 'integer':
            self.namePlate.SetEditAttribute(self.attribute, true)
            
    def AddNewAttributeValue(self, event):
        self.namePlate.SetEditAttribute(self.attribute, false)	

# utility class to actually set the attribute value
class SetAttributeHandler:
    def __init__(self, menuHandler, attributeValue):
        self.menuHandler = menuHandler
        self.attributeValue = attributeValue
    
    # this is invoked when the menu item is selected, to update both the view and the underlying contact
    def SetAttributeCommand(self, event):
        self.menuHandler.widget.SetLabel(self.attributeValue)
        self.menuHandler.namePlate.contact.SetAttribute(self.menuHandler.attribute, self.attributeValue)
                
