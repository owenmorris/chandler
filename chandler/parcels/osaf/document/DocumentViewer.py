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

from OSAF.document.RepositoryDocument import RepositoryDocument
from OSAF.document.TimeclockDocument import TimeclockDocument
from OSAF.document.MrMenusDocument import MrMenusDocument

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
        welcomeDocument = app.repository.find('//Documents/WelcomeDocument')
        if welcomeDocument != None:
            welcomeDocument.delete()
        welcomeDocument = Document('WelcomeDocument')
        container = BoxContainer('container', welcomeDocument)
        container.style['orientation'] = wxVERTICAL
        title = Label('title', container)
        title.style['label'] = 'Please choose the view you would like to see from the Document menu'
        title.style['weight'] = 0
        title.style['fontpoint'] = 14
        welcomeDocument.Render(self)
        
        self.mrMenusDocument = MrMenusDocument(self)
        self.timeclockDocument = TimeclockDocument(self)
        self.repositoryDocument = RepositoryDocument(self)
        EVT_MENU(self, XRCID('MrMenusDocument'), self.mrMenusDocument.ShowMrMenus)
        EVT_MENU(self, XRCID('TimeclockDocument'), self.timeclockDocument.ShowTimeclock)
        EVT_MENU(self, XRCID('RepositoryDocument'), self.repositoryDocument.ShowRepository)
        
        EVT_MENU(self, XRCID('MenuAboutDocument'), self.OnAboutDocument)
        
    def OnAboutDocument(self, event):
        pageLocation = self.model.path + os.sep + "AboutDocument.html"
        infoPage = SplashScreen(self, _("About Document"), pageLocation, 
                                False, False)
        infoPage.Show(True)

    