
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""
The PreferencesDialog package contains classes that implement the preferences dialog
"""

import os
import xml.sax.handler
from wxPython.wx import *

class PreferenceItem:
    """
       data for a single preferences item
    """
    def __init__(self, label, key, type, description):
        self.label = label
        self.key = key
        self.type = type
        self.description = description

class PreferenceMetadataHandler(xml.sax.handler.ContentHandler):
    """
        xml sax handler to parse the metadata xml file
    """
    def __init__(self, preferencesDictionary, orderDictionary):
        self.prefDictionary = preferencesDictionary
        self.currentSection = []
        self.sectionName = ''
        self.orderDictionary = orderDictionary
        
    def startElement(self, name, attributes):		                
        if name == 'Preferences':
            self.sectionName = attributes['section']
            self.order = attributes['order']
            self.currentSection = []
        elif name == 'PreferenceItem':
            key = attributes['key']
            label = attributes['label']
            type = attributes['type']
            
            if attributes.has_key('description'):
                description = attributes['description']
            else:
                description = None
            
            # allocate a new PreferenceItem, and add it to the section list
            item = PreferenceItem(label, key, type, description)
            self.currentSection.append(item)
            
    def endElement(self, name):					
        if name == 'Preferences':
            self.prefDictionary[self.sectionName] = self.currentSection
            if self.orderDictionary != None:
                self.orderDictionary[self.sectionName] = self.order
            self.currentSection = []

# package-level routine to load preferences metadata from an xml file
# it's not a method of PreferencesDialog so parcels can easily call it
# to load their parcel preference metadata
def LoadPreferencesMetadata(filePath, orderDictionary):
    parser = xml.sax.make_parser()
    metaDataDictionary = {}
    handler = PreferenceMetadataHandler(metaDataDictionary, orderDictionary)
                
    parser.setContentHandler(handler)
    parser.parse(filePath)

    return metaDataDictionary
        
class PreferencesDialog(wxDialog):
    def __init__(self, parent, title, preferencesData, default=None):    
        wxDialog.__init__(self, parent, -1, title)
        
        self.preferencesData = preferencesData
        self.defaultSection = default
            
        metadataPath = "application" + os.sep + "preferencesMetadata.xml"
        self.sectionOrder = {}
        
        self.preferencesMetadata = LoadPreferencesMetadata(metadataPath, self.sectionOrder)
        
        self.AddPackagePreferences()
        
        # base up baseID for events
        self.eventID = 100
        
        self.container = wxBoxSizer(wxVERTICAL)
        self.RenderWidgets()
        self.AddButtons()
        
        self.SetSizerAndFit(self.container)
        self.SetAutoLayout(true)
        
        EVT_ACTIVATE(self, self.OnActivate)
    
    # select the first field when activated
    def OnActivate(self, event):
        self.SelectFirstField()
        
    # sort function to sort sections by their order parameter
    def SortBySectionOrder(self, firstSection, secondSection):
        return cmp(self.sectionOrder[firstSection], self.sectionOrder[secondSection])

    # loop through the parcel list, adding preference metadata from each package
    def AddPackagePreferences(self):
        pass

    # allocate the section selector widget, and set up the first section
    def RenderWidgets(self):
        hBox = wxBoxSizer(wxHORIZONTAL)

        # get the section list
        sectionList = self.preferencesMetadata.keys()
        sectionList.sort(self.SortBySectionOrder)
        
        # add the section list box and wire it up
        self.listbox = wxListBox(self, self.eventID, wxDefaultPosition, wxSize(100, 120),
                       sectionList, wxLB_SINGLE)
        
        EVT_LISTBOX(self, self.eventID, self.SectionChanged)        
        self.eventID += 1
        hBox.Add(self.listbox, 0, wxNORTH | wxWEST | wxSOUTH, 8)  

        # set up the default section
        self.SelectSection(self.defaultSection)
        
        # add a small gap between the section list and the form
        hBox.Add(4, -1)
                
        # add the form container
        self.formContainer = wxScrolledWindow(self, -1)
        
        # render the form elements
        self.RenderSelectedForm() 
        hBox.Add(self.formContainer, 1, wxEXPAND | wxNORTH | wxEAST | wxSOUTH, 8)        
        
        self.container.Add(hBox, 1, wxEXPAND)

        self.formContainer.EnableScrolling(false, true)
        
    # select the passed in section
    def SelectSection(self, sectionName):
        if sectionName == None:
            index = 0
        else:
            try:
                sectionList = self.preferencesMetadata.keys()
                sectionList.sort(self.SortBySectionOrder)
                index = sectionList.index(sectionName)
            except ValueError:
                index = 0
        self.listbox.SetSelection(index)

    # render the form selected by the section listbox
    def RenderSelectedForm(self):
        section = self.listbox.GetStringSelection()
        formElements = self.preferencesMetadata[section]
        
        # allocate a gridSizer to contain the form elements
        self.ResetForm()
        
        # for this first implementation, we ignore the type
        for element in formElements:
            labelValue = element.label + ':'
            if element.type == 'password':
                widget = wxTextCtrl(self.formContainer, -1, style=wxTE_PASSWORD)
            elif element.type == 'boolean':
                labelValue = '        '
                widget = wxCheckBox(self.formContainer, -1,   '' + element.label, wxDefaultPosition, wxDefaultSize, wxNO_BORDER)
            else:
                widget = wxTextCtrl(self.formContainer, -1, style=wxTE_PROCESS_TAB | wxTE_PROCESS_ENTER)
                index = len(self.fieldList)
                handler = TextFieldHandler(self, index)
                EVT_CHAR(widget, handler.OnKeystroke)

            label = wxStaticText(self.formContainer, -1, labelValue)

            self.fieldList.append((element.key, widget, element.type))
            if element.type != 'boolean':
                widget.SetSize(wxSize(180, -1))
            
            self.gridSizer.Add(label, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)
            self.gridSizer.Add(widget, flag=wxEXPAND)

        self.formContainer.SetSizerAndFit(self.gridSizer)
        self.RestorePreferences()
        
    def ResetForm(self):
        self.gridSizer = wxFlexGridSizer(cols=2, vgap=4, hgap=4)
        self.gridSizer.AddGrowableCol(1)
        self.fieldList = []
    
    def ClearForm(self):
        self.formContainer.DestroyChildren()
        self.ResetForm()

    # SelectFirstField is called after rendering the form to set the focus to the first field in the list
    def SelectFirstField(self):
        for entry in self.fieldList:
            key, field, type = entry
            if type != 'boolean':
                field.SetFocus()
                field.SelectAll()
                return
        
    # add the command buttons
    def AddButtons(self):
        hBox = wxBoxSizer(wxHORIZONTAL)
        okButton = wxButton(self, wxID_OK, " OK ")
        okButton.SetDefault()
        hBox.Add(okButton, 0, wxALIGN_CENTER|wxALL, 5)

        cancelButton = wxButton(self, wxID_CANCEL, " Cancel ")
        hBox.Add(cancelButton, 0, wxALIGN_CENTER|wxALL, 5)

        self.container.Add(hBox, 0, wxALIGN_CENTER_VERTICAL|wxALIGN_RIGHT|wxALL, 5)

    # set up the fields with the currently saved values
    def RestorePreferences(self):
        for fieldItem in self.fieldList:
            key, field, type = fieldItem
            value = self.preferencesData.GetPreferenceValue(key)

            if type == 'boolean':
                value = value != None and value != 0
            if value == None:
                value = ''
            field.SetValue(value)
            
    # save the values in the fields to the persistent object
    def SavePreferences(self):
        for fieldItem in self.fieldList:
            key, field, type = fieldItem
            value = field.GetValue()
            self.preferencesData.SetPreferenceValue(key, value)
            
    # handle list box section changed
    def SectionChanged(self, event):
        self.SavePreferences()
        self.SelectSection(event.GetString())
        self.ClearForm()
        self.RenderSelectedForm()
        self.SelectFirstField()
        self.Layout()

# here's a utility class to handle tabbing between fields
class TextFieldHandler:
    def __init__(self, dialog, index):
        self.dialog = dialog
        self.index = index
        
    def OnKeystroke(self, event):
        keycode = event.GetKeyCode()
        # handle return and tab by bumping to the next field
        if keycode == 13 or keycode == 9:
           newIndex = self.index + 1
           if newIndex >= len(self.dialog.fieldList):
               newIndex = 0
           key, field, type = self.dialog.fieldList[newIndex]
           field.SetFocus()
           field.SelectAll()
       
        else:
            event.Skip()

       
    
