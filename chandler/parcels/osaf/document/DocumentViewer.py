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

from OSAF.document.model.Document import Document
from OSAF.document.model.SimpleContainers import *
from OSAF.document.model.SimpleControls import *

class DocumentViewer(ViewerParcel):
    def __init__(self):
        ViewerParcel.__init__(self)
            
    
class wxDocumentViewer(wxViewerParcel):
    """
      This is a very preliminary version of the document architecture.  Expect
    to see A LOT of changes in this parcel.  This is only the current way that
    things are done and arranged and it will probably change quite drastically
    over time.
    
    @@@ One thing that still has to be done is to abstract the window styles
    away from wxWindows (so that we could have any number of windowing 
    implementations).  We do not yet have a final solution for how best to do
    this and coming up with a half-thoughtout solution or creating a full
    one-to-one mapping is a little too much grunt work just to have it be 
    thrown out once we have a proper solution.
    """
    def OnInit(self):
        """
          Sets up the handlers for the menu items.
        """
        EVT_MENU(self, XRCID('MrMenusDocument'), self.OnShowMrMenus)
        EVT_MENU(self, XRCID('TimeclockDocument'), self.OnShowTimeclock)
        
        EVT_MENU(self, XRCID('MenuAboutDocument'), self.OnAboutDocument)
        
        if wxPlatform == '__WXMSW__':
            EVT_ERASE_BACKGROUND(self, self.OnEraseBackground)
            
    def OnShowMrMenus(self, event):
        """
          Show the MrMenus document.
        """
        mrmenusDocument = app.repository.find('//Document/MrMenusDocument')
        if mrmenusDocument != None:
            mrmenusDocument.delete()
        mrmenusDocument = self.CreateMrMenusDocument()
        mrmenusDocument.Render(self)

    def OnShowTimeclock(self, event):
        """
          Show the Timeclock document.
        """
        timeclockDocument = app.repository.find('//Document/TimeclockDocument')
        if timeclockDocument != None:
            timeclockDocument.delete()
        timeclockDocument = self.CreateTimeclockDocument()
        timeclockDocument.Render(self)
    
    def CreateMrMenusDocument(self):
        """
          Creates the MrMenus document to be shown.
        """
        mrmenusDocument = Document('MrMenusDocument')
        radiobox = RadioBox('RadioBox', mrmenusDocument)
        radiobox.style['label'] = 'Please choose'
        radiobox.style['dimensions'] = 1
        radiobox.style['choices'] = ['Lunch', 'Dinner']
        radiobox.style['weight'] = 0
        radiobox.style['flag'] = wxALIGN_CENTER|wxALL
        radiobox.style['border'] = 25
        
        return mrmenusDocument
    
    def CreateTimeclockDocument(self):
        """
          Creates the Timeclock document to be shown.
        """
        timeclockDocument = Document('TimeclockDocument')
        verticalSizer = BoxContainer('OuterSizer', timeclockDocument)
        verticalSizer.style['orientation'] = wxVERTICAL

        buttonSizer = BoxContainer('ButtonSizer', verticalSizer)
        buttonSizer.style['orientation'] = wxHORIZONTAL
        startButton = Button('StartButton', buttonSizer, 0)
        startButton.style['label'] = 'Start Clock'
        startButton.style['flag'] = wxALIGN_CENTRE|wxALL
        startButton.style['border'] = 5

        stopButton = Button('StopButton', buttonSizer, 1)
        stopButton.style['label'] = 'Stop Clock'
        stopButton.style['flag'] = wxALIGN_CENTRE|wxALL
        stopButton.style['border'] = 5

        radiobox = RadioBox('CustomerBox', verticalSizer, 1)
        radiobox.style['label'] = 'Customer:'
        radiobox.style['dimensions'] = 1
        radiobox.style['choices'] = ['Floss Recycling Incorporated', 
                                     'Northside Cowbell Foundry Corp.',
                                     'Cuneiform Designs, Ltd.']

        billableHours = Button('BillableHours', verticalSizer, 2)
        billableHours.style['label'] = 'See Billable Hours'

        billableAmount = Button('BillableAmount', verticalSizer, 3)
        billableAmount.style['label'] = 'See Billable Amount'
        
        return timeclockDocument
        
        
    def OnEraseBackground(self, event):
        pass
    
    def OnAboutDocument(self, event):
        pageLocation = self.model.path + os.sep + "AboutDocument.html"
        infoPage = SplashScreen(self, _("About Document"), pageLocation, 
                                False, False)
        infoPage.Show(True)

    