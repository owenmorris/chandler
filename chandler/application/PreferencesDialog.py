
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"

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
    def __init__(self, preferencesDictionary):
        self.prefDictionary = preferencesDictionary
        self.currentSection = []
        self.sectionName = ''
        
    def startElement(self, name, attributes):		                
        if name == 'Preferences':
            self.sectionName = attributes['section']
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
            self.currentSection = []

# package-level routine to load preferences metadata from an xml file
# it's not a method of PreferencesDialog so parcels can easily call it
# to load their parcel preference metadata
def LoadPreferencesMetadata(filePath):
    parser = xml.sax.make_parser()
    metaDataDictionary = {}
    handler = PreferenceMetadataHandler(metaDataDictionary)
                
    parser.setContentHandler(handler)
    parser.parse(filePath)

    return metaDataDictionary
        
class PreferencesDialog(wxDialog):
    def __init__(self, parent, title, preferencesData):    
        wxDialog.__init__(self, parent, -1, title)
        
        self.preferencesData = preferencesData
        metadataPath = "application" + os.sep + "preferencesMetadata.xml"
        self.preferencesMetadata = LoadPreferencesMetadata(metadataPath)
        
        self.AddPackagePreferences()
        
        # base up baseID for events
        self.eventID = 100
        
        self.container = wxBoxSizer(wxVERTICAL)
        self.RenderWidgets()
        self.AddButtons()

        self.SetSizerAndFit(self.container)
        self.SetAutoLayout(true)

    # loop through the parcel list, adding preference metadata from each package
    def AddPackagePreferences(self):
        pass

    # allocate the section selector widget, and set up the first section
    def RenderWidgets(self):
        hBox = wxBoxSizer(wxHORIZONTAL)

        # get the section list
        sectionList = self.preferencesMetadata.keys()
        
        # add the section list box and wire it up
        self.listbox = wxListBox(self, self.eventID, wxDefaultPosition, wxSize(100, 120),
                       sectionList, wxLB_SINGLE)
        hBox.Add(self.listbox, 0, wxNORTH | wxWEST | wxSOUTH, 8)
        self.eventID += 1

        # add a small gap between the section list and the form
        hBox.Add(4, -1)
                
        # add the form container
        self.formContainer = wxBoxSizer(wxVERTICAL)
        
        # render the form elements
        self.RenderSelectedForm() 
        hBox.Add(self.formContainer, 1, wxEXPAND | wxNORTH | wxEAST | wxSOUTH, 8)        
        
        self.container.Add(hBox, 1, wxEXPAND)
    
    # render the form selected by the section listbox
    def RenderSelectedForm(self):
        section = self.listbox.GetStringSelection()
        formElements = self.preferencesMetadata[section]
        
        # allocate a gridSizer to contain the form elements
        gridSizer = wxFlexGridSizer(cols=2, vgap=4, hgap=4)
        gridSizer.AddGrowableCol(1)
        self.fieldList = []
        
        # for this first implementation, we ignore the type
        for element in formElements:
            label = wxStaticText(self, -1, element.label + ':')

            field = wxTextCtrl(self, -1)
            self.fieldList.append((element.key, field))
            field.SetSize(wxSize(180, -1))
            
            gridSizer.Add(label, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)
            gridSizer.Add(field, flag=wxEXPAND)

        self.formContainer.Add(gridSizer, 1, wxEXPAND)
    
        self.RestorePreferences()
        
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
            key, field = fieldItem
            value = self.preferencesData.GetPreferenceValue(key)
            if value == None:
                value = ''
            field.SetValue(value)
            
    # save the values in the fields to the persistent object
    def SavePreferences(self):
        for fieldItem in self.fieldList:
            key, field = fieldItem
            value = field.GetValue()
            self.preferencesData.SetPreferenceValue(key, value)
            
       
    
