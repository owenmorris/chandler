#!bin/env python

"""
 Contact Attribute List for SingleContactView
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from application.Application import app
from application.repository.Repository import Repository
from parcels.OSAF.contacts.AutoCompleteTextCtrl import *

# here's the text widget used to display a group name, and link to the group when clicked on
class GroupTextWidget(wxStaticText):      
    def __init__(self, parent, group, attributeList):
        self.group = group
        self.attributeList = attributeList

        wxStaticText.__init__(self, parent, -1, group)
        self.SetFont(attributeList.plainFont)
        
        # handle left and right click the same way (at least until we have
        # something better to use right click for)
        EVT_LEFT_DOWN(self, self.OnClick)
        EVT_RIGHT_DOWN(self, self.OnClick)

    # routine to generate the "AddGroups" menu
    def MakeAddGroupsMenu(self):
        addGroupsMenu = wxMenu()
        contactsView = self.attributeList.singleContactView.contactsView
        contactName = self.attributeList.contact.GetFullName()
        contactGroups = self.attributeList.contact.GetGroups()
        
        allGroups = contactsView.contactMetaData.GetGroupsList()
        allGroups.sort()

        # build the menu by iterating through the groups
        for group in allGroups:
            helpMessage = _('Add %s to the %s group') % (contactName, group)
            addGroupsMenu.Append(contactsView.commandID, group, helpMessage)
            setGroupHandler = AddToGroupHandler(self.attributeList, group)
            wx.EVT_MENU(contactsView, contactsView.commandID, setGroupHandler.AddToGroup)
            
            # if the contact is already in this group, disable the item
            try:
                index = contactGroups.index(group)
                addGroupsMenu.Enable(contactsView.commandID, false)
            except ValueError:
                pass
            
            contactsView.commandID += 1

        label = _("Add to a New Group")
        addGroupsMenu.AppendSeparator()
        addGroupsMenu.Append(contactsView.commandID, label, label)
        wx.EVT_MENU(contactsView, contactsView.commandID, self.AddNewGroup)
        contactsView.commandID += 1

        return addGroupsMenu
       
    # when a group widget is clicked, pop up a menu for the options
    def OnClick(self, event):
        if self.attributeList.contact.IsRemote():
            contactsView = self.attributeList.singleContactView.contactsView
            contactsView.ShowCantEditDialog(self.attributeList.contact)
            return

        groupMenu = wxMenu()
        contactName = self.attributeList.contact.GetFullName()        
        contactsView = self.attributeList.singleContactView.contactsView
        
        if self.group == 'None':
            removeCommandText = _('No group to remove from')
            gotoCommandText = _('No group to go to')
        else:
            removeCommandText = _('Remove %s from the %s group') % (contactName, self.group)
            gotoCommandText = _('Go to the %s Group') % (self.group)
           
        # add the "goto group" command
        wx.EVT_MENU(contactsView, contactsView.commandID, self.GoToGroup)
        groupMenu.Append(contactsView.commandID, gotoCommandText, gotoCommandText)
        if self.group == 'None':
            groupMenu.Enable(contactsView.commandID, false)
        contactsView.commandID += 1
        
        groupMenu.AppendSeparator()
        
        # add the "remove from group command
        wx.EVT_MENU(contactsView, contactsView.commandID, self.RemoveFromGroup)
        groupMenu.Append(contactsView.commandID, removeCommandText, removeCommandText)
        if self.group == 'None':
            groupMenu.Enable(contactsView.commandID, false)
        contactsView.commandID += 1
        
        # add the "add group" command in a submenu
        subMenu = self.MakeAddGroupsMenu()
        addGroupText = _('Add %s to Group') % (contactName)
        groupMenu.AppendMenu(contactsView.commandID, addGroupText, subMenu)
        contactsView.commandID += 1
        
        # present the menu
        xPos, yPos = event.GetPositionTuple()
        self.attributeList.PopupMenu(groupMenu, (xPos, yPos))
                
    # handle the actions for the pop-up menu associated with a group
    def RemoveFromGroup(self, event):
        contact = self.attributeList.contact
        contact.RemoveGroup(self.group)
        self.attributeList.UpdateAttributes()
 
    # create a new group, and add the contact to that
    def AddNewGroup(self, event):
        caption = 'Enter the name of the new group to add:'
        dialog = wxTextEntryDialog(app.wxMainFrame, caption)
        if dialog.ShowModal() == wxID_OK:
            newGroupName = dialog.GetValue()
            self.attributeList.contact.AddGroup(newGroupName)
            self.attributeList.UpdateAttributes()
            
        dialog.Destroy()
       
    def GoToGroup(self, event):
        wxMessageBox(_("Go to Group command not implemented yet!"))

# this class handles "multienum" fields, which are a list of 0
# or more objects from an enumeration.
class MultiEnumText(wxStaticText):
    def __init__(self, parent, attribute, selectedList, possibleList, attributeWidget):
        self.attribute = attribute
        self.selectedList = selectedList
        self.possibleList = possibleList
        self.attributeWidget = attributeWidget
        self.checkMenu = None
        
        text = self.GetDisplayText()
        wxStaticText.__init__(self, parent, -1, text)
        
        # handle left and right click the same way (at least until we have
        # something better to use right click for)
        EVT_LEFT_DOWN(self, self.OnClick)
        EVT_RIGHT_DOWN(self, self.OnClick)
        
    # generate the text to display by looping through the selected items
    def GetDisplayText(self):
        text = ''
        for item in self.selectedList:
            if len(text) > 0:
                text = text + ', '
            text = text + item
        
        if len(text) == 0:
            text = 'None'
        
        return text
 
    # update the text to reflect the selected items
    def UpdateText(self):
        text = self.GetDisplayText()
        self.SetLabel(text)
    
    # return true if the attribute is in the select list
    def HasAttribute(self, attribute):
        try:
            index = self.selectedList.index(attribute)
            return true
        except ValueError:
            return false
        return false
    
    # display a pop-up menu with checks to enable/display attributes
    def ShowCheckMenu(self, event):
        self.checkMenu = wxMenu()
        contactsView = self.attributeWidget.singleContactView.contactsView
        
        # build the menu by iterating through the groups
        index = 0
        for item in self.possibleList:
            hasAttribute = self.HasAttribute(item)
            if hasAttribute:
                helpMessage = _('Remove %s from %s') % (item, self.attribute)
            else:
                 helpMessage = _('Add %s to %s') % (item, self.attribute)
               
            self.checkMenu.Append(contactsView.commandID, item, helpMessage, wxITEM_CHECK)
            checkItemHandler = CheckItemHandler(self, item, index)
            wx.EVT_MENU(contactsView, contactsView.commandID, checkItemHandler.ItemChanged)           
            self.checkMenu.Check(contactsView.commandID, hasAttribute)
            
            contactsView.commandID += 1
            index += 1
  
        # FIXME: Perhaps create a convenience method
        # Look up the attribute's display name. Search the repository
        # for the attribute template, using the attribute's url
        repository = Repository()
        attributeTemplate = repository.FindThing(self.attribute)
        attributeDisplayName = attributeTemplate.GetDisplayName()
        
        addLabel = _("Add a new %s") % (attributeDisplayName)
        self.checkMenu.AppendSeparator()
        self.checkMenu.Append(contactsView.commandID, addLabel, addLabel)
        wx.EVT_MENU(contactsView, contactsView.commandID, self.AddNewItem)
        contactsView.commandID += 1

        # present the menu
        xPos, yPos = event.GetPositionTuple()
        self.attributeWidget.PopupMenu(self.checkMenu, (xPos, yPos))

    # when a multienum widget is clicked, pop up a menu
    def OnClick(self, event):
        if self.attributeWidget.contact.IsRemote():
            contactsView = self.attributeWidget.singleContactView.contactsView
            contactsView.ShowCantEditDialog(self.attributeWidget.contact)
            return

        self.ShowCheckMenu(event)

    # handle adding a new item to the enumeration
    def AddNewItem(self, event):
        self.attributeWidget.SetEditAttribute(self.attribute, false)
        

# here's a utility class to handle the mulitenum menu items being selected
class CheckItemHandler:
    def __init__(self, enumItem, attribute, itemIndex):
        self.enumItem = enumItem
        self.attribute = attribute
        
    # the item was checked or unchecked, so adjust the display accordingly
    def ItemChanged(self, event):
         isChecked = event.IsChecked()              
         if not isChecked:
             try:
                 index = self.enumItem.selectedList.index(self.attribute)
             except ValueError:
                 self.enumItem.selectedList.append(self.attribute)
                 self.enumItem.selectedList.sort()
         else:
             try:
                 index = self.enumItem.selectedList.index(self.attribute)
                 del self.enumItem.selectedList[index]
             except:
                 pass
        
         self.enumItem.attributeWidget.contact.SetAttribute(self.attribute, self.enumItem.selectedList)
         self.enumItem.attributeWidget.RenderWidgets()
             
# here's a utility class to handle the menu commands
class AttributeMenuHandler:
    def __init__(self, widget, attributeList, attributeDictionary, attribute):
        self.widget = widget
        self.attributeList = attributeList
        self.attributeDictionary = attributeDictionary
        self.attribute = attribute

        # handle left and right click the same way (at least until we have
        # something better to use right click for)
        EVT_LEFT_DOWN(widget, self.OnClick)
        EVT_RIGHT_DOWN(widget, self.OnClick)

    def PresentMenu(self, menu, event):
        xPos, yPos = self.widget.GetPositionTuple()
        xOffset, yOffset = event.GetPositionTuple()
        position = (xPos + xOffset, yPos + yOffset)
        self.attributeList.PopupMenu(menu, position)
        
    # handle clicks on attribute text by presenting a pop-up menu
    def OnClick(self, event):
        if self.attributeList.contact.IsRemote():
            contactsView = self.attributeList.singleContactView.contactsView
            contactsView.ShowCantEditDialog(self.attributeList.contact)
            return

        attributeType = self.attributeDictionary.GetAttributeType(self.attribute)
        attributeData = self.attributeDictionary.GetAttributeData(self.attribute)
        contactsView = self.attributeList.singleContactView.contactsView
       
        if attributeType == 'enumeration':
            attributeMenu = wxMenu()
            choiceList = attributeData
            
            if len(choiceList) == 0:
                self.attributeList.SetEditAttribute(self.attribute, true)
                return
            
            choiceList.sort()
            
            currentAttribute = self.attributeList.contact.GetAttribute(self.attribute)
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
            self.attributeList.SetEditAttribute(self.attribute, true)
            
    def AddNewAttributeValue(self, event):
        self.attributeList.SetEditAttribute(self.attribute, false)	

# utility class to actually set the attribute value
class SetAttributeHandler:
    def __init__(self, menuHandler, attributeValue):
        self.menuHandler = menuHandler
        self.attributeValue = attributeValue
    
    # this is invoked when the menu item is selected, to update both the view and the underlying contact
    def SetAttributeCommand(self, event):
        self.menuHandler.widget.SetLabel(self.attributeValue)
        self.menuHandler.attributeList.contact.SetAttribute(self.menuHandler.attribute, self.attributeValue)
                
# here's the main class for displaying the attributes associated with a contact
class ContactAttributeList(wxPanel):
    def __init__(self, parent, contact, singleContactView, indexView, images):
        self.contact = contact
        self.singleContactView = singleContactView
        self.indexView = indexView
        self.images = images
        
        self.editAttribute = None
        self.editField = None
        
        wxPanel.__init__(self, parent, -1)

        # FIXME: fonts are hardwired for now
        self.plainFont = wxFont(10, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
        self.labelFont = wxFont(10, wxSWISS, wxNORMAL, wxBOLD, false, "Arial")

        self.LayoutWidgets()
                                
    def GetContact(self):
        return self.contact

    def SetContact(self, newContact):
        if self.contact != newContact:
            self.contact = newContact
            self.RenderWidgets()
                        
    def RenderWidgets(self):
        self.DestroyChildren()
        self.LayoutWidgets()

    def UpdateAttributes(self):
        self.RenderWidgets()

    # add a new value to an enumerated type, if necessary
    # FIXME: the attribute dictionary isn't persistent yet
    def UpdateEnumeration(self, newValue):
        attributeDictionary = self.singleContactView.contactsView.GetAttributeDictionary()
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
                    
                    attributeDictionary = self.singleContactView.contactsView.GetAttributeDictionary()
                    type = attributeDictionary.GetAttributeType(self.editAttribute)
                    if type == 'multienum':
                        choiceList = attributeDictionary.GetAttributeData(self.editAttribute)
                        choiceList.append(text)
                        
                        list = self.contact.GetAttribute(self.editAttribute)
                        if list == None:
                            list = []
                        
                        list.append(text)
                        self.contact.SetAttribute(self.editAttribute, list)
                    else:
                        self.contact.SetAttribute(self.editAttribute, text)
                        self.UpdateEnumeration(text)
                    
            self.editAttribute = ''
            self.singleContactView.DoneEditing()
                        
            # render for the new attribute
            self.editAttribute = newAttribute
            self.RenderWidgets()

    def DoneEditing(self):
        self.SetEditAttribute('', true)
               
    def LayoutWidgets(self):
        if self.contact == None:
            return
        
        container = wxFlexGridSizer(cols=2, vgap=4, hgap=8)
        container.AddGrowableCol(1)

        # add group links
        groups = self.contact.GetGroups()
        groupBox = wxBoxSizer(wxHORIZONTAL)
        labelWidget = wxStaticText(self, -1, _("Member of:"))
        labelWidget.SetFont(self.labelFont)
        container.Add(labelWidget, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)

        firstTime = true
        if len(groups) > 0:
            for group in groups:
                if firstTime:
                    firstTime = false
                else:
                    separatorWidget = wxStaticText(self, -1, ',  ')
                    groupBox.Add(separatorWidget, 0)
                                        
                groupWidget = GroupTextWidget(self, group, self)
                groupBox.Add(groupWidget, 0)
        else:
            groupWidget = GroupTextWidget(self, 'None', self)
            groupBox.Add(groupWidget, 0)
             
        container.Add(groupBox, 1, wxEXPAND)
                        
        # add relationship links

        # render the designated attributes
        attributes = self.contact.GetBodyAttributes()       
        attributeDictionary = self.singleContactView.contactsView.GetAttributeDictionary()
        
        for attribute in attributes:
            label = attributeDictionary.GetAttributeLabel(attribute)
            type = attributeDictionary.GetAttributeType(attribute)
            value = self.contact.GetAttribute(attribute)
            
            if label != None:
                label = label + ':'
                labelWidget = wxStaticText(self, -1, label)
                labelWidget.SetFont(self.labelFont)
                container.Add(labelWidget, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)

                if value == None:
                    value = attributeDictionary.GetAttributeDefaultValue(attribute)
                
                if attribute == self.editAttribute:
                    choiceList = attributeDictionary.GetAttributeChoices(attribute)
                    if type == 'multienum':
                        value = ''
                        choiceList = None
                    
                    widget = AutoCompleteTextCtrl(self, -1, value, choiceList, false, style=wxTE_RICH | wxTE_PROCESS_ENTER)
                    self.editField = widget
                        
                    width, height, descent, ascent = self.GetFullTextExtent(value, self.plainFont)
                    widget.SetSize((width + 32, height + descent + 4))
                    widget.SetFont(self.plainFont)
                    widget.SetFocus()
                    widget.SelectAll()
                        
                    EVT_CHAR(widget, self.OnKeystroke)
                else:
                    if type == 'multienum':
                        choiceList = attributeDictionary.GetAttributeData(attribute)                                                
                        widget = MultiEnumText(self, attribute, value, choiceList, self)
                    else:
                        widget = wxStaticText(self, -1, value)
                        handler = AttributeMenuHandler(widget, self, attributeDictionary, attribute)
                    
                    widget.SetFont(self.plainFont)
                
                container.Add(widget, 1, wxEXPAND)
                                
        # add mail and event links (not yet implemented)
        self.SetSizerAndFit(container)
        self.Layout()
    
    # ActivateNextField is used to handle tabs, by selecting the next field
    # calculate the index of the field after the current one
    def GetNextFieldIndex(self):
        if self.editAttribute == None or len(self.editAttribute) == 0:
            return 0
        
        fieldList = self.contact.GetBodyAttributes()
        
        # look up the current position
        index = fieldList.index(self.editAttribute)
                        
        # bump the index and wrap it around
        newIndex = index + 1
        if newIndex >= len(fieldList):
            newIndex = 0
            
        return newIndex
     
    # after the active one, or the first one if the last is activated
    def ActivateNextField(self):
        newIndex = self.GetNextFieldIndex()
        fieldList = self.contact.GetBodyAttributes()
        self.SetEditAttribute(fieldList[newIndex], true)

    # determine if the next field after the passed in one has it's default value
    def NextFieldHasDefaultValue(self):
        nextFieldIndex = self.GetNextFieldIndex()
        fieldList = self.contact.GetBodyAttributes()
        attribute = fieldList[nextFieldIndex]
        
        defaultValue = self.singleContactView.contactsView.GetAttributeDictionary().GetAttributeDefaultValue(attribute)
        currentValue = self.contact.GetAttribute(attribute)
        return currentValue == None or defaultValue == currentValue
    
    # some event handlers
    def OnKeystroke(self, event):
        keycode = event.GetKeyCode()
        # handle return by accepting whatever's in the field
        if keycode == 13:
            if self.NextFieldHasDefaultValue():
                self.ActivateNextField()
            else:
                self.DoneEditing()
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

# handler to add contacts to groups
class AddToGroupHandler:
    def __init__(self, attributeList, newGroup):
        self.attributeList = attributeList
        self.newGroup = newGroup

    def AddToGroup(self, event):
        self.attributeList.contact.AddGroup(self.newGroup)
        self.attributeList.RenderWidgets()
       
