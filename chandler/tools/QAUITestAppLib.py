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
import osaf.sharing.ICalendar as ICalendar
import os
import sys

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

def GetCollectionRow(cellName):
    """
    Return the row number in the sidebar corresponding to the given cell. (False if cell doesn't exist)
    @type cellName : string
    @param cellName : a cell name
    @return : int
    """
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
            self.view = App_ns.itsView
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
            scripting.User.idle()
            self.logger.Stop()
    
    def SetAttr(self, displayName=None, startDate=None, startTime=None, endDate=None, endTime=None, location=None, body=None,
                status=None, timeZone=None, recurrence=None, recurrenceEnd=None, alarm=None, fromAddress=None, toAddress=None,
                allDay=None, stampEvent=None, stampMail=None,stampTask=None):
        """
        Set the item attributes in a predefined order (see orderList)
        """
        methodDict = {displayName:self.SetDisplayName, startDate:self.SetStartDate, startTime:self.SetStartTime, endDate:self.SetEndDate, endTime:self.SetEndTime,
                      location:self.SetLocation, body:self.SetBody, status:self.SetStatus, alarm:self.SetAlarm, fromAddress:self.SetFromAddress,
                      toAddress:self.SetToAddress, allDay:self.SetAllDay, stampEvent:self.StampAsCalendarEvent, stampMail:self.StampAsMailMessage,
                      stampTask:self.StampAsTask, timeZone:self.SetTimeZone, recurrence:self.SetRecurrence, recurrenceEnd:self.SetRecurrenceEnd}
        orderList = [displayName, startDate, startTime, endDate, endTime, location, body, status, alarm, fromAddress, toAddress, allDay,
                     stampEvent, stampMail, stampTask, timeZone, recurrence, recurrenceEnd]

        self.logger.Start("Multiple Attribute Setting")
        for param in orderList:
            if param:
                methodDict[param](param, timeInfo=False)
        self.logger.Stop()
            
    def SetAttrInOrder(self, argList):
        """
        Set the item attributes in the argList order
        """
        methodDict = {"displayName":self.SetDisplayName, "startDate":self.SetStartDate, "startTime":self.SetStartTime, "endDate":self.SetEndDate, "endTime":self.SetEndTime,
                      "location":self.SetLocation, "body":self.SetBody, "status":self.SetStatus, "alarm":self.SetAlarm, "fromAddress":self.SetFromAddress,
                      "toAddress":self.SetToAddress, "allDay":self.SetAllDay, "stampEvent":self.StampAsCalendarEvent, "stampMail":self.StampAsMailMessage,
                      "stampTask":self.StampAsTask, "timeZone":self.SetTimeZone, "recurrence":self.SetRecurrence, "recurrenceEnd":self.SetRecurrenceEnd}

        self.logger.Start("Multiple Attribute Setting")
        for (key, value) in argList:
            methodDict[key](value, timeInfo=False)
        self.logger.Stop()

    def SelectItem(self):
        """
        Select the item in chandler (summary view or calendar view or sidebar selection)
        """
        if not self.isCollection:
            # if not in the Calendar view (select in the summary view)
            # check the button state
            button = App_ns.ApplicationBarEventButton
            buttonState = button.widget.IsToggled()
            if not buttonState:
                App_ns.summary.select(self.item)
                App_ns.summary.focus()
            # if in the Calendar view (select by clicking on the TimedCanvasItem)
            else:
                timedCanvas = App_ns.TimedEvents
                allDayCanvas = App_ns.AllDayEvents
                for canvasItem in reversed(allDayCanvas.widget.canvasItemList):
                    if canvasItem.item == self.item:
                        allDayCanvas.widget.OnSelectItem(canvasItem.item)
                        break
                for canvasItem in reversed(timedCanvas.widget.canvasItemList):
                    if canvasItem.item == self.item:
                        timedCanvas.widget.OnSelectItem(canvasItem.item)
                        break
        else: # the item is a collection (sidebar selection)
            App_ns.sidebar.select(self.item)
            App_ns.sidebar.focus()
            scripting.User.idle()
           
            
    def SetEditableBlock(self, blockName, description, value, timeInfo):
        """
        Set the value of an editable block
        @type blockName : string
        @param blockName : the name of the editable block
        @type description : string
        @param description : description of the action used by the logger
        @type value : string
        @param value : the new value for the editable block
        @type timeInfo: boolean
        """
        #select the item
        self.SelectItem()
        if timeInfo:
            self.logger.Start("%s setting" %description)
        block = App_ns.__getattr__(blockName)
        # Emulate the mouse click in the display name block
        scripting.User.emulate_click(block)
        # Select the old text
        block.widget.SelectAll()
        # Emulate the keyboard events
        scripting.User.emulate_typing(value)
        scripting.User.emulate_return()
        if timeInfo:
            self.logger.Stop()

    def SetBlockMenu(self, menuName, menuChoice, timeInfo):
        """
        Select a choice in a list menu
        @type menuName : string
        @param menuName : The name of the menu
        @type menuChoice : string
        @param menuChoice : the choice you want to select
        @type timeInfo: boolean
        @return : True if the selection is succesfull
        """
        #select the item
        self.SelectItem()
        block = App_ns.__getattr__(menuName)
        list_of_value = []
        for k in range(0,block.widget.GetCount()):
            list_of_value.append(block.widget.GetString(k))
        if not menuChoice in list_of_value:
            return False
        else:
            if timeInfo:
                self.logger.Start("%s setting" %menuName)
            # Emulate the mouse click in the menu
            scripting.User.emulate_click(block)
            block.widget.SetStringSelection(menuChoice)
            # Process the event corresponding to the selection
            selectionEvent = wx.CommandEvent(wx.wxEVT_COMMAND_CHOICE_SELECTED)
            selectionEvent.SetEventObject(block.widget)
            block.widget.ProcessEvent(selectionEvent)
            self.SelectItem()
            if timeInfo:
                self.logger.Stop()
            return True
    
    def SetDisplayName(self, displayName, timeInfo=True):
        """
        Set the title
        @type displayName : string
        @param displayName : the new title
        @type timeInfo: boolean
        """
        if not self.isCollection:
            self.SetEditableBlock("HeadlineBlock", "display name", displayName, timeInfo=timeInfo)
        else:
            # select the collection
            self.SelectItem()
            # edit the collection displayName (double click)
            scripting.User.emulate_sidebarClick(App_ns.sidebar, self.item.displayName, double=True)
            # select all
            App_ns.root.SelectAll()
            if timeInfo:
                self.logger.Start("Collection title setting")
            # Type the new collection displayName
            scripting.User.emulate_typing(displayName)
            # work around : emulate_return doesn't work
            #scripting.User.emulate_return()
            scripting.User.emulate_sidebarClick(App_ns.sidebar, "All")
            if timeInfo:
                self.logger.Stop()

    def SetStartTime(self, startTime, timeInfo=True):
        """
        Set the start time
        @type startTime : string
        @param startTime : the new start time (hh:mm PM or AM)
        @type timeInfo: boolean
        """
        if (self.isEvent and not self.allDay):
            self.SetEditableBlock("EditCalendarStartTime", "start time", startTime, timeInfo=timeInfo)
        else:
            self.logger.Print("SetStartTime is not available for this kind of item")
            return

    def SetStartDate(self, startDate, timeInfo=True):
        """
        Set the start date
        @type startDate : string
        @param startDate : the new start date (mm/dd/yyyy)
        @type timeInfo: boolean
        """
        if self.isEvent:
            self.SetEditableBlock("EditCalendarStartDate", "start date", startDate, timeInfo=timeInfo)
        else:
            self.logger.Print("SetStartDate is not available for this kind of item")
            return

    def SetEndTime(self, endTime, timeInfo=True):
        """
        Set the end time
        @type endTime : string
        @param endTime : the new end time (hh:mm PM or AM)
        @type timeInfo: boolean
        """
        if (self.isEvent and not self.allDay):
            self.SetEditableBlock("EditCalendarEndTime", "end time", endTime, timeInfo=timeInfo)
        else:
            self.logger.Print("SetEndTime is not available for this kind of item")
            return
    
    def SetEndDate(self, endDate, timeInfo=True):
        """
        Set the end date
        @type endDate : string
        @param endDate : the new end date (mm/dd/yyyy)
        @type timeInfo: boolean
        """
        if self.isEvent:
            self.SetEditableBlock("EditCalendarEndDate", "end date", endDate, timeInfo=timeInfo)
        else:
            self.logger.Print("SetEndDate is not available for this kind of item")
            return

    def SetLocation(self, location, timeInfo=True):
        """
        Set the location
        @type location : string
        @param location : the new location
        @type timeInfo: boolean
        """
        if self.isEvent:
            self.SetEditableBlock("CalendarLocation", "location", location, timeInfo=timeInfo)
        else:
            self.logger.Print("SetLocation is not available for this kind of item")
            return

    def SetAllDay(self, allDay, timeInfo=True):
        """
        Set the allday attribute
        @type allDay : boolean
        @param allDay : the new all-day value
        @type timeInfo: boolean
        """
        if self.isEvent:
            self.SelectItem()
            if timeInfo:
                self.logger.Start("All-day setting")
            allDayBlock = App_ns.detail.all_day  
            # Emulate the mouse click in the all-day block
            #scripting.User.emulate_click(allDayBlock)
            # work around : (the mouse click has not the good effect)
            # the bug #3336 appear on linux
            allDayBlock.widget.SetValue(allDay)
            if timeInfo:
                self.logger.Stop()
            self.allDay = allDay
        else:
            self.logger.Print("SetAllDay is not available for this kind of item")
            return
   
    def SetStatus(self, status, timeInfo=True):
        """
        Set the status
        @type status : string
        @param status : the new status value ("Confirmed" or "Tentative" or "FYI")
        @type timeInfo: boolean
        """
        if self.isEvent:
            self.SetBlockMenu("EditTransparency", status, timeInfo=timeInfo)
        else:
            self.logger.Print("SetStatus is not available for this kind of item")
            return

    def SetAlarm(self, alarm, timeInfo=True):
        """
        Set the alarm
        @type alarm : string
        @param alarm : the new alarm value ("1","5","10","30","60","90")
        @type timeInfo: boolean
        """
        if self.isEvent:
            if alarm == "1":
                alarm = alarm + " minute"
            else:
                alarm = alarm + " minutes"
            self.SetBlockMenu("EditReminder", alarm, timeInfo=timeInfo )
        else:
            self.logger.Print("SetAlarm is not available for this kind of item")
            return
    
    def SetBody(self, body, timeInfo=True):
        """
        Set the body text
        @type body : string
        @param body : the new body text
        @type timeInfo: boolean
        """
        if not self.isCollection:
            self.SetEditableBlock("NotesBlock", "body", body, timeInfo=timeInfo)
        else:
            self.logger.Print("SetBody is not available for this kind of item")
            return

    def SetToAddress(self, toAdd, timeInfo=True):
        """
        Set the to address
        @type toAdd : string
        @param toAdd : the new destination address value
        @type timeInfo: boolean
        """
        if self.isMessage:
            self.SetEditableBlock("EditMailTo", "to address", toAdd, timeInfo=timeInfo)
        else:
            self.logger.Print("SetToAddress is not available for this kind of item")
            return
        
    def SetCcAddress(self, ccAdd, timeInfo=True):
        """
        Set the CC address
        @type ccAdd : string
        @param ccAdd: the new CC address value
        @type timeInfo: boolean
        """
        if self.isMessage:
            self.SetEditableBlock("EditMailCc", "cc address", ccAdd, timeInfo=timeInfo)
        else:
            self.logger.Print("SetCcAddress is not available for this kind of item")
            return
        
    def SetBccAddress(self, bccAdd, timeInfo=True):
        """
        Set the BCC address
        @type bccAdd : string
        @param bccAdd : the new BCC address value
        @type timeInfo: boolean
        """
        if self.isMessage:
            self.SetEditableBlock("EditMailBcc", "bcc address", bccAdd, timeInfo=timeInfo)
        else:
            self.logger.Print("SetBccAddress is not available for this kind of item")
            return
        
    def SetFromAddress(self, fromAdd, timeInfo=True):
        """
        Set the from address (not available from UI)
        @type fromAdd : string
        @param fromAdd : the new from address value
        @type timeInfo: boolean
        """
        if self.isMessage:
            self.SetEditableBlock(self.item.isInbound and "EditMailInboundFrom" or "EditMailOutboundFrom", 
                                  "from address", fromAdd, timeInfo=timeInfo)
        else:
            self.logger.Print("SetFromAddress is not available for this kind of item")
            return
        
    def SetStamp(self, type, value, timeInfo=True):
        """
        Set the given stamp to the given value
        @type type : string
        @param type : the type of stamp to set
        @type value : boolean
        @param value : the new stamp value
        @type timeInfo: boolean
        """
        type_list = ["Mail", "Task", "Event"]
        if not type in type_list:
            return
        currentValue = {"Mail": self.isMessage, "Task": self.isTask, "Event": self.isEvent}
        buttonDict = {"Mail": "MailMessageButton", "Task": "TaskStamp", "Event": "CalendarStamp"}
        if not self.isCollection:
            if currentValue[type] == value: #Nothing to do
                return
            else:
                # select the item
                self.SelectItem()
                if timeInfo :
                    self.logger.Start("Change the %s stamp" %type)
                App_ns.markupbar.press(name=buttonDict[type])
                scripting.User.idle()
                if timeInfo:
                    self.logger.Stop()
        else:
            self.logger.Print("SetStamp is not available for this kind of item")
            return
                

    def StampAsMailMessage(self, stampMail, timeInfo=True):
        """
        Stamp as a mail
        @type stampMail : boolean
        @param stampMail : the new mail stamp value
        @type timeInfo: boolean
        """
        self.SetStamp("Mail", stampMail, timeInfo)
        # update the item state
        self.isMessage = stampMail
        
    def StampAsTask(self, stampTask, timeInfo=True):
        """
        Stamp as a task
        @type stampTask : boolean
        @param stampTask : the new task stamp value
        @type timeInfo: boolean
        """
        self.SetStamp("Task", stampTask, timeInfo)
        # update the item state
        self.isTask = stampTask
                
    def StampAsCalendarEvent(self, stampEvent, timeInfo=True):
        """
        Stamp as an event
        @type stampEvent : boolean
        @param stampEvent : the new event stamp value
        @type timeInfo: boolean
        """
        self.SetStamp("Event", stampEvent, timeInfo)
        # update the item state
        self.isEvent = stampEvent

    def SetTimeZone(self, timeZone, timeInfo=True):
        """
        Set the time zone
        @type timeZone : string
        @param timeZone : the new time zone value
        @type timeInfo: boolean
        """
        if self.isEvent:
            self.SetBlockMenu("EditTimeZone", timeZone, timeInfo=timeInfo)
        else:
            self.logger.Print("SetTimeZone is not available for this kind of item")
            return
        
    def SetRecurrence(self, recurrence, timeInfo=True):
        """
        Set the recurrence
        @type recurrence : string
        @param recurrence : the new recurrence value ("None","Daily","Weekly","Monthly","Yearly")
        @type timeInfo: boolean
        """
        if self.isEvent:
            self.SetBlockMenu("EditRecurrence", recurrence, timeInfo=timeInfo)
            if not recurrence == "Once":
                self.recurring = True
        else:
            self.logger.Print("SetRecurrence is not available for this kind of item")
            return

    def SetRecurrenceEnd(self, endDate, timeInfo=True):
        """
        Set the recurrence end date
        @type endDate : string
        @param endDate : the new recurrence end value ("mm/dd/yyyy")
        @type timeInfo: boolean
        """
        if self.isEvent and self.recurring:
            self.SetEditableBlock("EditRecurrenceEnd", "recurrence end", endDate, timeInfo=timeInfo)
        else:
            self.logger.Print("SetRecurrenceEnds is not available for this kind of item")
            return

    def SendMail(self, timeInfo=True):
        """
        Send a mail message
        @type timeInfo: boolean
        """
        if self.isMessage:
            #select the item
            self.SelectItem()
            #Send button is available only when the body is edited
            noteArea = App_ns.detail.notes
            scripting.User.emulate_click(noteArea)
            #Press the Send button
            if timeInfo:
                self.logger.Start("Sending the message")
            App_ns.appbar.press(name="ApplicationBarSendButton")
            wx.GetApp().Yield()
            #checkings
            self.logger.SetChecked(True)
            sent = None
            #check if an SMTP account is defined
            account = Mail.getCurrentSMTPAccount(App_ns.itsView)[0]
            if account._values['host']=='':
                self.logger.ReportFailure("(On SMTP account) - Host not defined")
            else:
                self.logger.ReportPass("(On SMTP account)")
                # wait for mail delivery    
                while not sent:
                    wx.GetApp().Yield()
                    try:
                        sent = self.item.deliveryExtension.state
                    except AttributeError:
                        sent = None
            if timeInfo:
                self.logger.Stop()
            #check mail delivery
            if sent == "SENT":
                self.logger.ReportPass("(On sending message Checking)")
            else:
                self.logger.ReportFailure("(On sending message Checking)")
            self.logger.Report("Send Mail")
        else:
            self.logger.Print("SendMail is not available for this kind of item")
            return

    def AddCollection(self, collectionName, timeInfo=True):
        """
        Put the item in the given collection
        @type collectionName : string
        @param collectionName : the name of a collection
        @type timeInfo: boolean
        """
        if not self.isCollection:
            col = App_ns.item_named(pim.AbstractCollection, collectionName)
            if timeInfo:
                self.logger.Start("Give a collection")
            if not col:
                self.logger.ReportFailure("(On collection search)")
                if timeInfo:
                    self.logger.Stop()
                self.logger.Report("Add collection")
                return
            col.add(self.item)
            if timeInfo:
                self.logger.Stop()
        else:
            self.logger.Print("SetCollection is not available for this kind of item")
            return

    def MoveToTrash(self, timeInfo=True):
        """
        Move the item into the trash collection
        @type timeInfo: boolean
        """
        if not self.isCollection:
            # Check if the item is not already in the Trash
            if self.Check_ItemInCollection("Trash", report=False):
                self.logger.Print("This item is already in the Trash")
                return
            # select the item
            scripting.User.emulate_click(App_ns.summary.widget.GetGridWindow()) #work around for summary.select highlight bug
            self.SelectItem()
            if timeInfo:
                self.logger.Start("Move the item into the Trash")
            # Processing of the corresponding CPIA event
            App_ns.root.Delete()
            # give the Yield
            wx.GetApp().Yield()
            if timeInfo:
                self.logger.Stop()
        else:
            self.logger.Print("MoveToTrash is not available for this kind of item")
            return

    def DeleteCollection(self, timeInfo=True):
        """
        Remove a collection from Chandler
        @type timeInfo: boolean
        """
        if self.isCollection:
            # select the collection
            self.SelectItem()
            if timeInfo:
                self.logger.Start("Remove collection")
            # Processing of the corresponding CPIA event
            App_ns.root.Remove()
            # give the Yield
            wx.GetApp().Yield()
            if timeInfo:
                self.logger.Stop()
        else:
            self.logger.Print("Remove is not available for this kind of item")
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
        @type buttonName : string
        @param buttonName : name of the button block to check
        @type description : string
        @param description : description of the action for the logger
        @type value : boolean
        @param value : expected value to compare
        """
        #get the button state
        state = App_ns.markupbar.pressed(name=buttonName)
        if not state == value :
            self.logger.ReportFailure("(On %s Checking) || detail view value = %s ; expected value = %s" %(description, state, value))
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
                self.CheckEditableBlock("EditMailFrom", "from address", dict[field])
            elif field == "toAddress": # to address checking
                self.CheckEditableBlock("EditMailTo", "to address", dict[field])
            elif field == "ccAddress": # cc address checking
                self.CheckEditableBlock("EditMailCc", "cc address", dict[field])
            elif field == "bccAddress": # bcc address checking
                self.CheckEditableBlock("EditMailBcc", "bcc address", dict[field])
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
            else: # Wrong check => set the report state to unchecked
                self.logger.SetChecked(False)
                
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
            else: # Wrong check => set the report state to unchecked
                self.logger.SetChecked(False)
        #report the checkings
        self.logger.Report("Object state")

    def Check_CollectionExistance(self, expectedName=None, expectedResult=True):
        """
        Check if the collection exists/doesn't exist and has the expected display name (displayed in the sidebar)
        @type expectedName : string
        @param expectedName : The expected title of the collection
        @type expectedResult : boolean
        @param expectedResult : expected result of the method
        @return : True if result is the same as the expected
        """
        if self.isCollection:
            if not expectedName:
                expectedName = self.item.displayName
            self.logger.SetChecked(True)
            # check the changing values
            if not GetCollectionRow(self.item.displayName):
                exist = False
                description = "%s doesn't exists" %self.item.displayName
            else:
                exist = True
                description = "%s exists" %self.item.displayName
            #report the checkings
            if exist == expectedResult and self.item.displayName == expectedName:
                self.logger.ReportPass("(On collection existance Checking) - %s" %description)
                result = True
            elif not exist == expectedResult:
                self.logger.ReportFailure("(On collection existance Checking) - %s" %description)
                result = False
            else:
                self.logger.ReportFailure("(On collection name Checking) - current name = %s ; expected name = %s" %(self.item.displayName, expectedName))
                result = False
            self.logger.Report("Collection existance")
            return result
        else:
            self.logger.Print("Check_CollectionExistance is not available for this kind of item")
            return False
        
    def Check_ItemInCollection(self, collectionName, expectedResult=True, report=True):
        """
        Check if the item is/is not in the given collection
        @type collectionName : string
        @type expectedResult : boolean
        @param expectedResult : expected result of the method
        @type report : boolean
        @return : True if the result is the same as the expected
        """
        if not self.isCollection or collectionName == "Trash":
            self.logger.SetChecked(True)
            # for All, In, Out, Trash collection find by item rather than itemName
            chandler_collections = {"All":scripting.schema.ns('osaf.app', Globals.mainViewRoot).allCollection,
                                    "Out":scripting.schema.ns('osaf.app', Globals.mainViewRoot).outCollection,
                                    "In":scripting.schema.ns('osaf.app', Globals.mainViewRoot).inCollection,
                                    "Trash":scripting.schema.ns('osaf.app', Globals.mainViewRoot).TrashCollection}
            if collectionName in chandler_collections.keys():
                col = chandler_collections[collectionName]
            else:
                col = App_ns.item_named(pim.AbstractCollection, collectionName)
            if col:
                if col.__contains__(self.item):
                    value = True
                    description = "item named %s is in %s" %(self.item.displayName, collectionName)
                else:
                    value = False
                    description = "item named %s is not in %s" %(self.item.displayName, collectionName)
                if value == expectedResult:
                    result = True
                    if report:
                        self.logger.ReportPass("(On Collection Checking) - %s" %description)
                        self.logger.Report("Item in collection")
                else:
                    result = False
                    if report:
                        self.logger.ReportFailure("(On Collection Checking) - %s" %description)
                        self.logger.Report("Item in collection")
            else:
                result = False
                if report:
                    self.logger.ReportFailure("(On collection search)")
                    self.logger.Report("Item in collection")
            return result 
        else:
            self.logger.Print("Check_ItemInCollection is not available for this kind of item")
            return False 
    
class UITestAccounts:
    def __init__(self, logger=None):
        self.view = App_ns.itsView
        self.logger = logger
        self.window = None
        self.accountTypeIndex = {'SMTP': 3, 'IMAP': 1, 'POP': 2, 'WebDAV': 4}
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
        self.window.choiceNewType.SetSelection(self.accountTypeIndex[type])
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
        @param keys : key:value pairs
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
    def __init__(self, logger, environmentFile=None):
        self.logger = logger
        self.view = App_ns.itsView
        #get the current view state
        self.state = self.GetCurrentState()

        # setup the test environment if an environment file was specified
        if environmentFile is not None:
            path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
            #Upcast path to unicode since Sharing requires a unicode path
            path = unicode(path, sys.getfilesystemencoding())
            share = Sharing.Sharing.OneTimeFileSystemShare(path, 
                            environmentFile, 
                            ICalendar.ICalendarFormat, 
                            view=App_ns.itsView)
            try:
                collection = share.get()
            except:
                logger.Stop()
                logger.ReportFailure("Importing calendar: exception raised")
            else:
                App_ns.sidebarCollection.add(collection)
                scripting.User.idle()
                # do another idle and yield to make sure the calendar is up.
                scripting.User.idle()
                logger.ReportPass("Importing calendar")

    def GetCurrentState(self):
        """
        Get the current state of the view
        @return : the current view name
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
        
    def DoubleClickInCalView(self, x=100, y=100, gotoTestDate=True):
        """
        Emulate a double click in the calendar a the given position
        @type x : int
        @param x : the x coordinate
        @type y : int
        @param y : the y coordinate
        """
        if self.state == "CalendarView":
            # move to a known date, otherwise we'll just be operating
            #  on whatever shows up on Today's calendar
            if gotoTestDate:
                if gotoTestDate is True:
                    # True sends us to the default test date
                    gotoTestDate = datetime(2005, 12, 24) # Dec has some free days
                App_ns.root.SelectedDateChanged(start=gotoTestDate)

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
                scripting.User.idle()
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
            TestItem = UITestItem(canvasItem.item, self.logger)
            return TestItem
        else:
            self.logger.Print("DoubleClickInCalView is not available in the current view : %s" %self.state)
            return
