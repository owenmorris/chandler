#!bin/env python

"""
This class implements the control bar for the contacts parcel
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *

from application.repository.Namespace import chandler

# here's the view type selector class
# FIXME: for now, the view types are hard-wired
class ContactViewTypeSelector(wxChoice):
    def __init__(self, parent, indexView):
        self.indexView = indexView
        self.controlBar = parent
        self.choiceList = [_(' View as Table '), _(' View as Cards ')]

        wxChoice.__init__(self, parent, -1, choices=self.choiceList)
        currentViewIndex = self.indexView.contactsView.model.currentViewTypeIndex
        self.SetStringSelection(self.choiceList[currentViewIndex])
        EVT_CHOICE(self, -1, self.ChoiceSelected)

    def ChoiceSelected(self, event):
        selectedChoice = event.GetString()
        selectedIndex = self.choiceList.index(selectedChoice)
        self.indexView.SelectViewType(selectedIndex, selectedChoice)

        # show or hide the zoom selector based on the view type
        self.controlBar.SetZoomVisible(self.indexView.IsZoomVisible())
        self.controlBar.Layout()
                
# here's the zoom selector class
class ContactZoomSelector(wxChoice):
    def __init__(self, parent, indexView):
        self.indexView = indexView
        self.choiceList = [_(' 50% '), _(' 100% '), _(' 200%') ]

        wxChoice.__init__(self, parent, -1, choices=self.choiceList)
        currentZoomIndex = self.indexView.contactsView.model.currentZoomIndex
        self.SetStringSelection(self.choiceList[currentZoomIndex])
        EVT_CHOICE(self, -1, self.ChoiceSelected)

    def ChoiceSelected(self, event):
        selectedChoice = event.GetString()
        selectedIndex = self.choiceList.index(selectedChoice)
        self.indexView.SetZoomIndex(selectedIndex, selectedChoice)

# here's the view sharing mode selector
class ContactSharingSelector(wxChoice):
    def __init__(self, parent, indexView):
        self.indexView = indexView
        
        attributeDictionary = self.indexView.contactsView.GetAttributeDictionary()
        self.choiceList = attributeDictionary.GetAttributeData(chandler.sharing)
        
        wxChoice.__init__(self, parent, -1, choices=self.choiceList)
        contactsView = self.indexView.contactsView
        currentSharingPolicy = contactsView.GetSharingPolicy()
        
        self.SetStringSelection(currentSharingPolicy)
        EVT_CHOICE(self, -1, self.ChoiceSelected)

    def ChoiceSelected(self, event):
        selectedChoice = event.GetString()
        contactsView = self.indexView.contactsView
        contactsView.SetSharingPolicy(selectedChoice)
        
# here's the main class for the control bar		
class ContactsControlBar(wxPanel):
    def __init__(self, parent, indexView, contentView, imageCache):
        self.indexView = indexView
        self.contentView = contentView
        self.images = imageCache
        
        wxPanel.__init__(self, parent, -1)
                
        # load resources used by the control bar
        self.nameFont = wxFont(18, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
        self.queryFont = wxFont(9, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")
        
        self.rightTriangle = self.images.LoadBitmapFile('triangle_right.gif')
        self.downTriangle = self.images.LoadBitmapFile('triangle_down.gif')

        self.indexView.contactsView.model.currentViewTypeIndex
        
        self.zoomVisible = self.indexView.contactsView.model.currentViewTypeIndex > 0
        self.LayoutWidgets()
            
    # set the visibility of the zoom control
    def SetZoomVisible(self, isVisible):
        if self.zoomVisible != isVisible:
            self.zoomVisible = isVisible
            if isVisible:
                self.indexZoomSelector.Show()
            else:
                self.indexZoomSelector.Hide()

    # routines for manipulating the persistent queryOpen flag
    def IsQueryOpen(self):
        return self.indexView.contactsView.model.queryOpen
    
    def SetQueryOpen(self, newFlag):
        self.indexView.contactsView.model.queryOpen = newFlag
        
    def RenderWidgets(self):
        self.DestroyChildren()
        self.LayoutWidgets()
        
    # derive the view title, by appending the count to the query description
    def GetViewTitle(self):
        count = self.indexView.GetContactsCount()
        title = self.indexView.contactsView.GetViewTitle()
        
        if count == 1:
            itemText = _("item")
        else:
            itemText = _("items")
        
        if self.indexView.contactsView.remoteLoadInProgress:
            viewTitle = title + ': loading...'
        else:
            viewTitle =  '%s: %d %s' % (title, count, itemText)
        
        return viewTitle
    
    def LayoutWidgets(self):
        container = wxBoxSizer(wxHORIZONTAL)
        hBox = wxBoxSizer(wxHORIZONTAL)
        vBox = wxBoxSizer(wxVERTICAL)
 
        # first, add the disclosure triangle
        if self.IsQueryOpen():
            image = self.downTriangle
        else:
            image = self.rightTriangle
            
        self.triangleWidget = wxStaticBitmap(self, -1, image)
        EVT_LEFT_DOWN(self.triangleWidget, self.ClickedTriangle)
        container.Add(self.triangleWidget, 0, wxALIGN_CENTER_VERTICAL | wxWEST, 2)
        
        viewLabel = self.GetViewTitle()
        self.nameWidget = wxStaticText(self, -1, viewLabel)
        self.nameWidget.SetFont(self.nameFont)
        container.Add(self.nameWidget, 0, wxEXPAND | wxEAST | wxWEST | wxTOP, 4)

        # add the zoom selector
        self.indexZoomSelector = ContactZoomSelector(self, self.indexView)
        hBox.Add(self.indexZoomSelector, 0)
        if not self.zoomVisible:
            self.indexZoomSelector.Hide()
                        
        # add the index view selector choice control. 
        self.indexViewChoices = ContactViewTypeSelector(self, self.indexView)
        hBox.Add(self.indexViewChoices, 0, wxALIGN_RIGHT | wxEAST | wxWEST, 4)

        vBox.Add(hBox, 0, wxALIGN_RIGHT | wxEAST, 4)
        container.Add(vBox, 1, wxALIGN_CENTER)
       
        # add the query and other controls if necessary
        if self.IsQueryOpen():
            contactsView = self.indexView.contactsView
            
            queryContainer = wxBoxSizer(wxVERTICAL)
            queryContainer.Add(container, 0, wxEXPAND)
            container = queryContainer
            
            hBox = wxBoxSizer(wxHORIZONTAL)
            
            queryString = '      ' + self.indexView.contactsView.GetQueryDescription()
            queryWidget = wxStaticText(self, -1, queryString)
            queryWidget.SetFont(self.queryFont)
            hBox.Add(queryWidget, 1, wxALIGN_LEFT)
            
            # add the sharing mode selector if necessary
            if not contactsView.IsRemote():
                label = wxStaticText(self, -1, _("Sharing Policy:"))
                hBox.Add(label, 0, wxALIGN_RIGHT | wxTOP | wxEAST, 3)
            
                self.sharingSelector = ContactSharingSelector(self, self.indexView)
                hBox.Add(self.sharingSelector, 0, wxALIGN_RIGHT | wxEAST, 8)
            else:
                self.sharingSelector = None
                
            container.Add(hBox, 1, wxEXPAND)
        
        container.Add(-1, 2)
        self.SetSizerAndFit(container)
        
    # handle clicks on the disclosure triangle
    def ClickedTriangle(self, event):
        self.SetQueryOpen(not self.IsQueryOpen())
        self.RenderWidgets()
        
        # the Fit operation sets the right size vertically, but it shrinks it horizontally;
        # so we add code to ensure it remains the right horizontal size
        size = self.GetSize()
        self.Fit()
        self.SetSize((size[0], -1))

        # force resize and layout
        self.indexView.contactsView.RelayoutControlBar()
                
    def UpdateTitle(self):
        newTitle = self.GetViewTitle()
        self.nameWidget.SetLabel(newTitle)
        
    # update the title when a contact is added or removed
    # FIXME: had to play unsavory games with the horizontal size here, too
    def ContactsChanged(self):
        size = self.GetSize()
        self.RenderWidgets()
        self.SetSize((size[0], -1))
        
                
