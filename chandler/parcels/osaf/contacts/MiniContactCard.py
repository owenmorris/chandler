#!bin/env python

"""
 Minicard for representing a contact
"""
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002, 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import urllib

from wxPython.wx import *
from wxPython.lib.imagebrowser import *

from application.Application import app

class MiniContactCard(wxPanel):
    def __init__(self, parent, miniCardView, contact, contactView, cardSize, position, images):
        self.contact = contact
        self.miniCardView = miniCardView
        self.contactView = contactView
        self.cardSize = cardSize
        self.images = images

        self.selected = false
                
        wxPanel.__init__(self, parent, -1, style=wxBORDER)

        self.SetBackgroundColour(wxWHITE)
        self.SetSize(cardSize)
        self.Move(position)
        
        self.LayoutWidgets()
                
        EVT_LEFT_DOWN(self, self.OnLeftDown)
   
    def GetContact(self):
        return self.contact

    def SetContact(self, newContact):
        if self.contact != newContact:
            self.contact = newContact
            self.RenderWidgets()

    def RenderWidgets(self):
        self.DestroyChildren()
        self.LayoutWidgets()

    def ContactChanged(self):
        self.RenderWidgets()
                
    def LayoutSmallCard(self, container, displayName):
        self.AddTextWidget(container, displayName, self.miniCardView.nameFont, 2)

        addressList = self.contact.GetAddresses()
        for addressItem in addressList:
            addressValue = addressItem.GetFirstFormattedValue()
            if addressValue == None:
                continue
                
            textWidget = wxStaticText(self, -1, addressValue)
            textWidget.SetFont(self.miniCardView.itemFont)
            container.Add(textWidget, 0, wxEXPAND)
            EVT_LEFT_DOWN(textWidget, self.OnLeftDown)

    def LayoutMediumCard(self, container, displayName):
        self.AddTextWidget(container, displayName, self.miniCardView.nameFont, 2)        
        addressList = self.contact.GetAddresses()
        for addressItem in addressList:
            addressValue = addressItem.GetFirstFormattedValue()
            if addressValue == None:
                continue
                
            hBox = wxBoxSizer(wxHORIZONTAL)
            hBox.Add(4, -1)

            if addressItem.GetMethodType() == 'phone':
                addressInitial = addressItem.GetLocationAbbreviation() + ':'

                textWidget = wxStaticText(self, -1, addressInitial)
                textWidget.SetFont(self.miniCardView.labelFont)
                EVT_LEFT_DOWN(textWidget, self.OnLeftDown)
                hBox.Add(textWidget, 0, wxEXPAND)
                hBox.Add(4, -1)
                                
            textWidget = wxStaticText(self, -1, addressValue)
            textWidget.SetFont(self.miniCardView.itemFont)
            hBox.Add(textWidget, 0, wxEXPAND)

            container.Add(hBox, 0, wxEXPAND)
            EVT_LEFT_DOWN(textWidget, self.OnLeftDown)

    def LayoutLargeCard(self, container, displayName):
        photoURL = self.contact.GetPhotoURL()
        if photoURL != None:
            try:
                photoBitmap = self.images.LoadBitmapURL(photoURL, maxWidth=60, maxHeight=60)
            except:
                photoBitmap = None  
        else:
            photoBitmap = None

        if photoBitmap != None:            
            photoWidget = wxStaticBitmap(self, -1, photoBitmap)
            hBox = wxBoxSizer(wxHORIZONTAL)
            vBox = wxBoxSizer(wxVERTICAL)
            hBox.Add(photoWidget, 0, wxALL, 4)
            hBox.Add(vBox, 1, wxEXPAND)
            container.Add(hBox, 0, wxEXPAND)
            EVT_LEFT_DOWN(photoWidget, self.GetPhotoImage)
        else:
            vBox = container
        
        # add the name
        self.AddTextWidget(vBox, displayName, self.miniCardView.nameFont, 2)

        # add header attributes if any
        fieldList = self.contact.GetHeaderAttributes()
        for field in fieldList:
            fieldValue = self.contact.GetAttribute(field)
            self.AddTextWidget(vBox, fieldValue, self.miniCardView.itemFont, 2)

        # add addresses
        addressList = self.contact.GetAddresses()
        gridSizer = wxFlexGridSizer(cols=2, vgap=0, hgap=8)
        gridSizer.AddGrowableCol(1)
        for addressItem in addressList:
            addressDescription = addressItem.GetMethodDescription() + ':'      
            addressValue = addressItem.GetFirstFormattedValue()
            if addressValue == None:
                continue
            
            labelWidget = wxStaticText(self, -1, addressDescription)
            labelWidget.SetFont(self.miniCardView.labelFont)
            gridSizer.Add(labelWidget, flag=wxALIGN_RIGHT | wxALIGN_CENTER_VERTICAL)
            EVT_LEFT_DOWN(labelWidget, self.OnLeftDown)

            textWidget = wxStaticText(self, -1, addressValue)
            textWidget.SetFont(self.miniCardView.itemFont)
            gridSizer.Add(textWidget, flag=wxEXPAND)
            EVT_LEFT_DOWN(textWidget, self.OnLeftDown)

        container.Add(gridSizer, 1, wxEXPAND | wxALL, 4)
        
    def LayoutCardWithZoom(self, container, displayName, zoomIndex):
        if zoomIndex == 0:
            self.LayoutSmallCard(container, displayName)
        elif zoomIndex == 1:
            self.LayoutMediumCard(container, displayName)
        elif zoomIndex == 2:
            self.LayoutLargeCard(container, displayName)
                        
    def AddTextWidget(self, container, text, font, padding):
        if text != None:
            textWidget = wxStaticText(self, -1, text)
            textWidget.SetFont(font)
            container.Add(textWidget, 0, wxEXPAND | wxWEST, padding)
            EVT_LEFT_DOWN(textWidget, self.OnLeftDown)
            return textWidget
        return None
    
   # select a photo for this address card
   # FIXME: this code is copied from ContactNamePlate - it
   # really should be in a common place
    def GetPhotoImage(self, event):
        contactView = self.contactView
        if self.contact.IsRemote():
            contactView.ShowCantEditDialog(self.contact)
            return

        if contactView.model.lastImageDirectory == None:
            contactView.model.lastImageDirectory = wxGetHomeDir()
 
        dialog = ImageDialog(app.wxMainFrame, contactView.model.lastImageDirectory)
        dialog.Centre()
        
        if dialog.ShowModal() == wxID_OK:
            path = dialog.GetFile()
            fileURL = urllib.pathname2url(path)
            self.contact.SetPhotoURL(fileURL)
            self.RenderWidgets()
 
        contactView.model.lastImageDirectory = dialog.GetDirectory()
        dialog.Destroy()
        
    def LayoutWidgets(self):
        container = wxBoxSizer(wxVERTICAL)
        zoomIndex = self.miniCardView.GetZoomIndex()

        fullName = self.contact.GetFullName()
        shortName = self.contact.GetShortName()

        width, height, descent, ascent = self.GetFullTextExtent(fullName, self.miniCardView.nameFont)
        if (width + 8) < self.cardSize[0]:
            displayName = fullName
        else:
            displayName = shortName
                                        
        self.LayoutCardWithZoom(container, displayName, zoomIndex)
                                
        self.SetSizer(container)
        self.Layout()

    def SetSelected(self, isSelected):
        if self.selected != isSelected:
            self.selected = isSelected
            if self.selected:
                self.SetBackgroundColour(wxColour(251, 235, 146))
            else:
                self.SetBackgroundColour(wxWHITE)

            self.RenderWidgets()
            self.Refresh()
            
    def OnLeftDown(self, event):
        self.miniCardView.SetSelectedCard(self)
        self.contactView.SetContact(self.contact)
        
