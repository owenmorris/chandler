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

    def __init__(self, **args):
        super (MrMenus, self).__init__ (**args)
        self.newAttribute ("radioSelection", 0)
 
class wxMrMenus(wxViewerParcel):

    def OnInit(self):
        """
          General initialization goes here, e.g. wiring up menus, etc.
        """
        EVT_RADIOBOX(self, XRCID ('RadioBox'), self.OnRadioBox)

        EVT_MENU(self, XRCID ('Parce1Menu0'), self.OnParce1Menu0)
        EVT_MENU(self, XRCID ('Parce1Menu1'), self.OnParce1Menu1)

        EVT_MENU(self, XRCID ('EditMenu0'), self.OnEditMenu0)
        EVT_UPDATE_UI(self, XRCID ('EditMenu0'), self.OnEditMenu0UpdateUI)

        EVT_MENU(self, XRCID ('EditMenu1'), self.OnEditMenu1)
        EVT_UPDATE_UI(self, XRCID ('EditMenu1'), self.OnEditMenu1UpdateUI)

        EVT_MENU(self, XRCID('AboutMrMenusMenuItem'), self.OnAboutMrMenus)
        
        EVT_TOOL(self, XRCID('Tool0'), self.OnTool0)
        EVT_TOOL(self, XRCID('Tool1'), self.OnTool1)

        self.radioBox = self.FindWindowById (XRCID ('RadioBox'))
        assert (self.radioBox != None)
        self.menuBar = app.wxMainFrame.GetMenuBar()
        assert (self.menuBar != None)

    def Activate(self):
        wxViewerParcel.Activate(self)
        self.SynchronizeParcelMenu()
        self.SynchronizeActionsBar()
        self.SynchronizeParcelViewer()

    def SynchronizeParcelMenu(self):
        if self.model.radioSelection == 0:
            self.menuBar.Check(XRCID ('Parce1Menu0'), TRUE)
        elif self.model.radioSelection == 1:
            self.menuBar.Check(XRCID ('Parce1Menu1'), TRUE)
            
    def SynchronizeParcelViewer(self):
        self.radioBox.SetSelection (self.model.radioSelection)
        
    def SynchronizeActionsBar(self):
        app.wxMainFrame.actionsBar.ToggleTool(XRCID('Tool0'), 
                                              self.model.radioSelection == 0)
        app.wxMainFrame.actionsBar.ToggleTool(XRCID('Tool1'), 
                                              self.model.radioSelection == 1)

    def OnRadioBox(self, event):
        self.model.radioSelection = self.radioBox.GetSelection()
        self.SynchronizeParcelMenu()
        self.SynchronizeActionsBar()

    def OnParce1Menu0(self, event):
        self.model.radioSelection = 0
        self.SynchronizeParcelViewer()
        self.SynchronizeActionsBar()

    def OnParce1Menu1(self, event):
        self.model.radioSelection = 1
        self.SynchronizeParcelViewer()
        self.SynchronizeActionsBar()

    def OnEditMenu0(self, event):
        if self.model.radioSelection == 0:
            self.model.radioSelection = 1
        elif self.model.radioSelection == 1:
            self.model.radioSelection = 0
        self.SynchronizeParcelViewer()
        self.SynchronizeParcelMenu()
        self.SynchronizeActionsBar()

    def OnEditMenu0UpdateUI(self, event):
        if self.model.radioSelection == 0:
            event.SetText (_('Set to Dinner'))
        elif self.model.radioSelection == 1:
            event.SetText (_('Set to Lunch'))
        
    def OnEditMenu1(self, event):
        self.model.radioSelection = 1
        self.SynchronizeParcelViewer()
        self.SynchronizeParcelMenu()
        self.SynchronizeActionsBar()

    def OnEditMenu1UpdateUI(self, event):
        event.Enable (self.model.radioSelection == 0)
        
    def OnTool0(self, event):
        self.model.radioSelection = 0
        self.SynchronizeParcelViewer()
        self.SynchronizeParcelMenu()
        self.SynchronizeActionsBar()
    
    def OnTool1(self, event):
        self.model.radioSelection = 1
        self.SynchronizeParcelViewer()
        self.SynchronizeParcelMenu()
        self.SynchronizeActionsBar()

    def OnAboutMrMenus(self, event):
        pageLocation = self.model.path + os.sep + "AboutMrMenus.html"
        infoPage = SplashScreen(self, _("About MrMenus"), pageLocation, 
                                False, False)
        infoPage.Show(True)
            