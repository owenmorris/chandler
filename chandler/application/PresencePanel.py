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

from wxPython.wx import *
from application.Application import app
from application.ChandlerJabber import *

class PresencePanel(wxScrolledWindow):
    def __init__(self, parent, jabberClient):
        self.jabberClient = jabberClient
         
        wxScrolledWindow.__init__(self, parent)

        self.nameFont = wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
        
        self.rightTriangle = self.LoadBitmap('triangle_right.gif')
        self.downTriangle = self.LoadBitmap('triangle_down.gif')
        self.presentBitmap = self.LoadBitmap('present.gif')
        self.absentBitmap = self.LoadBitmap('absent.gif')

        self.LayoutWidgets()

    # return the open state of the passed in jabberID
    def IsOpen(self, jabberID):
        return false

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
        return jabberID
    
    # render a presence entry for the passed-in ID
    def RenderPresenceEntry(jabberID):
        entryContainer = wxBoxSizer(wxHORIZONTAL)

        # add the disclosure triangle 
        if self.IsOpen(jabberID):
            image = self.downTriangle
        else:
            image = self.rightTriangle   
        
        triangleWidget = wxStaticBitmap(self, -1, image)
        handler = OpenHandler(self, jabberID)
        EVT_LEFT_DOWN(triangleWidget, OpenHandler.ClickedTriangle)
        entryContainer.Add(triangleWidget, 0, wxALIGN_CENTER_VERTICAL | wxWEST, 2)

        # add the presence state image
        if self.IsPresent(jabberID):
            image = self.presentBitmap
        else:
            image = self.absentBitmap
        presenceWidget = wxStaticBitmap(self, -1, image)
        entryContainer.Add(presenceWidget, 0, wxALIGN_CENTER_VERTICAL | wxWEST, 2)
            
        # get the display name and render it
        displayName = self.GetDisplayName(self, jabberID)
        nameWidget = wxStaticText(self, -1, displayName)
        nameWidget.SetFont(self.nameFont)
        entryContainer.Add(self.nameWidget, 0, wxEXPAND)
                
        return entryContainer
        
    # loop through the buddy list, rendering the presence state
    # of each entry
    def LayoutWidgets(self):
        container = wxBoxSizer(wxVERTICAL)        
        buddyList = self.jabberClient.GetRosterIDs()
                
        for jabberID in buddyList:
            presenceEntry = self.RenderPresenceEntry(presenceDictionary, jabberID)
            container.Add(presenceEntry, 0)
                                        
        self.SetSizerAndFit(container)           
        self.EnableScrolling(false, true)
        self.SetScrollRate(0, 20)

    # rerender the presence panel when the presence state changes
    def PresenceChanged(self, who):
        self.RenderWidgets()

    # utility routine to load a bitmap from a GIF file
    def LoadBitmap(self, filename):
        return None
        