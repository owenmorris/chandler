from QALogger import *
from datetime import datetime, timedelta
from osaf import pim
import osaf.pim.mail as Mail
import osaf.pim.collections as Collection
import osaf.sharing as Sharing
import application.Globals as Globals
import wx
import string
import osaf.framework.scripting as scripting

#Global AppProxy instance
App_ns = scripting.app_ns()

                       
def getTime(date):
    """
    Return a string representation in 24h format of the time corresponding to the given date
    @type date : datetime
    @return : string
    """
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

def SetBlockMenu(menuName, menuChoice):
    '''
    Select a choice in a list menu
    @type menuName : string
    @param menuName : The name of the menu
    @type menuChoice : string
    @param menuChoice : the choice you want to select
    @return : True if the selection is succesfull
    '''
    block = App_ns.__getattr__(menuName)
    list_of_value = []
    for k in range(0,block.widget.GetCount()):
        list_of_value.append(block.widget.GetString(k))
    if not menuChoice in list_of_value:
        return False
    else:
        # Emulate the mouse click in the menu
        scripting.User.emulate_click(block)
        block.widget.SetStringSelection(menuChoice)
        # Process the event corresponding to the selection
        selectionEvent = wx.CommandEvent(wx.wxEVT_COMMAND_CHOICE_SELECTED)
        selectionEvent.SetEventObject(block.widget)
        block.widget.ProcessEvent(selectionEvent)
        return True

def GetCollectionRow(cellName):
    for i in range(App_ns.sidebar.widget.GetNumberRows()):
        item = App_ns.sidebar.widget.GetTable().GetValue(i,0)[0]
        if item.displayName == cellName:
            return i
    return False

             
class UITestItem :       
    def __init__(self, type, logger):
        if not type in ["Event", "Note", "Task", "MailMessage", "Collection"]:
            # "Copy constructor"
            if isinstance(type,pim.calendar.CalendarEvent):
                self.isNote = self.isTask = self.isMessage = self.isCollection = self.allDay = self.recurring = False
                self.isEvent = True
                self.view = App_ns.itsView
                self.logger = logger
                self.item = type
            else:
                return
        else:
            self.isNote = self.isEvent = self.isTask = self.isMessage = self.isCollection = self.allDay = self.recurring = False
            self.logger = logger
            self.logger.Start("%s creation" %type)
            if type == "Event": # New Calendar Event
                # post the corresponding CPIA-event
                item = App_ns.root.NewCalendar()[0]
                self.isEvent = True
            elif type == "Note": # New Note
                # post the corresponding CPIA-event
                item = App_ns.root.NewNote()[0]
                self.isNote = True
            elif type == "Task": # New Task
                # post the corresponding CPIA-event
                item = App_ns.root.NewTask()[0]
                self.isTask = True
            elif type == "MailMessage": # New Mail Message
                # post the corresponding CPIA-event
                item = App_ns.root.NewMailMessage()[0]
                self.isMessage = True
            elif type == "Collection": # New Collection
                # post the corresponding CPIA-event
                item = App_ns.root.NewCollection()[0]
                self.isCollection = True
                
            self.item = item
            # Give the Yield
            wx.GetApp().Yield()
	    ev = wx.IdleEvent()
            wx.GetApp().ProcessEvent(ev)
            self.logger.Stop()
    
    def SetAttr(self, displayName=None, startDate=None, startTime=None, endDate=None, endTime=None, location=None, body=None,
                status=None, timeZone=None, recurrence=None, recurrenceEnd=None, alarm=None, fromAddress=None, toAddress=None,
                allDay=None, stampEvent=None, stampMail=None,stampTask=None, dict=None):
        """
        Set the item attributes in a predefined order (see orderList)
        """
        methodDict = {displayName:self.SetDisplayName, startDate:self.SetStartDate, startTime:self.SetStartTime, endDate:self.SetEndDate, endTime:self.SetEndTime,
                      location:self.SetLocation, body:self.SetBody, status:self.SetStatus, alarm:self.SetAlarm, fromAddress:self.SetFromAddress,
                      toAddress:self.SetToAddress, allDay:self.SetAllDay, stampEvent:self.StampAsCalendarEvent, stampMail:self.StampAsMailMessage,
                      stampTask:self.StampAsTask, timeZone:self.SetTimeZone, recurrence:self.SetRecurrence, recurrenceEnd:self.SetRecurrenceEnd}
        orderList = [displayName, startDate, startTime, endDate, endTime, location, body, status, alarm, fromAddress, toAddress, allDay,
                     stampEvent, stampMail, stampTask, timeZone, recurrence, recurrenceEnd]
        
        for param in orderList:
            if param:
                methodDict[param](param)
            
        if dict:
            self.logger.Start("Multiple Attribute Setting")
            self.logger.Stop()
            self.Check_DetailView(dict)
            
    def SetAttrInOrder(self, argList, dict=None):
        """
        Set the item attributes in the argList order
        """
        methodDict = {"displayName":self.SetDisplayName, "startDate":self.SetStartDate, "startTime":self.SetStartTime, "endDate":self.SetEndDate, "endTime":self.SetEndTime,
                      "location":self.SetLocation, "body":self.SetBody, "status":self.SetStatus, "alarm":self.SetAlarm, "fromAddress":self.SetFromAddress,
                      "toAddress":self.SetToAddress, "allDay":self.SetAllDay, "stampEvent":self.StampAsCalendarEvent, "stampMail":self.StampAsMailMessage,
                      "stampTask":self.StampAsTask, "timeZone":self.SetTimeZone, "recurrence":self.SetRecurrence, "recurrenceEnd":self.SetRecurrenceEnd}
        for (key, value) in argList:
            methodDict[key](value)
        if dict:
            self.logger.Start("Multiple Attribute Setting")
            self.logger.Stop()
            self.Check_DetailView(value)

    def SelectItem(self):
        """
        Select the item in chandler (summary view or calendar view selection)
        """
        #if not in the Calendar view (select in the summary view)
        #check the button state
        button = App_ns.ApplicationBarEventButton
        buttonState = button.widget.IsToggled()
        if not buttonState:
            App_ns.summary.select(self.item)
        #if in the Calendar view (select by clicking on the TimedCanvasItem)
        else:
            timedCanvas = App_ns.TimedEvents
            allDayCanvas = App_ns.AllDayEvents
            for canvasItem in reversed(allDayCanvas.widget.canvasItemList):
                if canvasItem._item == self.item:
		    allDayCanvas.widget.OnSelectItem(canvasItem.GetItem())
                    break
            for canvasItem in reversed(timedCanvas.widget.canvasItemList):
                if canvasItem._item == self.item:
                    timedCanvas.widget.OnSelectItem(canvasItem.GetItem())
                    break

    def SetEditableBlock(self, blockName, description, value, dict=None):
        """
        Set the value of an editable block
        @type blockName : string
        @param blockName : the name of the editable block
        @type description : string
        @param description : description of the action used by the logger
        @type value : string
        @param value : the new value for the editable block
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if dict:
            self.logger.Start("Set the %s to : %s" %(description, displayName))
        #select the item
        self.SelectItem()
        block = App_ns.__getattr__(blockName)
        # Emulate the mouse click in the display name block
        scripting.User.emulate_click(block)
        # Select the old text
        block.widget.SelectAll()
        # Emulate the keyboard events
        scripting.User.emulate_typing(value)
        scripting.User.emulate_return()
        if dict:
            self.logger.Stop()
            self.Check_DetailView(dict)
         
    def SetDisplayName(self, displayName, dict=None):
        """
        Set the title
        @type displayName : string
        @param displayName : the new title
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if (self.isNote or self.isEvent or self.isTask or self.isMessage):
            self.SetEditableBlock("HeadlineBlock", "display name", displayName, dict)
        elif(self.isCollection):
            # work around for mac bug (I guess relative to focus)
            if '__WXMAC__' in wx.PlatformInfo:
                #row = GetCollectionRow(self.item.displayName)
                #App_ns.sidebar.widget.SetCellValue(row, 0, displayName)
		self.item.displayName = displayName
            else:
                # select the collection
                scripting.User.emulate_sidebarClick(App_ns.sidebar, self.item.displayName)
                # edit the collection displayName (double click)
                scripting.User.emulate_sidebarClick(App_ns.sidebar, self.item.displayName, double=True)
                # Type the new collection displayName
                scripting.User.emulate_typing(displayName)
                # work around : KeyboardReturn doesn't work in that kind of editor
                scripting.User.emulate_sidebarClick(App_ns.sidebar, "All")            
        else:
            self.logger.Print("SetDisplayName is not available for this kind of item")
            return

    def SetStartTime(self, startTime, dict=None):
        """
        Set the start time
        @type startTime : string
        @param startTime : the new start time (hh:mm PM or AM)
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if (self.isEvent and not self.allDay):
            self.SetEditableBlock("EditCalendarStartTime", "start time", startTime, dict)
        else:
            self.logger.Print("SetStartTime is not available for this kind of item")
            return

    def SetStartDate(self, startDate, dict=None):
        """
        Set the start date
        @type startDate : string
        @param startDate : the new start date (mm/dd/yyyy)
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if self.isEvent:
            self.SetEditableBlock("EditCalendarStartDate", "start date", startDate, dict)
        else:
            self.logger.Print("SetStartDate is not available for this kind of item")
            return

    def SetEndTime(self, endTime, dict=None):
        """
        Set the end time
        @type endTime : string
        @param endTime : the new end time (hh:mm PM or AM)
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if (self.isEvent and not self.allDay):
            self.SetEditableBlock("EditCalendarEndTime", "end time", endTime, dict)
        else:
            self.logger.Print("SetEndTime is not available for this kind of item")
            return
    
    def SetEndDate(self, endDate, dict=None):
        """
        Set the end date
        @type endDate : string
        @param endDate : the new end date (mm/dd/yyyy)
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if self.isEvent:
            self.SetEditableBlock("EditCalendarEndDate", "end date", endDate, dict)
        else:
            self.logger.Print("SetEndDate is not available for this kind of item")
            return

    def SetLocation(self, location, dict=None):
        """
        Set the location
        @type location : string
        @param location : the new location
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if self.isEvent:
            self.SetEditableBlock("CalendarLocation", "location", location, dict)
        else:
            self.logger.Print("SetLocation is not available for this kind of item")
            return

    def SetAllDay(self, allDay, dict=None):
        """
        Set the allday attribute
        @type allDay : boolean
        @param allDay : the new all-day value
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if self.isEvent:
            if dict:
                self.logger.Start("Set the all Day to : %s" %allDay)
            self.SelectItem()
            allDayBlock = App_ns.detail.all_day  
            # Emulate the mouse click in the all-day block
            # scripting.User.emulate_click(allDayBlock)
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
   
    def SetStatus(self, status):
        """
        Set the status
        @type status : string
        @param status : the new status value ("Confirmed" or "Tentative" or "FYI")
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if self.isEvent:
            self.SelectItem()
            SetBlockMenu("EditTransparency",status)
            self.SelectItem()
        else:
            self.logger.Print("SetStatus is not available for this kind of item")
            return

    def SetAlarm(self, alarm):
        """
        Set the alarm
        @type alarm : string
        @param alarm : the new alarm value ("1","5","10","30","60","90")
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if self.isEvent:
            if alarm == "1":
                alarm = alarm + " minute"
            else:
                alarm = alarm + " minutes"
            self.SelectItem()
            SetBlockMenu("EditReminder",alarm)
            self.SelectItem()
        else:
            self.logger.Print("SetAlarm is not available for this kind of item")
            return
    
    def SetBody(self, body, dict=None):
        """
        Set the body text
        @type body : string
        @param body : the new body text
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        self.SetEditableBlock("NotesBlock", "body", body, dict)

    def SetToAddress(self, toAdd, dict=None):
        """
        Set the to address
        @type toAdd : string
        @param toAdd : the new destination address value
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if self.isMessage:
            self.SetEditableBlock("ToMailEditField", "to address", toAdd, dict)
        else:
            self.logger.Print("SetToAddress is not available for this kind of item")
            return
        
    def SetFromAddress(self, fromAdd, dict=None):
        """
        Set the from address (not available from UI)
        @type fromAdd : string
        @param fromAdd : the new from address value
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if self.isMessage:
            self.SetEditableBlock("FromEditField", "from address", fromAdd, dict)
        else:
            self.logger.Print("SetFromAddress is not available for this kind of item")
            return
        
    def StampAsMailMessage(self, stampMail, dict=None):
        """
        Stamp as a mail
        @type stampMail : boolean
        @param stampMail : the new mail stamp value
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if stampMail == self.isMessage:# Nothing to do
            return
        else:
            if dict:
                self.logger.Start("Change the Mail stamp to : %s" %stampMail)
            self.SelectItem()
            App_ns.markupbar.press(name='MailMessageButton')
	    wx.GetApp().Yield()
            self.isMessage = stampMail
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                
    def StampAsTask(self, stampTask, dict=None):
        """
        Stamp as a task
        @type stampTask : boolean
        @param stampTask : the new task stamp value
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if stampTask == self.isTask:# Nothing to do
            return
        else:
            if dict:
                self.logger.Start("Change the Task stamp to : %s" %stampTask)
            self.SelectItem()
            App_ns.markupbar.press(name='TaskStamp')
	    wx.GetApp().Yield()
            self.isTask = stampTask
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)
                
    def StampAsCalendarEvent(self, stampEvent, dict=None):
        """
        Stamp as an event
        @type stampEvent : boolean
        @param stampEvent : the new event stamp value
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if stampEvent == self.isEvent:# Nothing to do
            return
        else:
            if dict:
                self.logger.Start("Change the Calendar Event stamp to : %s" %stampEvent)
            self.SelectItem()
            App_ns.markupbar.press(name='CalendarStamp')
	    wx.GetApp().Yield()
            self.isEvent = stampEvent
            if dict:
                self.logger.Stop()
                self.Check_DetailView(dict)

    def SetTimeZone(self, timeZone):
        """
        Set the time zone
        @type timeZone : string
        @param timeZone : the new time zone value
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if self.isEvent:
            self.SelectItem()
            SetBlockMenu("EditTimeZone",timeZone)
            self.SelectItem()
        else:
            self.logger.Print("SetTimeZone is not available for this kind of item")
            return
        
    def SetRecurrence(self, recurrence):
        """
        Set the recurrence
        @type recurrence : string
        @param recurrence : the new recurrence value ("None","Daily","Weekly","Monthly","Yearly")
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if self.isEvent:
            self.SelectItem()
            SetBlockMenu("EditRecurrence",recurrence)
            self.SelectItem()
            if not recurrence == "Once":
                self.recurring = True
        else:
            self.logger.Print("SetRecurrence is not available for this kind of item")
            return

    def SetRecurrenceEnd(self, endDate):
        """
        Set the recurrence end date
        @type endDate : string
        @param endDate : the new recurrence end value ("mm/dd/yyyy")
        @type dict : dictionnary
        @param dict : optional dictionnary with expected item attributes values for automated checking
        """
        if self.isEvent and self.recurring:
            self.SetEditableBlock("EditRecurrenceEnd", "recurrence end", endDate, dict=None)
        else:
            self.logger.Print("SetRecurrenceEnds is not available for this kind of item")
            return

    def SendMail(self):
        """
        Send a mail message
        """
        if self.isMessage:
            #select the item
            self.SelectItem()
            #Send button is available only when the body is edited
            noteArea = App_ns.detail.notes
            scripting.User.emulate_click(noteArea)
            #Press the Send button
            self.logger.Start("Sending the message")
            App_ns.appbar.press(name="ApplicationBarSendButton")
	    wx.GetApp().Yield()
            self.logger.Stop()
            #checking
            self.logger.SetChecked(True)
            if self.item.isOutbound:
                self.logger.ReportPass("(On sending message Checking)")
            else:
                self.logger.ReportFailure("(On sending message Checking)")
            self.logger.Report("Send Mail")
        else:
            self.logger.Print("SendMail is not available for this kind of item")
            return

    def SetCollection(self, collectionName):
        """
        Put the item in the given collection
        @type collectionName : string
        @param collectionName : the name of a collection
        """
        if (self.isNote or self.isEvent or self.isTask or self.isMessage):
            col = App_ns.item_named(pim.AbstractCollection, collectionName)
            self.logger.Start("Give a collection")
            if not col:
                self.logger.ReportFailure("(On collection search)")
                self.logger.Stop()
                self.logger.Report()
                return
            col.add(self.item)
            self.logger.Stop()
            #checking
            self.logger.SetChecked(True)
            if col.__contains__(self.item):
                self.logger.ReportPass("(On give collection Checking)")
            else:
                self.logger.ReportFailure("(On give collection Checking)")
            self.logger.Report("Collection Setting")
        else:
            self.logger.Print("SetCollection is not available for this kind of item")
            return
    
    def CheckEditableBlock(self, blockName, description, value):
        """
        Check the value contained in the given editable block
        @type blockName : string
        @param blockName : name of the editable block to check
        @type description : string
        @param description : description of the action for the logger
        @type value : string
        @param value : expected value to compare
        """
        #find the block
        block = App_ns.__getattr__(blockName)
        #get the editable block value
        blockValue = block.widget.GetValue()
        if not blockValue == value :
            self.logger.ReportFailure("(On %s Checking)  || detail view value = %s ; expected value = %s" %(description, blockValue, value))
        else:
            self.logger.ReportPass("(On %s Checking)" %description)

    def CheckMenuBlock(self, blockName, description, value):
        """
        Check the current value of the given list-menu
        @type blockName : string
        @param blockName : name of the list-menu block to check
        @type description : string
        @param description : description of the action for the logger
        @type value : string
        @param value : expected value to compare
        """
        #find the block
        block = App_ns.__getattr__(blockName)
        #get the menu block value
        menuValue = block.widget.GetStringSelection()
        if not menuValue == value :
            self.logger.ReportFailure("(On %s Checking)  || detail view value = %s ; expected value = %s" %(description, menuValue, value))
        else:
            self.logger.ReportPass("(On %s Checking)" %description)

    def CheckButton(self, buttonName, description, value):
        """
        Check the current state of the given button
        @type blockName : string
        @param blockName : name of the button block to check
        @type description : string
        @param description : description of the action for the logger
        @type value : boolean
        @param value : expected value to compare
        """
        #get the button state
        state = App_ns.markupbar.pressed(name=buttonName)
        if not state == value :
            self.logger.ReportFailure("(On %s Checking) || detail view value = %s ; expected value = %s" %(state, value))
        else:
            self.logger.ReportPass("(On %s Checking)" %description)
        
    def Check_DetailView(self, dict):
        """
        Check expected values by comparation to the data diplayed in the detail view
        @type dict : dictionnary
        @param dict : dictionnary with expected item attributes values for checking {"attributeName":"expected value",...}
        """  
        self.logger.SetChecked(True)
        self.SelectItem()
        # call the check methods
        for field in dict.keys():
            if field == "displayName": # display name checking
                self.CheckEditableBlock("HeadlineBlock", "display name", dict[field])
            elif field == "startDate": # start date checking
                self.CheckEditableBlock("EditCalendarStartDate", "start date", dict[field])
            elif field == "startTime": # start time checking
                self.CheckEditableBlock("EditCalendarStartTime", "start time", dict[field])
            elif field == "endDate": # end date checking
                self.CheckEditableBlock("EditCalendarEndDate", "end date", dict[field])
            elif field == "endTime": # end time checking
                self.CheckEditableBlock("EditCalendarEndTime", "end time", dict[field])
            elif field == "location": # location checking
                self.CheckEditableBlock("CalendarLocation", "location", dict[field])
            elif field == "body": # body checking
                self.CheckEditableBlock("NotesBlock", "body", dict[field])
            elif field == "fromAddress": # from address checking
                self.CheckEditableBlock("FromEditField", "from address", dict[field])
            elif field == "toAddress": # to address checking
                self.CheckEditableBlock("ToMailEditField", "to address", dict[field])
            elif field == "status": # status checking
                self.CheckMenuBlock("EditTransparency", "status", dict[field])
            elif field == "timeZone": # time zone checking
                self.CheckMenuBlock("EditTimeZone", "time-zone", dict[field])
            elif field == "recurrence": # recurrence checking
                self.CheckMenuBlock("EditRecurrence", "recurrence", dict[field])
            elif field == "recurrenceEnd": # recurrence end date checking
                self.CheckEditableBlock("EditRecurrenceEnd", "recurrence end", dict[field])
            elif field == "alarm": # status checking
                self.CheckMenuBlock("EditReminder", "alarm", dict[field])
            elif field == "allDay": # status checking
                self.CheckEditableBlock("EditAllDay", "all-day", dict[field])
            elif field == "stampMail": # Mail stamp checking
                self.CheckButton("MailMessageButton", "mail stamp", dict[field])
            elif field == "stampTask": # Task stamp checking
                self.CheckButton("TaskStamp", "task stamp", dict[field])
            elif field == "stampEvent": # Event stamp checking
                self.CheckButton("CalendarStamp", "calendar stamp", dict[field])
        #report the checkings
        self.logger.Report("Detail View")
    
    def Check_Object(self, dict):
        """
        Check expected value by comparison to the data contained in the object attributes
        @type dict : dictionnary
        @param dict : dictionnary with expected item attributes values for checking {"attributeName":"expected value",...}
        """
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
            elif field == "timeZone": # time zone checking
                timeZone = "%s" %self.item.startTime.tzname()
                if not dict[field] == timeZone :
                    self.logger.ReportFailure("(On time zone Checking) || object time zone = %s ; expected time zone = %s" %(timeZone, dict[field]))
                else:
                    self.logger.ReportPass("(On time zone Checking)")
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

    def Check_Sidebar(self, dict):
        """
        Check expected values by comparison to the data displayed in the sidebar
        @type dict : dictionnary
        @param dict : dictionnary with expected item attributes values for checking {"attributeName":"expected value",...}
        """
        if self.isCollection:
            self.logger.SetChecked(True)
            # check the changing values
            for field in dict.keys():
                if field == "displayName": # display name checking
                    if not GetCollectionRow(dict[field]):
                        self.logger.ReportFailure("(On display name Checking)  || expected title = %s" %dict[field])
                    else:
                        self.logger.ReportPass("(On display name Checking)")
            #report the checkings
            self.logger.Report("Sidebar")
        
        
class UITestAccounts:
    def __init__(self, logger=None):
        self.view = App_ns.itsView
        self.logger = logger
        self.window = None
        self.accountNames = {'SMTP': 'Outgoing mail (SMTP)', 'IMAP': 'Incoming mail (IMAP)', 'POP': 'Incoming mail (POP)', 'WebDAV': 'Sharing (WebDAV)'}
        SMTPfields = {'displayName': 3, 'host': 5, 'username': 15, 'password': 17, 'security': 7, 'port':11,  'authentication': 13}
        IMAPfields = {'displayName': 3, 'email': 5, 'name': 7, 'host': 9, 'username': 11, 'password': 13, 'security': 15, 'port': 19, 'default': 21, 'server': 24}
        POPfields = {'displayName': 3, 'email': 5, 'name': 7, 'host': 9, 'username': 11, 'password': 13, 'security': 15,'port': 19, 'leave': 21,  'default': 23, 'server': 26}
        DAVfields = {'displayName': 3, 'host':5, 'path': 7, 'username':9, 'password':11, 'port': 13, 'ssl': 14, 'default': 16}
        self.fieldMap = {'SMTP': SMTPfields, 'IMAP': IMAPfields, 'WebDAV': DAVfields, 'POP': POPfields}        
        
    def Open(self):
        """
        Open the Account preferences dialog window in non-modal mode
        """
        # Have to do it the hard way since Account Preferences is modal by default
        import application
        application.dialogs.AccountPreferences.ShowAccountPreferencesDialog(wx.GetApp().mainFrame, view=self.view, modal=False)
        self.window = wx.FindWindowByLabel("Account Preferences")
        wx.GetApp().Yield()
        
    def Ok(self):
        """
        Call the OK button click handler
        """
        self.window.OnOk(None)
        self.window = None
        
    def Cancel(self):
        """
        Call the Cancel button click handler
        """
        self.window.OnCancel(None)
        self.window = None

    def CreateAccount(self, type):
        """
        Create an account of the given type
        @type type : string
        @param type : an account type (IMAP,SMTP,WebDAV,POP)
        """
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
        """
        Emulate keyboard typing in the given field
        @type field : string
        @param field : the name of the field in which you want to type
        @type value : string
        @param value : the text to type
        """
        child = self._GetField(field)
        child.SetFocus()
        child.Clear() #work around : SelectAll() doesn't work on mac
        wx.GetApp().Yield()
        scripting.User.emulate_typing(value)        

    def ToggleValue(self, field, value):
        """
        Toggle the given field
        @type field : string
        @param field : the name of the field in which you want to toggle
        @type value : boolean
        @param value : the toggle state value
        """
        child = self._GetField(field)
        child.SetValue(value)
        event = wx.CommandEvent()
        event.SetEventObject(child)
        self.window.OnLinkedControl(event)
        self.window.OnExclusiveRadioButton(event)
        wx.GetApp().Yield()
        
    def SelectValue(self, field, value):
        """
        Select a value in a list-menu
        @type field : string
        @param field : the name of the list-menu
        @type value : string
        @param value : the value you want to select in the menu
        """
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
        """
        Check the accounts settings
        @type type : string
        @param type : the type of account you want to check (IMAP,SMTP,WebDAV,POP)
        @type name : string
        @param name : the name of the account to check
        @pram keys : key:value pairs
        """
        if type == "SMTP":
            iter = Mail.SMTPAccount.iterItems(App_ns.itsView)
        elif type == "IMAP":
            iter = Mail.IMAPAccount.iterItems(App_ns.itsView)
        elif type == "WebDAV":
            iter = Sharing.WebDAVAccount.iterItems(App_ns.itsView)
        elif type == "POP":
            iter = Mail.POPAccount.iterItems(App_ns.itsView)
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
        #report the checkings
        self.logger.Report("%s values" %type)
        return result


class UITestView:
    def __init__(self, logger):
        self.logger = logger
        self.view = App_ns.itsView
        #get the current view state
        self.state = self.GetCurrentState()

    def GetCurrentState(self):
        """
        Get the current state of the view
        @return : the current view
        """
        if App_ns.appbar.pressed(name="ApplicationBarAllButton"):
            return "AllView"
        elif App_ns.appbar.pressed(name="ApplicationBarTaskButton"):
            return "TaskView"
        elif App_ns.appbar.pressed(name="ApplicationBarMailButton"):
            return "MailView"
        elif App_ns.appbar.pressed(name="ApplicationBarEventButton"):
            return "CalendarView"
        else:
            return False

    def SwitchView(self, viewName):
        """
        @type viewName : string
        @param viewName : name of the view to select (CalendarView,TaskView,MailView,AllView)
        """
        if self.state == viewName :
            return False
        elif viewName == "CalendarView":
            button = "ApplicationBarEventButton"
        elif viewName == "TaskView":
            button = "ApplicationBarTaskButton"
        elif viewName == "MailView":
            button = "ApplicationBarMailButton"
        elif viewName == "AllView":
            button = "ApplicationBarAllButton"
        else:
            return False
        self.state = viewName
        self.logger.Start("Switch to %s" %viewName)
        #process the corresponding event
        App_ns.appbar.press(name=button)
        wx.GetApp().Yield()
        self.logger.Stop()
        self.CheckView()

    def SwitchToCalView(self):
        """
        Switch to the calendar view
        """
        self.SwitchView("CalendarView")
        
    def SwitchToTaskView(self):
        """
        Switch to the task view
        """
        self.SwitchView("TaskView")

    def SwitchToMailView(self):
        """
        Switch to the email view
        """
        self.SwitchView("MailView")
        
    def SwitchToAllView(self):
        """
        Switch to the all view
        """
        self.SwitchView("AllView")
    
    def CheckView(self):
        """
        Check if the current view is the expected one
        """
        self.logger.SetChecked(True)
        if not self.state == self.GetCurrentState():
            self.logger.ReportFailure("(On wiew checking) || expected current view = %s ; Correspondig button is switch off " %self.state)
        else:
            self.logger.ReportPass("(On view checking)")
        #report the checkings
        self.logger.Report("View")
        
    def DoubleClickInCalView(self, x=300, y=100):
        """
        Emulate a double click in the calendar a the given position
        @type x : int
        @param x : the x coordinate
        @type y : int
        @param y : the y coordinate
        """
        if self.state == "CalendarView":
            self.timedCanvas = App_ns.TimedEvents
            canvasItem = None
            #process the corresponding event
            click = wx.MouseEvent(wx.wxEVT_LEFT_DCLICK)
            click.m_x = x
            click.m_y = y
            click.SetEventObject(self.timedCanvas.widget)
            #check if an event already exists at this x,y postion
            #and if yes put it in the canvasItem variable
            pos = self.timedCanvas.widget.CalcUnscrolledPosition(click.GetPosition())
            for elem in reversed(self.timedCanvas.widget.canvasItemList):
                if elem.isHit(pos):
                    canvasItem = elem
                    break

            #work around : process a double clik here edit the title (also when the canvasItem is not focused)
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
                #work around : SelectAll() doesn't work
                wx.Window.FindFocus().Clear()
            else:
                self.logger.Start("Double click in the calendar view")
                self.timedCanvas.widget.ProcessEvent(click)
                wx.GetApp().Yield()
                self.logger.Stop()
            
            #it's a new event
            if not canvasItem :
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
                   
            #create the corresponding UITestItem object
            TestItem = UITestItem(canvasItem._item, self.logger)
            return TestItem
        else:
            self.logger.Print("DoubleClickInCalView is not available in the current view : %s" %self.state)
            return
