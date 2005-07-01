########## thsi file is workspace for the refactoring


class OLDCalendarContainer(CalendarBlock):

    daysPerView = schema.One(schema.Integer)
    dayMode = schema.One(schema.Boolean)
    lastHue = schema.One(schema.Float, initialValue = -1.0)

    def __init__(self, *arguments, **keywords):
        super(OLDCalendarContainer, self).__init__ (*arguments, **keywords)

## REFACTOR being hacked apart and away
            
    def instantiateWidget(self):
        # @@@ KCP move to a callback that gets called from parcel loader
        # after item has all of its attributes assigned from parcel xml
        self.initAttributes()
        
        w = OLDwxCalendarContainer(self.parentBlock.widget,
                           Block.Block.getWidgetID(self))

        ### widget-centric code still works




## REFACTOR: being refactored away
class OLDwxCalendarContainer(CalendarEventHandler, 
                  DragAndDrop.DropReceiveWidget, 
                  DragAndDrop.DraggableWidget,
                  DragAndDrop.ItemClipboardHandler,
                  wx.Panel):
    def __init__(self, *arguments, **keywords):
        super (OLDwxCalendarContainer, self).__init__ (*arguments, **keywords)

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        


    def _doDrawingCalculations(self):
        """sets a bunch of drawing variables"""
        self.size = self.GetSize()
        
        try:
            oldDayWidth = self.dayWidth
        except AttributeError:
            oldDayWidth = -1

        self.dayWidth = (self.size.width - self.scrollbarWidth) / (self.blockItem.daysPerView + 1)

        ### calculate column widths for the all-7-days week view case
        # column layout rules are funky (e.g. bug 3290)
        # - all 7 days are fixed at self.dayWidth
        # - the last column (expando-button) is fixed
        # - the "Week" column is the same as self.dayWidth, plus leftover pixels
        columnCount = 9
        dayWidths = (self.dayWidth,) * 7

        self.middleWidth = self.dayWidth*7
        self.xOffset = self.GetSize().width - self.middleWidth - self.scrollbarWidth
        self.columnWidths = (self.xOffset,) +dayWidths+ (self.scrollbarWidth,)

        # the gradient brushes are based on dayWidth, so blow it away
        # when dayWidth changes
        if oldDayWidth != self.dayWidth:
            self.brushes.ClearCache()
        
        if self.blockItem.dayMode:
            self.columns = 1
        else:
            self.columns = self.blockItem.daysPerView        

        #print self.size, self.xOffset, self.dayWidth, self.columns #convenient interactive way to learn what these variables are, since they're tricky to describe verbally


    def _getDividerPositions(self):
        """tuple of divider lines for the wxWeek{Header,Column}Canvas's.
        unlike columnWidths, this IS sensitive whether you're viewing one day
        vs. week"""
        cw = self.columnWidths
        if self.blockItem.dayMode:
            lastDividerPos = sum(cw)
            return (cw[0], lastDividerPos)
        else:
            ## e.g. 10,40,40,40 => 0,10,50,90
            cumulSums =  [sum(cw[:i]) for i in range(len(cw))]
            return cumulSums[1:]

    dividerPositions = property(_getDividerPositions)

    def OnEraseBackground(self, event):
        pass

    def OnInit(self):
        self._doDrawingCalculations()
        self.calendarControl.OnInit()
        self.allDayEventsCanvas.OnInit()
        self.timedEventsCanvas.OnInit()
        
    def OnSize(self, event):
        self._doDrawingCalculations()
        event.Skip()

    def wxSynchronizeWidget(self):
        
        self._doDrawingCalculations()
        #self.Layout()
        self.calendarControl.wxSynchronizeWidget()
        self.allDayEventsCanvas.wxSynchronizeWidget()
        self.timedEventsCanvas.wxSynchronizeWidget()
        
    def PrintCanvas(self, dc):
        self.timedEventsCanvas.PrintCanvas(dc)

    def OnExpand(self):
        self.allDayEventsCanvas.toggleSize()
        self.Layout()
        
        
    """
    Methods for Drag and Drop and Cut and Paste
    """
    def SelectedItems(self):
        selection = self.blockItem.selection
        if selection is None:
            return []
        return [selection]

    def DeleteSelection(self):
        try:
            self.blockItem.DeleteSelection()
        except AttributeError:
            pass

    def AddItems(self, itemList):
        """ @@@ Need to complete this for Paste to work """

class OLDwxCalendarControl(wx.Panel):
    """This is the topmost area with the month name, event color selector,
    week navigation arrows, and the bar of Week/day selector buttons"""

    currentSelectedDate = None
    currentStartDate = None
    
    def OnInit(self):
        self.SetBackgroundColour(self.parent.bgColor) ##REFACTOR: cal ctrl wants this

##  REFACTOR: old funky layout code.  how do we put this back in to the block calcon?
##         box = wx.BoxSizer(wx.VERTICAL)
##         box.Add(self.calendarControl, 0, wx.EXPAND)
##         box.Add(self.allDayEventsCanvas, 0, wx.EXPAND)
##         box.Add(self.timedEventsCanvas, 1, wx.EXPAND)
##         self.SetSizer(box)



        # Set up sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        navigationRow = wx.BoxSizer(wx.HORIZONTAL)
        
        sizer.Add((5,5), 0, wx.EXPAND)
        sizer.Add(navigationRow, 0, wx.EXPAND)
        sizer.Add((5,5), 0, wx.EXPAND)

        # beginnings of  in the calendar
        self.colorSelect = colourselect.ColourSelect(self, -1, size=wx.Size(30,15))
        self.Bind(colourselect.EVT_COLOURSELECT, self.parent.OnSelectColor)
        navigationRow.Add((5,5), 0, wx.EXPAND)
        navigationRow.Add(self.colorSelect, 0, wx.CENTER)

        today = date.today()
        today = datetime(today.year, today.month, today.day)
        styles = self.parent

        self.monthText = wx.StaticText(self, -1)
        self.monthText.SetFont(styles.monthLabelFont)
        self.monthText.SetForegroundColour(styles.monthLabelColor)

        navigationRow.Add((0,0), 1)
        
        # add vertical margins above/below the month 
        monthSizer = wx.BoxSizer(wx.VERTICAL)
        monthSizer.Add((7,7),0)
        monthSizer.Add(self.monthText, 0)
        monthSizer.Add((5,5), 0)
        
        navigationRow.Add(monthSizer, 0, wx.ALIGN_CENTER)
        navigationRow.Add((0,0), 1)
        
        # top row - left/right buttons, anchored to the right
        self.prevButton = CollectionCanvas.CanvasBitmapButton(self, "backarrow.png")
        self.nextButton = CollectionCanvas.CanvasBitmapButton(self, "forwardarrow.png")
        self.Bind(wx.EVT_BUTTON, self.parent.OnPrev, self.prevButton)
        self.Bind(wx.EVT_BUTTON, self.parent.OnNext, self.nextButton)

        navigationRow.Add(self.prevButton, 0, wx.CENTER)
        navigationRow.Add((5,5), 0)
        navigationRow.Add(self.nextButton, 0, wx.CENTER)
        navigationRow.Add((5,5), 0)
        
        # finally the last row, with the header
        self.weekColumnHeader = wx.colheader.ColumnHeader(self)
        
        # turn this off for now, because our sizing needs to be exact
        self.weekColumnHeader.SetAttribute(wx.colheader.CH_ATTR_ProportionalResizing,False)
        headerLabels = ["Week", "S", "M", "T", "W", "T", "F", "S", "+"]
        for header in headerLabels:
            self.weekColumnHeader.AppendItem(header, wx.colheader.CH_JUST_Center, 5, bSortEnabled=False)
        self.Bind(wx.colheader.EVT_COLUMNHEADER_SELCHANGED, self.OnDayColumnSelect, self.weekColumnHeader)

        # set up initial selection
        self.weekColumnHeader.SetAttribute(wx.colheader.CH_ATTR_VisibleSelection,True)
        self.UpdateHeader()
        sizer.Add(self.weekColumnHeader, 0, wx.EXPAND)
        
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetSizer(sizer)
        sizer.SetSizeHints(self)
        self.Layout()

    def UpdateHeader(self):
        if self.parent.blockItem.dayMode:
            # ugly back-calculation of the previously selected day
            reldate = self.parent.blockItem.selectedDate - \
                      self.parent.blockItem.rangeStart
            self.weekColumnHeader.SetSelectedItem(reldate.days+1)
        else:
            self.weekColumnHeader.SetSelectedItem(0)

    def ResizeHeader(self):
        for (i,width) in enumerate(self.parent.columnWidths):
            self.weekColumnHeader.SetUIExtent(i, (0,width))

    def OnSize(self, event):
        self.ResizeHeader()
        event.Skip()
        
    def wxSynchronizeWidget(self):
        selectedDate = self.parent.blockItem.selectedDate
        startDate = self.parent.blockItem.rangeStart

        if (selectedDate == self.currentSelectedDate and
            startDate == self.currentStartDate):
            return

        # update the calendar with the calender's color
        self.colorSelect.SetColour(self.parent.blockItem.calendarData.eventColor.wxColor())

        # Update the month button given the selected date
        lastDate = startDate + timedelta(days=6)
        months = dateFormatSymbols.getMonths()
        if (startDate.month == lastDate.month):
            monthText = u"%s %d" %(months[selectedDate.month - 1],
                                   selectedDate.year)
        else:
            monthText = u"%s - %s %d" %(months[startDate.month - 1],
                                        months[lastDate.month - 1],
                                        lastDate.year)
     
        self.monthText.SetLabel(monthText)

        today = date.today()
        today = datetime(today.year, today.month, today.day)

        # ICU makes this list 1-based, 1st element is an empty string, so that
        # shortWeekdays[Calendar.SUNDAY] == 'short name for sunday'
        shortWeekdays = dateFormatSymbols.getShortWeekdays()
        firstDay = GregorianCalendar().getFirstDayOfWeek()

        for day in xrange(7):
            actualDay = ((day + firstDay - 1) % 7)
            currentDate = startDate + timedelta(days=day)
            if currentDate == today:
                dayName = "Today"
            else:
                dayName = u"%s %02d" %(shortWeekdays[actualDay + 1],
                                       currentDate.day)
            self.weekColumnHeader.SetLabelText(day+1, dayName)
            
        self.currentSelectedDate = selectedDate
        self.currentStartDate = startDate
        
        self.Layout()
        
    def OnDayColumnSelect(self, event):
        """
        dispatches to appropriate events in self.parent, 
        based on the column selected
        """
        
        colIndex = self.weekColumnHeader.GetSelectedItem()
        
        # column 0, week button
        if (colIndex == 0):
            return self.parent.OnWeekSelect()
            
        # last column, the "+" expand button
        # (this may change...)
        if (colIndex == 8):
            # re-fix selection so that the expand button doesn't stay selected
            self.UpdateHeader()
            return self.parent.OnExpand()
        
        # all other cases mean a day was selected
        # OnDaySelect takes a zero-based day, and our first day is in column 1
        return self.parent.OnDaySelect(colIndex-1)



#111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111

class wxAllDayEventsCanvas(wxCalendarCanvas):
    def __init__(self, *arguments, **keywords):
        super (wxAllDayEventsCanvas, self).__init__ (*arguments, **keywords)

        self.SetMinSize((-1,25))
        self.size = self.GetSize()
        self.fixed = True

    def OnInit(self):
        super (wxAllDayEventsCanvas, self).OnInit()
        
        # Event handlers
        self.Bind(wx.EVT_SIZE, self.OnSize)
                    
    
    def OnSize(self, event):
        self.size = self.GetSize()
        self.RebuildCanvasItems()
        
        self.Refresh()
        event.Skip()
        
    def wxSynchronizeWidget(self):
        self.RebuildCanvasItems()
        self.Refresh()

    def toggleSize(self):
        # Toggles size between fixed and large enough to show all tasks
        if self.fixed:
            self.oldFixedSize = self.GetMinSize()
            if self.fullHeight > self.oldFixedSize.height:
                self.SetMinSize((-1, self.fullHeight + 9))
            else:
                self.SetMinSize(self.oldFixedSize)
        else:
            self.SetMinSize(self.oldFixedSize)
        self.fixed = not self.fixed

    # Drawing code
    def DrawBackground(self, dc):
        styles = self.parent
        
        # Use the transparent pen for painting the background
        dc.SetPen(wx.TRANSPARENT_PEN)
        
        # Paint the entire background
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.DrawRectangle(0, 0, self.size.width, self.size.height)

        # Draw lines between days
        drawInfo = self.parent
        def drawDayLine(dayNum):
            x = drawInfo.dividerPositions[dayNum]
            dc.DrawLine(x, 0,   x, self.size.height)

        # Week/7days divider needs major color, the rest are minor.
        dc.SetPen(styles.majorLinePen)
        drawDayLine(0)

        dc.SetPen(styles.minorLinePen)
        for dayNum in range(1, drawInfo.columns):
            drawDayLine(dayNum)

        # Draw one extra line to parallel the scrollbar below
        dc.DrawLine(self.size.width - drawInfo.scrollbarWidth, 0,
                    self.size.width - drawInfo.scrollbarWidth, self.size.height)

        
    def DrawCells(self, dc):
        
        styles = self.parent

        dc.SetFont(styles.eventLabelFont)
        
        selectedBox = None
        brushOffset = self.GetPlatformBrushOffset()

        for canvasItem in self.canvasItemList:
            # save the selected box to be drawn last
            item = canvasItem.GetItem()
            if self.parent.blockItem.selection is item:
                selectedBox = canvasItem
            else:
                canvasItem.Draw(dc, styles, brushOffset, False)
        
        if selectedBox:
            selectedBox.Draw(dc, styles, brushOffset, True)

        # Draw a line across the bottom of the header
        dc.SetPen(styles.majorLinePen)
        dc.DrawLine(0, self.size.height - 1,
                    self.size.width, self.size.height - 1)
        dc.DrawLine(0, self.size.height - 4,
                    self.size.width, self.size.height - 4)
        dc.SetPen(styles.minorLinePen)
        dc.DrawLine(0, self.size.height - 2,
                    self.size.width, self.size.height - 2)
        dc.DrawLine(0, self.size.height - 3,
                    self.size.width, self.size.height - 3)

            
    def RebuildCanvasItems(self):
        self.canvasItemList = []

        if self.parent.blockItem.dayMode:
            startDay = self.parent.blockItem.selectedDate
            width = self.size.width - self.parent.scrollbarWidth
        else:
            startDay = self.parent.blockItem.rangeStart
            width = self.parent.dayWidth

        self.fullHeight = 0
        size = self.GetSize()
        for day in range(self.parent.columns):
            currentDate = startDay + timedelta(days=day)
            rect = wx.Rect((self.parent.dayWidth * day) + self.parent.xOffset, 0,
                           width, size.height)
            self.RebuildCanvasItemsByDay(currentDate, rect)


    def RebuildCanvasItemsByDay(self, date, rect):
        x = rect.x
        y = rect.y
        w = rect.width
        h = 15

        for item in self.parent.blockItem.getDayItemsByDate(date):
            itemRect = wx.Rect(x, y, w, h)
            
            canvasItem = HeaderCanvasItem(itemRect, item)
            self.canvasItemList.append(canvasItem)
            
            # keep track of the current drag/resize box
            if self._currentDragBox and self._currentDragBox.GetItem() == item:
                self._currentDragBox = canvasItem

            y += itemRect.height
            
        if (y > self.fullHeight):
            self.fullHeight = y
                    
    def OnCreateItem(self, unscrolledPosition):
        view = self.parent.blockItem.itsView
        newTime = self.getDateTimeFromPosition(unscrolledPosition)
        event = Calendar.CalendarEvent(view=view)
        event.InitOutgoingAttributes()
        event.ChangeStart(datetime(newTime.year, newTime.month, newTime.day,
                                   event.startTime.hour,
                                   event.startTime.minute))
        event.allDay = True
        event.anyTime = False

        self.parent.blockItem.contents.source.first().add(event)
        self.OnSelectItem(event)
        view.commit()
        return event

    def OnDraggingItem(self, unscrolledPosition):
        if self.parent.blockItem.dayMode:
            return
        
        newTime = self.getDateTimeFromPosition(unscrolledPosition)
        item = self._currentDragBox.GetItem()
        if (newTime.toordinal() != item.startTime.toordinal()):
            item.ChangeStart(datetime(newTime.year, newTime.month, newTime.day,
                                      item.startTime.hour,
                                      item.startTime.minute))
            self.Refresh()

    def OnEditItem(self, box):
        position = box.GetEditorPosition()
        size = box.GetMaxEditorSize()

        self.editor.SetItem(box.GetItem(), position, size, size.height)


    def getDateTimeFromPosition(self, position):
        # bound the position by the available space that the user 
        # can see/scroll to
        yPosition = max(position.y, 0)
        xPosition = max(position.x, self.parent.xOffset)
        
        if (self.fixed):
            height = self.GetMinSize().GetWidth()
        else:
            height = self.fullHeight
            
        yPosition = min(yPosition, height)
        xPosition = min(xPosition, self.parent.xOffset + self.parent.dayWidth * self.parent.columns - 1)

        if self.parent.blockItem.dayMode:
            newDay = self.parent.blockItem.selectedDate
        elif self.parent.dayWidth > 0:
            deltaDays = (xPosition - self.parent.xOffset) / self.parent.dayWidth
            startDay = self.parent.blockItem.rangeStart
            newDay = startDay + timedelta(days=deltaDays)
        else:
            newDay = self.parent.blockItem.rangeStart
        return newDay


