#!bin/env python

"""
 Dialog classes for the Roster Parcel
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from application.Application import app

from OSAF.contacts.ContactsModel import *

class RosterSubscribeDialog(wxDialog):
    def __init__(self, parent, title):
        wxDialog.__init__(self, parent, -1, title)
        sizer = wxBoxSizer(wxVERTICAL)
        
        # base ID for events
        self.eventID = 100
        
        # add an instructive label
        caption = _("Enter the user's name and Jabber ID to add them\nto your roster.")
        captionWidget = wxStaticText(self, -1, caption)
            
        sizer.Add(captionWidget, 0, wxALIGN_CENTER|wxALL, 8)
       
        # add the widgets that do the real work
        self.AddNameFields(sizer)
        
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

    def AddNameFields(self, sizer):
        gridSizer = wxFlexGridSizer(cols=2, vgap=4, hgap=4)
        gridSizer.AddGrowableCol(1)

        label = wxStaticText(self, -1, _("Name:"))
        self.nameEntry = wxTextCtrl(self, -1, style=wxTE_PROCESS_TAB | wxTE_PROCESS_ENTER)     
        gridSizer.Add(label, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)
        gridSizer.Add(self.nameEntry, flag=wxEXPAND)

        label = wxStaticText(self, -1, _("Jabber ID:"))
        self.jabberEntry = wxTextCtrl(self, -1, style=wxTE_PROCESS_TAB | wxTE_PROCESS_ENTER)     
        gridSizer.Add(label, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)
        gridSizer.Add(self.jabberEntry, flag=wxEXPAND)

        sizer.Add(gridSizer, 1, wxEXPAND | wxALL, 12)
        
    def GetFieldValues(self):
        name = self.nameEntry.GetValue()
        jabberID = self.jabberEntry.GetValue()
        return (name, jabberID)
    
