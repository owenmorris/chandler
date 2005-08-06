from datetime import datetime, timedelta
import ScriptingGlobalFunctions as Sgf
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.Notes as Notes
from osaf.contentmodel.tasks import Task
import osaf.contentmodel.mail as Mail
import osaf.sharing.WebDAV as WebDAV
import wx
import sys
import time
import string

#def Keyboard_Return(block):
#    try:
#        widget = block.widget
#    except AttributeError:
#        _logger.warning("Can't get the widget of the block %s" % block)
#    else:
#        ret = wx.KeyEvent(wx.wxEVT_CHAR)
#        ret.m_keyCode = 13
        
#        widget.ProcessEvent(ret)

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


class TestLogger:
    def __init__(self,filepath=None,description="A testcase"):
        if filepath:
            self.inTerminal = False
            try:
                self.File = open(filepath, 'a')
            except IOError:
                print "Unable to open file %s" % filepath
                print "log report in default_test.log"
                self.File = open("default_test.log", 'a')
        else:
            self.inTerminal = True
        # usefull inits
        self.startDate = datetime.now()
        self.nbPass = 0
        self.nbFail = 0
        self.nbUnchecked = 0
        self.nbAction = 0
        self.failureList = []
        self.passedList = []
        self.checked = False
        self.actionDescription = "No action description"
        self.mainDescription = description
        self.actionStartTime = self.actionEndTime = self.actionStartDate = self.actionEndDate = None
        # some printing
        self.Print("")
        self.Print("******* Testcase : %s (date : %s) *******" %(self.mainDescription, self.startDate))
            
    def Print(self,string):
        if self.inTerminal:
            print "%s" %string
        else:
            self.File.write(string+'\n')

    def Start(self,string):
        # usefull inits
        self.failureList = []
        self.passedList = []
        self.checked = False
        self.actionDescription = string
        self.actionStartTime = self.actionEndTime = time.time()
        self.actionStartDate = datetime.now()

    def Stop(self):
        self.actionEndTime = time.time()
        self.actionEndDate = datetime.now()
        

    def Report(self):
        self.nbAction = self.nbAction + 1
        elapsed = self.actionEndTime - self.actionStartTime
        self.Print("")
        self.Print("Action = "+self.actionDescription)
        if self.actionStartTime == None: # Stop method has not been called
            self.Print("!!! No time informations available !!!")
        else:
            self.Print("Start date (before %s) = %s" %(self.actionDescription, self.actionStartDate))
            self.Print("End date (after %s) = %s" %(self.actionDescription, self.actionEndDate))
            self.Print("Time Elapsed = %.3f seconds" %elapsed)
        self.Print("Report : ")
        for failure in self.failureList:
            self.Print("        - Error : %s" % failure)
        for passed in self.passedList:
            self.Print("        - Ok : %s" % passed)
        if len(self.failureList) == 0 and self.checked:
            status = "PASS"
            self.nbPass = self.nbPass + 1
        elif len(self.failureList) == 0 and not self.checked:
            status = "UNCHECKED"
            self.nbUnchecked = self.nbUnchecked + 1
        else:
            status = "FAIL"
            self.nbFail = self.nbFail + 1
        self.Print("ACTION STATUS = %s" % status)
        if self.checked:
            self.Print("-------------------------------------------------------------------------------------------------")
        else: 
            self.Print(".................................................................................................")
        
    def InitFailureList(self):
        self.failureList = []
    
    def ReportFailure(self, string):
        self.failureList.append(string)

    def ReportPass(self, string):
        self.passedList.append(string)

    def SetChecked(self, bool):
        self.checked = bool
    
    def Close(self):
        now = datetime.now()
        elapsed = now - self.startDate
        self.Print("------------------------------------------REPORT-------------------------------------------------")
        self.Print("Start date (before %s testcase) = %s" %(self.mainDescription, self.startDate))
        self.Print("End date (after %s testcase) = %s" %(self.mainDescription, now))
        self.Print("Time Elapsed = %s" %elapsed)
        self.Print("")
        self.Print("Total number of actions : %s" % self.nbAction)
        self.Print("Total number of actions PASSED : %s" %self.nbPass)
        self.Print("Total number of actions FAILED : %s" %self.nbFail)
        self.Print("Total number of actions UNCHECKED : %s" %self.nbUnchecked)
        self.Print("")
        if self.nbPass == self.nbAction:
            status = "PASS"
        else:
            status = "FAIL"
        # convert the elapsed tme in minutes
        elapsed_min = (elapsed.seconds / 60.0) + (elapsed.microseconds / 60000000.0)
        self.Print("#TINDERBOX# Testname = %s" %self.mainDescription)    
        self.Print("#TINDERBOX# Status = %s" %status)
        self.Print("#TINDERBOX# Time elapsed = %s" %elapsed_min)
        self.Print("OSAF_QA: %s | %s | %s | %s" %(self.mainDescription, 1, elapsed_min, elapsed_min)) 
        self.Print("")
        self.Print("******* End of Report *******")
        print("#TINDERBOX# Testname = %s" %self.mainDescription)    
        print("#TINDERBOX# Status = %s" %status)
        print("#TINDERBOX# Time elapsed = %s" %elapsed_min)
        print("OSAF_QA: %s | %s | %s | %s" %(self.mainDescription, 1, elapsed_min, elapsed_min)) 
        self.Print("******* End of Report *******")
        if not self.inTerminal:
            self.File.close()


class BaseByUI :
    def __init__(self, view, type, logger):
        if not type in ["Event", "Note", "Task", "MailMessage", "Collection"]:
            return
        else:
            self.isNote = self.isEvent = self.isTask = self.isMessage = self.allDay = False
            self.logger = logger
            now = datetime.now()
            if type == "Event": # New Calendar Event
                # set up the expected data dictionary with the default values
                self.expected_field_dict = {"displayName" : "New Event", "startTime" : now, "endTime" : now, "duration" : timedelta(minutes=60)}
                # create a default Calendar Event
                item = Calendar.CalendarEvent(view=view)
                item.startTime = self.expected_field_dict["startTime"] # because startTime is needed befor duration
                self.isEvent = True
            elif type == "Note": # New Note
                # set up the expected data dictionary with the default values
                self.expected_field_dict = {"displayName" : "New Note", "createdOn" : now}
                # create a default Note
                item = Notes.Note(view=view)
                self.isNote = True
            elif type == "Task": # New Task
                # set up the expected data dictionary with the default values
                self.expected_field_dict = {"displayName" : "New Task", "createdOn" : now}
                # create a default Task
                item = Task(view=view)
                self.isTask = True
            elif type == "MailMessage": # New Mail Message
                # set up the expected data dictionary with the default values
                email = Mail.EmailAddress(view=view)
                email.emailAddress = 'me'
                self.expected_field_dict = {"subject" : "untitled", "dateSent" : now, "fromAddress" : email}
                # create a default Message
                item = Mail.MailMessage(view=view)
                self.isMessage = True
            elif type == "Collection": # New Collection
                # set up the expected data dictionary with the default values
                self.expected_field_dict = {"displayName" : "Untitled"}
                # create a default Collection
                item = ItemCollection.ItemCollection(view=view)
                
                
            # fields affectation
            for field in self.expected_field_dict.keys():
                setattr(item, field, self.expected_field_dict[field])

            self.item = item

            if type =="Collection":
                Sgf.SidebarAdd(self.item)
                Sgf.SidebarSelect(self.item)
            else:
                Sgf.SummaryViewSelect(self.item)
                

    def SetAttr(self, displayName=None, startDate=None, startTime=None, endDate=None, endTime=None, location=None, body=None,
                status=None, alarm=None, fromAddress=None, toAddress=None, allDay=None, stampEvent=None, stampMail=None,
                stampTask=None, dict=None):
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
            self.logger.Report()
        
        
    
    def updateExpectedFieldDict(self, dict):
        for field in dict.keys():
            if field == "startDate": # start date update
                tmp = string.split(dict[field],"/")
                if self.expected_field_dict.has_key("startTime"):
                    startTime = self.expected_field_dict["startTime"]
                    new = datetime(month=string.atoi(tmp[0]), day=string.atoi(tmp[1]), year=string.atoi(tmp[2]), hour=startTime.hour, minute=startTime.minute)
                else:
                    new = datetime(month=string.atoi(tmp[0]), day=string.atoi(tmp[1]), year=string.atoi(tmp[2]))
                self.expected_field_dict["startTime"] = new
            elif field == "startTime": # start time update
                tmp = string.split(dict[field],":")
                if self.expected_field_dict.has_key("startTime"):
                    startTime = self.expected_field_dict["startTime"]
                    new = datetime(month=startTime.month, day=startTime.day, year=startTime.year, hour=string.atoi(tmp[0]), minute=string.atoi(tmp[1][:2]))
                else:
                    new = datetime(hour=string.atoi(tmp[0]), minute=string.atoi(tmp[1]))
                self.expected_field_dict["startTime"] = new
            elif field == "endDate": # end date update
                tmp = string.split(dict[field],"/")
                if self.expected_field_dict.has_key("endTime"):
                    endTime = self.expected_field_dict["endTime"]
                    new = datetime(month=string.atoi(tmp[0]), day=string.atoi(tmp[1]), year=string.atoi(tmp[2]), hour=endTime.hour, minute=endTime.minute)
                else:
                    new = datetime(month=string.atoi(tmp[0]), day=string.atoi(tmp[1]), year=string.atoi(tmp[2]))
                self.expected_field_dict["endTime"] = new
            elif field == "endTime": # end time update
                tmp = string.split(dict[field],":")
                if self.expected_field_dict.has_key("endTime"):
                    endTime = self.expected_field_dict["endTime"]
                    new = datetime(month=endTime.month, day=endTime.day, year=endTime.year, hour=string.atoi(tmp[0]), minute=string.atoi(tmp[1][:2]))
                else:
                    new = datetime(hour=string.atoi(tmp[0]), minute=string.atoi(tmp[1]))
                self.expected_field_dict["endTime"] = new
            elif field == "fromAddress": # from address update
                email = Mail.EmailAddress(view=view)
                email.emailAddress = dict[field]
                self.expected_field_dict["fromAdress"] = email
            elif field == "toAddress": # from address update
                email = Mail.EmailAddress(view=view)
                email.emailAddress = dict[field]
                self.expected_field_dict["toAdress"] = email
                
            else:
                self.expected_field_dict[field] = dict[field]
            
                
    def SetDisplayName(self, displayName, dict=None):
        if (self.isNote or self.isEvent or self.isTask or self.isMessage):
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            if dict:
                self.logger.Start("Set the display name to : %s" %displayName)
            s1 = time.time()
            Sgf.SummaryViewSelect(self.item)
            displayNameBlock = Sgf.DisplayName()
            # Emulate the mouse click in the display name block
            Sgf.LeftClick(displayNameBlock)
            # Select the old text
            displayNameBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(displayName)
            Sgf.SummaryViewSelect(self.item)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()  
        else:
            self.logger.Print("SetDisplayName is not available for this kind of item")
            return

    def SetStartTime(self, startTime, dict=None):
        if (self.isEvent and not self.allDay):
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            if dict:
                self.logger.Start("Set the start time to : %s" %startTime)
            Sgf.SummaryViewSelect(self.item)
            startTimeBlock = Sgf.StartTime()
            # Emulate the mouse click in the start time block
            Sgf.LeftClick(startTimeBlock)
            # Select the old text
            startTimeBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(startTime)
            Sgf.SummaryViewSelect(self.item)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()  
        else:
            self.logger.Print("SetStartTime is not available for this kind of item")
            return

    def SetStartDate(self, startDate, dict=None):
        if self.isEvent:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            if dict:
                self.logger.Start("Set the start date to : %s" %startDate)
            Sgf.SummaryViewSelect(self.item)
            startDateBlock = Sgf.StartDate()
            # Emulate the mouse click in the start date block
            Sgf.LeftClick(startDateBlock)
            # Select the old text
            startDateBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(startDate)
            Sgf.SummaryViewSelect(self.item)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()
        else:
            self.logger.Print("SetStartDate is not available for this kind of item")
            return

    def SetEndTime(self, endTime, dict=None):
        if (self.isEvent and not self.allDay):
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            if dict:
                self.logger.Start("Set the end time to : %s" %endTime)
            Sgf.SummaryViewSelect(self.item)
            endTimeBlock = Sgf.EndTime()
            # Emulate the mouse click in the end time block
            Sgf.LeftClick(endTimeBlock)
            # Select the old text
            endTimeBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(endTime)
            Sgf.SummaryViewSelect(self.item)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()
        else:
            self.logger.Print("SetEndTime is not available for this kind of item")
            return
    
    def SetEndDate(self, endDate, dict=None):
        if self.isEvent:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            if dict:
                self.logger.Start("Set the end date to : %s" %endDate)
            Sgf.SummaryViewSelect(self.item)
            endDateBlock = Sgf.EndDate()
            # Emulate the mouse click in the end date block
            Sgf.LeftClick(endDateBlock)
            # Select the old text
            endDateBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(endDate)
            Sgf.SummaryViewSelect(self.item)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()
        else:
            self.logger.Print("SetEndDate is not available for this kind of item")
            return

    def SetLocation(self, location, dict=None):
        if self.isEvent:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            if dict:
                self.logger.Start("Set the location to : %s" %location)
            Sgf.SummaryViewSelect(self.item)
            locationBlock = Sgf.Location()
            Sgf.LeftClick(locationBlock)
            # Select the old text
            locationBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(location)
            Sgf.SummaryViewSelect(self.item)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()
        else:
            self.logger.Print("SetLocation is not available for this kind of item")
            return

    def SetAllDay(self, allDay, dict=None):
        if self.isEvent:
            if dict:
                self.logger.Start("Set the all Day to : %s" %allDay)
            Sgf.SummaryViewSelect(self.item)
            allDayBlock = Sgf.FindNamedBlock("EditAllDay")
            # Emulate the mouse click in the all-day block
            Sgf.LeftClick(allDayBlock)
            # Process the event corresponding to the selection
            allDayBlock.widget.SetValue(allDay)
            selectionEvent = wx.CommandEvent(wx.wxEVT_COMMAND_CHECKBOX_CLICKED)
            selectionEvent.SetEventObject(allDayBlock.widget)
            allDayBlock.widget.ProcessEvent(selectionEvent)
            Sgf.SummaryViewSelect(self.item)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()
            self.allDay = allDay
        else:
            self.logger.Print("SetAllDay is not available for this kind of item")
            return
   
    def SetStatus(self, status, dict=None):
        if self.isEvent:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
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
                Sgf.SummaryViewSelect(self.item)
                if dict:
                    self.logger.Stop()
                    self.Check_DetailView(dict)
                    self.logger.Report()
        else:
            self.logger.Print("SetStatus is not available for this kind of item")
            return

    def SetAlarm(self, alarm, dict=None):
        if self.isEvent:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            if alarm == "1":
                alarm = alarm + " minute"
            else:
                alarm = alarm + " minutes"
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
                Sgf.SummaryViewSelect(self.item)
                if dict:
                    self.logger.Stop()
                    self.Check_DetailView(dict)
                    self.logger.Report()
        else:
            self.logger.Print("SetAlarm is not available for this kind of item")
            return
    
    def SetBody(self, body, dict=None):
        #self.updateExpectedFieldDict(dict) # update the expected field dict
        if dict:
            self.logger.Start("Set the body")
        Sgf.SummaryViewSelect(self.item)
        noteArea = Sgf.FindNamedBlock("NotesArea")
        # Emulate the mouse click in the note area
        Sgf.LeftClick(noteArea)
        noteArea.widget.SelectAll()
        # Emulate the keyboard events
        Sgf.Type(body)
        Sgf.SummaryViewSelect(self.item)
        if dict:
            self.logger.Stop()
            self.Check_DetailView(dict)
            self.logger.Report()

    def SetToAddress(self, toAdd, dict=None):
        if self.isMessage:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            if dict:
                self.logger.Start("Set the to address to : %s" %toAdd)
            Sgf.SummaryViewSelect(self.item)
            toBlock = Sgf.FindNamedBlock("ToMailEditField")
            # Emulate the mouse click in the to block
            Sgf.LeftClick(toBlock)
            toBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(toAdd)
            Sgf.SummaryViewSelect(self.item)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()
        else:
            self.logger.Print("SetToAddress is not available for this kind of item")
            return
        
    def SetFromAddress(self, fromAdd, dict=None):
        if self.isMessage:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            if dict:
                self.logger.Start("Set the from address to : %s" %fromAdd)
            Sgf.SummaryViewSelect(self.item)
            fromBlock = Sgf.FindNamedBlock("FromEditField")
            # Emulate the mouse click in the from block
            Sgf.LeftClick(fromBlock)
            fromBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(fromAdd)
            Sgf.SummaryViewSelect(self.item)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()
        else:
            self.logger.Print("SetFromAddress is not available for this kind of item")
            return

    
    def StampAsMailMessage(self, stampMail, dict=None):
        if stampMail == self.isMessage:# Nothing to do
            return
        else:
            if dict:
                self.logger.Start("Change the Mail stamp to : %s" %stampMail)
            Sgf.SummaryViewSelect(self.item)
            Sgf.StampAsMailMessage()
            self.isMessage = stampMail
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()

    def StampAsTask(self, stampTask, dict=None):
        if stampTask == self.isTask:# Nothing to do
            return
        else:
            if dict:
                self.logger.Start("Change the Task stamp to : %s" %stampTask)
            Sgf.SummaryViewSelect(self.item)
            Sgf.StampAsTask()
            self.isTask = stampTask
            stampTaskBlock = Sgf.FindNamedBlock("TaskStamp")
            stampTaskBlock.widget.SetToggle(stampTask)
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()

    def StampAsCalendarEvent(self, stampEvent, dict=None):
        if stampEvent == self.isEvent:# Nothing to do
            return
        else:
            if dict:
                self.logger.Start("Change the Calendar Event stamp to : %s" %stampEvent)
            Sgf.SummaryViewSelect(self.item)
            Sgf.StampAsCalendarEvent()
            self.isEvent = stampEvent
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                self.logger.Report()
        
    def Check_DetailView(self, dict):
        self.logger.InitFailureList()
        self.logger.SetChecked(True)
        # check the changing values
        for field in dict.keys():
            Sgf.SummaryViewSelect(self.item)
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
                locationBlock = Sgf.FindNamedBlock("AECalendarLocation")
                loc = locationBlock.widget.GetValue()
                if not dict[field] == loc :
                    self.logger.ReportFailure("(On location Checking) || detail view location = %s ; expected location = %s" %(loc, dict[field]))
                else:
                    self.logger.ReportPass("(On location Checking)")
            elif field == "body": # body checking
                noteBlock = Sgf.FindNamedBlock("NotesArea")
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
                print stampMail
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
        
    
    def Check_Object(self, dict):
        self.logger.InitFailureList()
        self.logger.SetChecked(True)
        # check the changing values
        for field in dict.keys():
            if field == "displayName": # display name checking
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
                endTime = self.item.startTime + self.item.duration
                e_date = "%s/%s/%s" %(endTime.month, endTime.day, endTime.year) 
                if not dict[field] == e_date :
                    self.logger.ReportFailure("(On end date Checking) || object end date = %s ; expected end date = %s" %(e_date, dict[field]))
                else:
                    self.logger.ReportPass("(On end date Checking)")
            elif field == "endTime": # end time checking
                endTime = self.item.startTime + self.item.duration
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
            #elif field == "alarm": # status checking
            #    r_time = self.item.reminderTime - self.item.startTime
            #    alarm = "%s" %r_time
            #    if not dict[field] == alarm :
            #        self.logger.ReportFailure("(On alarm Checking) || object alarm = %s ; expected alarm = %s" %(alarm, dict[field]))
            #    else:
            #        self.logger.ReportPass("(On alarm Checking)")
            elif field == "allDay": # status checking
                allDay = self.item.allDay
                if not dict[field] == allDay :
                    self.logger.ReportFailure("(On all Day Checking) || object all day = %s ; expected all day = %s" %(allDay, dict[field]))
                else:
                    self.logger.ReportPass("(On all Day Checking)")

        
class Accounts:
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
