#!bin/env python

"""
 The MiniContactCardView is an index view that represents a contact
 as a minicard.
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *

from parcels.OSAF.contacts.ContactsModel import *
from parcels.OSAF.contacts.MiniContactCard import *

# FIXME:  this implemention (which flashes alot) is due to be replace with one built on the SimpleCanvas
# soon

class MiniContactCardView(wxPanel):
    def __init__(self, parent, contactView):
        self.indexView = parent
        self.contactView = contactView
        self.zoomSizes = [(80, 50), (128, 80), (256, 160)]
        self.zoomIndex = self.indexView.contactsView.model.currentZoomIndex
        wxPanel.__init__(self, parent, -1, style=wxSUNKEN_BORDER)

        self.miniCards = []
        self.miniCardIndex = {}
        
        sizer = wxBoxSizer(wxVERTICAL)
        self.miniCardArea = wxScrolledWindow(self, -1, style=wxNO_BORDER)
        sizer.Add(self.miniCardArea, 1, wxEXPAND)
        
        # set up fonts for the minicards to use
        self.SetUpFonts()

        # determine the number of minicards to fill the screen, and their layout
        self.CalculateCardCount()
        
        self.selectedCard = None
        self.selectedContact = None
        
        self.cardOffset = 0
        
        self.LayoutWidgets()
        self.SetSizerAndFit(sizer)
        
        self.UpdateVirtualSize(self.GetSize())
        self.miniCardArea.EnableScrolling(false, true)
        self.miniCardArea.SetScrollRate(0, 1)

        # notify us when the size or scroll position changes
        EVT_SIZE(self, self.OnSize)
        EVT_SCROLLWIN(self.miniCardArea, self.ScrollChanged)
        
    # set up the fonts according to the zoom index
    def SetUpFonts(self):
        if self.zoomIndex == 0:
            self.nameFont = wxFont(7, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
            self.itemFont = wxFont(7, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
            self.labelFont = wxFont(7, wxSWISS, wxNORMAL, wxBOLD, false, "Arial")

        elif self.zoomIndex == 1:
            self.nameFont = wxFont(10, wxSWISS, wxNORMAL, wxBOLD, false, "Arial")
            self.itemFont = wxFont(10, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
            self.labelFont = wxFont(10, wxSWISS, wxNORMAL, wxBOLD, false, "Arial")
        else:
            self.nameFont = wxFont(18, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
            self.itemFont = wxFont(10, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
            self.labelFont = wxFont(10, wxSWISS, wxNORMAL, wxBOLD, false, "Arial")

    # get the contact list
    def GetContactList(self):
        return self.contactView.GetSortedContacts()

    def GetContactsCount(self):
        return len(self.contactView.GetSortedContacts())
    
    # routines to maintain the selection
    def GetSelectedContact(self):
        return self.selectedContact
    

    def SetSelectedContact(self, newContact):
        if newContact == self.selectedContact:
            return
        
        if newContact != None:
            # perhaps the selected contact was deleted, so check for that
            if self.miniCardIndex.has_key(newContact):
                miniCard = self.miniCardIndex[newContact]
            else:
                miniCard = None
        else:
            miniCard = None
        
        self.selectedContact = newContact
        self.SetSelectedCard(miniCard)
        if miniCard != None:
            self.contactView.SetContact(miniCard.contact)

    def GetSelectedIndex(self):
        if self.selectedCard == None:
            return None
        else:
            contactList = self.contactView.GetSortedContacts()
            try:
                return contactList.index(self.selectedCard.contact)
            except:
                return None
            
    def SetSelectedIndex(self, newIndex):
        if newIndex == None:
            contact = None
        else:
            contactList = self.contactView.GetSortedContacts()
            contact = contactList[newIndex]

        self.SetSelectedContact(contact)
        self.contactView.SetContact(contact)

    # FIXME: for now, we don't support multiple selection, so just return singleton lists
    def GetSelectionList(self):
        index = self.GetSelectedIndex()
        list = []
        if index != None:
            list.append(index)
        return list
    
    def GetSelectedContacts(self):
        contact = self.GetSelectedContact()
        list = []
        if contact != None:
            list.append(contact)
        return list
 
    def ClearSelectionList(self):
        pass

    # calculate how many minicards in each row and column to fill the screen   
    def CalculateCardCount(self):
        self.numberOfColumns = self.CalculateColumnCount()
        self.numberOfRowsOnScreen = self.CalculateRowsOnScreen()
        self.numberOfCards = self.numberOfColumns * self.numberOfRowsOnScreen

    # calculate the number of columns that fit on the screen
    def CalculateColumnCount(self):
        size = self.GetSize()
        zoomSize = self.GetZoomSize()

        columns = ((size[0] - 16) / (zoomSize[0] + 12))	
        if columns <= 0:
            columns = 1

        return columns
    
    # calculate the number of columns that fit on the screen
    def CalculateRowsOnScreen(self):
        size = self.GetSize()
        zoomSize = self.GetZoomSize()

        rows = ((size[1] - 16) / (zoomSize[1] + 12))
        return rows + 2

    # move all the cards by the specified delta, and update their contact
    def AdjustCards(self, vPosition, vInterval):
        cardOffset = self.cardOffset
        contactList = self.GetContactList()
        contactListSize = len(contactList)
        newSelectedCard = None
         
        currentColumn = 0
        for card in self.miniCards:
            if currentColumn >= self.numberOfColumns:
                currentColumn = 0
                vPosition += vInterval
         
            currentColumn += 1
            if cardOffset < contactListSize:     
                position = card.GetPosition()
                newPosition = (position[0], vPosition + 4)
            
                card.Move(newPosition)
            
                contact = contactList[cardOffset]
                card.SetContact(contact)              
                card.SetSelected(contact == self.selectedContact)
                if contact == self.selectedContact:
                    newSelectedCard = card
                cardOffset += 1
                
        self.selectedCard = newSelectedCard
        
    # handle the scroll position changing, by repositioning
    # cards and update their contacts as necessary
    def ScrollChanged(self, event):
        newScrollPosition = self.miniCardArea.GetScrollPos(wxVERTICAL)
        cardSize = self.GetZoomSize()
       
        vInterval = cardSize[1] + 12
        rowIndex = newScrollPosition / vInterval
        self.cardOffset = rowIndex * self.numberOfColumns            
        self.AdjustCards(-1 * (newScrollPosition % vInterval), vInterval)
                
        event.Skip()
                
    # re-render the cards, preserving the selection, if any
    def RenderWidgets(self):    
        selectedContact = self.GetSelectedContact()	
        self.selectedCard = None

        self.miniCardArea.DestroyChildren()        
        self.LayoutWidgets()
        
        self.SetSelectedContact(selectedContact)

     # add a minicard to the view and index
    def AddMiniCard(self, contact, contactSize, position, images):
        miniCard = MiniContactCard(self.miniCardArea, self, contact, self.contactView, contactSize, position, images)
        self.miniCardIndex[contact] = miniCard
        return miniCard
    
    # key routine to calculate a cards position based on the row, column and scroll values
    def CalculateCardPosition(self, row, column, cardSize):
        hPos = column * (cardSize[0] + 12)
        vPos = row * (cardSize[1] + 12)
        return (8 + hPos, 8 + vPos)
    
    # here's where we allocate the minicards
    def LayoutWidgets(self):
        contactList = self.GetContactList()
        contactListSize = len(contactList)
        
        cardOffset = self.cardOffset
        cardSize = self.GetZoomSize()
        
        self.miniCards = []
        self.miniCardIndex = {}
        contactsView = self.indexView.contactsView
        
        index = 0
        for row in range(self.numberOfRowsOnScreen):
            for column in range(self.numberOfColumns):
                position = self.CalculateCardPosition(row, column, cardSize)
                
                if self.cardOffset + index < contactListSize:
                    contact = contactList[self.cardOffset + index]
                    miniCard = self.AddMiniCard(contact, cardSize, position, contactsView.images)
                    self.miniCards.append(miniCard)
                    index += 1
                
# stuff for zooming
    def IsZoomVisible(self):
        return true
        
    def GetZoomSize(self):
        return self.zoomSizes[self.zoomIndex]
        
    def GetZoomIndex(self):
        return self.zoomIndex
        
    def SetZoomIndex(self, newIndex, newLabel):
        if self.zoomIndex != newIndex:
            self.zoomIndex = newIndex
            self.SetUpFonts()
            
            self.CalculateCardCount()	
            self.UpdateVirtualSize(self.GetSize())
            self.RenderWidgets()
            
    def SetSelectedCard(self, miniCard):
        if self.selectedCard == miniCard:
            return
                
        if self.selectedCard != None:
            self.selectedCard.SetSelected(false)

        self.selectedCard = miniCard
        
        if miniCard != None:
            self.selectedContact = miniCard.contact
            miniCard.SetSelected(true)
                
    def ContactsChanged(self):
        self.CalculateCardCount()	
        self.UpdateVirtualSize(self.GetSize())
        self.RenderWidgets()
        
    # UpdateContact is called when the content view changes an attribute
    # to allow the current index view to reflect it. 
    def UpdateContact(self, contact):
        if self.miniCardIndex.has_key(contact):
            miniCard = self.miniCardIndex[contact]
            if miniCard != None:
                miniCard.ContactChanged()
                        
    def UpdateVirtualSize(self, realsize):
        virtualSizeH = realsize[0]
        cardCount = self.GetContactsCount()
        zoomSize = self.GetZoomSize()
        virtualSizeV = (1 + (cardCount / self.numberOfColumns)) * (zoomSize[1] + 12)
        self.miniCardArea.SetVirtualSize((virtualSizeH, virtualSizeV))
        #self.SetScrollbars(0, 50, cardCount / self.numberOfColumns, virtualSizeV)
                
    def OnSize(self, event):
        event.Skip()
                
        self.CalculateCardCount()	
        self.UpdateVirtualSize(self.GetSize())
        self.RenderWidgets()
