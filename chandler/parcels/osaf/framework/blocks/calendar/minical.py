#   Copyright (c) 2003-2006 Open Source Applications Foundation
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
    (week, maxday) = monthrange(newYear, newMonth)
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
        retval = True

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

        if '__WXMAC__' in wx.PlatformInfo:
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
        scale = self.blockItem.scale

        return wx.Size(width * scale, height * scale)

    def GetMonthSize(self):

        width = DAYS_PER_WEEK * self.widthCol
        height = (WEEKS_TO_DISPLAY * self.heightRow + self.rowOffset +
                  EXTRA_MONTH_HEIGHT)
        scale = self.blockItem.scale

        return wx.Size(width * scale, height * scale)

    def DrawLine(self, gc, x0, y0, x1, y1):

        return gc.DrawLines(((x0, y0), (x1, y1)))

    def DrawPolygon(self, gc, points, offsetx, offsety, rule):

        points = [(x + offsetx, y + offsety) for x, y in points]
        points.append(points[0])

        return gc.DrawLines(points, rule)
        
    def GetTextExtent(self, gc, dc, text):

        if '__WXGTK__' in wx.PlatformInfo:
            # on Linux
            # using dc as gc.GetTextExtent() is not yet implemented
            # using GetFullTextExtent() as gc.DrawText() is off by baseline
            w, h, descent, externalLeading = dc.GetFullTextExtent(text)
            return w, h, h - descent
        else:
            w, h = gc.GetTextExtent(text)
            return w, h, 0

    def DrawText(self, gc, text, x, y, brush, baseline):

        if '__WXGTK__' in wx.PlatformInfo:
            # on Linux gc.DrawText() is off by the baseline
            y += baseline

        gc.DrawText(text, x, y, brush)

    # event handlers
    def OnMiniCalSize(self, event):

        # force a full redraw as scaling might change (except on mac)
        if '__WXMAC__' not in wx.PlatformInfo:
            self.Refresh(False)

    def OnMiniCalPaint(self, event):

        size = self.GetClientSize()
        width, height = self.CalcGeometry() # the ideal, unscaled size

        if '__WXMSW__' in wx.PlatformInfo:
            dc = wx.BufferedPaintDC(self)
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            dc.Clear()
        else:
            dc = wx.PaintDC(self)
        
        gc = wx.GraphicsContext.Create(dc)

        scale = 1.0
        if size.x != width:
            scale = float(size.x) / float(width)
            if scale < 0.5:
                scale = 0.5
            gc.Scale(scale, scale)

        self.blockItem.scale = scale

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
        todayw, todayh, baseline = self.GetTextExtent(gc, dc, todaytext)

        # Draw today button
        self.todayRect = wx.Rect(buttonWidth, y,
                                 buttonWidth * 4, self.todayHeight)
        todayx = (buttonWidth * 5 - todayw) / 2
        todayy = y + (self.todayHeight - todayh) / 2

        self.DrawText(gc, todaytext, todayx, todayy,
                      gc.CreateBrush(wx.TRANSPARENT_BRUSH), baseline)

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

    def GetDeviceFont(self):
        font = self.GetFont()

        if "__WXMAC__" in wx.PlatformInfo:
            font = wx.Font(font.GetPointSize() - 2, font.GetFamily(),
                           font.GetStyle(), font.GetWeight(),
                           font.GetUnderlined(), font.GetFaceName(),
                           font.GetEncoding())
         
        return font

    def CalcGeometry(self):
        """
        return best, unscaled, width and size
        """

        width = DAYS_PER_WEEK * self.widthCol + 2 * SEPARATOR_MARGIN
        height = (self.todayHeight + VERT_MARGIN +
                  MONTHS_TO_DISPLAY *
                  (WEEKS_TO_DISPLAY * self.heightRow +
                   self.rowOffset + EXTRA_MONTH_HEIGHT) + 17)

        if "__WXMAC__" in wx.PlatformInfo:
            width += 4
        elif '__WXMSW__' in wx.PlatformInfo:
            width += 2
        
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
        monthw, monthh, baseline = self.GetTextExtent(gc, dc, headertext)

        # draw month-name centered above weekdays
        monthx = (clientWidth - monthw) / 2
        monthy = ((self.heightRow - monthh) / 2) + y + 3
        self.DrawText(gc, headertext, monthx,  monthy, transparentBrush,
                      baseline)

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
                dayw, dayh, baseline = self.GetTextExtent(gc, dc, 
                                                          self.weekdays[n+1])
                self.DrawText(gc, self.weekdays[n+1],
                              (wd*self.widthCol) + ((self.widthCol- dayw) / 2),
                              y, # center the day-name
                              transparentBrush, baseline)

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
                width, height, baseline = self.GetTextExtent(gc, dc, dayStr)

                columnStart = SEPARATOR_MARGIN + weekDay * self.widthCol
                x = columnStart + (self.widthCol - width) / 2

                if highlightDate:
                    # either highlight the selected week or the
                    # selected day depending upon the style
                    highlightWeek = (self.GetWindowStyle() &
                                     CAL_HIGHLIGHT_WEEK) != 0

                    if (self.hoverDate == weekDate or
                        # only highlight days that fall in the current month
                        (weekDate.month == startDate.month and
                         # highlighting week and the week we are drawing matches
                         ((highlightWeek and
                           self.CompareWeeks(weekDate, self.selectedDate)) or 
                         # highlighting a single day
                          (not highlightWeek and
                           weekDate == self.selectedDate)))):

                        startX = columnStart
                        width = self.widthCol

                        gc.SetFont(highlightFont)
                        gc.SetBrush(self.highlightColourBrush)

                        if '__WXMAC__' in wx.PlatformInfo:
                            gc.SetPen(wx.TRANSPARENT_PEN)
                        else:
                            gc.SetPen(self.highlightColourPen)

                        gc.DrawRectangle(startX, y, width, self.heightRow) 

                # draw free/busy indicator
                if weekDate.month == startDate.month:
                    busyPercentage = self.GetBusy(weekDate)
                    if '__WXMAC__' in wx.PlatformInfo:
                        YAdjust = 7
                    else:
                        YAdjust = 6
                    height = (self.heightRow - YAdjust) * busyPercentage

                    gc.SetBrush(self.busyColourBrush)

                    if '__WXMAC__' in wx.PlatformInfo:
                        gc.SetPen(wx.TRANSPARENT_PEN)
                    else:
                        gc.SetPen(self.busyColourPen)

                    gc.DrawRectangle(columnStart + 1,
                                     y + self.heightRow - height - 1, 2, height)

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

                if '__WXMAC__' in wx.PlatformInfo:
                    YAdjust = 2
                else:
                    YAdjust = 1
                self.DrawText(gc, dayStr, x, y + YAdjust, wx.NullGraphicsBrush,
                              baseline)

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
        dayAdjust = (self.firstDayOfWeek - 1) - (targetDate.weekday() + 1)
        if dayAdjust > 0:
            dayAdjust -= 7
        elif dayAdjust == -7:
            dayAdjust = 0

        return targetDate + timedelta(days=dayAdjust)

    def GetWeekOfMonth(self, dt):
        """
        there may be issues with monday/sunday first day of week
        """
        week = self.FirstDayOfWeek(dt).weekday()
        firstWeek = date(dt.year, dt.month, 1).weekday()

        return week - firstWeek


    def GetWeek(self, targetDate, useRelative=True):
        """
        get the week (row, in range 1..WEEKS_TO_DISPLAY) for the given date
        """
        # week of the month
        if useRelative:
            return self.GetWeekOfMonth(targetDate)

        # week of the year
        targetDate = self.FirstDayOfWeek(targetDate)
        year, week, day = targetDate.isocalendar()

        return week

    def CompareWeeks(self, date1, date2):

        d1w1 = self.FirstDayOfWeek(date1).isocalendar()[:2]
        d2w2 = self.FirstDayOfWeek(date2).isocalendar()[:2]
        return d1w1 == d2w2

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

        rect = wx.Rect(x,y,width,height)
        # VZ: for some reason, the selected date seems to occupy more
        # space under MSW - this is probably some bug in the font size
        # calculations, but I don't know where exactly. This fix is
        # ugly and leads to more refreshes than really needed, but
        # without it the selected days leaves even more ugly
        # underscores on screen.

        if '__WXMSW__' in wx.PlatformInfo:
            rect.Inflate(0, 1)

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

