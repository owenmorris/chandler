""" Columnar Sub View
    Common base class for sub-views of the ColumnarView: 
    Head, Foot and Time views
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.xrc import *
from mx import DateTime

from application.Application import app
from application.SimpleCanvas import wxSimpleCanvas

from persistence import Persistent
from persistence.dict import PersistentDict

from parcels.OSAF.calendar.CalendarEvents import *

class ColumnarSubView (Persistent):
    def __init__(self, columnarView):
        self.columnarView = columnarView
        
        # Subclasses should set these attributes
        # self.xrcName = None
        # self.viewHeight = 0
        
    def SynchronizeView(self, view):
        view.OnInit(self)
    
    def getViewWidth(self):
        return self.columnarView.viewWidth
    
    def getDaysPerView(self):
        return self.columnarView.daysPerView
    
    def getDayWidth(self):
        return self.columnarView.dayWidth
    
    def getOffset(self):
        return self.columnarView.offset
    
    viewWidth = property(getViewWidth)
    daysPerView = property(getDaysPerView)
    dayWidth = property(getDayWidth)
    offset = property(getOffset)

class wxColumnarSubView(wxSimpleCanvas):
    def __init__(self):
        value = wxPreScrolledWindow()
        self.this = value.this
        self._setOORInfo(self)

    def OnInit(self, model, dropTargetDataObject):
        self.model = model
        
        wxSimpleCanvas.OnInit(self, dropTargetDataObject)
        
        self.SetVirtualSize((self.model.viewWidth, self.model.viewHeight))
        self.SetScrollRate(0,0)
        
    def UpdateSize(self):
        # @@@ with scrollbar:
        # self.SetVirtualSize((self.model.viewWidth, self.model.viewHeight))
        # @@@ without scrollbar:
        self.SetVirtualSize((self.GetClientSize().width, self.model.viewHeight))
        
    def UpdateDateRange(self):
        self.Refresh()
        
    def DrawBackground(self, dc):
        # @@@ setup colors so they can be changed as data?

        # Use the transparent pen for painting the background
        dc.SetPen(wxTRANSPARENT_PEN)
        
        # Paint the entire background
        dc.SetBrush(wxBrush(wxColour(222, 231, 239)))
        size = self.GetVirtualSize()
        dc.DrawRectangle(0, 0, size.x, size.y)
        
        # Set up the font
        dc.SetTextForeground(wxColour(63, 87, 119))
        dc.SetFont(wxFont(9, wxSWISS, wxNORMAL, wxBOLD))

        # Set the pen for the lines separating the days
        dc.SetPen(wxBLACK_PEN)        

        # Draw lines between the days
        for i in range(self.model.daysPerView):
            dc.DrawLine(self.model.offset + self.model.dayWidth * i, 0,
                        self.model.offset + self.model.dayWidth * i, 
                        self.model.viewHeight)

