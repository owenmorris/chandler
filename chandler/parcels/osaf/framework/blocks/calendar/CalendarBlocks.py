""" Calendar Blocks
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx
import wx.calendar
import wx.minical

from mx import DateTime

import osaf.framework.blocks.Block as Block



class wxMiniCalendar(wx.minical.wxMiniCalendar):
    def __init__(self, *arguments, **keywords):
        super (wxMiniCalendar, self).__init__(*arguments, **keywords)
        self.Bind(wx.minical.EVT_MINI_CALENDAR_SEL_CHANGED,
                  self.OnWXSelectItem)

    def wxSynchronizeWidget(self):
        self.SetWindowStyle(wx.minical.wxCAL_SUNDAY_FIRST |
                            wx.minical.wxCAL_SHOW_SURROUNDING_WEEKS)

    def Destroy(self):
        #super (wxMiniCalendar, self).Destroy()
        pass
        
    def OnWXSelectItem(self, event):
        self.blockItem.postEventByName ('SelectedDateChanged',
                                        {'start': self.getSelectedDate()})

    def getSelectedDate(self):
        wxdate = self.GetDate()
        mxdate = DateTime.DateTime(wxdate.GetYear(),
                                   wxdate.GetMonth() + 1,
                                   wxdate.GetDay())
        return mxdate

    def setSelectedDate(self, mxdate):
        wxdate = wx.DateTimeFromDMY(mxdate.day,
                                    mxdate.month - 1,
                                    mxdate.year)
        self.SetDate(wxdate)

    
    def setSelectedDateRange(self, mxstart, mxend):
        self.resetMonth()
        self.setSelectedDate(mxstart)
        
        if (mxstart.month != mxend.month):
            endday = mxstart.days_in_month + 1
        else:
            endday = mxend.day + 1
        
        for day in range(mxstart.day, endday):
            attr = wx.CalendarDateAttr(wx.WHITE, wx.BLUE, wx.WHITE,
                                       wx.SWISS_FONT)
            self.SetAttr(day, attr)
            
        today = DateTime.today()
        if ((today.year == mxstart.year) and (today.month == mxstart.month)):
            self.SetHoliday(today.day)
            
        self.Refresh()
    
    def resetMonth(self):
        for day in range(1,32):
            self.ResetAttr(day)

class MiniCalendar(Block.RectangularChild):
    def __init__(self, *arguments, **keywords):
        super (MiniCalendar, self).__init__(*arguments, **keywords)

    def instantiateWidget(self):
        return wxMiniCalendar(self.parentBlock.widget,
                              Block.Block.getWidgetID(self))

    def onSelectedDateChangedEvent(self, event):
        self.widget.setSelectedDate(event.arguments['start'])


