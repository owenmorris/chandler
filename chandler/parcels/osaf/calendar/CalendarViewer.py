""" Calendar Viewer Parcel
"""

__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.calendar import *
from wxPython.wx import *
from wxPython.xrc import *

from mx import DateTime

from persistence import Persistent
from persistence.dict import PersistentDict
from persistence.list import PersistentList

from application.Application import app
from application.ViewerParcel import *
from application.SplashScreen import SplashScreen

from OSAF.calendar.ColumnarViewer import ColumnarViewer
from OSAF.calendar.MonthViewer import MonthViewer
from OSAF.calendar.TableViewer import TableViewer
from OSAF.calendar.CalendarDialog import wxCalendarDialog
from OSAF.calendar.MonthNavigator import MonthNavigator

from OSAF.calendar.CalendarTest import CalendarTest

from OSAF.calendar.CalendarEvents import *

class CalendarViewer(ViewerParcel):
    def __init__(self):
        ViewerParcel.__init__(self)
        self.viewTypes = PersistentList()
        self.viewTypes = (ColumnarViewer(self), MonthViewer(self), TableViewer(self))
        self.remoteAddress = None
        self.currentViewType = 0
        self.showFreeBusy = false
        self.overlayRemoteItems = false
        self.sharingPolicy = 'private'
        self.monthNavigator = MonthNavigator()

# Remote viewing methods

    # Return a list of accessible views (for now, ones that are public)
    # A menu item determines whether or not the one view is public
    # or private.
    def GetAccessibleViews(self, who):
        if self.sharingPolicy == 'public':
            return ['Calendar']
        return []
    
    # add the objects in the passed-in list to the objectlist,
    # pass it to each view type
    def AddObjectsToView(self, url, objectList, lastFlag):
        for viewer in self.viewTypes:
            viewer.AddObjectsToView(url, objectList, lastFlag)

        
    # determine if the passed-in jabberID has access to the passed in url
    # @@@ sharing policies will become objects, so this will be rewritten
    def HasPermission(self, jabberID, url):
        return self.sharingPolicy == 'public'
    
    # return a list of objects from the view specified by the url.
    # @@@ for now, just return all calendar events
    def GetViewObjects(self, url, jabberID):
        eventList = []
        for item in app.repository.find("//Calendar"):
            eventList.append(item)
        return eventList
    
    # handle errors - just pass it down the the wxViewer
    def HandleErrorResponse(self, jabberID, url, errorMessage):
        viewer = app.association[id(self)]
        viewer.HandleErrorResponse(jabberID, url, errorMessage)
    
   # there's no real views yet, so for now we just rememeber remoteAddress
    def GoToURL(self, remoteAddress, url):
        self.remoteAddress = remoteAddress
        self.SynchronizeView()
        
        viewer = app.association[id(self)]
        viewer.UpdateCurrentView()
        
        return true
    
class wxCalendarViewer(wxViewerParcel):

    # Window setup

    def OnInit(self):
        """Initialize the calendar view parcel. This method is called
           when the wxCalendarViewer is created -- we use the opportunity
           to hook up menus, buttons, other controls. For the calendar,
           that includes the subViews (Month, Day, Year).
        """
        
        EVT_MENU(self, XRCID("MenuGoToday"), self.OnToday)
        EVT_MENU(self, XRCID("MenuGoDate"), self.OnDate)
        EVT_MENU(self, XRCID("MenuFreeBusy"), self.OnFreeBusy)
        EVT_MENU(self, XRCID("MenuOverlayRemote"), self.OnOverlayRemote)
        EVT_MENU(self, XRCID("MenuSharingPolicy"), self.OnSharingPolicy)
        EVT_MENU(self, XRCID("MenuAboutCalendar"), self.OnAboutCalendar)
        EVT_MENU(self, XRCID("MenuGenerateEvents"), self.OnGenerateEvents)
        EVT_MENU(self, XRCID("MenuDeleteCalendar"), self.OnDelete)
        EVT_MENU(self, wxID_CLEAR, self.OnDelete)
        
        self._initCalendarTitle()
        self._initViewTypeList()
        self._initCurrentView()
        self._initRangeDisplay()
        self._initMonthNavigator()
        
        EVT_BUTTON(self, XRCID("Prev"), self.OnPrev)
        EVT_BUTTON(self, XRCID("Next"), self.OnNext)
        EVT_BUTTON(self, XRCID("Today"), self.OnToday)
        
        EVT_CALENDAR_DATE(self, self.OnCalendarDate)
        
        # Only bind erase background on Windows for flicker reasons
        if wxPlatform == '__WXMSW__':
            EVT_ERASE_BACKGROUND(self, self.OnEraseBackground)
        
    def OnEraseBackground(self, event):
        pass

    # Override ReplaceViewParcelMenu to set up the parcel menu,
    # append the available views to it, and enable the items properly
    def ReplaceViewParcelMenu(self):    
        self.calendarMenu = wxViewerParcel.ReplaceViewParcelMenu(self)
        self._UpdateMenus()

    # make sure the menus reflect the application state
    def _UpdateMenus(self):
        isShared = self.model.sharingPolicy == 'public'
        self.calendarMenu.Check(XRCID("MenuFreeBusy"), self.model.showFreeBusy)
        self.calendarMenu.Check(XRCID("MenuOverlayRemote"), self.model.overlayRemoteItems)
        self.calendarMenu.Check(XRCID("MenuSharingPolicy"), isShared)
        
        self.calendarMenu.Enable(XRCID("MenuOverlayRemote"), self.model.remoteAddress != None)
         
    def _initCalendarTitle(self):
        """
          load the calendar title widget and update the title
        """
        self.calendarTitle = XRCCTRL(self, "CalendarLabel")
        self.calendarTitle.SetFont(wxFont(18, wxSWISS, wxNORMAL, wxNORMAL))

        self.UpdateTitle()

    def _initViewTypeList(self):
        """Sets up the combo box for choosing view types. Looks at the model 
           to get the choices, set up the selection. 
        """
        # @@@ How to make this easy to change to buttons?
        viewTypeList = XRCCTRL(self, "ViewTypeList")
        for viewType in self.model.viewTypes:
            viewTypeList.Append(viewType.displayName)
            
        viewTypeList.SetSelection(self.model.currentViewType)

        EVT_CHOICE(self, XRCID("ViewTypeList"), self.OnChangeView)

    def _initCurrentView(self):
        """Initial loading of the current view.
        """
        self.viewTypes = {}
        self.sizer = self.getViewTypeSizer()
        
        # @@@ Load both view types at the start: change this eventually
        columnarView = self.getViewType(0)
        monthView = self.getViewType(1)
        
        self.sizer.Show(columnarView, 0)
        self.sizer.Show(monthView, 0)
        
        self.currentView = self.getViewType(self.model.currentViewType)
        self.sizer.Show(self.currentView, 1)
        
    def _initRangeDisplay(self):
        """Displays the date range, sets up the right font, looks at the current view.
           Expects the current view to already be setup.
        """
        self.rangeDisplay = XRCCTRL(self, "RangeLabel")
        self.rangeDisplay.SetFont(wxFont(9, wxSWISS, wxNORMAL, wxBOLD))
        self.rangeDisplay.SetLabel(self.currentView.getRangeString())
        
    def _initMonthNavigator(self):
        """Control used to navigate through time.
        """
        self.monthNavigator = XRCCTRL(self, "MonthNavigator")
        self.model.monthNavigator.SynchronizeView(self.monthNavigator)
        
        start, end = self.currentView.getRange()
        self.monthNavigator.SetSelectedDateRange(start, end)
        
        EVT_CALENDAR_SEL_CHANGED(self, XRCID("MonthNavigator"), 
                                 self.OnSelectionChanged)

    # update the calendar title by using the remote address if necessary
    def UpdateTitle(self):
        titleStr = _("Calendar")
        if self.model.remoteAddress != None:
            remoteName = app.jabberClient.GetNameFromID(self.model.remoteAddress)
            remoteText = _('(from %s)') % (remoteName)
            titleStr = titleStr + ' ' + remoteText
        self.calendarTitle.SetLabel(titleStr)

    # update current view is called when the current view changes,
    # to update the title and current view contents
    def UpdateCurrentView(self):
        self.UpdateTitle()
        self.currentView.model.UpdateItems()
        self._UpdateMenus()
    
    # UpdateFromRepository is called to tell the calendar that new objects
    # have been added to the repository.  Just pass it down to the wxView
    def UpdateFromRepository(self):
        self.UpdateCurrentView()

    # handle sharing errors - put up a message
    def HandleErrorResponse(self, jabberID, url, errorMessage):
        wxMessageBox(errorMessage)
        
    def getViewTypeSizer(self):
        # @@@ Find a cleaner way to find the sizer
        sizer = self.GetSizer()
        childList = sizer.GetChildren()
        sizerItem = childList[0]
        viewTypeSizer = sizerItem.GetSizer()
        return viewTypeSizer
    
    # Menu Handlers

    def OnFreeBusy(self, event):
        self.model.showFreeBusy = event.IsChecked()
        self.currentView.UpdateDisplay()
    
    def OnOverlayRemote(self, event):
        self.model.overlayRemoteItems = event.IsChecked()
        self.UpdateCurrentView()
    
    def OnSharingPolicy(self, event):
        if event.IsChecked():
            self.model.sharingPolicy = 'public'
        else:
            self.model.sharingPolicy = 'private'
        
        app.jabberClient.PermissionsChanged('Calendar')
        
    def OnDate(self, event):
        dialog = wxCalendarDialog(self, self.currentView.getRangeDate(),
                                  self.resources)
        result = dialog.ShowModal()
        if result == wxID_OK:
            selectedDate = dialog.GetSelectedDate()
            selectedDateTime = DateTime.DateTime(selectedDate.GetYear(),
                                                 selectedDate.GetMonth() + 1,
                                                 selectedDate.GetDay())
            
            self.currentView.ChangeDateRange(selectedDateTime)
            
        dialog.Destroy()

    def OnAboutCalendar(self, event):
        pageLocation = self.model.path + os.sep + "AboutCalendar.html"
        infoPage = SplashScreen(self, _("About Calendar"), pageLocation, 
                                False, False)
        infoPage.Show(True)

    def OnGenerateEvents(self, event):
        """ Generates 100 events over the next few months """
        generator = CalendarTest(app.repository)
        # Generate 20 events in the next two weeks
        generator.generateEvents(20, 14)
        # Generate 80 events in the next 6 months
        generator.generateEvents(80, 180)
        self.currentView.model.UpdateItems()
        app.repository.commit()

    # Navigation event handlers

    def OnPrev(self, event):
        self.currentView.DecrementDateRange()

    def OnNext(self, event):
        self.currentView.IncrementDateRange()
        
    def OnToday(self, event):
        self.currentView.ChangeDateRange(DateTime.today())
        
    def OnSelectionChanged(self, event):
        """Called when the date range is changed from the month navigator
        """
        selectedDate = self.monthNavigator.GetSelectedDate()
        self.currentView.ChangeDateRange(selectedDate)

    def OnDelete(self, event):
        self.currentView.OnDelete(event)

    def OnChangeView(self, event):
        self.model.currentViewType = event.GetSelection()
        view = self.getViewType(self.model.currentViewType)
        self.sizer.Show(self.currentView, 0)
        self.currentView = view

        # @@@ use the last selected date
        selectedDate = self.monthNavigator.GetSelectedDate()
        self.currentView.ChangeDateRange(selectedDate)
        
        self.sizer.Show(self.currentView, 1)
        self.sizer.Layout()

    def getViewType(self, viewTypeIndex):
        # @@@ We might want this to be managed by wxViewerParcel?
        viewTypeModel = self.model.viewTypes[viewTypeIndex]
        xrcClass = viewTypeModel.xrcClass
        xrcName = viewTypeModel.xrcName
        if (self.viewTypes.has_key(xrcName)):
            view = self.viewTypes[xrcName]
        else:
            # Load the requested sub-view for the first time
            view = self.resources.LoadObject(self, xrcName, xrcClass)
            assert (view != None)
            self.viewTypes[xrcName] = view
            self.sizer.Add(view, 1, wxEXPAND)
            model = self.model.viewTypes[viewTypeIndex]
            model.SynchronizeView(view)
        return view
    
    def OnCalendarDate(self, event):
        self.rangeDisplay.SetLabel(self.currentView.getRangeString())
        start, end = self.currentView.getRange()
        self.monthNavigator.SetSelectedDateRange(start, end)
        event.Skip()

