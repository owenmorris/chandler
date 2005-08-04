from datetime import datetime, timedelta
import ScriptingGlobalFunctions as Sgf
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.Notes as Notes
from osaf.contentmodel.tasks import Task
import osaf.contentmodel.mail as Mail
import wx
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


class TestLogger:
    def __init__(self,filepath):
        try:
            self.File = open(filepath, 'a')
        except IOError:
            print "Unable to open file %s" % filepath
            print "log report in default_test.log"
            self.File = open("default_test.log", 'a')
        self.startDate = datetime.now()
        # usefull counters init
        self.nbPass = 0
        self.nbFail = 0
        self.nbUnchecked = 0
        self.nbTestCase = 0
        self.Print("")
        self.Print("******* New Report :  date : %s *******" % self.startDate)
            
    def Print(self,string):
        self.File.write(string+'\n')

    def Start(self,string):
        self.failureList = []
        self.passedList = []
        self.checked = False
        self.description = string
        self.startTime = time.time()
        self.stopTime = None

    def Stop(self):
        self.stopTime = time.time()

    def Report(self):
        self.nbTestCase = self.nbTestCase + 1
        elapsed = self.stopTime - self.startTime
        self.Print("")
        self.Print("Test case = "+self.description)
        self.Print("Start Time = %s // Stop Time = %s // Time Elapsed = %s" %(self.startTime, self.stopTime, elapsed))
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
        self.Print("STATUS = %s" % status)
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
        self.Print("------------------------------------------REPORT-------------------------------------------------")
        self.Print("start : %s // end : %s // Time Elapsed : %s" %(self.startDate, now, now-self.startDate))
        self.Print("Total number of test case : %s" % self.nbTestCase)
        self.Print("Total number of test case PASSED : %s" % self.nbPass)
        self.Print("Total number of test case FAILED : %s" % self.nbFail)
        self.Print("Total number of test case UNCHECKED : %s" % self.nbUnchecked)
        self.Print("")
        self.Print("******* End of Report *******")
        self.File.close()


class ItemByUI :
    def __init__(self, view, type, logger):
        if not type in ["Event", "Note", "Task", "MailMessage", "Collection"]:
            return
        else:
            self.isNote = self.isEvent = self.isTask = self.isMessage = False
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

    def SetAttr(self, displayName=None, startDate=None, startTime=None, endDate=None, endTime=None, dict=None):
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
        if (self.isNote or self.isEvent or self.isTask or self.isMessage) :
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            self.logger.Start("Set the display name")
            Sgf.SummaryViewSelect(self.item)
            displayNameBlock = Sgf.DisplayName()
            # Emulate the mouse click in the display name block
            Sgf.LeftClick(displayNameBlock)
            # Select the old text
            displayNameBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(displayName)
            Sgf.SummaryViewSelect(self.item)
            self.logger.Stop()
            if dict:
                self.Check_DetailView(dict)
            self.logger.Report()  
        else:
            print "not available for this kind of item"
            return

    def SetStartTime(self, startTime, dict=None):
        if self.isEvent:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            self.logger.Start("Set the start time")
            Sgf.SummaryViewSelect(self.item)
            startTimeBlock = Sgf.StartTime()
            # Emulate the mouse click in the start time block
            Sgf.LeftClick(startTimeBlock)
            # Select the old text
            startTimeBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(startTime)
            Sgf.SummaryViewSelect(self.item)
            self.logger.Stop()
            if dict:
                self.Check_DetailView(dict)
            self.logger.Report()  
        else:
            print "not available for this kind of item"
            return

    def SetStartDate(self, startDate, dict=None):
        if self.isEvent:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            self.logger.Start("Set the start date")
            Sgf.SummaryViewSelect(self.item)
            startDateBlock = Sgf.StartDate()
            # Emulate the mouse click in the start date block
            Sgf.LeftClick(startDateBlock)
            # Select the old text
            startDateBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(startDate)
            Sgf.SummaryViewSelect(self.item)
            self.logger.Stop()
            if dict:
                self.Check_DetailView(dict)
            self.logger.Report()
        else:
            print "not available for this kind of item"
            return

    def SetEndTime(self, endTime, dict=None):
        if self.isEvent:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            self.logger.Start("Set the end time")
            Sgf.SummaryViewSelect(self.item)
            endTimeBlock = Sgf.EndTime()
            # Emulate the mouse click in the end time block
            Sgf.LeftClick(endTimeBlock)
            # Select the old text
            endTimeBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(endTime)
            Sgf.SummaryViewSelect(self.item)
            self.logger.Stop()
            if dict:
                self.Check_DetailView(dict)
            self.logger.Report()
        else:
            print "not available for this kind of item"
            return
    
    def SetEndDate(self, endDate, dict=None):
        if self.isEvent:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            self.logger.Start("Set the end date")
            Sgf.SummaryViewSelect(self.item)
            endDateBlock = Sgf.EndDate()
            # Emulate the mouse click in the end date block
            Sgf.LeftClick(endDateBlock)
            # Select the old text
            endDateBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(endDate)
            Sgf.SummaryViewSelect(self.item)
            self.logger.Stop()
            if dict:
                self.Check_DetailView(dict)
            self.logger.Report()
        else:
            print "not available for this kind of item"
            return

    def SetLocation(self, location, dict=None):
        if self.isEvent:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            self.logger.Start("Set the location")
            Sgf.SummaryViewSelect(self.item)
            locationBlock = Sgf.Location()
            Sgf.LeftClick(locationBlock)
            # Select the old text
            locationBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(location)
            Sgf.SummaryViewSelect(self.item)
            self.logger.Stop()
            if dict:
                self.Check_DetailView(dict)
            self.logger.Report()
        else:
            print "not available for this kind of item"
            return

    def ClickAllDay(self):
        if self.isEvent:
            Sgf.SummaryViewSelect(self.item)
            allDayBlock = Sgf.AllDay()
            # Emulate the mouse click in the all-day block
            Sgf.LeftClick(allDayBlock)
            # Process the event corresponding to the selection
            allDayBlock.widget.SetValue(True)
            selectionEvent = wx.CommandEvent(wx.wxEVT_COMMAND_CHECKBOX_CLICKED)
            selectionEvent.SetEventObject(allDayBlock.widget)
            allDayBlock.widget.ProcessEvent(selectionEvent)
            Sgf.SummaryViewSelect(self.item)
            
        else:
            print "not available for this kind of item"
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
                # Emulate the mouse click in the status block
                Sgf.LeftClick(statusBlock)
                statusBlock.widget.SetStringSelection(status)
                # Process the event corresponding to the selection
                selectionEvent = wx.CommandEvent(wx.wxEVT_COMMAND_CHOICE_SELECTED)
                selectionEvent.SetEventObject(statusBlock.widget)
                statusBlock.widget.ProcessEvent(selectionEvent)
                

                    
                #Sgf.SummaryViewSelect(self.item)
        else:
            print "not available for this kind of item"
            return

    def SetAlarm(self, alarm, dict=None):
        if self.isEvent:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            alarmBlock = Sgf.FindNamedBlock("EditReminder")
            list_of_value = []
            for i in range(0,statusBlock.widget.GetCount()):
                list_of_value.append(statusBlock.widget.GetString(i))
            if not alarm in list_of_value:
                return
            else:
                # Emulate the mouse click in the reminder block
                Sgf.LeftClick(alarmBlock)
                alarmBlock.widget.SetStringSelection(alarm) # bad: the status is not saved
                Sgf.SummaryViewSelect(self.item)
        else:
            print "not available for this kind of item"
            return
    
    def SetNote(self, note, dict=None):
        #self.updateExpectedFieldDict(dict) # update the expected field dict
        self.logger.Start("Set the location")
        Sgf.SummaryViewSelect(self.item)
        noteArea = Sgf.FindNamedBlock("NotesArea")
        # Emulate the mouse click in the note area
        Sgf.LeftClick(noteArea)
        noteArea.widget.SelectAll()
        # Emulate the keyboard events
        Sgf.Type(note)
        Sgf.SummaryViewSelect(self.item)
        self.logger.Stop()
        if dict:
            self.Check_DetailView(dict)
        self.logger.Report()

    def SetToAddress(self, toAdd, dict=None):
        if self.isMessage:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            self.logger.Start("Set the to address")
            Sgf.SummaryViewSelect(self.item)
            toBlock = Sgf.FindNamedBlock("ToMailEditField")
            # Emulate the mouse click in the to block
            Sgf.LeftClick(toBlock)
            toBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(toAdd)
            Sgf.SummaryViewSelect(self.item)
            self.logger.Stop()
            if dict:
                self.Check_DetailView(dict)
            self.logger.Report()
        else:
            print "not available for this kind of item"
            return
        
    def SetFromAddress(self, fromAdd, dict=None):
        if self.isMessage:
            #self.updateExpectedFieldDict(dict) # update the expected field dict
            self.logger.Start("Set the from address")
            Sgf.SummaryViewSelect(self.item)
            fromBlock = Sgf.FindNamedBlock("FromEditField")
            # Emulate the mouse click in the from block
            Sgf.LeftClick(fromBlock)
            fromBlock.widget.SelectAll()
            # Emulate the keyboard events
            Sgf.Type(fromAdd)
            Sgf.SummaryViewSelect(self.item)
            self.logger.Stop()
            if dict:
                self.Check_DetailView(dict)
            self.logger.Report()
        else:
            print "not available for this kind of item"
            return

    
    def StampAsMailMessage(self):
        Sgf.SummaryViewSelect(self.item)
        Sgf.StampAsMailMessage()
        if not self.isMessage :
            self.isMessage = True
        else:
            self.isMessage = False

    def StampAsTask(self):
        Sgf.SummaryViewSelect(self.item)
        Sgf.StampAsTask()
        if not self.isTask :
            self.isTask = True
        else:
            self.isTask = False

    def StampAsCalendarEvent(self):
        Sgf.SummaryViewSelect(self.item)
        Sgf.StampAsCalendarEvent()
        if not self.isEvent :
            self.isEvent = True
        else:
            self.isEvent = False
        
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
            elif field == "note": # note checking
                noteBlock = Sgf.FindNamedBlock("NotesArea")
                note = noteBlock.widget.GetValue()
                if not dict[field] == note :
                    self.logger.ReportFailure("(On note Checking) || detail view note = %s ; expected note = %s" %(note, dict[field]))
                else:
                     self.logger.ReportPass("(On note Checking)")
            elif field == "status": # status checking
                statusBlock = Sgf.FindNamedBlock("EditTransparency")
                status = statusBlock.GetStringSelection()
                if not dict[field] == status :
                    self.logger.ReportFailure("(On status Checking) || detail view status = %s ; expected status = %s" %(status, dict[field]))
                else:
                    self.logger.ReportPass("(On status Checking)")
            elif field == "alarm": # alarm checking
                alarmBlock = Sgf.FindNamedBlock("EditTransparency")
                alarm = alarmBlock.GetStringSelection()
                if not dict[field] == alarm :
                    self.logger.ReportFailure("(On alarm Checking) || detail view alarm = %s ; expected alarm = %s" %(alarm, dict[field]))
                else:
                    self.logger.ReportPass("(On alarm Checking)")
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

    

    

    




    
