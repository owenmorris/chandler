#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import wx
from i18n import ChandlerMessageFactory as _
from PyICU import DateFormatSymbols, GregorianCalendar
from CalendarUtility import getCalendarRange
from datetime import date, timedelta
from calendar import monthrange

VERT_MARGIN = 5
EXTRA_MONTH_HEIGHT = 4                  # space between month title and days
SEPARATOR_MARGIN = 3                    # left and right margins

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

CAL_HIGHLIGHT_WEEK         = 0x0008 # select an entire week at a time
CAL_HIGHLIGHT_MULTI_WEEK   = 0x0010 # select multiple weeks
if wx.Platform == "__WXMAC__":
    WIDTH_CORRECTION = 4
    Y_ADJUSTMENT_BIG = 7
    Y_ADJUSTMENT_SMALL = 2
elif wx.Platform == "__WXMSW__":
    WIDTH_CORRECTION = 2
    Y_ADJUSTMENT_BIG = 6
    Y_ADJUSTMENT_SMALL = 1
else:
    WIDTH_CORRECTION = 0
    Y_ADJUSTMENT_BIG = 6
    Y_ADJUSTMENT_SMALL = 1


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
    maxday = monthrange(newYear, newMonth)[1]
    day = min(maxday, dt.day)
    return date(newYear, newMonth, day)
    

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

        # date
        self.selectedDate = None
        self.firstVisibleDate = None

        self.lowerDateLimit = None
        self.upperDateLimit = None

        # colors
        self.colHighlightFg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
        self.colHighlightBg = wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        self.colHeaderFg = wx.BLACK
        self.colHeaderBgPen = wx.WHITE_PEN
        self.colHeaderBgBrush = wx.WHITE_BRUSH

        self.mainColour = wx.Colour(0, 0, 0)
        self.lightColour = wx.Colour(255, 255, 255)
        self.highlightColour = wx.Colour(204, 204, 204)
        self.highlightColourBrush = wx.Brush(self.highlightColour)
        self.highlightColourPen = wx.Pen(self.highlightColour)
        
        lineColour = wx.Colour(229, 229, 229)
        self.lineColourPen = wx.Pen(lineColour, 2)
        self.lineColourPen.SetCap(wx.CAP_BUTT)
        
        self.busyColour = wx.Colour(127, 191, 255)
        self.busyColourBrush = wx.Brush(self.busyColour)
        self.busyColourPen = wx.Pen(self.busyColour)


        self.widthCol = 0
        self.heightRow = 0

        dateFormatSymbols = DateFormatSymbols()

        self.months = dateFormatSymbols.getMonths()
        
        # this is a 1-based array as entry [0] is an empty string
        self.weekdays = [unicode(d) for d in
                         dateFormatSymbols.getWeekdays(DateFormatSymbols.STANDALONE,
                                                       DateFormatSymbols.NARROW)]
        self.firstDayOfWeek = GregorianCalendar().getFirstDayOfWeek()
        
        self.busyPercent = {}
                
        self.hoverDate = None

        self.rowOffset = 0
        self.todayHeight = 0

        self.leftArrowRect = None
        self.rightArrowRect = None
        self.todayRect = None

        self.lineAboveToday = False

        self.Bind(wx.EVT_PAINT, self.OnMiniCalPaint)
        if wx.Platform != "__WXMAC__":
            self.Bind(wx.EVT_SIZE, self.OnMiniCalSize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClick)
        
    def Create(self, parent, id=-1, pos=wx.DefaultPosition,
               size=wx.DefaultSize, style=0, name="PyMiniCalendar", targetDate=None):
        # needed to get the arrow keys normally used for the dialog navigation
        self.SetWindowStyle(style)

        if targetDate is not None:
            self.selectedDate = targetDate
        else:
            self.selectedDate = date.today()
        self.firstVisibleDate = self.selectedDate

        self.lowerDateLimit = self.upperDateLimit = None

        # we need to set the position as well because the main control
        # position is not the same as the one specified in pos if we
        # have the controls above it
        self.SetBestSize(size)
        self.SetPosition(pos)

        # Since we don't paint the whole background make sure that the
        # platform will use the right one.
        self.SetBackgroundColour(wx.WHITE)

        self.CalcGeometry()

        return True
    

    # set/get the current date
    # ------------------------

    def SetDate(self, date):

        sameMonth = (self.selectedDate.month == date.month and
                     self.selectedDate.year == date.year)

        if self.IsDateInRange(date):

            if sameMonth:
                self.ChangeDay(date)

            else:
                self.firstVisibleDate = self.selectedDate = date
                self.GenerateEvents(EVT_MINI_CALENDAR_UPDATE_BUSY)

                self.Refresh()
                     
    def GetDate(self):
        return self.selectedDate
        
    # set/get the range in which selection can occur
    # ---------------------------------------------

    def SetLowerDateLimit(self, lowdate):
        # XXX WTF is this crazy algebra
        if ((lowdate is None) or (self.upperDateLimit is not None and
                                  lowdate <= self.upperDateLimit)):
            self.lowerDateLimit = lowdate
            return True

        return False
    
    def SetUpperDateLimit(self, highdate):

        # XXX WTF is this crazy algebra
        if ((highdate is None) or (self.lowerDateLimit is not None and
                                   highdate >= self.lowerDateLimit)):
            self.upperDateLimit = date
            return True

        return False
        
    def SetDateRange(self, lowerdate=None, upperdate=None):

        # XXX WTF is this crazy algebra
        if ((lowerdate is None or (upperdate is not None and
                                   lowerdate <= upperdate)) and
            (upperdate is None or (lowerdate is not None and
                                   upperdate >= lowerdate))):
            self.lowerDateLimit = lowerdate
            self.upperDateLimit = upperdate
            return True

        return False

    def SetBusy(self, busyDate, busy):
        self.busyPercent[busyDate] = busy

    # returns a tuple (CAL_HITTEST_XXX...) and then a date, and maybe a weekday
    # returns one of CAL_HITTEST_XXX constants and fills either date or wd
    # with the corresponding value (none for NOWHERE, the date for DAY and wd
    # for HEADER)
    def HitTest(self, pos):
        
        # we need to find out if the hit is on left arrow, on month or
        # on right arrow

        if wx.Platform == '__WXMAC__':
            x, y = self.transform.TransformPoint(pos.x, self.yOffset - pos.y)
        else:
            x, y = self.transform.TransformPoint(pos.x, pos.y)
        pos = wx.Point(int(round(x)), int(round(y)))
        x, y = pos.x, pos.y

        # left arrow?
        if self.leftArrowRect.Inside(pos):
            lastMonth = MonthDelta(self.firstVisibleDate, -1)
            if self.IsDateInRange(lastMonth):
                return (CAL_HITTEST_DECMONTH, lastMonth)
            else:
                return (CAL_HITTEST_DECMONTH, self.lowerDateLimit)

        # right arrow?
        if self.rightArrowRect.Inside(pos):
            nextMonth = MonthDelta(self.firstVisibleDate, 1)
            if self.IsDateInRange(nextMonth):
                return (CAL_HITTEST_INCMONTH, nextMonth)
            else:
                return (CAL_HITTEST_INCMONTH, self.upperDateLimit)

        if self.todayRect.Inside(pos):
            return (CAL_HITTEST_TODAY, date.today())

        # Header: Days
        wday = pos.x / self.widthCol
        initialHeight = self.todayHeight
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
        #lastWeek = False
        for month in xrange(MONTHS_TO_DISPLAY):
            if (y > (initialHeight + month * monthHeight + headerHeight) and
                y < (initialHeight + (month + 1) * monthHeight)):

                week = (y - initialHeight -
                        month * monthHeight -
                        headerHeight) / self.heightRow
                found = True
                #if week == (WEEKS_TO_DISPLAY - 1):
                #    lastWeek = True
                break

        if wday >= DAYS_PER_WEEK or not found:
            return (CAL_HITTEST_NOWHERE, None)

        clickDate = date(self.firstVisibleDate.year, self.firstVisibleDate.month, 1)
        clickDate = MonthDelta(clickDate, month)
        clickDate = self.FirstDayOfWeek(clickDate)

        clickDate += timedelta(days=DAYS_PER_WEEK * week + wday)
        targetMonth = self.firstVisibleDate.month + month
        if targetMonth > 12:
            targetMonth -= 12

        if clickDate.month != targetMonth:
            return (CAL_HITTEST_NOWHERE, None)

        if clickDate.month == self.firstVisibleDate.month:
            return (CAL_HITTEST_DAY, clickDate)
        else:
            return (CAL_HITTEST_SURROUNDING_WEEK, clickDate)


    # get the date from which we start drawing days
    def GetStartDate(self):
        
        # roll back to the beginning of the month
        startDate = date(self.firstVisibleDate.year, self.firstVisibleDate.month, 1)

        # now to back to the beginning of the week
        return self.FirstDayOfWeek(startDate)

    # Get sizes of individual components
    def GetHeaderSize(self):

        width = DAYS_PER_WEEK * self.widthCol
        height = self.todayHeight + VERT_MARGIN
        scale = self.calculateScale()

        return wx.Size(width * scale, height * scale)

    def GetMonthSize(self):

        width = DAYS_PER_WEEK * self.widthCol
        height = (WEEKS_TO_DISPLAY * self.heightRow + self.rowOffset +
                  EXTRA_MONTH_HEIGHT)
        scale = self.calculateScale()

        return wx.Size(width * scale, height * scale)

    def DrawLine(self, gc, x0, y0, x1, y1):

        return gc.DrawLines(((x0, y0), (x1, y1)))

    def DrawPolygon(self, gc, points, offsetx, offsety, rule):

        points = [(x + offsetx, y + offsety) for x, y in points]
        points.append(points[0])

        return gc.DrawLines(points, rule)
        
    # event handlers
    if wx.Platform != "__WXMAC__":
        def OnMiniCalSize(self, event):    
            # force a full redraw as scaling might change (except on mac)
            self.Refresh(False)

    def calculateScale (self):
        size = self.GetClientSize()
        width = self.CalcGeometry()[0] # the ideal, unscaled size
        scale = float(size.x) / float(width)
        return scale if scale > 0.5 else 0.5

    def OnMiniCalPaint(self, event):

        width, height = self.CalcGeometry() # the ideal, unscaled size

        if wx.Platform == "__WXMSW__":
            dc = wx.BufferedPaintDC(self)
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            dc.Clear()
        else:
            dc = wx.PaintDC(self)
        
        scale = self.calculateScale()

        gc = wx.GraphicsContext.Create(dc)
        gc.Scale(scale, scale)

        transform = gc.GetTransform()
        self.transform = gc.CreateMatrix(*transform.Get())
        self.yOffset = transform.Get()[-1]  # for hit tests on Mac
        self.transform.Invert()

        font = self.GetDeviceFont()
        boldFont = wx.Font(font.GetPointSize(), font.GetFamily(),
                           font.GetStyle(), wx.BOLD, font.GetUnderlined(), 
                           font.GetFaceName(), font.GetEncoding())
        y = 0

        # draw the sequential month-selector
        gc.SetBrush(wx.TRANSPARENT_BRUSH)
        gc.SetPen(wx.LIGHT_GREY_PEN)
        if self.lineAboveToday:
            self.DrawLine(gc, 0, y, width, y)
        self.DrawLine(gc, 0, y + self.todayHeight,
                          width, y + self.todayHeight)
        buttonWidth = width / 5
        self.DrawLine(gc, buttonWidth, y,
                          buttonWidth, y + self.todayHeight)
        self.DrawLine(gc, buttonWidth * 4, y, 
                          buttonWidth * 4, y + self.todayHeight)

        # Get extent of today button
        todaytext = _(u"Today")
        gc.SetFont(gc.CreateFont(boldFont, wx.BLACK))
        todayw, todayh = gc.GetTextExtent(todaytext)

        # Draw today button
        self.todayRect = wx.Rect(buttonWidth, y,
                                 buttonWidth * 4, self.todayHeight)
        todayx = (buttonWidth * 5 - todayw) / 2
        todayy = y + (self.todayHeight - todayh) / 2

        gc.DrawText(todaytext, todayx, todayy,
                    gc.CreateBrush(wx.TRANSPARENT_BRUSH))

        # calculate month arrows
        arrowheight = todayh - 5

        leftarrow = [(0, arrowheight / 2),
                     (arrowheight / 2, 0),
                     (arrowheight / 2, arrowheight - 1)]
        rightarrow = [(0, 0),
                      (arrowheight / 2, arrowheight / 2),
                      (0, arrowheight - 1)]

        # draw month arrows
        arrowy = (self.todayHeight - arrowheight) / 2 + y
        larrowx = (buttonWidth - (arrowheight / 2)) / 2
        rarrowx = (buttonWidth / 2) + buttonWidth * 4

        self.leftArrowRect = wx.Rect(0, y, buttonWidth - 1,
                                     self.todayHeight)
        self.rightArrowRect = wx.Rect(buttonWidth * 4 + 1, y, buttonWidth - 1,
                                      self.todayHeight)

        pen = wx.Pen(wx.BLACK);
        pen.SetJoin(wx.JOIN_MITER)
        gc.SetPen(pen)
        gc.SetBrush(wx.BLACK_BRUSH)

        self.DrawPolygon(gc, leftarrow, larrowx, arrowy, wx.WINDING_RULE)
        self.DrawPolygon(gc, rightarrow, rarrowx, arrowy, wx.WINDING_RULE)

        y += self.todayHeight

        dateToDraw = self.firstVisibleDate
        for i in xrange(MONTHS_TO_DISPLAY):
            y = self.DrawMonth(gc, dc, dateToDraw, y, True, font, boldFont,
                               width, height, transform)
            dateToDraw = MonthDelta(dateToDraw, 1)


    def OnClick(self, event):
        (region, value) = self.HitTest(event.GetPosition())

        if region == CAL_HITTEST_DAY:
            if self.IsDateInRange(value):
                self.ChangeDay(value)
                self.GenerateEvents(EVT_MINI_CALENDAR_DAY_CHANGED,
                                    EVT_MINI_CALENDAR_SEL_CHANGED)

        elif region == CAL_HITTEST_HEADER:
            event.Skip()

        elif region == CAL_HITTEST_TODAY:
            self.SetDateAndNotify(value)
            self.SetVisibleDateAndNotify(value, True)


        elif region == CAL_HITTEST_SURROUNDING_WEEK:
            self.SetVisibleDateAndNotify(value, False)

        elif region in (CAL_HITTEST_DECMONTH, CAL_HITTEST_INCMONTH):
            self.SetVisibleDate(value, True)

        elif region == CAL_HITTEST_NOWHERE:
            event.Skip()

        else:
            assert False, "Unknown hit region?"
                    

    def OnDClick(self, event):
        #(region, value) = self.HitTest(event.GetPosition())

        #if region == CAL_HITTEST_DAY:
            #event.Skip()

        #else:
        # it's not clear why one would want to avoid propagating the double
        # click if it hit a day, so just propagate all doubleclicks
        self.GenerateEvents(EVT_MINI_CALENDAR_DOUBLECLICKED)
            

    # override some base class virtuals
    def DoGetBestSize(self):

        dc = wx.ClientDC(self)
        font = self.GetDeviceFont()
        dc.SetFont(font)

        # determine the column width (we assume that the widest digit
        # plus busy bar is wider than any weekday character (hopefully
        # in any language))
        self.widthCol = 0
        for day in xrange(1, 32):
            (self.heightRow, width) = dc.GetTextExtent(unicode(day))
            if width > self.widthCol:
                self.widthCol = width

        # leave some margins
        self.widthCol += 8
        self.heightRow += 6

        self.rowOffset = self.heightRow * 2
        self.todayHeight = self.heightRow + 2

        width, height = self.CalcGeometry()
        best = wx.Size(width, height)
        self.CacheBestSize(best)

        return best

    if wx.Platform == '__WXMAC__':
        def GetDeviceFont(self):
            font = self.GetFont()
    
            font = wx.Font(font.GetPointSize() - 2, font.GetFamily(),
                           font.GetStyle(), font.GetWeight(),
                           font.GetUnderlined(), font.GetFaceName(),
                           font.GetEncoding())
             
            return font
    else:
        def GetDeviceFont(self):
            return self.GetFont()
        
    def CalcGeometry(self):
        """
        return best, unscaled, width and size
        """

        width = DAYS_PER_WEEK * self.widthCol + 2 * SEPARATOR_MARGIN + WIDTH_CORRECTION
        height = (self.todayHeight + VERT_MARGIN +
                  MONTHS_TO_DISPLAY *
                  (WEEKS_TO_DISPLAY * self.heightRow +
                   self.rowOffset + EXTRA_MONTH_HEIGHT) + 17)

        return width, height

    def IsExposed(self, x, y, w, h, transform=None):

        if transform is not None:
            x, y = transform.TransformPoint(x, y)
            w, h = transform.TransformPoint(w, h)

        return super(PyMiniCalendar, self).IsExposed(x, y, w, h)

    def DrawMonth(self, gc, dc, startDate, y, highlightDate, font, boldFont,
                  clientWidth, clientHeight, transform):
        """
        draw a single month
        return the updated value of y
        """

        mainFont = gc.CreateFont(font, self.mainColour)
        highlightFont = gc.CreateFont(font, self.highlightColour)
        lightFont = gc.CreateFont(font, self.lightColour)
        blackFont = gc.CreateFont(boldFont, wx.BLACK)
        transparentBrush = gc.CreateBrush(wx.TRANSPARENT_BRUSH)

        # Get extent of month-name + year
        headertext = _(u'%(currentMonth)s %(currentYear)d') % {
            'currentMonth' : self.months[startDate.month-1],
            'currentYear' : startDate.year }
        gc.SetFont(blackFont)
        monthw, monthh = gc.GetTextExtent(headertext)

        # draw month-name centered above weekdays
        monthx = (clientWidth - monthw) / 2
        monthy = ((self.heightRow - monthh) / 2) + y + 3
        gc.DrawText(headertext, monthx,  monthy, transparentBrush)

        y += self.heightRow + EXTRA_MONTH_HEIGHT

        # draw the week day names
        if self.IsExposed(0, y, DAYS_PER_WEEK * self.widthCol, self.heightRow,
                          transform):
            gc.SetFont(gc.CreateFont(font, self.colHeaderFg))
            gc.SetBrush(self.colHeaderBgBrush)
            gc.SetPen(self.colHeaderBgPen)

            # draw the background
            gc.DrawRectangle(0, y-1, clientWidth, self.heightRow+2)

            for wd in xrange(DAYS_PER_WEEK):
                n = (wd + self.firstDayOfWeek - 1) % DAYS_PER_WEEK
                dayw = gc.GetTextExtent(self.weekdays[n+1])[0]
                gc.DrawText(self.weekdays[n+1],
                            (wd*self.widthCol) + SEPARATOR_MARGIN +
                            ((self.widthCol- dayw) / 2), # center the day-name
                            y, 
                            transparentBrush)

        y += self.heightRow - 1
        
        weekDate = date(startDate.year, startDate.month, 1)
        weekDate = self.FirstDayOfWeek(weekDate)

        gc.SetFont(mainFont)
        
        for nWeek in xrange(1, WEEKS_TO_DISPLAY+1):
            # if the update region doesn't intersect this row, don't paint it
            if not self.IsExposed(0, y, DAYS_PER_WEEK * self.widthCol,
                                  self.heightRow - 1, transform):
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

            for weekDay in xrange(DAYS_PER_WEEK):

                dayStr = str(weekDate.day)
                width = gc.GetTextExtent(dayStr)[0]

                columnStart = SEPARATOR_MARGIN + weekDay * self.widthCol
                x = columnStart + (self.widthCol - width) / 2

                if highlightDate:
                    # highlight the selected week, month or day depending on
                    # the style
                    style = self.GetWindowStyle()
                    highlightWeek  = style & CAL_HIGHLIGHT_WEEK
                    highlightMonth = style & CAL_HIGHLIGHT_MULTI_WEEK
                    highlightDay = not highlightWeek and not highlightMonth

                    if (self.hoverDate == weekDate or
                        # only highlight days that fall in the current month
                        (weekDate.month == startDate.month and
                         # highlighting week and the week we are drawing matches
                         ((highlightWeek and self.InWeek(weekDate)) or 
                         # highlighting a single day
                          (highlightDay and weekDate == self.selectedDate) or
                         # highlighting month
                          (highlightMonth and self.InMonth(weekDate))))):

                        startX = columnStart + 1
                        width = self.widthCol

                        gc.SetFont(highlightFont)
                        gc.SetBrush(self.highlightColourBrush)
                        gc.SetPen(self.highlightColourPen)

                        gc.DrawRectangle(startX, y, width, self.heightRow - 2) 

                # draw free/busy indicator
                if weekDate.month == startDate.month:
                    busyPercentage = self.GetBusy(weekDate)
                    assert busyPercentage >= 0
                    if busyPercentage > 0:
                        height = (self.heightRow - Y_ADJUSTMENT_BIG) * busyPercentage
                        gc.SetBrush(self.busyColourBrush)
                        gc.SetPen(wx.TRANSPARENT_PEN)
                        gc.DrawRectangle(columnStart + 1,
                                         y + self.heightRow - height - 2, 2, height)

                if (weekDate.month != startDate.month or
                    not self.IsDateInRange(weekDate)):
                    # surrounding week or out-of-range
                    # draw "disabled"
                    gc.SetFont(lightFont)
                else:
                    gc.SetBrush(wx.BLACK_BRUSH)
                    gc.SetPen(wx.BLACK_PEN)

                    # today should be printed as bold
                    if weekDate == date.today():
                        gc.SetFont(blackFont)
                    else:
                        gc.SetFont(mainFont)

                gc.DrawText(dayStr, x, y + Y_ADJUSTMENT_SMALL,
                            wx.NullGraphicsBrush)

                weekDate += timedelta(days=1)

            # draw lines between each set of weeks
            if nWeek <= WEEKS_TO_DISPLAY and nWeek != 1:
                gc.SetPen(self.lineColourPen)
                self.DrawLine(gc, SEPARATOR_MARGIN, y - 1,
                              clientWidth - SEPARATOR_MARGIN,
                              y - 1)
            y += self.heightRow

        return y

    def SetDateAndNotify(self, date):
        """
        set the date and send the notification
        """
        self.SetDate(date)
        self.GenerateEvents(EVT_MINI_CALENDAR_YEAR_CHANGED,
                            EVT_MINI_CALENDAR_SEL_CHANGED)

    def SetVisibleDate(self, date, setVisible):

        sameMonth = (self.firstVisibleDate.month == date.month)
        sameYear  = (self.firstVisibleDate.year == date.year)

        if self.IsDateInRange(date):
            if sameMonth and sameYear:
                self.ChangeDay(date)
            else:

                if setVisible:
                    self.firstVisibleDate = date
                else:
                    self.selectedDate = date

                self.GenerateEvents(EVT_MINI_CALENDAR_UPDATE_BUSY)
                
                # update the calendar
                self.Refresh(False)
                
    def SetVisibleDateAndNotify(self, newDate, setVisible):
        if setVisible:
            oldDate = self.firstVisibleDate
        else:
            oldDate = self.selectedDate

        if newDate.year != oldDate.year:
            eventType = EVT_MINI_CALENDAR_YEAR_CHANGED
        elif newDate.month != oldDate.month:
            eventType = EVT_MINI_CALENDAR_MONTH_CHANGED
        elif newDate.day != oldDate.day:
            eventType = EVT_MINI_CALENDAR_DAY_CHANGED
        else:
            return

        self.SetVisibleDate(newDate, setVisible)
        self.GenerateEvents(eventType, EVT_MINI_CALENDAR_SEL_CHANGED)


    def FirstDayOfWeek(self, targetDate):
        """
        rewind the selected date to the previous specified date
        
        Unfortunately, firstDayOfWeek has sunday = 1, and weekday()
        has monday=0, so they're actually off by 2!
        """
        return getCalendarRange(targetDate, 'week', self.firstDayOfWeek)[0]

    def GetWeek(self, dt):
        """
        Get the row associated with the given date.
        """
        weekStart = self.FirstDayOfWeek(dt)
        if weekStart.month != dt.month:
            return 1
        else:
            return (weekStart.day - 2)/ 7 + 2

    def InWeek(self, dt):
        start, end = getCalendarRange(self.selectedDate, 'week',
                                      self.firstDayOfWeek)
        return start <= dt < end

    def InMonth(self, dt):
        start, end = getCalendarRange(self.selectedDate, 'multiweek',
                                      self.firstDayOfWeek)
        return start <= dt < end
        

    def IsDateInRange(self, date):
        """
        is this date in the given range?
        """
        if self.lowerDateLimit is not None:
            lowvalid = date >= self.lowerDateLimit
        else:
            lowvalid = True

        if self.upperDateLimit is not None:
            highvalid = date <= self.upperDateLimit
        else:
            highvalid = True

        return lowvalid and highvalid

    def RefreshDate(self, date):
        """
        redraw the given date
        """

        x = 0
        y = (self.heightRow * (self.GetWeek(date) - 1) +
             self.todayHeight + EXTRA_MONTH_HEIGHT + self.rowOffset)

        width = DAYS_PER_WEEK * self.widthCol
        height = self.heightRow

        rect = wx.Rect(x, y, width, height)
        self.RefreshRect(rect, False)

    def GetBusy(self, date):
        """
        get the busy state for the desired position
        """
        return self.busyPercent.get(date, 0.0)
     
    def ChangeDay(self, date):
        """
        change the date inside the same month/year
        """
        if self.selectedDate != date:
            # we need to refresh the row containing the old date and the one
            # containing the new one
            dateOld = self.selectedDate
            self.firstVisibleDate = self.selectedDate = date
            self.RefreshDate(dateOld)
            

            # if the date is in the same row, it was already drawn correctly
            if self.GetWeek(self.selectedDate) != self.GetWeek(dateOld):
                self.RefreshDate(self.selectedDate)

    def GenerateEvents(self, *events):
        """
        generate the given calendar event(s)
        """
        for evt in events:
            event = wx.PyCommandEvent(evt.evtType[0])
            self.GetEventHandler().ProcessEvent(event)

