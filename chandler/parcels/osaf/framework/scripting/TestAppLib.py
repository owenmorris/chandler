from datetime import datetime, timedelta
import ScriptingGlobalFunctions as Sgf
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.Notes as Notes
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.mail.Mail as Mail
import wx
import time


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
        self.nbPass = 0
        self.nbFail = 0
        self.nbTestCase = 0
        self.Print("")
        self.Print("******* New Report :  date : %s *******" % self.startDate)
            
    def Print(self,string):
        self.File.write(string+'\n')

    def Start(self,string):
        self.failureList = []
        self.description = string
        self.startTime = time.time()
        self.stopTime = None

    def Stop(self):
        self.stopTime = time.time()

    def SetStatus(self,status):
        self.status = status

    def Report(self):
        self.nbTestCase = self.nbTestCase + 1
        elapsed = self.stopTime - self.startTime
        self.Print("")
        self.Print("Test case = "+self.description)
        self.Print("Start Time = %s // Stop Time = %s // Time Elapsed = %s" %(self.startTime, self.stopTime, elapsed))
        self.Print("Status : ")
        if len(self.failureList) == 0:
            self.nbPass = self.nbPass + 1
            self.Print("        - PASS")
        else :
            self.nbFail = self.nbFail + 1
            for failure in self.failureList:
                self.Print("        - %s" % failure)
        
        self.Print("................................................................................................")
        
    def InitFailureList(self):
        self.failureList = []
    
    def reportFailure(self, string):
        self.failureList.append(string)
        
    def Close(self):
        now = datetime.now()
        self.Print("------------------------------------------REPORT-------------------------------------------------")
        self.Print("start : %s // end : %s // Time Elapsed : %s" %(self.startDate, now, now-self.startDate))
        self.Print("Total number of test case : %s" % self.nbTestCase)
        self.Print("Total number of test case PASSED : %s" % self.nbPass)
        self.Print("Total number of test case FAILED : %s" % self.nbFail)
        self.Print("")
        self.Print("******* End of Report *******")
        self.File.close()

class Item :
    def SetDisplayName(self, displayName):
        self.displayName = displayName # put into memory the expected value
        #self.logger.Start("Set the display name in the detail view") # start the log
        Sgf.SummaryViewSelect(self.item)
        displayNameBlock = Sgf.DisplayName()
        # Emulate the mouse click in the display name block
        Sgf.LeftClick(displayNameBlock)
        # Select the old text
        displayNameBlock.widget.SelectAll()
        # Emulate the keyboard events
        Sgf.Type(self.displayName)
        #self.logger.Stop() # stop the log

        #self.Check_DetailView() # check the detail view
        #self.logger.Report() # make the report

    def StampAsMailMessage(self):
        Sgf.SummaryViewSelect(self.item)
        Sgf.StampAsMailMessage()

    def StampAsTask(self):
        Sgf.SummaryViewSelect(self.item)
        Sgf.StampAsTask()

    def StampAsCalendarEvent(self):
        Sgf.SummaryViewSelect(self.item)
        Sgf.StampAsCalendarEvent()

    def SetNote(self, string):
        Sgf.SummaryViewSelect(self.item)
        # Emulate the mouse click in the note area
        noteArea = Sgf.FindNamedBlock("NotesArea")
        # Emulate the mouse click in the note area
        Sgf.LeftClick(noteArea)
        noteArea.widget.SelectAll()
        # Emulate the keyboard events
        Sgf.Type(string)
        

class CalendarEventByUI(Item):
    def __init__(self, view, logger):
        # set the attributes and put into memory the expected default value
        self.logger = logger
        self.displayName = "New Event"
        now = datetime.now()
        self.startTime = "%s:%s" %(now.hour, now.minute)
        year = "%s" %now.year
        self.startDate = "%s/%s/%s" %(now.month, now.day, year[-2:])# [-2:] chandler display yy not yyyy
        self.duration = 60
        # create a default calendar event
        self.logger.Start("Default calendar event creation") # start the log
        event = Calendar.CalendarEvent(view=view)
        event.startTime = now
        event.duration = timedelta(minutes=self.duration)
        event.displayName = self.displayName
        Sgf.SummaryViewSelect(event)
        self.item = event
        self.logger.Stop() # stop the log
        # Check the detail view display
        self.Check_DetailView()
        self.logger.Report() # make the report
        
    def Check_DetailView(self):
        self.logger.InitFailureList()
        # Check the displayName
        Sgf.SummaryViewSelect(self.item)
        displayNameBlock = Sgf.DisplayName()
        d_name = displayNameBlock.widget.GetValue()
        if not self.displayName == d_name :
            self.logger.reportFailure("FAIL (On display name Checking)  || detail view title = %s ; expected title = %s" %(d_name, self.displayName))
        # Check the start date
        #Sgf.SummaryViewSelect(self.item)
        #startDateBlock = Sgf.StartDate()
        #s_date = startDateBlock.widget.GetValue()
        #if not self.startDate == s_date :
        #    self.logger.reportFailure("FAIL (On start date Checking) || detail view start date = %s ; expected start date= %s" %(s_date, self.startDate))
        # Check the end date
        
    def SetStartTime(self, startTime):
        Sgf.SummaryViewSelect(self.item)
        startTimeBlock = Sgf.StartTime()
        # Emulate the mouse click in the start time block
        Sgf.LeftClick(startTimeBlock)
        # Emulate the keyboard events
        Sgf.Type(startTime)

    def SetEndTime(self, endTime):
        Sgf.SummaryViewSelect(self.item)
        endTimeBlock = Sgf.EndTime()
        # Emulate the mouse click in the end time block
        Sgf.LeftClick(endTimeBlock)
        # Emulate the keyboard events
        Sgf.Type(endTime)

    def SetStartDate(self, startDate):
        self.startDate = startDate # put into memory the expected value
        #self.logger.Start("Set the start date in the detail view") # start the log
        Sgf.SummaryViewSelect(self.item)
        startDateBlock = Sgf.StartDate()
        # Emulate the mouse click in the start date block
        Sgf.LeftClick(startDateBlock)
        # Emulate the keyboard events
        startDateBlock.widget.SelectAll()
        Sgf.Type(startDate)
        #self.logger.Stop() # stop the log
        #self.Check_DetailView() # Check the detail view
        #self.logger.Report() # make the report
        
    def SetEndDate(self, endDate):
        Sgf.SummaryViewSelect(self.item)
        endDateBlock = Sgf.EndDate()
        # Emulate the mouse click in the end date block
        Sgf.LeftClick(endDateBlock)
        # Emulate the keyboard events
        Sgf.Type(endDate)

    def SetLocation(self, location):
        Sgf.SummaryViewSelect(self.item)
        locationBlock = Sgf.Location()
        Sgf.LeftClick(locationBlock)
        # Select the old text
        locationBlock.widget.SelectAll()
        # Emulate the keyboard events
        Sgf.Type(location)

    def ClickAllDay(self):
        Sgf.SummaryViewSelect(self.item)
        allDayBlock = Sgf.AllDay()
        # Emulate the mouse click in the all-day block
        Sgf.LeftClick(allDayBlock)
   
    def SetStatus(self, status):
        statusBlock = Sgf.FindNamedBlock("EditTransparency")
        list_of_value = []
        for i in range(0,statusBlock.widget.GetCount()):
            list_of_value.append(statusBlock.widget.GetString(i))
        if not status in list_of_value:
            return
        else:
            # Emulate the mouse click in the status block
            Sgf.LeftClick(statusBlock)
            statusBlock.widget.SetStringSelection(status) # bad: the status is not saved

    def SetAlarm(self, alarm):
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


class NoteByUI(Item) :
    def __init__(self, view, logger=None):
        self.displayName = "New Note"
        self.createdOn = datetime.now()
        note = Notes.Note(view=view)
        note.displayName = self.displayName
        note.createdOn = self.createdOn
        self.item = note
        Sgf.SummaryViewSelect(self.item)


class TaskByUI(Item):
    def __init__(self, view, logger=None):
        self.displayName = "New Task"
        self.createdOn = datetime.now()
        task = Task.Task(view=view)
        task.displayName = self.displayName
        task.createdOn = self.createdOn
        self.item = task
        Sgf.SummaryViewSelect(self.item)

    
