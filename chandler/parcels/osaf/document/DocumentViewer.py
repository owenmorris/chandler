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
        
        EVT_MENU(self, XRCID('MenuAboutDocument'), self.OnAboutDocument)
        
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
        if calendarDocument != None:
            calendarDocument.delete()
        calendarDocument = self.CreateCalendarDocument()
        self.RenderDocument(calendarDocument)

    def OnShowContacts(self, event):
        """
          Show the Contacts document.
          
          NOT YET IMPLEMENTED.
        """
        contactsDocument = app.repository.find('//Document/ContactsDocument')
        if contactsDocument != None:
            contactsDocument.delete()
        contactsDocument = self.CreateContactsDocument()
        self.RenderDocument(contactsDocument)

    def OnShowMrMenus(self, event):
        """
          Show the MrMenus document.
        """
        mrmenusDocument = app.repository.find('//Document/MrMenusDocument')
        if mrmenusDocument != None:
            mrmenusDocument.delete()
        mrmenusDocument = self.CreateMrMenusDocument()
        self.RenderDocument(mrmenusDocument)

    def OnShowRepositoryViewer(self, event):
        """
          Show the Repository Viewer document.
          
          NOT YET IMPLEMENTED.
        """
        repositoryDocument = app.repository.find('//Document/RepositoryDocument')
        if repositoryDocument != None:
            repositoryDocument.delete()
        repositoryDocument = self.CreateRepositoryDocument()
        self.RenderDocument(repositoryDocument)

    def OnShowRoster(self, event):
        """
          Show the Roster document.
          
          NOT YET IMPLEMENTED.
        """
        rosterDocument = app.repository.find('//Document/RosterDocument')
        if rosterDocument != None:
            rosterDocument.delete()
        rosterDocument = self.CreateRosterDocument()
        self.RenderDocument(rosterDocument)

    def OnShowTimeclock(self, event):
        """
          Show the Timeclock document.
          
          NOT YET IMPLEMENTED.
        """
        timeclockDocument = app.repository.find('//Document/TimeclockDocument')
        if timeclockDocument != None:
            timeclockDocument.delete()
        timeclockDocument = self.CreateTimeclockDocument()
        self.RenderDocument(timeclockDocument)

    def OnShowZaoBao(self, event):
        """
          Show the ZaoBao document.
          
          NOT YET IMPLEMENTED.
        """
        zaobaoDocument = app.repository.find('//Document/ZaoBaoDocument')
        if zaobaoDocument != None:
            zaobaoDocument.delete()
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
        radiobox.style['weight'] = 0
        radiobox.style['flag'] = wxALIGN_CENTER|wxALL
        radiobox.style['border'] = 25
        
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
                                                                        'button', 
                                                                        positionInParent=0)
        startButton.style['label'] = 'Start Clock'
        startButton.style['flag'] = wxALIGN_CENTRE|wxALL
        startButton.style['border'] = 5

        stopButton = BlockFactory(app.repository, buttonSizer).NewItem('StopButton', 
                                                                       'button',
                                                                       positionInParent=1)
        stopButton.style['label'] = 'Stop Clock'
        stopButton.style['flag'] = wxALIGN_CENTRE|wxALL
        stopButton.style['border'] = 5
        
        radiobox = BlockFactory(app.repository, verticalSizer).NewItem('CustomerBox',
                                                                       'radiobox',
                                                                       positionInParent=1)
        radiobox.style['label'] = 'Customer:'
        radiobox.style['dimensions'] = 1
        radiobox.style['choices'] = ['Floss Recycling Incorporated', 
                                     'Northside Cowbell Foundry Corp.',
                                     'Cuneiform Designs, Ltd.']

        billableHours = BlockFactory(app.repository, verticalSizer).NewItem('BillableHours',
                                                                            'button',
                                                                            positionInParent=2)
        billableHours.style['label'] = 'See Billable Hours'

        billableAmount = BlockFactory(app.repository, verticalSizer).NewItem('BillableAmount',
                                                                            'button',
                                                                             positionInParent=3)
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
        orientation = wxVERTICAL
        
        for key in document.style.keys():
            exec(key + ' = document.style[\'' + key + '\']')

        self.DestroyChildren()
        sizer = wxBoxSizer(orientation)
        self.RenderChildren(document, self, sizer)
        self.SetSizerAndFit(sizer)
                    
    def RenderChildren(self, item, parent, sizer):
        """
          Renders all of the children of the item provided (if they exist).
          
        @@@ This method for ordering puts a lot of the burdon of ordering on
        the client.  We may or may not want a method where the order of elements
        is derived from the client's order of adding items.

        """
        try:
            children = item._children
        except:
            return # Item has no children
        childList = []
        for key in children.keys():
            childItem = children[key]
            childList.append(childItem)
        childList.sort(self.SortChildren)
        for childItem in childList:
            self.RenderItem(childItem, parent, sizer)

    def SortChildren(self, itemOne, itemTwo):
        return itemOne.positionInParent - itemTwo.positionInParent
            
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
        blockStyle = BlockStyle()
        
        for key in item.style.keys():
            exec('blockStyle.' + key + ' = item.style[\'' + key + '\']')

        sizer = wxBoxSizer(blockStyle.orientation)
        parentSizer.Add(sizer, blockStyle.weight, blockStyle.flag, 
                        blockStyle.border)
        self.RenderChildren(item, parent, sizer)
    
    def RenderButton(self, item, parent, sizer):
        blockStyle = BlockStyle()

        for key in item.style.keys():
            exec('blockStyle.' + key + ' = item.style[\'' + key + '\']')

        button = wxButton(parent, blockStyle.id, 
                          blockStyle.label, style=blockStyle.style)
        sizer.Add(button, blockStyle.weight, blockStyle.flag, 
                  blockStyle.border)
        
    def RenderList(self, item, parent, sizer):
        blockStyle = BlockStyle()

        for key in item.style.keys():
            exec('blockStyle.' + key + ' = item.style[\'' + key + '\']')

        list = wxListCtrl(parent, blockStyle.id, style=blockStyle.style)
        sizer.Add(list, blockStyle.weight, blockStyle.flag, blockStyle.border)

    def RenderTextCtrl(self, item, parent, sizer):
        blockStyle = BlockStyle()

        for key in item.style.keys():
            exec('blockStyle.' + key + ' = item.style[\'' + key + '\']')

        text = wxTextCtrl(parent, blockStyle.id, blockStyle.value, 
                          style=blockStyle.style)
        sizer.Add(text, blockStyle.weight, blockStyle.flag, blockStyle.border)

    def RenderLabel(self, item, parent, sizer):
        blockStyle = BlockStyle()
        
        for key in item.style.keys():
            exec('blockStyle.' + key + ' = item.style[\'' + key + '\']')

        label = wxStaticText(parent, blockStyle.id, blockStyle.label, 
                             style=blockStyle.style)
        sizer.Add(label, blockStyle.weight, blockStyle.flag, blockStyle.border)

    def RenderScrolledWindow(self, item, parent, sizer):
        blockStyle = BlockStyle()

        for key in item.style.keys():
            exec('blockStyle.' + key + ' = item.style[\'' + key + '\']')
            
        scrolledWindow = wxScrolledWindow(parent, blockStyle.id, 
                                          style=blockStyle.style)
        sizer.Add(scrolledWindow, blockStyle.weight, blockStyle.flag, 
                  blockStyle.border)

    def RenderToggleButton(self, item, parent, sizer):
        blockStyle = BlockStyle()

        for key in item.style.keys():
            exec('blockStyle.' + key + ' = item.style[\'' + key + '\']')
            
        toggleButton = wxToggleButton(parent, blockStyle.id, blockStyle.label, 
                                      style=blockStyle.style)
        sizer.Add(toggleButton, blockStyle.weight, blockStyle.flag, 
                  blockStyle.border)

    def RenderChoice(self, item, parent, sizer):
        blockStyle = BlockStyle()

        for key in item.style.keys():
            exec('blockStyle.' + key + ' = item.style[\'' + key + '\']')

        choice = wxChoice(parent, blockStyle.id, choices=blockStyle.choices, 
                          style=blockStyle.style)
        sizer.Add(choice, blockStyle.weight, blockStyle.flag, blockStyle.border)
            
    def RenderTree(self, item, parent, sizer):
        blockStyle = BlockStyle()

        for key in item.style.keys():
            exec('blockStyle.' + key + ' = item.style[\'' + key + '\']')
            
        tree = wxTreeCtrl(parent, blockStyle.id, style=blockStyle.style)
        sizer.Add(tree, blockStyle.weight, blockStyle.flag, blockStyle.border)

    def RenderRadioBox(self, item, parent, sizer):
        blockStyle = BlockStyle()

        for key in item.style.keys():
            exec('blockStyle.' + key + ' = item.style[\'' + key + '\']')

            
        radioBox = wxRadioBox(parent, blockStyle.id, blockStyle.label, 
                              choices=blockStyle.choices, style=blockStyle.style, 
                              majorDimension=blockStyle.dimensions)
        sizer.Add(radioBox, blockStyle.weight, blockStyle.flag, blockStyle.border)

    def RenderRadioButton(self, item, parent, sizer):
        blockStyle = BlockStyle()

        for key in item.style.keys():
            exec('blockStyle.' + key + ' = item.style[\'' + key + '\']')
            
        radioButton = wxRadioButton(parent, blockStyle.id, blockStyle.label, 
                                    style=blockStyle.style)
        sizer.Add(radioButton, blockStyle.weight, blockStyle.flag, blockStyle.border)

    def OnEraseBackground(self, event):
        pass

    def OnAboutDocument(self, event):
        pageLocation = self.model.path + os.sep + "AboutDocument.html"
        infoPage = SplashScreen(self, _("About Document"), pageLocation, 
                                False, False)
        infoPage.Show(True)

class BlockStyle:
    def __init__(self):
        self.label = ""
        self.id = -1
        orientation = wxVERTICAL
        value = ''
        choices = []
        dimensions = 1
        self.style = 0
        self.weight = 1
        self.flag = 0
        self.border = 0
