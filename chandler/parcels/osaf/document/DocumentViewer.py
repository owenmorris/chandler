__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.xrc import *

from persistence import Persistent
from persistence.dict import PersistentDict
from persistence.list import PersistentList

from application.Application import app
from application.ViewerParcel import *
from application.SplashScreen import SplashScreen

from OSAF.document.model.Document import DocumentFactory
from OSAF.document.model.BoxContainer import BoxContainerFactory
from OSAF.document.model.Block import BlockFactory


class DocumentViewer(ViewerParcel):
    def __init__(self):
        ViewerParcel.__init__(self)
            
    
class wxDocumentViewer(wxViewerParcel):
    def OnInit(self):
        """
          Sets up the handlers for the menu items.
        """
        EVT_MENU(self, XRCID('CalendarDocument'), self.OnShowCalendar)
        EVT_MENU(self, XRCID('ContactsDocument'), self.OnShowContacts)
        EVT_MENU(self, XRCID('MrMenusDocument'), self.OnShowMrMenus)
        EVT_MENU(self, XRCID('RepositoryViewerDocument'), self.OnShowRepositoryViewer)
        EVT_MENU(self, XRCID('RosterDocument'), self.OnShowRoster)
        EVT_MENU(self, XRCID('TimeclockDocument'), self.OnShowTimeclock)
        EVT_MENU(self, XRCID('ZaoBaoDocument'), self.OnShowZaoBao)
        
        if wxPlatform == '__WXMSW__':
            EVT_ERASE_BACKGROUND(self, self.OnEraseBackground)

    def ReplaceViewParcelMenu(self):
        """
          Override ViewerParcel's ReplaceViewParcelMenu so that we can gain a 
        handle to the parcel menu.
        """
        self.documentMenu = wxViewerParcel.ReplaceViewParcelMenu(self)
        self._UpdateMenus()
    
    def _UpdateMenus(self):
        """
          Disable the menu items that are not implemented yet.
        """
        self.documentMenu.Enable(XRCID('CalendarDocument'), False)
        self.documentMenu.Enable(XRCID('ContactsDocument'), False)
        self.documentMenu.Enable(XRCID('MrMenusDocument'), True)
        self.documentMenu.Enable(XRCID('RepositoryViewerDocument'), False)
        self.documentMenu.Enable(XRCID('RosterDocument'), False)
        self.documentMenu.Enable(XRCID('TimeclockDocument'), True)
        self.documentMenu.Enable(XRCID('ZaoBaoDocument'), False)
            
    def OnShowCalendar(self, event):
        """
          Show the Calendar document.
          
          NOT YET IMPLEMENTED.
        """
        calendarDocument = app.repository.find('//Document/CalendarDocument')
        if calendarDocument == None:
            calendarDocument = self.CreateCalendarDocument()
        self.RenderDocument(calendarDocument)

    def OnShowContacts(self, event):
        """
          Show the Contacts document.
          
          NOT YET IMPLEMENTED.
        """
        contactsDocument = app.repository.find('//Document/ContactsDocument')
        if contactsDocument == None:
            contactsDocument = self.CreateContactsDocument()
        self.RenderDocument(contactsDocument)

    def OnShowMrMenus(self, event):
        """
          Show the MrMenus document.
        """
        mrmenusDocument = app.repository.find('//Document/MrMenusDocument')
        if mrmenusDocument == None:
            mrmenusDocument = self.CreateMrMenusDocument()
        self.RenderDocument(mrmenusDocument)

    def OnShowRepositoryViewer(self, event):
        """
          Show the Repository Viewer document.
          
          NOT YET IMPLEMENTED.
        """
        repositoryDocument = app.repository.find('//Document/RepositoryDocument')
        if repositoryDocument == None:
            repositoryDocument = self.CreateRepositoryDocument()
        self.RenderDocument(repositoryDocument)

    def OnShowRoster(self, event):
        """
          Show the Roster document.
          
          NOT YET IMPLEMENTED.
        """
        rosterDocument = app.repository.find('//Document/RosterDocument')
        if rosterDocument == None:
            rosterDocument = self.CreateRosterDocument()
        self.RenderDocument(rosterDocument)

    def OnShowTimeclock(self, event):
        """
          Show the Timeclock document.
          
          NOT YET IMPLEMENTED.
        """
        timeclockDocument = app.repository.find('//Document/TimeclockDocument')
        if timeclockDocument == None:
            timeclockDocument = self.CreateTimeclockDocument()
        self.RenderDocument(timeclockDocument)

    def OnShowZaoBao(self, event):
        """
          Show the ZaoBao document.
          
          NOT YET IMPLEMENTED.
        """
        zaobaoDocument = app.repository.find('//Document/ZaoBaoDocument')
        if zaobaoDocument == None:
            zaobaoDocument = self.CreateZaoBaoDocument()
        self.RenderDocument(zaobaoDocument)
        
        
    """
      CREATING DOCUMENTS SECTION
    """
    def CreateCalendarDocument(self):
        """
          Creates the Calendar document to be shown.
          
          NOT YET IMPLEMENTED.
        """
        calendarDocument = DocumentFactory(app.repository).NewItem('CalendarDocument')
        return calendarDocument
    
    def CreateContactsDocument(self):
        """
          Creates the Contacts document to be shown.
          
          NOT YET IMPLEMENTED.
        """
        contactsDocument = DocumentFactory(app.repository).NewItem('ContactsDocument')
        return contactsDocument
    
    def CreateMrMenusDocument(self):
        """
          Creates the MrMenus document to be shown.
        """
        mrmenusDocument = DocumentFactory(app.repository).NewItem('MrMenusDocument')
        radiobox = BlockFactory(app.repository, mrmenusDocument).NewItem('RadioBox',
                                                                         'radiobox')
        radiobox.style['label'] = 'Please choose'
        radiobox.style['dimensions'] = 1
        radiobox.style['choices'] = ['Lunch', 'Dinner']
        
        return mrmenusDocument
    
    def CreateRepositoryViewerDocument(self):
        """
          Creates the Repository Viewer document to be shown.
          
          NOT YET IMPLEMENTED.
        """
        repositoryDocument = DocumentFactory(app.repository).NewItem('RepositoryDocument')
        return repositoryDocument
    
    def CreateRosterDocument(self):
        """
          Creates the Roster document to be shown.
          
          NOT YET IMPLEMENTED.
        """
        rosterDocument = DocumentFactory(app.repository).NewItem('RosterDocument')
        return rosterDocument
    
    def CreateTimeclockDocument(self):
        """
          Creates the Timeclock document to be shown.
        """
        timeclockDocument = DocumentFactory(app.repository).NewItem('TimeclockDocument')
        verticalSizer = BoxContainerFactory(app.repository, timeclockDocument).NewItem('OuterSizer',
                                                                                   'container')
        verticalSizer.style['orientation'] = wxVERTICAL
        buttonSizer = BoxContainerFactory(app.repository, verticalSizer).NewItem('ButtonSizer',
                                                                             'container')
        buttonSizer.style['orientation'] = wxHORIZONTAL
        startButton = BlockFactory(app.repository, buttonSizer).NewItem('StartButton',
                                                                        'button')
        startButton.style['label'] = 'Start Clock'
        stopButton = BlockFactory(app.repository, buttonSizer).NewItem('StopButton',
                                                                       'button')
        stopButton.style['label'] = 'Stop Clock'


        radiobox = BlockFactory(app.repository, verticalSizer).NewItem('CustomerBox',
                                                                       'radiobox')
        radiobox.style['label'] = 'Customer:'
        radiobox.style['dimensions'] = 1
        radiobox.style['choices'] = ['Floss Recycling Incorporated', 
                                     'Northside Cowbell Foundry Corp.',
                                     'Cuneiform Designs, Ltd.']

        billableHours = BlockFactory(app.repository, verticalSizer).NewItem('BillableHours',
                                                                            'button')
        billableHours.style['label'] = 'See Billable Hours'

        billableAmount = BlockFactory(app.repository, verticalSizer).NewItem('BillableAmount',
                                                                            'button')
        billableAmount.style['label'] = 'See Billable Amount'
        

        return timeclockDocument
        
    def CreateZaoBaoDocument(self):
        """
          Creates the ZaoBao document to be shown.
          
          NOT YET IMPLEMENTED.
        """
        zaobaoDocument = DocumentFactory(app.repository).NewItem('ZaoBaoDocument')
        return zaobaoDocument

    
    """
      RENDERING DOCUMENTS SECTION
    """
    def RenderDocument(self, document):
        """
          Renders the document provided.
        """
        assert(document.blocktype == 'document')
        orientation = wxHORIZONTAL
        
        for key in document.style.keys():
            exec(key + ' = document.style[\'' + key + '\']')

        sizer = wxBoxSizer(orientation)
        self.RenderChildren(document, self, sizer)
        self.SetSizerAndFit(sizer)
                    
    def RenderChildren(self, item, parent, sizer):
        """
          Renders all of the children of the item provided (if they exist).
          
        @@@ Ordering is not currently preserved among children.  This is the
        first thing I plan to fix.
        """
        try:
            children = item._children
        except:
            return # Item has no children
        for key in children.keys():
            childItem = children[key]
            self.RenderItem(childItem, parent, sizer)

    def RenderItem(self, item, parent, sizer):
        """
          Renders the given item of unknown type.
        """
        if item.blocktype == 'container':
            self.RenderContainer(item, parent, sizer)
        elif item.blocktype == 'button':
            self.RenderButton(item, parent, sizer)
        elif item.blocktype == 'list':
            self.RenderList(item, parent, sizer)
        elif item.blocktype == 'text':
            self.RenderTextCtrl(item, parent, sizer)
        elif item.blocktype == 'label':
            self.RenderLabel(item, parent, sizer)
        elif item.blocktype == 'scrolledwindow':
            self.RenderScrolledWindow(item, parent, sizer)
        elif item.blocktype == 'togglebutton':
            self.RenderToggleButton(item, parent, sizer)
        elif item.blocktype == 'choice':
            self.RenderLabel(item, parent, sizer)
        elif item.blocktype == 'tree':
            self.RenderTree(item, parent, sizer)
        elif item.blocktype == 'radiobox':
            self.RenderRadioBox(item, parent, sizer)
        elif item.blocktype == 'radiobutton':
            self.RenderRadioButton(item, parent, sizer)
        else:
            print 'This kind of block is not yet supported'
            assert(True)            
            
    def RenderContainer(self, item, parent, parentSizer):
        """
          Renders a container and all of it's children.
        """
        id = -1
        orientation = wxHORIZONTAL
        weight = 1
        
        for key in item.style.keys():
            exec(key + ' = item.style[\'' + key + '\']')

        sizer = wxBoxSizer(orientation)
        parentSizer.Add(sizer, weight, wxEXPAND)            
        self.RenderChildren(item, parent, sizer)
    
    def RenderButton(self, item, parent, sizer):
        label = ""
        id = -1
        style = 0
        weight = 1

        for key in item.style.keys():
            exec(key + ' = item.style[\'' + key + '\']')

        button = wxButton(parent, id, label, style=style)
        sizer.Add(button, weight, wxEXPAND)
        
    def RenderList(self, item, parent, sizer):
        id = -1
        style = wxLC_ICON
        weight = 1

        for key in item.style.keys():
            exec(key + ' = item.style[\'' + key + '\']')

        list = wxListCtrl(parent, id, style=style)
        sizer.Add(list, weight, wxEXPAND)

    def RenderTextCtrl(self, item, parent, sizer):
        id = -1
        value = ''
        style = 0
        weight = 1

        for key in item.style.keys():
            exec(key + ' = item.style[\'' + key + '\']')

        text = wxTextCtrl(parent, id, value, style=style)
        sizer.Add(text, weight, wxEXPAND)

    def RenderLabel(self, item, parent, sizer):
        id = -1
        label = ''
        style = 0
        weight = 1
        
        for key in item.style.keys():
            exec(key + ' = item.style[\'' + key + '\']')

        label = wxStaticText(parent, id, label, style=style)
        sizer.Add(label, weight, wxEXPAND)

    def RenderScrolledWindow(self, item, parent, sizer):
        id = -1
        style = wxHSCROLL|wxVSCROLL
        weight = 1

        for key in item.style.keys():
            exec(key + ' = item.style[\'' + key + '\']')
            
        scrolledWindow = wxScrolledWindow(parent, id, style=style)
        sizer.Add(scrolledWindow, weight, wxEXPAND)

    def RenderToggleButton(self, item, parent, sizer):
        id = -1
        label = ''
        style = 0
        weight = 1

        for key in item.style.keys():
            exec(key + ' = item.style[\'' + key + '\']')
            
        toggleButton = wxToggleButton(parent, id, label, style=style)
        sizer.Add(toggleButton, weight, wxEXPAND)

    def RenderChoice(self, item, parent, sizer):
        id = -1
        chioces = []
        style = 0
        weight = 1

        for key in item.style.keys():
            exec(key + ' = item.style[\'' + key + '\']')

        choice = wxChoice(parent, id, choices=choices, style=style)
        sizer.Add(choice, weight, wxEXPAND)
            
    def RenderTree(self, item, parent, sizer):
        id = -1
        style = wxTR_HAS_BUTTONS
        weight = 1

        for key in item.style.keys():
            exec(key + ' = item.style[\'' + key + '\']')
            
        tree = wxTreeCtrl(parent, id, style=style)
        sizer.Add(tree, weight, wxEXPAND)

    def RenderRadioBox(self, item, parent, sizer):
        id = -1
        label = ''
        choices = []
        style = wxRA_SPECIFY_COLS
        dimensions = 1
        weight = 1

        for key in item.style.keys():
            exec(key + ' = item.style[\'' + key + '\']')

            
        radioBox = wxRadioBox(parent, id, label, choices=choices, 
                              style=style, majorDimension=dimensions)
        sizer.Add(radioBox, weight, wxEXPAND)

    def RenderRadioButton(self, item, parent, sizer):
        id = -1
        label = ''
        style = 0
        weight = 1

        for key in item.style.keys():
            exec(key + ' = item.style[\'' + key + '\']')
            
        radioButton = wxRadioButton(parent, id, label, style=style)
        sizer.Add(radioButton, weight, wxEXPAND)

    def OnEraseBackground(self, event):
        pass

    def OnAboutDocument(self, event):
        pageLocation = self.model.path + os.sep + "AboutDocument.html"
        infoPage = SplashScreen(self, _("About Document"), pageLocation, false)
        infoPage.ShowModal()
        infoPage.Destroy()
