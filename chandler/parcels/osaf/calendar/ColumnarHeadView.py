""" Columnar Head View (the top section of the columnar view).
    With typical calendar data, this view is meant to display events that
    apply to the day (all-day or banner events).
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

from ColumnarSubView import ColumnarSubView, wxColumnarSubView

class ColumnarHeadView (ColumnarSubView):
    def __init__(self, columnarView):
        ColumnarSubView.__init__(self, columnarView)
        self.xrcName = "ColumnarHeadView"
        # @@@ height may depend on banners, etc.
        #     or get from xrc, prefs, etc.
        self.viewHeight = 50
        
    def getRangeStart(self):
        return self.columnarView.rangeStart
    
    rangeStart = property(getRangeStart)

class wxColumnarHeadView(wxColumnarSubView):

    def OnInit(self, model):
        # @@@ For now, don't accept drag and drop data objects
        dropTargetDataObject = wxCustomDataObject()
        wxColumnarSubView.OnInit(self, model, dropTargetDataObject)

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

        today = DateTime.today()
        
        # Draw the day headers, lines separating the days       
        for i in range(self.model.daysPerView):

            # Label the column with the day. If today, choose a different color
            date = self.model.rangeStart + DateTime.RelativeDateTime(days=i)
            if (date == today) :
                dc.SetTextForeground(wxRED)
            dc.DrawText(date.Format("%a"), 
                        self.model.offset + (self.model.dayWidth * i) + 10, 
                        0)
            dc.DrawText(date.Format("%d"), self.model.offset + (self.model.dayWidth * (i + 1)) - 20, 0)
            if (date == today) :
                dc.SetTextForeground(wxColour(63, 87, 119))

            # Draw the line separating the days
            dc.DrawLine(self.model.offset + self.model.dayWidth * i, 0,
                        self.model.offset + self.model.dayWidth * i, 
                        self.model.viewHeight)

