__author__ = "John Anderson"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"


from wxPython.wx import *
from application.ViewerParcel import *
from application.Application import app
from application.SplashScreen import SplashScreen

class MrMenus(ViewerParcel):

    def __init__(self):
        ViewerParcel.__init__(self)
        self.radioSelection = 0
 
class wxMrMenus(wxViewerParcel):

    def OnInit(self):
        """
          General initialization goes here, e.g. wiring up menus, etc.
        """
        EVT_RADIOBOX(self, XRCID ('RadioBox'), self.OnRadioBox)

        EVT_MENU(self, XRCID ('Parce1Menu0'), self.OnParce1Menu0)
        EVT_MENU(self, XRCID ('Parce1Menu1'), self.OnParce1Menu1)

        EVT_MENU(self, XRCID ('EditMenu0'), self.OnEditMenu0)
        EVT_UPDATE_UI(self, XRCID ('EditMenu0'), self.OnEditMenu0UIUpdate)

        EVT_MENU(self, XRCID ('EditMenu1'), self.OnEditMenu0)
        EVT_UPDATE_UI(self, XRCID ('EditMenu1'), self.OnEditMenu1UIUpdate)

        EVT_MENU(self, XRCID('AboutMrMenusMenuItem'), self.OnAboutMrMenus)

        self.radioBox = self.FindWindowById (XRCID ('RadioBox'))
        assert (self.radioBox != None)
        self.menuBar = app.wxMainFrame.GetMenuBar()
        assert (self.menuBar != None)

    def Activate(self):
        wxViewerParcel.Activate(self)
        self.SynchronizeParcelMenu()
        self.SynchronizeParcelViewer()

    def SynchronizeParcelMenu(self):
        if self.model.radioSelection == 0:
            self.menuBar.Check(XRCID ('Parce1Menu0'), TRUE)
        elif self.model.radioSelection == 1:
            self.menuBar.Check(XRCID ('Parce1Menu1'), TRUE)
        
    def SynchronizeParcelViewer(self):
        self.radioBox.SetSelection (self.model.radioSelection)

    def OnRadioBox(self, event):
        self.model.radioSelection = self.radioBox.GetSelection()
        self.SynchronizeParcelMenu()

    def OnParce1Menu0(self, event):
        self.model.radioSelection = 0
        self.SynchronizeParcelViewer()

    def OnParce1Menu1(self, event):
        self.model.radioSelection = 1
        self.SynchronizeParcelViewer()

    def OnEditMenu0(self, event):
        if self.model.radioSelection == 0:
            self.model.radioSelection = 1
        elif self.model.radioSelection == 1:
            self.model.radioSelection = 0
        self.SynchronizeParcelViewer()

    def OnEditMenu0UIUpdate(self, event):
        if self.model.radioSelection == 0:
            event.SetText (_('Set Radio1'))
        elif self.model.radioSelection == 1:
            event.SetText (_('Set Radio0'))
        
    def OnEditMenu1(self, event):
        self.model.radioSelection = 1
        self.SynchronizeParcelViewer()

    def OnEditMenu1UIUpdate(self, event):
        event.Enable (self.model.radioSelection == 0)
        
    def OnAboutMrMenus(self, event):
        pageLocation = "parcels" + os.sep + "OSAF" + os.sep +\
                     "mrmenus" + os.sep + "AboutMrMenus.html"
        infoPage = SplashScreen(self, _("About MrMenus"), pageLocation, false)
        if infoPage.ShowModal():
            infoPage.Destroy()
            