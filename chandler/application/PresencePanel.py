#!bin/env python

"""
The PresencePanel shows the presence state of other Chandler Client
and provides a UI for subscribing and unsubscribing to presence
as well as sending instant messages.
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"

import os
from wxPython.wx import *
from application.ChandlerJabber import *
import application.Application

class PresenceWindow(wxFrame):
    def __init__(self, title, jabberClient):
        self.jabberClient = jabberClient
        
        wxFrame.__init__(self, None, -1, title, size=(200, 120), style=wxSTAY_ON_TOP | wxDEFAULT_FRAME_STYLE)
        sizer = wxBoxSizer(wxVERTICAL)
        
        # base ID for events
        self.eventID = 100

        # add the presence panel
        self.presencePanel = PresencePanel(self, self.jabberClient)
        sizer.Add(self.presencePanel, 1, wxEXPAND)
       
        self.SetSizer(sizer)
        self.SetAutoLayout(true)
        #sizer.Fit(self)

    def PresenceChanged(self, who):
        self.presencePanel.PresenceChanged(who)
        
class PresencePanel(wxScrolledWindow):
    def __init__(self, parent, jabberClient):
        self.jabberClient = jabberClient
        self.openState = {}
        
        wxScrolledWindow.__init__(self, parent)

        self.nameFont = wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
        
        self.rightTriangle = self.LoadBitmap('triangle_right.gif')
        self.downTriangle = self.LoadBitmap('triangle_down.gif')
        self.presentBitmap = self.LoadBitmap('present.gif')
        self.absentBitmap = self.LoadBitmap('absent.gif')

        self.LayoutWidgets()

    # routines to manipulate the open state associated with an id
    
    # return the open state of the passed in jabberID
    def IsOpen(self, jabberID):
        key = str(jabberID)
        if self.openState.has_key(key):
            return self.openState[key]
        return false
    
    # set the open state associated with an id
    def SetOpen(self, jabberID, openFlag):
        key = str(jabberID)
        self.openState[key] = openFlag
        
    # toggle the open state associated with an id
    def ToggleOpen(self, jabberID):
        key = str(jabberID)
        self.SetOpen(key, not self.IsOpen(key))
        
    # return the present state of the passed in jabberID
    def IsPresent(self, jabberID):
        return self.jabberClient.IsPresent(jabberID)
    
    # render the presence panel
    def RenderWidgets(self):
        self.DestroyChildren()
        self.LayoutWidgets()

    # get the displayname associated with the passed in jabberID
    # for now, it's just the jabberID itself, but soon we'll look
    # it up in Contacts
    def GetDisplayName(self, jabberID):
        return str(jabberID)
    
    # render a presence entry for the passed-in ID
    def RenderPresenceEntry(self, jabberID):
        entryContainer = wxBoxSizer(wxHORIZONTAL)

        # add the disclosure triangle 
        if self.IsOpen(jabberID):
            image = self.downTriangle
        else:
            image = self.rightTriangle   
        
        triangleWidget = wxStaticBitmap(self, -1, image)
        handler = OpenHandler(self, jabberID)
        EVT_LEFT_DOWN(triangleWidget, handler.ClickedTriangle)
        entryContainer.Add(triangleWidget, 0, wxALIGN_CENTER_VERTICAL | wxWEST, 2)

        # add the presence state image
        if self.IsPresent(jabberID):
            image = self.presentBitmap
            textColor = wxBLACK
        else:
            image = self.absentBitmap
            textColor = wxColor(31, 31, 31)
            
        presenceWidget = wxStaticBitmap(self, -1, image)
        entryContainer.Add(presenceWidget, 0, wxALIGN_CENTER_VERTICAL | wxWEST | wxEAST, 2)
            
        # get the display name and render it
        displayName = self.GetDisplayName(jabberID)
        nameWidget = wxStaticText(self, -1, displayName)
        nameWidget.SetFont(self.nameFont)
        nameWidget.SetForegroundColour(textColor)
        
        entryContainer.Add(nameWidget, 0, wxEXPAND)
                
        return entryContainer
        
    # loop through the buddy list, rendering the presence state
    # of each entry
    def LayoutWidgets(self):
        container = wxBoxSizer(wxVERTICAL)        
        if not self.jabberClient.IsConnected():
            message = _("You are not logged in.  Click here \nto fill out your account information.")
            textWidget = wxStaticText(self, -1, message)
            EVT_LEFT_DOWN(textWidget, self.ShowPreferencesDialog)
            container.Add(textWidget, 0, wxEXPAND | wxALIGN_CENTRE | wxALL, 12)
        else:
            buddyList = self.jabberClient.GetRosterIDs(false)
        
            for jabberID in buddyList:
                presenceEntry = self.RenderPresenceEntry(jabberID)
                container.Add(presenceEntry, 0, wxEXPAND)
                container.Add(-1, 4)
                
        self.SetSizer(container)           
        self.Layout()
        
        self.EnableScrolling(false, true)
        self.SetScrollRate(0, 20)

    # show the preferences dialog
    def ShowPreferencesDialog(self, event):
        app = application.Application.app
        app.OnPreferences(event)
        
    # rerender the presence panel when the presence state changes
    def PresenceChanged(self, who):
        self.RenderWidgets()
        
    # utility routine to load a bitmap from a GIF file
    def LoadBitmap(self, filename):
        app = application.Application.app
        path = app.chandlerDirectory + os.sep + 'application' + os.sep + 'images' + os.sep + filename
        image = wxImage(path, wxBITMAP_TYPE_GIF)
        bitmap = image.ConvertToBitmap()
        return bitmap

class OpenHandler:
    def __init__(self, presencePanel, jabberID):
        self.presencePanel = presencePanel
        self.jabberID = jabberID
        
    def ClickedTriangle(self, event):
        self.presencePanel.ToggleOpen(self.jabberID)
        self.presencePanel.RenderWidgets()
        
        