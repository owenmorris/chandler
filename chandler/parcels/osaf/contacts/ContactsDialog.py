#!bin/env python

"""
 Dialog classes for the Contacts Parcel
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from application.Application import app

from OSAF.contacts.ContactsModel import *
from OSAF.contacts.ContactViewInfo import *

class ContactsDialog(wxDialog):
    def __init__(self, parent, title, label):
        wxDialog.__init__(self, parent, -1, title)
        sizer = wxBoxSizer(wxVERTICAL)
        
        # base ID for events
        self.eventID = 100
        
        # add an instructive label
        caption = self.GetCaption(label)
        captionWidget = wxStaticText(self, -1, label)
        captionFont = self.GetCaptionFont()
        if captionFont != None:
            captionWidget.SetFont(captionFont)
            
        sizer.Add(captionWidget, 0, wxALIGN_CENTER|wxALL, 6)
       
        # add the widgets that do the real work
        self.AddSelector(sizer)

        # give a chance to add some command buttons
        self.AddCommandButtons(sizer)
        
        # add the OK and cancel buttons
        hBox = wxBoxSizer(wxHORIZONTAL)
        okButton = wxButton(self, wxID_OK, " OK ")
        okButton.SetDefault()
        hBox.Add(okButton, 0, wxALIGN_CENTER|wxALL, 5)

        cancelButton = wxButton(self, wxID_CANCEL, " Cancel ")
        hBox.Add(cancelButton, 0, wxALIGN_CENTER|wxALL, 5)

        sizer.AddSizer(hBox, 0, wxALIGN_CENTER_VERTICAL|wxALIGN_RIGHT|wxALL, 5)
        self.SetSizer(sizer)
        self.SetAutoLayout(true)
        sizer.Fit(self)

    # the default handler just echos back the passed-in caption
    def GetCaption(self, caption):
        return caption
    
    # there's no selection widgets in the base class
    def AddSelector(self, sizer):
        pass
    
    # use the default font in the base class
    def GetCaptionFont(self):
        return None

    # no command buttons in the base class
    def AddCommandButtons(self, sizer):
        pass
   
    # here's a utility routine to return a list of all the editable attributes of Contact,
    # used by a number of the dialogs
    # FIXME: this should be in the model stuff, and the exceptions should be a property of the template,
    # instead of the comparisons here
    def GetAttributeList(self):
        # attributeList is the list of attribute url's
        # attributeChoices is the list of attribute display names
        attributeData = self.viewer.contactMetaData.GetAttributeDictionary()
        attributeList = []
        self.contactAttributeKeys = []
        self.contactAttributeMap = {}
        
        for template in attributeData.GetAllAttributeTemplates():
            attributeURL = template.GetURL()
            if ((attributeURL != chandler.contactType) and
                (attributeURL != chandler.contactName) and
                (attributeURL != chandler.contactMethod) and
                (attributeURL != chandler.photoURL) and
                (attributeURL != chandler.group) and
                (attributeURL != chandler.headerAttribute) and
                (attributeURL != chandler.bodyAttribute)):     
                
                displayName = template.GetDisplayName()
                attributeList.append(displayName)
                self.contactAttributeKeys.append(attributeURL)
                self.contactAttributeMap[displayName] = attributeURL
                
        return attributeList
    
class ContactChoiceDialog(ContactsDialog):
    def __init__(self, parent, title, label, selectorLabel, choices, lastChoiceType):
        self.choices = choices
        self.selectorLabel = selectorLabel
        self.lastChoiceType = lastChoiceType
        ContactsDialog.__init__(self, parent, title, label)

    def AddSelector(self, sizer):
        # add the type selector       
        hBox = wxBoxSizer(wxHORIZONTAL)
        label = wxStaticText(self, -1, self.selectorLabel)
        hBox.Add(label, 0, wxALIGN_CENTER|wxALL, 5)

        self.typeSelector = wxChoice(self, -1, choices=self.choices)
        if self.lastChoiceType == None:
            self.lastChoiceType = self.choices[0]
        self.typeSelector.SetStringSelection(self.lastChoiceType)
        EVT_CHOICE(self.typeSelector, -1, self.ChoiceSelected)

        hBox.Add(self.typeSelector, 0, wxALIGN_CENTER|wxALL, 5)
        sizer.AddSizer(hBox, 0, wxGROW|wxALIGN_CENTER_VERTICAL|wxALL, 5)
       
    # FIXME: soon, we'll use this to set up an image
    def ChoiceSelected(self, event):
        pass

    # return the selection result
    def GetSelection(self):
        index = self.typeSelector.GetSelection()
        selectedLabel = self.typeSelector.GetString(index)
        return selectedLabel       

class ContactCheckboxDialog(ContactsDialog):
    def __init__(self, parent, title, label, choices, selectionState):
        self.choices = choices        
        self.selectionState = selectionState
        ContactsDialog.__init__(self, parent, title, label)

    # add two checkListBoxes, one for the header and one for the body
    # and set their initial state from the passed in array
    # FIXME: we should probably specify most of this in the .xrc file
    def AddSelector(self, sizer):
       self.headerListBox = wxCheckListBox(self, -1, wxDefaultPosition, wxDefaultSize, self.choices)
       self.bodyListBox = wxCheckListBox(self, -1, wxDefaultPosition, wxDefaultSize, self.choices)
       
       headerSelectionState = self.selectionState[0]
       for index in range(len(self.choices)):
           self.headerListBox.Check(index, headerSelectionState[index])
       
       bodySelectionState = self.selectionState[1]
       for index in range(len(self.choices)):
           self.bodyListBox.Check(index, bodySelectionState[index])
       
       hBox = wxBoxSizer(wxHORIZONTAL)
       
       # add the header checkboxes
       vBox = wxBoxSizer(wxVERTICAL)
       labelWidget = wxStaticText(self, -1, _("Header Attributes"))
       
       vBox.Add(labelWidget, 0, wxALIGN_CENTER)
       vBox.Add(self.headerListBox, 1, wxEXPAND | wxALL, 4)
       hBox.Add(vBox, 1, wxEXPAND)
       
       # add some padding in the middle
       hBox.Add(12, -1)
       
       # add the right side checkboxes
       vBox = wxBoxSizer(wxVERTICAL)
       labelWidget = wxStaticText(self, -1, _("Other Attributes"))
        
       vBox.Add(labelWidget, 0, wxALIGN_CENTER)
       vBox.Add(self.bodyListBox, 1, wxEXPAND | wxALL, 4)
       hBox.Add(vBox, 1, wxEXPAND)
       
       sizer.Add(hBox, 1, wxEXPAND)
 
    # use a bolder font for the caption
    def GetCaptionFont(self):
        return wxFont(10, wxSWISS, wxNORMAL, wxBOLD, false, "Arial")

    # return a list of the selected attributes
    def GetSelection(self):
        selectedAttributes = []
        
        for index in range(len(self.choices)):
            if self.listBox.IsChecked(index):
                selectedAttributes.append(self.choices[index])
        return selectedAttributes
  
    # return a list of boolean, indicating the enable state of each attribute
    def GetSelectionState(self):
        headerSelectionResult = []
        bodySelectionResult = []
        for index in range(len(self.choices)):
            headerSelectionResult.append(self.headerListBox.IsChecked(index))
            bodySelectionResult.append(self.bodyListBox.IsChecked(index))
            
        return (headerSelectionResult, bodySelectionResult)
    
class TemplateDialog(ContactsDialog):
    def __init__(self, parent, title, label, viewer, addressList):
        self.addressList = addressList
        self.viewer = viewer
        
        self.templateSelectIndex = -1
        self.templateList = []
        self.contactMethodList = []
        self.contactAttributeKeys = []
        
        ContactsDialog.__init__(self, parent, title, label)

    # construct the guts of the template editor by asking the contactsDictionary
    # for the list of templates and their attributes
    # FIXME: we should probably specify most of this in the .xrc file
    def AddSelector(self, sizer):
        # get the list of templates
        self.templateList = self.viewer.contactMetaData.GetTemplateNames()
        self.templateList.sort()

        hBox = wxBoxSizer(wxHORIZONTAL)
        
        # set up the template list box
        vBox = wxBoxSizer(wxVERTICAL)
        labelWidget = wxStaticText(self, -1, _("Templates"))
        self.templatesListBox = wxListBox(self, self.eventID, wxDefaultPosition, wxDefaultSize, self.templateList, wxLB_SINGLE)
        EVT_LISTBOX(self, self.eventID, self.TemplateSelected)
        self.eventID += 1
        
        vBox.Add(labelWidget, 0, wxALIGN_CENTER)
        vBox.Add(self.templatesListBox, 1, wxEXPAND | wxALL, 4)
        hBox.Add(vBox, 1, wxEXPAND)
        hBox.Add(2, -1)
        
        # set up the contact methods check box list
        self.contactMethodList = self.addressList.locationProperties.keys()
        self.contactMethodList.sort()
        
        vBox = wxBoxSizer(wxVERTICAL)
        labelWidget = wxStaticText(self, -1, _("Contact Methods"))
        self.methodsListBox = wxCheckListBox(self, -1, wxDefaultPosition, wxDefaultSize, self.contactMethodList)
      
        vBox.Add(labelWidget, 0, wxALIGN_CENTER)
        vBox.Add(self.methodsListBox, 1, wxEXPAND | wxALL, 4)
        hBox.Add(vBox, 1, wxEXPAND)
        
        attributeList = self.GetAttributeList()
        
        # set up the header attributes check box list
        vBox = wxBoxSizer(wxVERTICAL)
        labelWidget = wxStaticText(self, -1, _("Header Attributes"))
        self.headerListBox = wxCheckListBox(self, -1, wxDefaultPosition, wxDefaultSize, attributeList)
      
        vBox.Add(labelWidget, 0, wxALIGN_CENTER)
        vBox.Add(self.headerListBox, 1, wxEXPAND | wxALL, 4)
        hBox.Add(vBox, 1, wxEXPAND)
       
        # set up the body attributes check box list
        vBox = wxBoxSizer(wxVERTICAL)
        labelWidget = wxStaticText(self, -1, _("Other Attributes"))
        self.bodyListBox = wxCheckListBox(self, -1, wxDefaultPosition, wxDefaultSize, attributeList)
      
        vBox.Add(labelWidget, 0, wxALIGN_CENTER)
        vBox.Add(self.bodyListBox, 1, wxEXPAND | wxALL, 4)
        hBox.Add(vBox, 1, wxEXPAND)
        
        sizer.Add(hBox, 1, wxEXPAND)
      
        # check the boxes as appropriate
        self.SetSelectIndex(0)
    
    # use a bolder font for the caption
    def GetCaptionFont(self):
        return wxFont(12, wxSWISS, wxNORMAL, wxBOLD, false, "Arial")

    # add command buttons for new and remove
    
    def AddCommandButtons(self, sizer):
        hBox = wxBoxSizer(wxHORIZONTAL)
        createButton = wxButton(self, self.eventID, " Create New Template ")
        EVT_BUTTON(self, self.eventID, self.CreateTemplate)
        hBox.Add(createButton, 0, wxALIGN_CENTER|wxALL, 5)
        self.eventID += 1
        
        removeButton = wxButton(self, self.eventID, " Delete Template ")
        EVT_BUTTON(self, self.eventID, self.DeleteSelectedTemplate)
        hBox.Add(removeButton, 0, wxALIGN_CENTER|wxALL, 5)
        self.eventID += 1

        sizer.AddSizer(hBox, 0, wxALIGN_CENTER_VERTICAL|wxALIGN_LEFT|wxALL, 5)
       
    # set up the checkboxes with information from the selected template
    def SetSelectIndex(self, newIndex):
        if self.templateSelectIndex == newIndex:
            return
       
        if self.templateSelectIndex != -1:
            self.UpdateTemplate()
            
        self.templateSelectIndex = newIndex
        
        # update the three sets of checkboxes with information from the template
        templateName = self.templateList[self.templateSelectIndex]
        template = self.viewer.contactMetaData.GetTemplate(templateName)
       
        # set up the contact methods
        for index in range(len(self.contactMethodList)):
            contactMethod = self.contactMethodList[index]
            self.methodsListBox.Check(index, template.HasContactMethod(contactMethod))
 
        # set up the header attributes
        for index in range(len(self.contactAttributeKeys)):
            attributeKey = self.contactAttributeKeys[index]
            self.headerListBox.Check(index, template.HasAttribute(attributeKey, 'header'))
 
        # set up the body attributes
        for index in range(len(self.contactAttributeKeys)):
            attributeKey = self.contactAttributeKeys[index]
            self.bodyListBox.Check(index, template.HasAttribute(attributeKey, 'body'))
 
    # do the reverse: update the selected template with the information in the checkboxes
    def UpdateTemplate(self):
        # update the template with the state of three sets of checkboxes
        templateName = self.templateList[self.templateSelectIndex]
        template = self.viewer.contactMetaData.GetTemplate(templateName)
       
        # update the contact methods
        for index in range(len(self.contactMethodList)):
            contactMethod = self.contactMethodList[index]
            isChecked = self.methodsListBox.IsChecked(index)
            if isChecked:
                template.AddContactMethod(contactMethod)
            else:
                template.RemoveContactMethod(contactMethod)
                
        # update the header attributes
        for index in range(len(self.contactAttributeKeys)):
            attributeKey = self.contactAttributeKeys[index]
            isChecked = self.headerListBox.IsChecked(index)
            
            if isChecked:
                template.AddAttribute(attributeKey, 'header')
            else:
                template.RemoveAttribute(attributeKey, 'header')

        # update the header attributes
        for index in range(len(self.contactAttributeKeys)):
            attributeKey = self.contactAttributeKeys[index]
            isChecked = self.bodyListBox.IsChecked(index)
            
            if isChecked:
                template.AddAttribute(attributeKey, 'body')
            else:
                template.RemoveAttribute(attributeKey, 'body')
   
    def TemplateSelected(self, event):
        newSelectIndex = event.GetSelection()
        self.SetSelectIndex(newSelectIndex)
    
   # handler to create and delete templates
    def CreateTemplate(self, event):
        caption = 'Enter the name of the new template:'
        dialog = wxTextEntryDialog(app.wxMainFrame, caption)
        if dialog.ShowModal() == wxID_OK:
            newTemplateName = dialog.GetValue()
            newTemplate = ContactTemplate(newTemplateName)
            self.viewer.contactMetaData.AddContactTemplate(newTemplateName, newTemplate)

            self.templateList.append(newTemplateName)
            self.templateList.sort()
            self.templatesListBox.Set(self.templateList)
            
            index = self.templatesListBox.FindString(newTemplateName)
            self.templatesListBox.SetSelection(index, true)
            self.SetSelectIndex(index)
            
    def DeleteSelectedTemplate(self, event):
        templateName = self.templateList[self.templateSelectIndex]
        del self.templateList[self.templateSelectIndex]
        self.viewer.contactMetaData.RemoveContactTemplate(templateName)
        
        self.templatesListBox.Set(self.templateList)
  
        newIndex = self.templateSelectIndex
        if newIndex >= self.templatesListBox.GetCount():
            newIndex -= 1

        self.templatesListBox.SetSelection(newIndex, true)
        self.templateSelectIndex = -1
        self.SetSelectIndex(newIndex)

# here's the edit view dialog, which lets the user create
# new views and edit existing ones
class EditContactViewDialog(ContactsDialog):
    def __init__(self, parent, title, label, viewer, viewInfo):
        self.viewer = viewer
        self.viewInfo = viewInfo
        ContactsDialog.__init__(self, parent, title, label)

    # add a form to acquire the view title, description, permissions and filter
    # for the view
    def AddSelector(self, sizer):
        gridSizer = wxFlexGridSizer(cols=2, vgap=4, hgap=4)
        gridSizer.AddGrowableCol(1)

        # add the title field
        label = wxStaticText(self, -1, _("View Name:"))
        self.titleEntry = wxTextCtrl(self, -1, style=wxTE_PROCESS_TAB | wxTE_PROCESS_ENTER)
        gridSizer.Add(label, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)
        gridSizer.Add(self.titleEntry, flag=wxEXPAND)

        # add the description field
        label = wxStaticText(self, -1, _("View Description:"))
        self.descriptionEntry = wxTextCtrl(self, -1, style=wxTE_PROCESS_TAB | wxTE_PROCESS_ENTER)     
        gridSizer.Add(label, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)
        gridSizer.Add(self.descriptionEntry, flag=wxEXPAND)

        # add the sharing policy
        label = wxStaticText(self, -1, _("Sharing Policy:"))
        gridSizer.Add(label, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)

        # get the sharing policies.
        # FIXME: For now, there's just public and private, expressed
        # string constants,  but soon sharing policies will be objects themselves
        choices = ['private', 'public']
        self.sharingPolicyWidget = wxChoice(self, -1, choices=choices)
        self.sharingPolicyWidget.SetStringSelection(choices[0])
        gridSizer.Add(self.sharingPolicyWidget)

        # now, generate controls for the filter conditions.
        # there's a choice control for the attribute and one for the value.
        # FIXME: this is still mostly scaffolding - we need to get the real attributes
        self.conditionContainer = wxBoxSizer(wxHORIZONTAL)
        
        label = wxStaticText(self, -1, _("Condition:"))
        gridSizer.Add(label, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)
      
        attributeChoices = self.GetAttributeList()
        attributeChoices = [_('No Condition'), _('Member of')] + attributeChoices
        self.attributeChoiceWidget = wxChoice(self, -1, choices=attributeChoices)
        self.attributeChoiceWidget.SetStringSelection(_('Member of'))
        self.conditionContainer.Add(self.attributeChoiceWidget, 0, wxALL, 4)
        EVT_CHOICE(self.attributeChoiceWidget, -1, self.AttributeChanged)

        self.valueChoiceWidget = None
        self.SetUpAttributeChoices()
        
        # set up defaults if necessary
        if self.viewInfo != None:
            self.titleEntry.SetValue(self.viewInfo.GetTitle())
            self.descriptionEntry.SetValue(self.viewInfo.GetDescription())
            self.sharingPolicyWidget.SetStringSelection(self.viewInfo.GetSharingPolicy())
            
        gridSizer.Add(self.conditionContainer, flag=wxEXPAND)        
        sizer.Add(gridSizer, 1, wxEXPAND | wxALL, 12)
 
    # set up the attribute choice control, whose value depends on the selected attribute
    def SetUpAttributeChoices(self):
        attributeIndex = self.attributeChoiceWidget.GetSelection()
        attributeValue = self.attributeChoiceWidget.GetString(attributeIndex)
         
        if self.valueChoiceWidget != None:
            self.valueChoiceWidget.Destroy()
            self.valueChoiceWidget = None
            
        if attributeValue == _('No Condition'):
            return

        if attributeValue == _('Member of'):
            choiceList = self.viewer.contactMetaData.GetGroupsList()
        else:
            attribute = self.contactAttributeMap[attributeValue]
            dictionary = self.viewer.GetAttributeDictionary()
            choiceList = dictionary.GetAttributeChoices(attribute)
                    
        self.valueChoiceWidget = wxChoice(self, -1, choices=choiceList)
        if len(choiceList) > 0:
            self.valueChoiceWidget.SetStringSelection(choiceList[0])
        self.conditionContainer.Add(self.valueChoiceWidget, 0, wxALL, 4)

        self.Fit()
        self.conditionContainer.Layout()
        
    # the following is invoked when the attribute choice box is changed
    def AttributeChanged(self, event):
        self.SetUpAttributeChoices()
        
    # return the selection result
    def GetNewViewInfo(self):
        label = self.titleEntry.GetValue()
        description = self.descriptionEntry.GetValue()
        
        sharingIndex = self.sharingPolicyWidget.GetSelection()
        sharingPolicy = self.sharingPolicyWidget.GetString(sharingIndex)
        
        attributeIndex = self.attributeChoiceWidget.GetSelection()
        attributeValue = self.attributeChoiceWidget.GetString(attributeIndex)
         
        valueIndex = self.valueChoiceWidget.GetSelection()
        value = self.valueChoiceWidget.GetString(valueIndex)
  
        # FIXME: this is a hack.  Soon, the user will be able to specify the operation, and
        # the right one will be presented as a default
        if attributeValue == _('Member of'):
            operation = 'hasgroup'
            attribute = None
        else:
            operation = 'contains'
            attribute = self.contactAttributeMap[attributeValue]
            
        condition = FilterCondition(attribute, operation, value, true)
        
        return (label, description, sharingPolicy, [condition])
    

           
