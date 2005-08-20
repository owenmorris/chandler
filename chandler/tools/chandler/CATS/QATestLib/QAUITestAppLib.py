from QALogger import *
from datetime import datetime, timedelta
import ScriptingGlobalFunctions as Sgf
from osaf import pim
import osaf.pim.mail as Mail
import osaf.sharing as Sharing
import application.Globals as Globals
import wx
import string


                       
def getTime(date):
    hour = date.hour
    minute = date.minute
    if minute == 0:
        minute = "00"
    else:
        minute = "%s" %minute
    if hour > 12:
        hour = hour - 12
        minute = minute + " PM"
    else:
        minute = minute + "AM"
    return "%s:%s" %(hour, minute)


class UITestItem :       
    def __init__(self, view, type, logger):
        if not type in ["Event", "Note", "Task", "MailMessage", "Collection"]:
            # "Copy constructor"
            if isinstance(type,pim.calendar.CalendarEvent):
                self.isNote = self.isTask = self.isMessage = self.isCollection = self.allDay = False
                self.isEvent = True
                self.view = view
                self.logger = logger
                self.item = type
            else:
                return
        else:
            self.isNote = self.isEvent = self.isTask = self.isMessage = self.isCollection = self.allDay = False
            self.logger = logger
            if type == "Event": # New Calendar Event
                # post the corresponding CPIA-event
                item = Globals.mainViewRoot.postEventByName('NewCalendar',{})[0]
                self.isEvent = True
            elif type == "Note": # New Note
                # post the corresponding CPIA-event
                item = Globals.mainViewRoot.postEventByName('NewNote',{})[0]
                self.isNote = True
            elif type == "Task": # New Task
                # post the corresponding CPIA-event
                item = Globals.mainViewRoot.postEventByName('NewTask',{})[0]
                self.isTask = True
            elif type == "MailMessage": # New Mail Message
                # post the corresponding CPIA-event
                item = Globals.mainViewRoot.postEventByName('NewMailMessage',{})[0]
                self.isMessage = True
            elif type == "Collection": # New Collection
                # post the corresponding CPIA-event
                item = Globals.mainViewRoot.postEventByName('NewItemCollection',{})[0]
                self.isCollection = True
                
            self.item = item
                 

    def SetAttr(self, displayName=None, startDate=None, startTime=None, endDate=None, endTime=None, location=None, body=None,
                status=None, alarm=None, fromAddress=None, toAddress=None, allDay=None, stampEvent=None, stampMail=None,
                stampTask=None, dict=None):
        """ Set the item attributes in a predefined order """
        if displayName:
            self.SetDisplayName(displayName)
        if startDate:
            self.SetStartDate(startDate)
        if startTime:
            self.SetStartTime(startTime)
        if endDate:
            self.SetEndDate(endDate)
        if endTime:
            self.SetEndTime(endTime)
        if location:
            self.SetLocation(location)
        if body:
            self.SetBody(body)
        if status:
            self.SetStatus(status)
        if alarm:
            self.SetAlarm(alarm)
        if fromAddress:
            self.SetFromAddress(fromAddress)
        if toAddress:
            self.SetToAddress(toAddress)
        if allDay:
            self.SetAllDay(allDay)
        if stampEvent:
            self.StampAsEvent(stampEvent)
        if stampMail:
            self.StampAsMailMessage(stampMail)
        if stampTask:
            self.StampAsTask(stampTask)
        if dict:
            self.logger.Start("Multiple Attribute Setting")
            self.logger.Stop()
            self.Check_DetailView(dict)
            

    def SetAttrInOrder(self, argList, dict=None):
        """ Set the item attributes in the argList order """
        for (key, value) in argList:
            if key == "displayName":
                self.SetDisplayName(value)
            if key == "startDate":
                self.SetStartDate(value)
            if key == "startTime":
                self.SetStartTime(value)
            if key == "endDate":
                self.SetEndDate(value)
            if key == "endTime":
                self.SetEndTime(value)
            if key == "location":
                self.SetLocation(value)
            if key == "body":
                self.SetBody(value)
            if key == "status":
                self.SetStatus(value)
            if key == "alarm":
                self.SetAlarm(value)
            if key == "fromAddress":
                self.SetFromAddress(value)
            if key == "toAddress":
                self.SetToAddress(value)
            if key == "allDay":
                self.SetAllDay(value)
            if key == "stampEvent":
                self.StampAsCalendarEvent(value)
            if key == "stampMail":
                self.StampAsMailMessage(value)
            if key == "stampTask":
                self.StampAsTask(value)
            if key == "dict":
                self.logger.Start("Multiple Attribute Setting")
                self.logger.Stop()
                self.Check_DetailView(value)

    def SelectItem(self):
        #if not in the Calendar view (select in the summary view)
        #check the button state
        button = Sgf.FindNamedBlock("ApplicationBarEventButton") 
        buttonState = button.widget.IsToggled()
        if not buttonState:
            Sgf.SummaryViewSelect(self.item)
        #if in the Calendar view (select by clicking on the TimedCanvasItem)
        else:
            timedCanvas = Sgf.FindNamedBlock("TimedEventsCanvas")
            for canvasItem in reversed(timedCanvas.widget.canvasItemList):
                if canvasItem._item == self.item:
                    #process the mouse event at the good coord
                    pos = canvasItem.GetDragOrigin()
                    click = wx.MouseEvent(wx.wxEVT_LEFT_DOWN)
                    click.m_x = pos.x
                    click.m_y = pos.y
                    click.SetEventObject(timedCanvas.widget)
                    wx.GetApp().Yield()
                    break
        
            
    def SetDisplayName(self, displayName, dict=None):
        ''' Set the title '''
        if (self.isNote or self.isEvent or self.isTask or self.isMessage):
            if dict:
                self.logger.Start("Set the display name to : %s" %displayName)
            #select the item
            self.SelectItem()
            displayNameBlock = Sgf.DisplayName()
            # Emulate the mouse click in the display name block
            Sgf.LeftClick(displayNameBlock)
            # Select the old text
            displayNameBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(displayName)
            Sgf.KeyboardReturn(displayNameBlock)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)          
        else:
            self.logger.Print("SetDisplayName is not available for this kind of item")
            return

    def SetStartTime(self, startTime, dict=None):
        ''' Set the start time '''
        if (self.isEvent and not self.allDay):
            if dict:
                self.logger.Start("Set the start time to : %s" %startTime)
            self.SelectItem()
            startTimeBlock = Sgf.StartTime()
            # Emulate the mouse click in the start time block
            Sgf.LeftClick(startTimeBlock)
            # Select the old text
            startTimeBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(startTime)
            Sgf.KeyboardReturn(startTimeBlock)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)    
        else:
            self.logger.Print("SetStartTime is not available for this kind of item")
            return

    def SetStartDate(self, startDate, dict=None):
        ''' Set the start date '''
        if self.isEvent:
            if dict:
                self.logger.Start("Set the start date to : %s" %startDate)
            self.SelectItem()
            startDateBlock = Sgf.StartDate()
            # Emulate the mouse click in the start date block
            Sgf.LeftClick(startDateBlock)
            # Select the old text
            startDateBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(startDate)
            Sgf.KeyboardReturn(startDateBlock)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
        else:
            self.logger.Print("SetStartDate is not available for this kind of item")
            return

    def SetEndTime(self, endTime, dict=None):
        ''' Set the end time '''
        if (self.isEvent and not self.allDay):
            if dict:
                self.logger.Start("Set the end time to : %s" %endTime)
            self.SelectItem()
            endTimeBlock = Sgf.EndTime()
            # Emulate the mouse click in the end time block
            Sgf.LeftClick(endTimeBlock)
            # Select the old text
            endTimeBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(endTime)
            Sgf.KeyboardReturn(endTimeBlock)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
        else:
            self.logger.Print("SetEndTime is not available for this kind of item")
            return
    
    def SetEndDate(self, endDate, dict=None):
        ''' Set the end date '''
        if self.isEvent:
            if dict:
                self.logger.Start("Set the end date to : %s" %endDate)
            self.SelectItem()
            endDateBlock = Sgf.EndDate()
            # Emulate the mouse click in the end date block
            Sgf.LeftClick(endDateBlock)
            # Select the old text
            endDateBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(endDate)
            Sgf.KeyboardReturn(endDateBlock)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
        else:
            self.logger.Print("SetEndDate is not available for this kind of item")
            return

    def SetLocation(self, location, dict=None):
        ''' Set the location '''
        if self.isEvent:
            if dict:
                self.logger.Start("Set the location to : %s" %location)
            self.SelectItem()
            locationBlock = Sgf.Location()
            print locationBlock
            print locationBlock.widget
            Sgf.LeftClick(locationBlock)
            # Select the old text
            locationBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(location)
            Sgf.KeyboardReturn(locationBlock)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
        else:
            self.logger.Print("SetLocation is not available for this kind of item")
            return

    def SetAllDay(self, allDay, dict=None):
        ''' Set the allday attribute '''
        if self.isEvent:
            if dict:
                self.logger.Start("Set the all Day to : %s" %allDay)
            self.SelectItem()
            allDayBlock = Sgf.FindNamedBlock("EditAllDay")  
            # Emulate the mouse click in the all-day block
            #Sgf.LeftClick(allDayBlock)
            # work around : (the mouse click has not the good effect)
            # the bug #3336 appear on linux
            allDayBlock.widget.SetValue(allDay)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
            self.allDay = allDay
        else:
            self.logger.Print("SetAllDay is not available for this kind of item")
            return
   
    def SetStatus(self, status, dict=None):
        ''' Set the status '''
        if self.isEvent:
            self.SelectItem()
            statusBlock = Sgf.FindNamedBlock("EditTransparency")
            list_of_value = []
            for k in range(0,statusBlock.widget.GetCount()):
                list_of_value.append(statusBlock.widget.GetString(k))
            if not status in list_of_value:
                return
            else:
                if dict:
                    self.logger.Start("Set the status to : %s" %status)
                # Emulate the mouse click in the status block
                Sgf.LeftClick(statusBlock)
                statusBlock.widget.SetStringSelection(status)
                # Process the event corresponding to the selection
                selectionEvent = wx.CommandEvent(wx.wxEVT_COMMAND_CHOICE_SELECTED)
                selectionEvent.SetEventObject(statusBlock.widget)
                statusBlock.widget.ProcessEvent(selectionEvent)
                self.SelectItem()
                if dict:
                    self.logger.Stop()
                    self.Check_DetailView(dict)
        else:
            self.logger.Print("SetStatus is not available for this kind of item")
            return

    def SetAlarm(self, alarm, dict=None):
        ''' Set the alarm '''
        if self.isEvent:
            if alarm == "1":
                alarm = alarm + " minute"
            else:
                alarm = alarm + " minutes"
            self.SelectItem()
            alarmBlock = Sgf.FindNamedBlock("EditReminder")
            list_of_value = []
            for k in range(0,alarmBlock.widget.GetCount()):
                list_of_value.append(alarmBlock.widget.GetString(k))
            if not alarm in list_of_value:
                return
            else:
                if dict:
                    self.logger.Start("Set the alarm to : %s" %alarm)
                # Emulate the mouse click in the reminder block
                Sgf.LeftClick(alarmBlock)
                alarmBlock.widget.SetStringSelection(alarm)
                # Process the event corresponding to the selection
                selectionEvent = wx.CommandEvent(wx.wxEVT_COMMAND_CHOICE_SELECTED)
                selectionEvent.SetEventObject(alarmBlock.widget)
                alarmBlock.widget.ProcessEvent(selectionEvent)
                self.SelectItem()
                if dict:
                    self.logger.Stop()
                    self.Check_DetailView(dict)
        else:
            self.logger.Print("SetAlarm is not available for this kind of item")
            return
    
    def SetBody(self, body, dict=None):
        ''' Set the body text '''
        if dict:
            self.logger.Start("Set the body")
        self.SelectItem()
        noteArea = Sgf.FindNamedBlock("NotesBlock")
        # Emulate the mouse click in the note area
        Sgf.LeftClick(noteArea)
        noteArea.widget.SelectAll()
        # Emulate the keyboard events
        Sgf.Type(body)
        Sgf.KeyboardReturn(noteArea)
        if dict:
            self.logger.Stop()
            self.Check_DetailView(dict)
            

    def SetToAddress(self, toAdd, dict=None):
        ''' Set the to address '''
        if self.isMessage:
            if dict:
                self.logger.Start("Set the to address to : %s" %toAdd)
            self.SelectItem()
            toBlock = Sgf.FindNamedBlock("ToMailEditField")
            # Emulate the mouse click in the to block
            Sgf.LeftClick(toBlock)
            toBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(toAdd)
            Sgf.KeyboardReturn(toBlock)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
        else:
            self.logger.Print("SetToAddress is not available for this kind of item")
            return
        
    def SetFromAddress(self, fromAdd, dict=None):
        ''' Set the from address (not available from UI) '''
        if self.isMessage:
            if dict:
                self.logger.Start("Set the from address to : %s" %fromAdd)
            self.SelectItem()
            fromBlock = Sgf.FindNamedBlock("FromEditField")
            # Emulate the mouse click in the from block
            Sgf.LeftClick(fromBlock)
            fromBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(fromAdd)
            Sgf.KeyboardReturn(fromBlock)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
        else:
            self.logger.Print("SetFromAddress is not available for this kind of item")
            return

    
    def StampAsMailMessage(self, stampMail, dict=None):
        ''' Stamp as a mail '''
        if stampMail == self.isMessage:# Nothing to do
            return
        else:
            if dict:
                self.logger.Start("Change the Mail stamp to : %s" %stampMail)
            self.SelectItem()
            Sgf.StampAsMailMessage()
            self.isMessage = stampMail
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                

    def StampAsTask(self, stampTask, dict=None):
        ''' Stamp as a task '''
        if stampTask == self.isTask:# Nothing to do
            return
        else:
            if dict:
                self.logger.Start("Change the Task stamp to : %s" %stampTask)
            self.SelectItem()
            Sgf.StampAsTask()
            self.isTask = stampTask
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                

    def StampAsCalendarEvent(self, stampEvent, dict=None):
        ''' Stamp as an event '''
        if stampEvent == self.isEvent:# Nothing to do
            return
        else:
            if dict:
                self.logger.Start("Change the Calendar Event stamp to : %s" %stampEvent)
            self.SelectItem()
            Sgf.StampAsCalendarEvent()
            self.isEvent = stampEvent
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                
        
    def Check_DetailView(self, dict):
        ''' Check expected values by comparation to the data diplayed in the detail view '''
        self.logger.SetChecked(True)
        # check the changing values
        for field in dict.keys():
            self.SelectItem()
            if field == "displayName": # display name checking
                displayNameBlock = Sgf.FindNamedBlock("HeadlineBlock")
                d_name = displayNameBlock.widget.GetValue()
                if not dict[field] == d_name :
                    self.logger.ReportFailure("(On display name Checking)  || detail view title = %s ; expected title = %s" %(d_name, dict[field]))
                else:
                    self.logger.ReportPass("(On display name Checking)")
            elif field == "startDate": # start date checking
                startDateBlock = Sgf.FindNamedBlock("EditCalendarStartDate")
                s_date = startDateBlock.widget.GetValue()
                if not dict[field] == s_date :
                    self.logger.ReportFailure("(On start date Checking) || detail view start date = %s ; expected start date = %s" %(s_date, dict[field]))
                else:
                    self.logger.ReportPass("(On start date Checking)")
            elif field == "startTime": # start time checking
                startTimeBlock = Sgf.FindNamedBlock("EditCalendarStartTime")
                s_time = startTimeBlock.widget.GetValue()
                if not dict[field] == s_time :
                    self.logger.ReportFailure("(On start time Checking) || detail view start time = %s ; expected start time = %s" %(s_time, dict[field]))
                else:
                    self.logger.ReportPass("(On start time Checking)")
            elif field == "endDate": # end date checking
                endDateBlock = Sgf.FindNamedBlock("EditCalendarEndDate")
                e_date = endDateBlock.widget.GetValue()
                if not dict[field] == e_date :
                    self.logger.ReportFailure("(On end date Checking) || detail view end date = %s ; expected end date = %s" %(e_date, dict[field]))
                else:
                    self.logger.ReportPass("(On end date Checking)")
            elif field == "endTime": # end time checking
                endTimeBlock = Sgf.FindNamedBlock("EditCalendarEndTime")
                e_time = endTimeBlock.widget.GetValue()
                if not dict[field] == e_time :
                    self.logger.ReportFailure("(On end time Checking) || detail view end time = %s ; expected end time = %s" %(e_time, dict[field]))
                else:
                    self.logger.ReportPass("(On end time Checking)")
            elif field == "location": # location checking
                locationBlock = Sgf.FindNamedBlock("CalendarLocation")
                loc = locationBlock.widget.GetValue()
                if not dict[field] == loc :
                    self.logger.ReportFailure("(On location Checking) || detail view location = %s ; expected location = %s" %(loc, dict[field]))
                else:
                    self.logger.ReportPass("(On location Checking)")
            elif field == "body": # body checking
                noteBlock = Sgf.FindNamedBlock("NotesBlock")
                body = noteBlock.widget.GetValue()
                if not dict[field] == body :
                    self.logger.ReportFailure("(On body Checking) || detail view body = %s ; expected body = %s" %(body, dict[field]))
                else:
                     self.logger.ReportPass("(On body Checking)")
            elif field == "fromAddress": # from address checking
                fromBlock = Sgf.FindNamedBlock("FromEditField")
                f = fromBlock.widget.GetValue()
                if not dict[field] == f :
                    self.logger.ReportFailure("(On from address Checking) || detail view from address = %s ; expected from address = %s" %(f, dict[field]))
                else:
                    self.logger.ReportPass("(On from address Checking)")
            elif field == "toAddress": # to address checking
                toBlock = Sgf.FindNamedBlock("ToMailEditField")
                t = toBlock.widget.GetValue()
                if not dict[field] == t :
                    self.logger.ReportFailure("(On to address Checking) || detail view to address = %s ; expected to address = %s" %(t, dict[field]))
                else:
                    self.logger.ReportPass("(On to address Checking)")
            elif field == "status": # status checking
                statusBlock = Sgf.FindNamedBlock("EditTransparency")
                status = statusBlock.widget.GetStringSelection()
                if not dict[field] == status :
                    self.logger.ReportFailure("(On status Checking) || detail view status = %s ; expected status = %s" %(status, dict[field]))
                else:
                    self.logger.ReportPass("(On status Checking)")
            elif field == "alarm": # status checking
                alarmBlock = Sgf.FindNamedBlock("EditReminder")
                alarm = alarmBlock.widget.GetStringSelection()
                if not dict[field] == alarm :
                    self.logger.ReportFailure("(On alarm Checking) || detail view alarm = %s ; expected alarm = %s" %(alarm, dict[field]))
                else:
                    self.logger.ReportPass("(On alarm Checking)")
            elif field == "allDay": # status checking
                allDayBlock = Sgf.FindNamedBlock("EditAllDay")
                allDay = allDayBlock.widget.GetValue()
                if not dict[field] == allDay :
                    self.logger.ReportFailure("(On all Day Checking) || detail view all day = %s ; expected all day = %s" %(allDay, dict[field]))
                else:
                    self.logger.ReportPass("(On all Day Checking)")
            elif field == "stampMail": # Mail stamp checking
                stampMail = Sgf.ButtonPressed("MailMessageButton")
                if not dict[field] == stampMail :
                    self.logger.ReportFailure("(On Mail Stamp Checking) || detail view Mail Stamp = %s ; expected Mail Stamp = %s" %(stampMail, dict[field]))
                else:
                    self.logger.ReportPass("(On Mail Stamp Checking)")
            elif field == "stampTask": # Task stamp checking
                stampTask = Sgf.ButtonPressed("TaskStamp")
                if not dict[field] == stampTask :
                    self.logger.ReportFailure("(On Task Stamp Checking) || detail view Task Stamp = %s ; expected Task Stamp = %s" %(stampTask, dict[field]))
                else:
                    self.logger.ReportPass("(On Task Stamp Checking)")
            elif field == "stampEvent": # Event stamp checking
                stampEvent = Sgf.ButtonPressed("CalendarStamp")
                if not dict[field] == stampEvent :
                    self.logger.ReportFailure("(On Event Stamp Checking) || detail view Event Stamp = %s ; expected Event Stamp = %s" %(stampEvent, dict[field]))
                else:
                    self.logger.ReportPass("(On Event Stamp Checking)")
        #report the checkings
        self.logger.Report("Detail View")
    
    def Check_Object(self, dict):
        ''' Check expected values by comparation to the data contained in the object attributes '''
        self.logger.SetChecked(True)
        # check the changing values
        for field in dict.keys():
            if field == "displayName": # display name checking
                if self.isMessage:
                    d_name = "%s" %self.item.subject
                else:
                    d_name = "%s" %self.item.displayName
                if not dict[field] == d_name :
                    self.logger.ReportFailure("(On display name Checking)  || object title = %s ; expected title = %s" %(d_name, dict[field]))
                else:
                    self.logger.ReportPass("(On display name Checking)")
            elif field == "startDate": # start date checking
                startTime = self.item.startTime
                s_date = "%s/%s/%s" %(startTime.month, startTime.day, startTime.year) 
                if not dict[field] == s_date :
                    self.logger.ReportFailure("(On start date Checking) || object start date = %s ; expected start date = %s" %(s_date, dict[field]))
                else:
                    self.logger.ReportPass("(On start date Checking)")
            elif field == "startTime": # start time checking
                startTime = self.item.startTime
                s_time = getTime(startTime)
                if not dict[field] == s_time :
                    self.logger.ReportFailure("(On start time Checking) || object start time = %s ; expected start time = %s" %(s_time, dict[field]))
                else:
                    self.logger.ReportPass("(On start time Checking)")
            elif field == "endDate": # end date checking
                endTime = self.item.endTime
                e_date = "%s/%s/%s" %(endTime.month, endTime.day, endTime.year) 
                if not dict[field] == e_date :
                    self.logger.ReportFailure("(On end date Checking) || object end date = %s ; expected end date = %s" %(e_date, dict[field]))
                else:
                    self.logger.ReportPass("(On end date Checking)")
            elif field == "endTime": # end time checking
                endTime = self.item.endTime
                e_time = getTime(endTime)
                if not dict[field] == e_time :
                    self.logger.ReportFailure("(On end time Checking) || object end time = %s ; expected end time = %s" %(e_time, dict[field]))
                else:
                    self.logger.ReportPass("(On end time Checking)")
            elif field == "location": # location checking
                loc = "%s" %self.item.location
                if not dict[field] == loc :
                    self.logger.ReportFailure("(On location Checking) || object location = %s ; expected location = %s" %(loc, dict[field]))
                else:
                    self.logger.ReportPass("(On location Checking)")
            elif field == "body": # body checking
                body = "%s" %self.item.bodyString
                if not dict[field] == body :
                    self.logger.ReportFailure("(On body Checking) || object body = %s ; expected body = %s" %(body, dict[field]))
                else:
                     self.logger.ReportPass("(On body Checking)")
            elif field == "fromAddress": # from address checking
                f = "%s" %self.item.fromAddress
                if not dict[field] == f :
                    self.logger.ReportFailure("(On from address Checking) || object from address = %s ; expected from address = %s" %(f, dict[field]))
                else:
                    self.logger.ReportPass("(On from address Checking)")
            elif field == "toAddress": # to address checking
                t = "%s" %self.item.toAddress
                if not dict[field] == t :
                    self.logger.ReportFailure("(On to address Checking) || object to address = %s ; expected to address = %s" %(t, dict[field]))
                else:
                    self.logger.ReportPass("(On to address Checking)")
            elif field == "status": # status checking
                status = "%s" %string.upper(self.item.transparency)
                if not dict[field] == status :
                    self.logger.ReportFailure("(On status Checking) || object status = %s ; expected status = %s" %(status, dict[field]))
                else:
                    self.logger.ReportPass("(On status Checking)")
            elif field == "alarm": # status checking
                alarm = self.item.startTime - self.item.reminderTime
                field = timedelta(minutes = string.atoi(dict[field]))
                if not field == alarm :
                    self.logger.ReportFailure("(On alarm Checking) || object alarm = %s ; expected alarm = %s" %(alarm, field))
                else:
                    self.logger.ReportPass("(On alarm Checking)")
            elif field == "allDay": # status checking
                allDay = self.item.allDay
                if not dict[field] == allDay :
                    self.logger.ReportFailure("(On all Day Checking) || object all day = %s ; expected all day = %s" %(allDay, dict[field]))
                else:
                    self.logger.ReportPass("(On all Day Checking)")
            elif field == "stampMail": # Mail stamp checking
                kind = "%s" %self.item.getKind()
                if not string.find(kind, "MailMessage") == -1:
                    stampMail = True
                else:
                    stampMail = False
                if not dict[field] == stampMail :
                    self.logger.ReportFailure("(On Mail Stamp Checking) || object Mail Stamp = %s ; expected Mail Stamp = %s" %(stampMail, dict[field]))
                else:
                    self.logger.ReportPass("(On Mail Stamp Checking)")
            elif field == "stampTask": # Task stamp checking
                kind = "%s" %self.item.getKind()
                if not string.find(kind, "Task") == -1:
                    stampTask = True
                else:
                    stampTask = False
                if not dict[field] == stampTask :
                    self.logger.ReportFailure("(On Task Stamp Checking) || object Task Stamp = %s ; expected Task Stamp = %s" %(stampTask, dict[field]))
                else:
                    self.logger.ReportPass("(On Task Stamp Checking)")
            elif field == "stampEvent": # Event stamp checking
                kind = "%s" %self.item.getKind()
                if not string.find(kind, "CalendarEvent") == -1:
                    stampEvent = True
                else:
                    stampEvent = False
                if not dict[field] == stampEvent :
                    self.logger.ReportFailure("(On Event Stamp Checking) || object Event Stamp = %s ; expected Event Stamp = %s" %(stampEvent, dict[field]))
                else:
                    self.logger.ReportPass("(On Event Stamp Checking)")
        #report the checkings
        self.logger.Report("Object state")
        
class UITestAccounts:
    def __init__(self, view = None, logger=None):
        import wx
        self.view = view
        self.logger = logger
        self.window = None
        self.accountNames = {'SMTP': 'Outgoing mail (SMTP)', 'IMAP': 'Incoming mail (IMAP)', 'POP': 'Incoming mail (POP)', 'WebDAV': 'Sharing (WebDAV)'}
        SMTPfields = {'displayName': 3, 'host': 5, 'username': 15, 'password': 17, 'security': 7, 'port':11,  'authentication': 13}
        IMAPfields = {'displayName': 3, 'email': 5, 'name': 7, 'host': 9, 'username': 11, 'password': 13, 'security': 15, 'port': 19, 'default': 21, 'server': 24}
        POPfields = {'displayName': 3, 'email': 5, 'name': 7, 'host': 9, 'username': 11, 'password': 13, 'security': 15,'port': 19, 'leave': 21,  'default': 23, 'server': 26}
        DAVfields = {'displayName': 3, 'host':5, 'path': 7, 'username':9, 'password':11, 'port': 13, 'ssl': 14, 'default': 16}
        self.fieldMap = {'SMTP': SMTPfields, 'IMAP': IMAPfields, 'WebDAV': DAVfields, 'POP': POPfields}        
        
    def Open(self):
        # EditAccountPreferences()
        # Have to do it the hard way since Account Preferences is modal by default
        import application
        application.dialogs.AccountPreferences.ShowAccountPreferencesDialog(wx.GetApp().mainFrame, view=self.view, modal=False)
        self.window = Sgf.GetWindow("Account Preferences")
        
    def Ok(self):
        self.window.OnOk(None)
        self.window = None
        
    def Cancel(self):
        self.window.OnCancel(None)
        self.window = None

    def CreateAccount(self, type):
        self.window.choiceNewType.SetStringSelection(self.accountNames[type])
        self.window.OnNewAccount(None)

    def _GetField(self, field):
        index = self._GetIndex(field)
        return self._GetChild(index)
    
    def _GetIndex(self, field):
        type = self.window.currentPanelType
        return self.fieldMap[type][field]
    
    def _GetChild(self, child):
        return self.window.currentPanel.GetChildren()[child]
        
    def TypeValue(self, field, value):
        child = self._GetField(field)
        child.SetFocus()
        child.SelectAll()
        Sgf.Type(value);
        wx.GetApp().Yield()

    def ToggleValue(self, field, value):
        child = self._GetField(field)
        child.SetValue(value)
        event = wx.CommandEvent()
        event.SetEventObject(child)
        self.window.OnLinkedControl(event)
        self.window.OnExclusiveRadioButton(event)
        wx.GetApp().Yield()
        
    def SelectValue(self, field, value):
        child = self._GetField(field)
        if isinstance(child, wx.RadioButton):
            offset = {'None': 0, 'No':0, 'TLS': 1, 'SSL': 2}[value]
            index = self._GetIndex(field)
            button = self._GetChild(index + offset)
            button.SetValue(True)
            event = wx.CommandEvent()
            event.SetEventObject(button)
            self.window.OnLinkedControl(event)  
            self.window.OnExclusiveRadioButton(event)
        else:
            child.SetStringSelection(value)
        
    def VerifyValues(self, type, name, **keys):
        if type == "SMTP":
            iter = Mail.SMTPAccount.iterItems()
        elif type == "IMAP":
            iter = Mail.IMAPAccount.iterItems()
        elif type == "WebDAV":
            iter = Sharing.WebDAVAccount.iterItems()
        elif type == "POP":
            iter = Mail.POPAccount.iterItems()
        else:
            raise AttributeError
        for account in iter:
            if account.displayName == name:
                break
        self.logger.SetChecked(True)
        result = True
        for (key, value) in keys.items():
            if account._values[key] != value:
                self.logger.ReportFailure("Checking %s %s: expected %s, but got %s" % (type, key, value, account._values[key]))
                result = False
            else:
                self.logger.ReportPass("Checking %s %s" % (type, key))
        return result


class UITestView:
    def __init__(self, view, logger):
        self.logger = logger
        self.view = view
        #by default the all view is selected
        Sgf.PressButton("ApplicationBarAllButton")
        self.state = "AV"

    def SwitchToCalView(self):
        if not self.state == "CV":
            self.state = "CV"
            button = Sgf.FindNamedBlock("ApplicationBarEventButton")
            toolBar = Sgf.FindNamedBlock("ApplicationBar")

            self.logger.Start("Switch to calendar view")
            #process the corresponding event
            ev = wx.CommandEvent(wx.wxEVT_COMMAND_TOOL_CLICKED,button.widget.GetId())
            toolBar.widget.ProcessEvent(ev)
            wx.GetApp().Yield()
            self.logger.Stop()
            self.CheckView()
            #get the timedEventsCanvas corresponding to the cal view
            self.timedCanvas = Sgf.FindNamedBlock('TimedEventsCanvas') 
        
    def SwitchToTaskView(self):
        if not self.state == "TV":
            self.state = "TV"
            button = Sgf.FindNamedBlock("ApplicationBarTaskButton")
            toolBar = Sgf.FindNamedBlock("ApplicationBar")
            
            self.logger.Start("Switch to task view")
            #process the corresponding event
            ev = wx.CommandEvent(wx.wxEVT_COMMAND_TOOL_CLICKED,button.widget.GetId())
            toolBar.widget.ProcessEvent(ev)
            wx.GetApp().Yield()
            self.logger.Stop()
            self.CheckView()

    def SwitchToMailView(self):
        if not self.state == "MV":
            self.state = "MV"
            button = Sgf.FindNamedBlock("ApplicationBarMailButton")
            toolBar = Sgf.FindNamedBlock("ApplicationBar")

            self.logger.Start("Switch to email view")
            #process the corresponding event
            ev = wx.CommandEvent(wx.wxEVT_COMMAND_TOOL_CLICKED,button.widget.GetId())
            toolBar.widget.ProcessEvent(ev)
            wx.GetApp().Yield()
            self.logger.Stop()
            self.CheckView()
        
    def SwitchToAllView(self):
        if not self.state == "AV":
            self.state = "AV"
            button = Sgf.FindNamedBlock("ApplicationBarAllButton")
            toolBar = Sgf.FindNamedBlock("ApplicationBar")
            
            self.logger.Start("Switch to all view")
            #process the corresponding event
            ev = wx.CommandEvent(wx.wxEVT_COMMAND_TOOL_CLICKED,button.widget.GetId())
            toolBar.widget.ProcessEvent(ev)
            wx.GetApp().Yield()
            self.logger.Stop()
            self.CheckView()
            
    def CheckView(self):
        self.logger.SetChecked(True)
        if self.state == "AV":
            #the all view button should be toggled
            button = Sgf.FindNamedBlock("ApplicationBarAllButton")
        elif self.state == "TV":
            #the task view button should be toggled
            button = Sgf.FindNamedBlock("ApplicationBarTaskButton")
        elif self.state == "MV":
            #the mail view button should be toggled
            button = Sgf.FindNamedBlock("ApplicationBarMailButton")
        elif self.state == "CV":
            #the calendar view button should be toggled
            button = Sgf.FindNamedBlock("ApplicationBarEventButton")
        else:
            print "error"
            return
        
        buttonState = button.widget.IsToggled()
        if not buttonState:
            self.logger.ReportFailure("(On wiew checking) || expected current view = %s ; Correspondig button is switch off " %self.state)
        else:
            self.logger.ReportPass("(On view checking)")
            
        #report the checkings
        self.logger.Report("View")
        
    def DoubleClickInCalView(self, x=101, y=25):
        if self.state == "CV":
            self.timedCanvas = Sgf.FindNamedBlock('TimedEventsCanvas') 
            canvasItem = None
            #process the corresponding event
            click = wx.MouseEvent(wx.wxEVT_LEFT_DCLICK)
            click.m_x = x
            click.m_y = y
            click.SetEventObject(self.timedCanvas.widget)
            #check if an event already exists at this x,y postion
            #and if yes put it in the canvasItem variable
            #print "list before : %s" %self.timedCanvas.widget.canvasItemList
            pos = self.timedCanvas.widget.CalcUnscrolledPosition(click.GetPosition())
            for elem in reversed(self.timedCanvas.widget.canvasItemList):
                if elem.isHit(pos):
                    canvasItem = elem
                    break

            #workaround : process a double clik here edit the title (also when the canvasItem is not focused)
            #behavior in chandler is different just a selection (I guess something linked to the focus)
            #so I just process a simple click before the double click to focus the canvasItem
            if canvasItem:
                click2 = wx.MouseEvent(wx.wxEVT_LEFT_DOWN)
                click2.m_x = x
                click2.m_y = y
                click2.SetEventObject(self.timedCanvas.widget)
                self.timedCanvas.widget.ProcessEvent(click2)
                wx.GetApp().Yield()
        
                self.logger.Start("Double click in the calendar view")
                self.timedCanvas.widget.ProcessEvent(click)
                wx.GetApp().Yield()
                self.logger.Stop()
                #workaround
                wx.Window.FindFocus().Clear()
            else:
                self.logger.Start("Double click in the calendar view")
                self.timedCanvas.widget.ProcessEvent(click)
                wx.GetApp().Yield()
                self.logger.Stop()
            
            #it's a new event
            if not canvasItem :
                #get the created item (it should be the last one)
                #canvasItem = self.timedCanvas.widget.canvasItemList[-1]
                for elem in reversed(self.timedCanvas.widget.canvasItemList):
                    if elem.isHit(pos):
                        canvasItem = elem
                        self.logger.ReportPass("On double click in Calendar view checking (event creation)")
                        break
            else:
                self.logger.ReportPass("On double click in Calendar view checking (event selection)")

            #checking
            self.logger.SetChecked(True)
            self.logger.Report("Double click")
            if not canvasItem:
                self.logger.SetChecked(True)
                self.logger.ReportFailure("The event has not been created or selected")
                self.logger.Report()
                return
                   
            #print "list after : %s" %self.timedCanvas.widget.canvasItemList
            #create the corresponding UITestItem object
            TestItem = UITestItem(self.view, canvasItem._item, self.logger)
            return TestItem
        else:
            self.logger.Print("DoubleClickInCalView is not available in the current view : %s" %self.state)
            return
