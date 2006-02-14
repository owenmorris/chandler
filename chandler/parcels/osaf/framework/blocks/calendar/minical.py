

import wx
from i18n import OSAFMessageFactory as _

from datetime import date, timedelta
import calendar

VERT_MARGIN = 5
EXTRA_MONTH_HEIGHT = 4
SEPARATOR_MARGIN = 3

DAYS_PER_WEEK = 7
WEEKS_TO_DISPLAY = 6
MONTHS_TO_DISPLAY = 3
NUMBER_TO_PREVIEW = 5

CAL_HITTEST_NOWHERE = 0      # outside of anything
CAL_HITTEST_HEADER = 1       # on the header (weekdays)
CAL_HITTEST_DAY = 2          # on a day in the calendar
CAL_HITTEST_TODAY = 3        # on the today button
CAL_HITTEST_INCMONTH = 4
CAL_HITTEST_DECMONTH = 5
CAL_HITTEST_SURROUNDING_WEEK = 6


CAL_SUNDAY_FIRST           = 0x0000 # show Sunday as the first day of
                                    # the week (default)
CAL_MONDAY_FIRST           = 0x0001 # show Monder as the first day of
                                    # the week
CAL_SHOW_SURROUNDING_WEEKS = 0x0002 # show the neighbouring weeks in
                                    # the previous and next
                                    # month
CAL_SHOW_PREVIEW           = 0x0004 # show a preview of events on the 
                                    # selected day
CAL_HIGHLIGHT_WEEK         = 0x0008 # select an entire week at a time
CAL_SHOW_BUSY              = 0x0010 # show busy bars

def PreviousWeekday(targetDate, targetWeekday):
    """
    rewind the selected date to the previous specified date
    """
    dayAdjust = targetWeekday - targetDate.weekday()
    if dayAdjust > 0:
        dayAdjust -= 7

    return targetDate + timedelta(days=dayAdjust)

def GetWeekOfMonth(dt, ignored):
    """
    there may be issues with monday/sunday first day of week
    """
    year,week,day = dt.isocalendar()
    
    firstYear, firstWeek, firstDay = \
               date(dt.year, dt.month, 1).isocalendar()

    return week - firstWeek

def MonthDelta(dt, months):
    """
    Adjust the given date by the specified number of months, maxing
    out the day of the month with the new month
    """
    newYear = dt.year
    newMonth = dt.month + months

    # this could be done in constant time, I'm being lazy..
    if months > 0:
        while newMonth > 12:
            newYear += 1
            newMonth -= 12
    else:
        while newMonth < 1:
            newYear -= 1
            newMonth += 12

    # careful when going from going from mm/31/yyyy to a month that
    # doesn't have 31 days!
    (week, maxday) = calendar.monthrange(newYear, newMonth)
    day = min(maxday, dt.day)
    return date(newYear, newMonth, day)
    

class PyMiniCalendarEvent(wx.CommandEvent):
    """
    Not sure if these are even used?
    """

    def GetDate(self):
        return self.selected

    def SetDate(self, date):
        self.selected = date

    def SetWeekDay(self, wd):
        self.wday = wd

    def GetWeekDay(self):
        return self.wday

EVT_MINI_CALENDAR_SEL_CHANGED   = wx.PyEventBinder(wx.NewEventType(), 1)
EVT_MINI_CALENDAR_DAY_CHANGED   = wx.PyEventBinder(wx.NewEventType(), 1)
EVT_MINI_CALENDAR_MONTH_CHANGED = wx.PyEventBinder(wx.NewEventType(), 1)
EVT_MINI_CALENDAR_YEAR_CHANGED  = wx.PyEventBinder(wx.NewEventType(), 1)
EVT_MINI_CALENDAR_UPDATE_BUSY   = wx.PyEventBinder(wx.NewEventType(), 1)
EVT_MINI_CALENDAR_DOUBLECLICKED = wx.PyEventBinder(wx.NewEventType(), 1)

#  ----------------------------------------------------------------------------
#  wxMiniCalendar: a control allowing the user to pick a date interactively
#  ----------------------------------------------------------------------------
class PyMiniCalendar(wx.PyControl):

    def __init__(self, parent, id, *args, **kwds):
        # do we need this if we're just calling Create()?
        super(PyMiniCalendar, self).__init__(parent, id, *args, **kwds)

        self.Init()
        self.Create(parent, id, *args, **kwds)

    def Init(self):
        self.staticYear = None
        self.staticMonth = None

        # date
        self.selected = None
        self.visible = None

        self.lowdate = None
        self.highdate = None

        # colors
        self.colHighlightFg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
        self.colHighlightBg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        self.colHeaderFg = wx.BLACK
        self.colHeaderBg = wx.WHITE

        self.userChangedYear = False

        self.widthCol = 0
        self.heightRow = 0
        self.todayHeight = 0

        # TODO fill weekdays with names from PyICU
        self.weekdays = ["S", "M", "T", "W", "T", "F", "S"]

        self.busyPercent = [0.0] * (DAYS_PER_WEEK *
                                    WEEKS_TO_DISPLAY * MONTHS_TO_DISPLAY)

        # I'm sure this will really get initialized in RecalcGeometry
        self.rowOffset = 0
        self.todayHeight = 0

        self.leftArrowRect = None
        self.rightArrowRect = None
        self.todayRect = None

        self.normalFont = None
        self.boldFont = None

        self.Bind(wx.EVT_PAINT, self.OnMiniCalPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)

        
    def Create(self, parent, id=-1, pos=wx.DefaultPosition,
               size=wx.DefaultSize, style=0, name="PyMiniCalendar", targetDate=None):
        if not super(PyMiniCalendar, self).Create(parent, id, pos, size,
                                                  style | wx.CLIP_CHILDREN,
                                                  wx.DefaultValidator, name):
            return False

        # needed to get the arrow keys normally used for the dialog navigation
        self.SetWindowStyle(style)

        if targetDate is not None:
            self.selected = targetDate
        else:
            self.selected = date.today()
        self.visible = self.selected

        self.lowdate = self.highdate = None

        self.ShowCurrentControls()

        # we need to set the position as well because the main control
        # position is not the same as the one specified in pos if we
        # have the controls above it
        self.SetBestSize(size)
        self.SetPosition(pos)

        # Since we don't paint the whole background make sure that the
        # platform will use the right one.
        self.SetBackgroundColour(self.GetBackgroundColour())

        return True
    
    def Destroy(self):
        # this is just a stub in case I need to deal with it later, otherwise it should be destroying self.staticMonth and self.staticYear
        super(PyMiniCalendar, self).Destroy()
        

    # set/get the current date
    # ------------------------

    def SetDate(self, date):

        retval = True

        sameMonth = (self.selected.month == date.month and
                     self.selected.year == date.year)

        if self.IsDateInRange(date):

            if sameMonth:
                self.ChangeDay(date)

            else:
                self.visible = self.selected = date
                self.GenerateEvent(EVT_MINI_CALENDAR_UPDATE_BUSY)

                self.Refresh()

                     
        self.userChangedYear = False

    def GetDate(self):
        return self.selected
        
    # set/get the range in which selection can occur
    # ---------------------------------------------

    def SetLowerDateLimit(self, lowdate):
        retval = True

        # XXX WTF is this crazy algebra
        if ( (lowdate is None) or (self.highdate is not None and
                                    lowdate <= self.highdate)):
            self.lowdate = lowdate

        else:
            retval = False
            
        return retval
    
    def GetLowerDateLimit(self):
        return self.lowdate

    def SetUpperDateLimit(self, highdate):
        retval = True

        # XXX WTF is this crazy algebra
        if ( (highdate is None) or (self.lowdate is not None and
                                highdate >= self.lowdate)):
            self.highdate = date

        else:
            retval = False
            
        return retval
        
    def GetUpperDateLimit(self):
        return self.highdate

    def SetDateRange(self, lowerdate=None, upperdate=None):
        retval = True

        # XXX WTF is this crazy algebra
        if ((lowerdate is None or (upperdate is not None and
                                  lowerdate <= upperdate)) and
            (upperdate is None or (lowerdate is not None and
                                   upperdate >= lowerdate))):
            self.lowdate = lowerdate
            self.highdate = upperdate
        else:
            retval = False

        return retval

    # calendar mode
    # -------------

    # some calendar styles can't be changed after the control creation by
    # just using SetWindowStyle() and Refresh() and the functions below
    # should be used instead for them

    # customization
    # -------------

    # header colours are used for painting the weekdays at the top
    
    def SetHeaderColours(self, colFg, colBg):
        self.colHeaderFg = colFg
        self.colHeaderBg = colBg

    def GetHeaderColourFg(self):
        return self.colHeaderFg
    def GetHeaderColourBg(self):
        return self.colHeaderBg

    # highlight colour is used for the currently selected date
    def SetHighlightColours(self, colFg, colBg):
        self.colHighlightFg = colFg
        self.colHighlightBg = colBg

    def GetHighlightColourFg(self):
        return self.colHighlightFg
    def GetHighlightColourBg(self):
        return self.colHighlightBg

    def SetBusy(self, busyDate, busy):
        startDate = self.GetStartDate()
        firstOfMonth = date(self.visible.year, self.visible.month, 1)

        # Only update months that are being displayed
        if (busyDate<firstOfMonth or
            busyDate >= MonthDelta(startDate, MONTHS_TO_DISPLAY)):
            return

        # Figure out which month this date is in
        monthDiff = busyDate.month - self.visible.month
        if monthDiff < 0:
            monthDiff += 12

        # Calculate the startDate of the proper month
        startDate = date(busyDate.year, busyDate.month, 1)
        if self.GetWindowStyle() & CAL_MONDAY_FIRST:
            startDate = PreviousWeekday(startDate, 0) # monday
        else:
            startDate = PreviousWeekday(startDate, 6) # sunday

        difference = (busyDate - startDate).days
        if difference < 0:
            days += 365

        difference += (monthDiff * DAYS_PER_WEEK * WEEKS_TO_DISPLAY)

        self.busyPercent[difference] = busy
        self.Refresh()
        

    # returns a tuple (CAL_HITTEST_XXX...) and then a date, and maybe a weekday
    
    # returns one of CAL_HITTEST_XXX constants and fills either date or wd
    # with the corresponding value (none for NOWHERE, the date for DAY and wd
    # for HEADER)
    def HitTest(self, pos):
        self.RecalcGeometry()
        
        # we need to find out if the hit is on left arrow, on month or
        # on right arrow

        # left arrow?
        y = pos.y

        if self.leftArrowRect.Inside(pos):
            lastMonth = MonthDelta(self.visible, -1)
            if self.IsDateInRange(lastMonth):
                return (CAL_HITTEST_DECMONTH, lastMonth)
            else:
                return (CAL_HITTEST_DECMONTH, self.GetLowerDateLimit())

        if self.rightArrowRect.Inside(pos):
            nextMonth = MonthDelta(self.visible, 1)
            if self.IsDateInRange(nextMonth):
                return (CAL_HITTEST_INCMONTH, nextMonth)
            else:
                return (CAL_HITTEST_INCMONTH, self.GetUpperDateLimit())

        if self.todayRect.Inside(pos):
            return (CAL_HITTEST_TODAY, date.today())

        # Header: Days
        wday = pos.x / self.widthCol
        initialHeight = self.todayHeight + self.heightPreview
        monthHeight = (self.rowOffset + 
                       WEEKS_TO_DISPLAY * self.heightRow +
                       EXTRA_MONTH_HEIGHT)
        headerHeight = self.rowOffset + EXTRA_MONTH_HEIGHT

        for month in xrange(MONTHS_TO_DISPLAY):
            if y < (month * monthHeight + initialHeight + headerHeight):
                if y > (month * monthHeight + initialHeight):
                    if wday == (DAYS_PER_WEEK-1):
                        return (CAL_HITTEST_HEADER, 0)
                    else:
                        return (CAL_HITTEST_HEADER, wday + 1)

        week = 0
        found = False
        lastWeek = False
        for month in xrange(MONTHS_TO_DISPLAY):
            if (y > (initialHeight + month * monthHeight + headerHeight) and
                y < (initialHeight + (month + 1) * monthHeight)):

                week = (y - initialHeight -
                        month * monthHeight -
                        headerHeight) / self.heightRow
                found = True
                if week == (WEEKS_TO_DISPLAY - 1):
                    lastWeek = True
                break

        if wday >= DAYS_PER_WEEK or not found:
            return (CAL_HITTEST_NOWHERE, None)

        clickDate = date(self.visible.year, self.visible.month, 1)
        clickDate = MonthDelta(clickDate, month)
        if self.GetWindowStyle() & CAL_MONDAY_FIRST:
            clickDate = PreviousWeekday(clickDate, 0)
        else:
            clickDate = PreviousWeekday(clickDate, 6)

        clickDate += timedelta(days=DAYS_PER_WEEK * week + wday)
        targetMonth = self.visible.month + month
        if targetMonth > 12:
            targetMonth -= 12

        if clickDate.month != targetMonth:
            return (CAL_HITTEST_NOWHERE, None)

        if self.IsDateShown(clickDate):

            if clickDate.month == self.visible.month:
                return (CAL_HITTEST_DAY, clickDate)
            else:
                return (CAL_HITTEST_SURROUNDING_WEEK, clickDate)

        else:
            return (CAL_HITTEST_NOWHERE, None)
        

    # implementation only from now on
    # -------------------------------

    # forward these functions to all subcontrols
    def Enable(self, enable):
        # XXX do we really need to even implement this function?
        # shouldn't child widgets hide themselves?
        if not super(PyMiniCalendar, self).Enable(enable):
            return False

        if self.GetMonthControl():
            self.GetMonthControl.Enable(enable)
            self.GetYearControl.Enable(enable)

        return True

    def Show(self, show):
        # XXX do we really need to even implement this function?
        # shouldn't child widgets hide themselves?
        if not super(PyMiniCalendar, self).Show(show):
            return False

        if self.GetMonthControl():
            self.GetMonthControl.Show(show)
            self.GetYearControl.Show(show)

        return True

    def GetDefaultAttributes(self):
        return self.GetClassDefaultAttributes(self.GetWindowVariant())

    @staticmethod
    def GetClassDefaultAttributes(variant):
        return wx.ListBox.GetClassDefaultAttributes(variant)

    # get the date from which we start drawing days
    def GetStartDate(self):
        
        # roll back to the beginning of the month
        startDate = date(self.visible.year, self.visible.month, 1)

        # now to back to the previous sun/mon
        if self.GetWindowStyle() & CAL_MONDAY_FIRST:
            targetDay = 0               # monday
        else:
            targetDay = 6               # sunday

        return PreviousWeekday(startDate, targetDay)

    # Get sizes of individual components
    def GetHeaderSize(self):
        self.RecalcGeometry()

        width = DAYS_PER_WEEK * self.widthCol
        height = self.todayHeight + self.heightPreview + VERT_MARGIN

        return wx.Size(width,height)

    def GetMonthSize(self):
        self.RecalcGeometry()

        width = DAYS_PER_WEEK * self.widthCol
        height = WEEKS_TO_DISPLAY * self.heightRow + self.rowOffset + EXTRA_MONTH_HEIGHT
        return wx.Size(width, height)
    
    # event handlers
    def OnMiniCalPaint(self, event):
        dc = wx.PaintDC(self)

        font = self.GetFont()

        if "__WXMAC__" in wx.PlatformInfo:
            font = wx.Font(font.GetPointSize() - 2, font.GetFamily(),
                              font.GetStyle(), font.GetWeight(), font.GetUnderlined(), font.GetFaceName(), font.GetEncoding())

        dc.SetFont(font)

        self.RecalcGeometry()

        y = 0

        # draw the preview portion
        y += self.heightPreview

        # draw the sequential month-selector
        dc.SetBackgroundMode(wx.TRANSPARENT)
        dc.SetTextForeground(wx.BLACK)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetPen(wx.Pen(wx.LIGHT_GREY, 1, wx.SOLID))
        #    dc.DrawLine(0, y, GetClientSize().x, y)
        dc.DrawLine(0, y + self.todayHeight, self.GetClientSize().x, y + self.todayHeight)
        buttonCoord = self.GetClientSize().x / 5
        dc.DrawLine(buttonCoord, y, buttonCoord, y + self.todayHeight)
        dc.DrawLine(buttonCoord * 4, y, buttonCoord * 4, y + self.todayHeight)

        # Get extent of today button
        self.normalFont = dc.GetFont()
        self.boldFont = wx.Font(self.normalFont.GetPointSize(), self.normalFont.GetFamily(),
                                self.normalFont.GetStyle(), wx.BOLD, self.normalFont.GetUnderlined(), 
                                self.normalFont.GetFaceName(), self.normalFont.GetEncoding())
        dc.SetFont(self.boldFont)
        todaytext = _(u"Today")
        (todayw, todayh) = dc.GetTextExtent(todaytext)

        # Draw today button
        self.todayRect = wx.Rect(buttonCoord, y, buttonCoord * 4, self.todayHeight)
        todayx = ((self.widthCol * DAYS_PER_WEEK) - todayw) / 2
        todayy = ((self.todayHeight - todayh) / 2) + y
        dc.DrawText(todaytext, todayx, todayy)
        dc.SetFont(self.normalFont)

        # calculate the "month-arrows"

        arrowheight = todayh - 5

        leftarrow = [wx.Point(0, arrowheight / 2),
                     wx.Point(arrowheight / 2, 0),
                     wx.Point(arrowheight / 2, arrowheight - 1)]

        rightarrow = [wx.Point(0, 0),
                      wx.Point(arrowheight / 2, arrowheight / 2),
                      wx.Point(0, arrowheight - 1)]

        # draw the "month-arrows"
        arrowy = (self.todayHeight - arrowheight) / 2 + y
        larrowx = (buttonCoord - (arrowheight / 2)) / 2
        rarrowx = (buttonCoord / 2) + buttonCoord * 4

        # Draw left arrow
        self.leftArrowRect = wx.Rect(0, y, buttonCoord - 1, self.todayHeight)
        dc.SetBrush(wx.Brush(wx.BLACK, wx.SOLID))
        dc.SetPen(wx.Pen(wx.BLACK, 1, wx.SOLID))
        dc.DrawPolygon(leftarrow, larrowx , arrowy, wx.WINDING_RULE)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)

        # Draw right arrow
        self.rightArrowRect = wx.Rect(buttonCoord * 4 + 1, y, buttonCoord - 1, self.todayHeight)
        dc.SetBrush(wx.Brush(wx.BLACK, wx.SOLID))
        dc.SetPen(wx.Pen(wx.BLACK, 1, wx.SOLID))
        dc.DrawPolygon(rightarrow, rarrowx , arrowy, wx.WINDING_RULE)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)

        y += self.todayHeight

        dateToDraw = self.visible
        dayPosition = 0
        for i in xrange(MONTHS_TO_DISPLAY):
            y = self.DrawMonth(dc, dateToDraw, y, dayPosition, True)
            dateToDraw = MonthDelta(dateToDraw, 1)
            dayPosition += DAYS_PER_WEEK * WEEKS_TO_DISPLAY


    def OnClick(self, event):
        (region, value) = self.HitTest(event.GetPosition())

        if region == CAL_HITTEST_DAY:
            date = value
            if self.IsDateInRange(date):
                self.ChangeDay(date)
                self.GenerateEvents(EVT_MINI_CALENDAR_DAY_CHANGED,
                                    EVT_MINI_CALENDAR_SEL_CHANGED)

        elif region == CAL_HITTEST_HEADER:
            event.Skip()

        elif region == CAL_HITTEST_TODAY:
            date = value
            self.SetDateAndNotify(date)

        elif region == CAL_HITTEST_SURROUNDING_WEEK:
            date = value
            self.SetVisibleDateAndNotify(date, False)
            # self.SetDateAndNotify(date)

        elif region in (CAL_HITTEST_DECMONTH, CAL_HITTEST_INCMONTH):
            date = value
            self.SetVisibleDate(date, True)

        elif region == CAL_HITTEST_NOWHERE:
            event.Skip()

        else:
            assert False, "Unknown hit region?"
                    

    def OnDClick(self, event):
        (region, value) = self.HitTest(event.GetPosition())

        if region == CAL_HITTEST_DAY:
            event.Skip()

        else:
            self.GenerateEvent(EVT_MINI_CALENDAR_DOUBLECLICKED)
            

    # override some base class virtuals
    def DoGetBestSize(self):
        self.RecalcGeometry()

        width = DAYS_PER_WEEK * self.widthCol
        height = (self.todayHeight + self.heightPreview + VERT_MARGIN +
                  MONTHS_TO_DISPLAY *
                  (WEEKS_TO_DISPLAY * self.heightRow +
                   self.rowOffset + EXTRA_MONTH_HEIGHT) + 15)

        if self.HasFlag(wx.BORDER_NONE):
            height += 6
            width += 4

        best = wx.Size(width, height)
        self.CacheBestSize(best)
        return best

    # I don't exactly know why we MUST override these, but otherwise
    # things don't relly lay out.
    def DoGetPosition(self):
        result = super(PyMiniCalendar, self).DoGetPosition()
        return result
    
    def DoGetSize(self):
        result = super(PyMiniCalendar, self).DoGetSize()
        return result
    
    def DoSetSize(self, x, y, width, height, sizeFlags):
        return super(PyMiniCalendar, self).DoSetSize(x,y,width,height,sizeFlags)
    
    def DoMoveWindow(self, x, y, width, height):
        return super(PyMiniCalendar, self).DoMoveWindow(x,y,width,height)
    
    def RecalcGeometry(self):
        """
        (re)calc self.widthCol and self.heightRow
        """
        dc = wx.ClientDC(self)

        font = self.GetFont()

        if "__WXMAC__" in wx.PlatformInfo:
            font = wx.Font(font.GetPointSize() - 2, font.GetFamily(),
                              font.GetStyle(), font.GetWeight(), font.GetUnderlined(), font.GetFaceName(), font.GetEncoding())
            
        dc.SetFont(font)

        # determine the column width (we assume that the widest digit
        # plus busy bar is wider than any weekday character (hopefully
        # in any language))
        self.widthCol = 0
        for day in xrange (1, 32):
            (self.heightRow, width) = dc.GetTextExtent(unicode(day))
            if width > self.widthCol:
                self.widthCol = width

        # leave some margins
        self.widthCol += 8
        self.heightRow += 6

        if self.GetWindowStyle() & CAL_SHOW_PREVIEW:
            self.heightPreview = NUMBER_TO_PREVIEW * self.heightRow
        else:
            self.heightPreview = 0

        self.rowOffset = self.heightRow * 2
        self.todayHeight = self.heightRow + 2

    def DrawMonth(self, dc, startDate, y, startDayPosition, highlightDate = False):
        """
        draw a single month
        return the updated value of y
        """
        dc.SetTextForeground(wx.BLACK);

        # Get extent of month-name + year
        headertext = startDate.strftime("%B %Y")
        dc.SetFont(self.boldFont)
        (monthw, monthh) = dc.GetTextExtent(headertext)

        # draw month-name centered above weekdays
        monthx = ((self.widthCol * DAYS_PER_WEEK) - monthw) / 2
        monthy = ((self.heightRow - monthh) / 2) + y + 3
        dc.DrawText(headertext, monthx,  monthy)
        dc.SetFont(self.normalFont)

        y += self.heightRow + EXTRA_MONTH_HEIGHT

        dc.SetPen(wx.Pen(wx.BLACK, 1, wx.SOLID))
        dc.DrawRectangle(0,y,DAYS_PER_WEEK*self.widthCol, self.heightRow)
        # draw the week day names
        if self.IsExposed(0, y, DAYS_PER_WEEK * self.widthCol, self.heightRow):
            dc.SetBackgroundMode(wx.TRANSPARENT)
            dc.SetTextForeground(self.colHeaderFg)
            dc.SetBrush(wx.Brush(self.colHeaderBg, wx.SOLID))
            dc.SetPen(wx.Pen(self.colHeaderBg, 1, wx.SOLID))

            # draw the background
            dc.DrawRectangle(0, y, self.GetClientSize().x, self.heightRow)

            startOnMonday = (self.GetWindowStyle() & CAL_MONDAY_FIRST) != 0
            
            for wd in xrange(DAYS_PER_WEEK):
                if startOnMonday:
                    if (wd == (DAYS_PER_WEEK - 1)):
                        n = 0
                    else:
                        wd + 1
                else:
                    n = wd
                    
                (dayw, dayh) = dc.GetTextExtent(self.weekdays[n])
                dc.DrawText(self.weekdays[n],
                            (wd*self.widthCol) + ((self.widthCol- dayw) / 2),
                            y) # center the day-name

        y += (self.heightRow - 1)
        
        weekDate = date(startDate.year, startDate.month, 1)
        if self.GetWindowStyle() & CAL_MONDAY_FIRST:
            weekDate = PreviousWeekDay(weekDate,0)   # monday
        else:
            weekDate = PreviousWeekday(weekDate,6)   # sunday

        mainColour = wx.Colour(0, 0, 0)
        lightColour = wx.Colour(255, 255, 255)
        highlightColour = wx.Colour(204, 204, 204)
        lineColour = wx.Colour(229, 229, 229)
        busyColour = wx.Colour(0, 0, 0)

        dc.SetTextForeground(mainColour)
        dc.SetTextForeground(wx.RED)
        for nWeek in xrange(1,WEEKS_TO_DISPLAY+1):
            # if the update region doesn't intersect this row, don't paint it
            if not self.IsExposed(0, y, DAYS_PER_WEEK * self.widthCol,
                              self.heightRow - 1):
                weekDate += timedelta(days=7)
                y += self.heightRow
                continue

            # don't draw last week if none of the days appear in the month
            if (nWeek == WEEKS_TO_DISPLAY and
                (weekDate.month != startDate.month or
                 not self.IsDateInRange(weekDate))):
                weekDate += timedelta(days=7)
                y += self.heightRow
                continue

            for wd in xrange(DAYS_PER_WEEK):

                dayPosition = startDayPosition + (nWeek - 1) * DAYS_PER_WEEK + wd
                if self.IsDateShown(weekDate):

                    dayStr = str(weekDate.day)
                    width, height = dc.GetTextExtent(dayStr)
                    
                    changedColours = False
                    changedFont = False
                    
                    x = wd * self.widthCol + (self.widthCol - width) / 2

                    if highlightDate:
                        # either highlight the selected week or the
                        # selected day depending upon the style
                        if (((self.GetWindowStyle() & CAL_HIGHLIGHT_WEEK) and
                             (self.GetWeek(weekDate, False) == self.GetWeek(self.selected, False))) or
                            (not (self.GetWindowStyle() & CAL_HIGHLIGHT_WEEK) and
                             (weekDate == self.selected))):

                            if wd == 0:
                                startX = SEPARATOR_MARGIN
                            else:
                                startX = wd * self.widthCol

                            endX = self.widthCol
                            if wd == ( DAYS_PER_WEEK - 1 ):
                                endX -= (SEPARATOR_MARGIN)

                            dc.SetTextBackground(highlightColour)
                            dc.SetBrush(wx.Brush(highlightColour, wx.SOLID))

                            if '__WXMAC__' in wx.PlatformInfo:
                                dc.SetPen(wx.TRANSPARENT_PEN)
                            else:
                                dc.SetPen(wx.Pen(highlightColour, 1, wx.SOLID))
                                
                            dc.DrawRectangle(startX, y, endX, self.heightRow) 

                            changedColours = True

                    # draw free/busy indicator
                    if self.GetWindowStyle() & CAL_SHOW_BUSY:
                        busyPercentage = self.GetBusy(dayPosition)
                        height = (self.heightRow - 8) * busyPercentage

                        dc.SetTextBackground(busyColour)
                        dc.SetBrush(wx.Brush(busyColour, wx.SOLID))

                        if '__WXMAC__' in wx.PlatformInfo:
                            dc.SetPen(wx.TRANSPARENT_PEN)
                        else:
                            dc.SetPen(wx.Pen(busyColour, 1, wx.SOLID))

                        dc.DrawRectangle(x-3, y + self.heightRow - height - 4, 2, height)
                        changedColours = True

                    if (weekDate.month != startDate.month or
                        not self.IsDateInRange(weekDate)):
                        # surrounding week or out-of-range
                        # draw "disabled"
                        dc.SetTextForeground(lightColour)
                        changedColours = True
                    else:
                        dc.SetBrush(wx.Brush(wx.BLACK, wx.SOLID))
                        dc.SetPen(wx.Pen(wx.BLACK, 1, wx.SOLID))

                        # today should be printed as bold
                        if weekDate == date.today():
                            dc.SetFont(self.boldFont)
                            dc.SetTextForeground(wx.BLACK)
                            changedFont = True
                            changedColours = True

                    dc.DrawText(dayStr, x, y + 1)

                    dc.SetBrush(wx.TRANSPARENT_BRUSH)

                    if changedColours:
                        dc.SetTextForeground(mainColour)
                        dc.SetTextBackground(self.GetBackgroundColour())

                    if changedFont:
                        dc.SetFont(self.normalFont)

                #else: just don't draw it
                weekDate += timedelta(days=1)

            # draw lines between each set of weeks
            if  nWeek <= WEEKS_TO_DISPLAY and nWeek != 1:
                pen = wx.Pen(lineColour, 2, wx.SOLID)
                pen.SetCap(wx.CAP_BUTT)
                dc.SetPen(pen)
                dc.DrawLine(SEPARATOR_MARGIN, y - 1,
                            DAYS_PER_WEEK * self.widthCol - SEPARATOR_MARGIN,
                            y - 1)
            y += self.heightRow
        return y

    def SetDateAndNotify(self, date):
        """
        set the date and send the notification
        """
        if self.SetDate(date):
            self.GenerateEvents(EVT_MINI_CALENDAR_YEAR_CHANGED,
                                EVT_MINI_CALENDAR_SEL_CHANGED)
            

    def SetVisibleDate(self, date, setVisible):

        sameMonth = (self.visible.month == date.month)
        sameYear  = (self.visible.year == date.year)

        if self.IsDateInRange(date):
            if sameMonth and sameYear:
                self.ChangeDay(date)
            else:

                if setVisible:
                    self.visible = date
                else:
                    self.selected = date

                self.GenerateEvent(EVT_MINI_CALENDAR_UPDATE_BUSY)
                
                # update the calendar
                self.Refresh()

        self.userChangedYear = False

        return True
                
    def SetVisibleDateAndNotify(self, newDate, setVisible):
        if setVisible:
            oldDate = self.visible
        else:
            oldDate = self.selected

        if newDate.year != oldDate.year:
            eventType = EVT_MINI_CALENDAR_YEAR_CHANGED
        elif newDate.month != oldDate.month:
            eventType = EVT_MINI_CALENDAR_MONTH_CHANGED
        elif newDate.day != oldDate.day:
            eventType = EVT_MINI_CALENDAR_DAY_CHANGED
        else:
            return

        if (self.SetVisibleDate(newDate, setVisible)):
            self.GenerateEvents(eventType, EVT_MINI_CALENDAR_SEL_CHANGED)

    def GetWeek(self, targetDate, useRelative=True):
        """
        get the week (row, in range 1..WEEKS_TO_DISPLAY) for the given date
        XXX some issues with monday/sunday first in the week
        """
        if useRelative:
            # week of the month
            if self.GetWindowStyle() & CAL_MONDAY_FIRST:
                return GetWeekOfMonth(targetDate, 0) # monday
            else:
                return GetWeekOfMonth(targetDate, 6) # sunday

        # week of the year
        if self.GetWindowStyle() & CAL_MONDAY_FIRST:
            targetDate = PreviousWeekday(targetDate, 0)
        else:
            targetDate = PreviousWeekday(targetDate, 6)
        (year, week, day) = targetDate.isocalendar()
        return week

    def IsDateShown(self, date):
        """
        is this date shown?
        """
        if not (self.GetWindowStyle() & CAL_SHOW_SURROUNDING_WEEKS):
            return date.month == self.visible.month
        
        return True

    def IsDateInRange(self, date):
        """
        is this date in the given range?
        """
        if self.lowdate is not None:
            lowvalid = date >= self.lowdate
        else:
            lowvalid = True

        if self.highdate is not None:
            highvalid = date <= self.highdate
        else:
            highvalid = True

        return lowvalid and highvalid

    def RefreshDate(self, date):
        """
        redraw the given date
        """
        self.RecalcGeometry()

        x = 0
        y = (self.heightRow * (self.GetWeek(date) - 1)) + self.todayHeight + EXTRA_MONTH_HEIGHT + self.rowOffset + self.heightPreview

        width = DAYS_PER_WEEK * self.widthCol
        height = self.heightRow

        rect = wx.Rect(x,y,width,height)
        # VZ: for some reason, the selected date seems to occupy more space under
        #     MSW - this is probably some bug in the font size calculations, but I
        #     don't know where exactly. This fix is ugly and leads to more
        #     refreshes than really needed, but without it the selected days
        #     leaves even more ugly underscores on screen.
        
        # MSW only: rect.Inflate(0, 1)

        self.RefreshRect(rect)

    def GetBusy(self, dayPosition):
        """
        get the busy state for the desired position
        """
        return self.busyPercent[dayPosition]
     
    def ChangeDay(self, date):
        """
        change the date inside the same month/year
        """
        if self.selected != date:
            # we need to refresh the row containing the old date and the one
            # containing the new one
            dateOld = self.selected
            self.visible = self.selected = date
            self.RefreshDate(dateOld)
            

            # if the date is in the same row, it was already drawn correctly
            if self.GetWeek(self.selected) != self.GetWeek(dateOld):
                self.RefreshDate(self.selected)

    def GenerateEvent(self, eventType):
        """
        generate the given calendar event(s)
        """
        event = PyMiniCalendarEvent(eventType.evtType[0])
        self.GetEventHandler().ProcessEvent(event)

    def GenerateEvents(self, type1, type2):
        self.GenerateEvent(type1)
        self.GenerateEvent(type2)

    def ShowCurrentControls(self):
        """
        show the correct controls
        """
        # XXX wow, no implementation at all!
        pass

    def GetMonthControl(self):
        """
        get the currently shown control for month/year
        """
        return self.staticMonth
    
    def GetYearControl(self):
        return self.staticYear

    # OnPaint helper-methods

    def HighlightRange(self, dc, fromdate, todate, pen, brush):
        """
        Highlight the [fromdate : todate] range using pen and brush
        """
        if todate >=fromdate:

            fd, fw = self.GetDateCoord(fromdate)
            td, tw = self.GetDateCoord(todate)

            if -1 not in (fd, fw, td, tw):
                # special case: interval 7 days or less not in same week
                # split in two seperate intervals
                tfd = fromdate + timedelta(days=DAYS_PER_WEEK - fd)
                ftd = tfd + timedelta(days=1)

                # draw seperately
                self.HighlightRange(pDC, fromdate, tfd, pen, brush);
                self.HighlightRange(pDC, ftd, todate, pen, brush);
                
            else:
                corners = []

                if fw == tw:
                    # simple case: same week
                    corners.append(wx.Point((fd - 1) * self.widthCol,
                                            fw * self.heightRow +
                                            self.rowOffset +
                                            self.heightPreview))
                    corners.append(wx.Point((fd - 1) * self.widthCol,
                                            ((fw + 1 ) * self.heightRow) +
                                            self.rowOffset +
                                            self.heightPreview))
                    corners.append(wx.Point(td * self.widthCol,
                                            ((tw + 1) * self.heightRow) +
                                            self.rowOffset +
                                            self.heightPreview))
                    corners.append(wx.Point(td * self.widthCol,
                                            tw * self.heightRow +
                                            self.rowOffset +
                                            self.heightPreview))
                else:
                    # "complex" polygon
                    corners.append(wx.Point((fd - 1) * self.widthCol,
                                            (fw * self.heightRow) +
                                            self.rowOffset +
                                            self.heightPreview))

                    if ( fd > 1 ):
                        corners.append(wx.Point((fd - 1) * self.widthCol,
                                                (fw + 1) * self.heightRow +
                                                self.rowOffset +
                                                self.heightPreview))
                        corners.append(wx.Point(0,
                                                (fw + 1) * self.heightRow +
                                                self.rowOffset +
                                                self.heightPreview))

                    corners.append(wx.Point(0,
                                            (tw + 1) * self.heightRow +
                                            self.rowOffset +
                                            self.heightPreview))
                    corners.append(wx.Point(td * self.widthCol,
                                            (tw + 1) * self.heightRow +
                                            self.rowOffset +
                                            self.heightPreview))

                    if td < DAYS_PER_WEEK:
                        corners.append(wx.Point(td * self.widthCol,
                                                tw * self.heightRow +
                                                self.rowOffset +
                                                self.heightPreview))
                        corners.append(wx.Point(DAYS_PER_WEEK * self.widthCol,
                                                tw * self.heightRow +
                                                self.rowOffset +
                                                self.heightPreview))

                    corners.append(wx.Point(DAYS_PER_WEEK * self.widthCol,
                                            (fw * self.heightRow) +
                                            self.rowOffset +
                                            self.heightPreview))


                # draw the polygon
                dc.SetBrush(brush)
                dc.SetPen(pen)
                dc.DrawPolygon(corners)
            
    
    def GetDateCoord(self, targetDate):
        """
        Get the "coordinates" for the date relative to the month
        currently displayed.  using (day, week): upper left coord is (1,
        1), lower right coord is (7, 6)
        
        if the date isn't visible (-1, -1) is put in (day, week) and
        False is returned
        """
        if self.IsDateShown(date):
            startOnMonday = ( self.GetWindowStyle() & wxCAL_MONDAY_FIRST ) != 0

            # Find day
            day = targetDate.weekday()

            # this is a quick, but ugly way to map date-based
            # weekdays to our (1..7) coordinate system
            if startOnMonday:
                day +=1                 # weekday is monday-based
            else:
                # weekday is kind of sunday-based starting at -1
                day += 2
                if day == DAYS_PER_WEEK + 1:
                    day = 0

            # XXX use timedelta, this is ugly
            targetmonth = targetDate.month + (12 * targetDate.year)
            thismonth = self.visible.month + (12 * self.visible.year)

            # Find week
            if targetmonth == thismonth:
                week = self.GetWeek(targetDate)
            elif targetmonth < thismonth:
                week = 1 # trivial
            else: # targetmonth > thismonth

                # get the datecoord of the last day in the month currently shown
                ldcm = (date(self.visible.year, self.visible.month+1,1) -
                        timedelta(days=1))
                (lastday, lastweek) = self.GetDateCoord(ldcm)

                span = targetDate - ldcm

                daysfromlast = span.days
                if daysfromlast + lastday > DAYS_PER_WEEK: # past week boundary
                    wholeweeks = (daysfromlast / DAYS_PER_WEEK)
                    week = wholeweeks + lastweek
                    if (daysfromlast - (DAYS_PER_WEEK * wholeweeks) + lastday) > DAYS_PER_WEEK:
                        week += 1
                else:
                    week = lastweek

        else:
            day = -1
            week = -1

        return day,week

