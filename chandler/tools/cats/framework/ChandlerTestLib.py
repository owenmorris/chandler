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

"""ChandlerTestLib is a library for testing chandler.

Originally this library was called QAUITestAppLib.
"""
__author__ =  'Dan Steinicke <dan@osafoundation.org>'
__version__=  '0.2'

from tools.QALogger import *
from datetime import datetime, timedelta, time
from time import mktime, strptime
from PyICU import ICUtzinfo
from osaf import pim
import osaf.pim.mail as Mail
import osaf.pim.collections as Collection
import osaf.sharing as Sharing
import application.Globals as Globals
import wx
import string
import osaf.framework.scripting as scripting
import osaf.sharing.ICalendar as ICalendar
import os, sys
from itertools import chain

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
        minute = u"00"
    else:
        minute = "%s" % minute
    if hour > 12:
        hour = hour - 12
        minute = minute + " PM"
    else:
        minute = minute + " AM"
    return u"%s:%s" % (hour, minute)

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

# this probably shouldn't live here, but it's helpful for finding occurrences
# of recurring events.  If you can, use event.getNextOccurrence instead.
def GetOccurrence(name, date):
    master = App_ns.item_named(pim.CalendarEvent, name).getMaster()
    start = datetime.combine(date, time(0, tzinfo=ICUtzinfo.floating))
    end   = start + timedelta(1)
    occurrences = list(master.getOccurrencesBetween(start,end))
    if len(occurrences) > 0:
        return occurrences[0]

# Sets the value of a choice widget, propagating the wx event
def SetChoice(choiceWidget, string):
    choiceWidget.SetStringSelection(string)
    selectionEvent = wx.CommandEvent(wx.wxEVT_COMMAND_CHOICE_SELECTED)
    selectionEvent.SetEventObject(choiceWidget)
    choiceWidget.ProcessEvent(selectionEvent)

# it would be nice if this were just a list, and we could map type ->
# 'New' + type.. but at the moment there is no 'NewEvent' - so 'Event'
# probably needs to be 'CalendarEvent' and 'NewCalendar' should
# probably be 'NewCalendarEvent'

DataTypes = { 'Event' : 'NewCalendar',
              'Note' : 'NewNote',
              'Task' : 'NewTask',
              'MailMessage' : 'NewMailMessage',
              'Collection' : 'NewCollection',
              }
             
class UITestItem(object):       
    def __init__(self, type, logger):
        for key in DataTypes.iterkeys():
            # set isTask, etc
            setattr(self, 'is' + key, False)
        
        if type not in DataTypes:
            # "Copy constructor"
            if isinstance(type,pim.calendar.CalendarEvent):
                self.isEvent = True
                self.view = App_ns.itsView
                self.logger = logger
                self.item = type
                self.recurring = hasattr(type, 'recurrenceID')
            else:
                return
        else:
            self.allDay = self.recurring = False
            self.view = App_ns.itsView
            self.logger = logger
            self.logger.startAction("%s creation" % type)
            
            setattr(self, 'is' + type, True)
            constructorName = DataTypes[type]
            constructor = getattr(App_ns.root, constructorName)
            self.item = constructor()
            
            # Give the Yield
            scripting.User.idle()
            self.logger.endAction(True)
    
    def SetAttr(self, msg="Multiple Attribute Setting", **args):
        """
        Set the item attributes in a predefined order (see orderList)
        """
        methodOrder = (
            ('displayName', self.SetDisplayName),
            ('startDate', self.SetStartDate),
            ('startTime', self.SetStartTime),
            ('endDate', self.SetEndDate),
            ('endTime', self.SetEndTime),
            ('location', self.SetLocation),
            ('body', self.SetBody),
            ('status', self.SetStatus),
            ('alarm', self.SetAlarm),
            ('fromAddress', self.SetFromAddress),
            ('toAddress', self.SetToAddress),
            ('allDay', self.SetAllDay),
            ('stampEvent', self.StampAsCalendarEvent),
            ('stampMail', self.StampAsMailMessage),
            ('stampTask', self.StampAsTask),
            ('timeZone', self.SetTimeZone),
            ('recurrence', self.SetRecurrence),
            ('recurrenceEnd', self.SetRecurrenceEnd),
            )
        
        self.FocusInDetailView()
        self.logger.startAction(msg)
        for param, method in methodOrder:
            if param in args:
                method(args[param], timeInfo=False)
        self.logger.endAction(True)
            
    def SetAttrInOrder(self, argList, msg="Multiple Attribute Setting In Order"):
        """
        Set the item attributes in the argList order
        """
        methodDict = {
            "displayName": self.SetDisplayName,
            "startDate": self.SetStartDate,
            "startTime": self.SetStartTime,
            "endDate": self.SetEndDate,
            "endTime": self.SetEndTime,
            "location": self.SetLocation,
            "body": self.SetBody,
            "status": self.SetStatus,
            "alarm": self.SetAlarm,
            "fromAddress": self.SetFromAddress,
            "toAddress": self.SetToAddress,
            "allDay": self.SetAllDay,
            "stampEvent": self.StampAsCalendarEvent,
            "stampMail": self.StampAsMailMessage,
            "stampTask": self.StampAsTask,
            "timeZone": self.SetTimeZone,
            "recurrence": self.SetRecurrence,
            "recurrenceEnd": self.SetRecurrenceEnd
            }

        self.logger.startAction(msg)
        for (key, value) in argList:
            methodDict[key](value, timeInfo=False)
        self.logger.endAction(True)

    def CalendarVisible(self):
        """In the calendar view?"""
        # if the Dashboard is selected, the state of the ApplicationBar isn't
        # enough to determine if the calendar is in view
        return (App_ns.ApplicationBarEventButton.widget.IsToggled() 
                and getattr(App_ns, 'TimedEvents', False))

    def SelectItem(self, catchException=False):
        """
        Select the item in chandler (summary view or calendar view or sidebar selection)
        """
        try:
            if not self.isCollection:
                if not self.CalendarVisible():
                    App_ns.summary.select(self.item)
                    App_ns.summary.focus()
                else:
                    # in the Calendar view, select by selecting the CanvasItem
                    foundItem = False
                    timedCanvas = App_ns.TimedEvents
                    allDayCanvas = App_ns.AllDayEvents
                    for canvasItem in reversed(allDayCanvas.widget.canvasItemList):
                        if canvasItem.item is self.item:
                            allDayCanvas.widget.OnSelectItem(canvasItem.item)
                            foundItem = True
                            break
                    if not foundItem:
                        for canvasItem in reversed(timedCanvas.widget.canvasItemList):
                            if canvasItem.item is self.item:
                                timedCanvas.widget.OnSelectItem(canvasItem.item)
                                foundItem = True
                                break
    
                        
            else: # the item is a collection (sidebar selection)
                App_ns.sidebar.select(self.item)
                App_ns.sidebar.focus()
                scripting.User.idle()
        except:
            if not catchException:
                raise
            
            
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
            self.logger.startAction("%s setting" % description)
        block = getattr(App_ns, blockName)
        # Emulate the mouse click in the display name block
        scripting.User.emulate_click(block)
        # Select the old text
        block.widget.SelectAll()
        # Emulate the keyboard events
        scripting.User.emulate_typing(value)
        scripting.User.emulate_return()
        if timeInfo:
            self.logger.endAction(True)

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
        block = getattr(App_ns, menuName)
        list_of_value = []
        for k in range(0,block.widget.GetCount()):
            list_of_value.append(block.widget.GetString(k))
        if not menuChoice in list_of_value:
            return False
        else:
            if timeInfo:
               self.logger.startAction("%s setting" % menuName)
            # Emulate the mouse click in the menu
            scripting.User.emulate_click(block)
            block.widget.SetStringSelection(menuChoice)
            # Process the event corresponding to the selection
            selectionEvent = wx.CommandEvent(wx.wxEVT_COMMAND_CHOICE_SELECTED)
            selectionEvent.SetEventObject(block.widget)
            block.widget.ProcessEvent(selectionEvent)
            self.SelectItem()
            if timeInfo:
                self.logger.endAction(True)
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
                self.logger.startAction("Collection title setting")
            # Type the new collection displayName
            scripting.User.emulate_typing(displayName)
            # work around : emulate_return doesn't work
            #scripting.User.emulate_return()
            scripting.User.emulate_sidebarClick(App_ns.sidebar, "Dashboard")
            # check this actually worked.  This assert was commented out, but
            # SetDisplayName failure associated with weirdness when there's a
            # Sidebar scrollbar have been causing errors like bug 6727, so we
            # really want to know when the collection isn't successfully renamed
            assert self.item.displayName == displayName, '%s != %s' % \
              (self.item.displayName.encode('raw_unicode_escape'), displayName.encode('raw_unicode_escape'))
            if timeInfo:
                self.logger.endAction(True)

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
            self.logger.addComment("SetStartTime is not available for this kind of item")
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
            self.logger.addComment("SetStartDate is not available for this kind of item")

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
            self.logger.addComment("SetEndTime is not available for this kind of item")
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
            self.logger.addComment("SetEndDate is not available for this kind of item")
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
            self.logger.addComment("SetLocation is not available for this kind of item")
            return

    def SetAllDay(self, allDay, timeInfo=True):
        """
        Set the allday attribute
        @type allDay : boolean
        @param allDay : the new all-day value
        @type timeInfo: boolean
        """
        self.logger.startAction("All-day setting")
        if self.isEvent:
            self.SelectItem()
            if self.allDay != allDay:   
                allDayBlock = App_ns.detail.EditAllDay
                scripting.User.emulate_click(allDayBlock)
                self.allDay = allDay
            else:self.logger.addComment("SetAllDay: allDay is already %s" % allDay)
        else:
            self.logger.addComment("SetAllDay is not available for this kind of item")
            self.logger.endAction(True)
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
            self.logger.addComment("SetStatus is not available for this kind of item")
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
            self.logger.addComment("SetAlarm is not available for this kind of item")
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
            self.logger.addComment("SetBody is not available for this kind of item")
            return

    def SetToAddress(self, toAdd, timeInfo=True):
        """
        Set the to address
        @type toAdd : string
        @param toAdd : the new destination address value
        @type timeInfo: boolean
        """
        if self.isMailMessage:
            self.SetEditableBlock("EditMailTo", "to address", toAdd, timeInfo=timeInfo)
        else:
            self.logger.addComment("SetToAddress is not available for this kind of item")
            return
        
    def SetCcAddress(self, ccAdd, timeInfo=True):
        """
        Set the CC address
        @type ccAdd : string
        @param ccAdd: the new CC address value
        @type timeInfo: boolean
        """
        if self.isMailMessage:
            self.SetEditableBlock("EditMailCc", "cc address", ccAdd, timeInfo=timeInfo)
        else:
            self.logger.addComment("SetCcAddress is not available for this kind of item")
            return
        
    def SetBccAddress(self, bccAdd, timeInfo=True):
        """
        Set the BCC address
        @type bccAdd : string
        @param bccAdd : the new BCC address value
        @type timeInfo: boolean
        """
        if self.isMailMessage:
            self.SetEditableBlock("EditMailBcc", "bcc address", bccAdd, timeInfo=timeInfo)
        else:
            self.logger.addComment("SetBccAddress is not available for this kind of item")
            return
        
    def SetFromAddress(self, fromAdd, timeInfo=True):
        """
        Set the from address (not available from UI)
        @type fromAdd : string
        @param fromAdd : the new from address value
        @type timeInfo: boolean
        """
        if self.isMailMessage:
            blockName = (self.item.isOutbound and "EditMailOutboundFrom" 
                         or "EditMailInboundFrom")
            self.SetEditableBlock(blockName, "from address", fromAdd, 
                                  timeInfo=timeInfo)
        else:
            self.logger.addComment("SetFromAddress is not available for this kind of item")
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
        type_states = {"Mail": dict(isOfType=self.isMailMessage,
                                    button="MailMessageButton"),
                       "Task": dict(isOfType=self.isTask,
                                    button="TaskStamp"),
                       "Event": dict(isOfType=self.isEvent,
                                     button="CalendarStamp"),
                       }
        if not type in type_states:
            return

        if not self.isCollection:
            if type_states[type]['isOfType'] == value: #Nothing to do
                return
            else:
                # select the item
                self.SelectItem()
                if timeInfo :
                    self.logger.startAction("Change the %s stamp" % type)
                # markup bar tests disabled for now -- Reid
                buttonBlock = getattr(App_ns, type_states[type]['button'])
                scripting.User.emulate_click(buttonBlock, 10, 10)
                scripting.User.idle()
                if timeInfo:
                    self.logger.endAction(True)
        else:
            self.logger.addComment("SetStamp is not available for this kind of item")
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
        self.isMailMessage = stampMail
        
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
        
    def FocusInDetailView(self):
        self.logger.startAction("Focusing in Detail View")
       #process the corresponding event
        def traverse(block):
            """Depth first traversal of blocks for a widget that accepts focus."""
            if block.widget.AcceptsFocus():
                return block
            for block in block.childrenBlocks():
                if traverse(block) is not None:
                    return block
            return None
        focusBlock = traverse(App_ns.DetailRoot)
        if focusBlock is not None:
            focusBlock.widget.SetFocus()
            # do it twice because if an event in the calendar view is being
            # edited it will be re-selected after the first SetFocus()
            focusBlock.widget.SetFocus() 
            self.logger.report(True, name="Focus set in Detail View")
        else:
            self.logger.report(False, name="Focus set in Detail View", comment="Detail View had no focusable blocks")
        wx.GetApp().Yield()
        self.logger.endAction(True)
        
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
            self.logger.addComment("SetTimeZone is not available for this kind of item")
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
            self.logger.addComment("SetRecurrence is not available for this kind of item")
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
            self.logger.addComment("SetRecurrenceEnds is not available for this kind of item")
            return

    def SendMail(self, timeInfo=True):
        """
        Send a mail message
        @type timeInfo: boolean
        """
        if self.isMailMessage:
            #select the item
            self.SelectItem()
            #Send button is available only when the body is edited
            noteArea = App_ns.detail.NotesBlock
            scripting.User.emulate_click(noteArea)
            #Press the Send button
            if timeInfo:
                self.logger.startAction("Sending the message")
            App_ns.appbar.press(name="ApplicationBarSendButton")
            wx.GetApp().Yield()
            #checkings
            
            sent = None
            #check if an SMTP account is defined
            account = Mail.getCurrentSMTPAccount(App_ns.itsView)[0]
            if account._values['host']=='':
                self.logger.report(False, name="check if an SMTP account is defined", comment="(On SMTP account) - Host not defined")
            else:
                self.logger.report(True, name="(On SMTP account)")
                # wait for mail delivery    
                while not sent:
                    wx.GetApp().Yield()
                    try:
                        sent = self.item.deliveryExtension.state
                    except AttributeError:
                        sent = None
            if timeInfo:
                self.logger.endAction(True)
            #check mail delivery
            if sent == "SENT":
                self.logger.report(True, name="(On sending message Checking)")
            else:
                self.logger.report(False, name="(On sending message Checking)")
            self.logger.addComment("Send Mail")
        else:
            self.logger.addComment("SendMail is not available for this kind of item")
            return

    def AddCollection(self, collectionName, timeInfo=True):
        """
        Put the item in the given collection
        @type collectionName : string
        @param collectionName : the name of a collection
        @type timeInfo: boolean
        """
        if not self.isCollection:
            col = App_ns.item_named(pim.ContentCollection, collectionName)
            if timeInfo:
                self.logger.startAction("Give a collection")
            if not col:
                self.logger.report(False, name="(On collection search)")
                if timeInfo:
                    self.logger.endAction(True)
                self.logger.addComment("Add collection")
                return
            col.add(self.item)
            if timeInfo:
                self.logger.endAction(True)
        else:
            self.logger.addComment("SetCollection is not available for this kind of item")
            return

    def MoveToTrash(self, timeInfo=True):
        """
        Move the item into the trash collection
        @type timeInfo: boolean
        """
        if not self.isCollection:
            # Check if the item is not already in the Trash
            if self.Check_ItemInCollection("Trash", report=False):
                self.logger.addComment("This item is already in the Trash")
                return
            # select the item
            if self.CalendarVisible():
                scripting.User.emulate_click(App_ns.AllDayEvents.widget)
            else:
                scripting.User.emulate_click(App_ns.summary.widget.GetGridWindow()) #work around for summary.select highlight bug
            self.SelectItem()
            if not self.Check_ItemSelected(report=False):
                self.logger.addComment("Item could not be selected in the calendar")
                return
            
            if timeInfo:
                self.logger.startAction("Move the item into the Trash")
            # Processing of the corresponding CPIA event
            App_ns.root.Delete()
            # give the Yield
            wx.GetApp().Yield()
            if timeInfo:
                self.logger.endAction(True)
        else:
            self.logger.addComment("MoveToTrash is not available for this kind of item")
            return

    def DeleteCollection(self, timeInfo=True):
        """
        Remove a collection from Chandler
        @type timeInfo: boolean
        """
        #turn off delete confirmation dialog for collection deletion
        confimDialog=scripting.schema.ns("osaf.views.main",wx.GetApp().UIRepositoryView).clearCollectionPref
        confimDialog.askNextTime = False
        confimDialog.response = True
        if self.isCollection:
            # select the collection
            #self.SelectItem()
            if timeInfo:
                self.logger.startAction("Remove collection")
            # Processing of the corresponding CPIA event
            App_ns.root.Remove()
            # give the Yield
            wx.GetApp().Yield()
            if timeInfo:
                self.logger.endAction(True)
        else:
            self.logger.addComment("Remove is not available for this kind of item")
        confimDialog.askNextTime = True
        return

    def CheckBlockVisibility(self, blockName, shouldBeVisible):
        """
        If this block's supposed to be hidden, make sure it is. Otherwise, make
        sure it's visible.
        """        
        # Walk up the block tree until we find a hidden or unrendered block, or
        # an event boundary. If we get to the event boundary first, consider it
        # visible; otherwise, not.
        block = getattr(App_ns, blockName)
        isVisible = True
        while block is not None and not block.eventBoundary:
            widget = getattr(block, 'widget', None)
            if widget is None or not widget.IsShown():
                isVisible = False
                break
            block = block.parentBlock
         
        # Did we get what we wanted?
        if self.logger: #sometimes the logger goes away
            if isVisible != shouldBeVisible:
                self.logger.report(False, name="CheckBlockVisibility", comment="(On %s Visibility)  || detail view "
                                          "= %s ; expected value = %s" % 
                                          (blockName, isVisible, 
                                           shouldBeVisible))
            else:
                self.logger.report(True, name="(On %s Visibility)" % blockName)
            return isVisible

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
        block = getattr(App_ns, blockName)
        #get the editable block value
        valueMethod = getattr(block.widget, 'GetValue', None)
        if valueMethod is None:
            valueMethod = getattr(block.widget, 'GetStringSelection')
        blockValue = valueMethod()
        if not blockValue == value :
            self.logger.report(False, name="CheckEditableBlock", comment="(On %s Checking)  || detail view value = %s ; expected value = %s" % (description, blockValue, value))
        else:
            self.logger.report(True, name="CheckEditableBlock", comment="(On %s Checking)" % description)

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
        block = getattr(App_ns,blockName)
        #get the menu block value
        menuValue = block.widget.GetStringSelection()
        if not menuValue == value :
            self.logger.report(False, name="CheckMenuBlock", comment="(On %s Checking)  || detail view value = %s ; expected value = %s" %(description, menuValue, value))
        else:
            self.logger.report(True, name="CheckMenuBlock", comment="(On %s Checking)" % description)
            
    def formatDate(self, dateStr):
            """if year has 4 digits removes first 2
                 also removes leading zeros from month/ day
                 to resolve bug 5031"""
            month, day, year = dateStr.split('/')
            month = str(int(month)) # get rid of leading zeros
            day = str(int(day))
            if len(year) == 4:
                year = year[2:]
            return  '%s/%s/%s' % (month, day, year)
                    

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
        buttonBlock = getattr(App_ns, buttonName)
        state = buttonBlock.isStamped()
        if not state == value :
            self.logger.report(False, name="CheckButton", comment="(On %s Checking) || detail view value = %s ; expected value = %s" % (description, state, value))
        else:
            self.logger.report(True, name="CheckButton", comment="(On %s Checking)" % description)
    
    def CheckDisplayedValues(self, msg="Displayed Values", **dict):
        """
        Check that these blocks have the right values and visibility and values
        Argument names are block names; values are tuples containing a
          boolean visibility value and optionally a value to check. If the 
          value isn't present in the tuple, only the visibility will be tested.
        Example: item.CheckDisplayedValues(HeadlineBlock=(True, "My Title"),
                                           AllDayArea=(False,))
        """
        self.SelectItem()
        for blockName, visValueTuple in dict.items():
            self.CheckBlockVisibility(blockName, visValueTuple[0])
            if len(visValueTuple) > 1:
                self.CheckEditableBlock(blockName, blockName, visValueTuple[1])

        #report the checkings
        self.logger.report(True, name="CheckDisplayedValues", comment=msg)

    def Check_DetailView(self, dict):
        """
        Check expected values by comparation to the data diplayed in the detail view
        @type dict : dictionary
        @param dict : dictionary with expected item attributes values for checking {"attributeName":"expected value",...}
        """          
        self.SelectItem()
        self.logger.startAction(name='Check_DetailView')
        # call the check methods
        for field,value in dict.iteritems():
            if field == "displayName": # display name checking
                self.CheckEditableBlock("HeadlineBlock", "display name", value)
            elif field == "startDate": # start date checking
                self.CheckEditableBlock("EditCalendarStartDate", "start date", self.formatDate(value))
            elif field == "startTime": # start time checking
                self.CheckEditableBlock("EditCalendarStartTime", "start time", value)
            elif field == "endDate": # end date checking
                self.CheckEditableBlock("EditCalendarEndDate", "end date", self.formatDate(value))
            elif field == "endTime": # end time checking
                self.CheckEditableBlock("EditCalendarEndTime", "end time", value)
            elif field == "location": # location checking
                self.CheckEditableBlock("CalendarLocation", "location", value)
            elif field == "body": # body checking
                self.CheckEditableBlock("NotesBlock", "body", value)
            elif field == "fromAddress": # from address checking
                self.CheckEditableBlock("EditMailFrom", "from address", value)
            elif field == "toAddress": # to address checking
                self.CheckEditableBlock("EditMailTo", "to address", value)
            elif field == "ccAddress": # cc address checking
                self.CheckEditableBlock("EditMailCc", "cc address", value)
            elif field == "bccAddress": # bcc address checking
                self.CheckEditableBlock("EditMailBcc", "bcc address", value)
            elif field == "status": # status checking
                self.CheckMenuBlock("EditTransparency", "status", value)
            elif field == "timeZone": # time zone checking
                self.CheckMenuBlock("EditTimeZone", "time-zone", value)
            elif field == "recurrence": # recurrence checking
                self.CheckMenuBlock("EditRecurrence", "recurrence", value)
            elif field == "recurrenceEnd": # recurrence end date checking
                self.CheckEditableBlock("EditRecurrenceEnd", "recurrence end", self.formatDate(value))
            elif field == "alarm": # status checking
                self.CheckMenuBlock("EditReminder", "alarm", value)
            elif field == "allDay": # status checking
                self.CheckEditableBlock("EditAllDay", "all-day", value)
            elif field == "stampMail": # Mail stamp checking
                self.CheckButton("MailMessageButton", "mail stamp", value)
            elif field == "stampTask": # Task stamp checking
                self.CheckButton("TaskStamp", "task stamp", value)
            elif field == "stampEvent": # Event stamp checking
                self.CheckButton("CalendarStamp", "calendar stamp", value)
            else: # Wrong check => set the report state to unchecked
                self.logger.report(False, name="Check_DetailView", comment="unable to check field %s, value %s" % (field, value))
                
        self.logger.endAction()
        
    
    def Check_Object(self, dict):
        """
        Check expected value by comparison to the data contained in the object attributes
        @type dict : dictionary
        @param dict : dictionary with expected item attributes values for checking {"attributeName":"expected value",...}
        """
        # check the changing values
        for field,value in dict.iteritems():
            if field == "displayName": # display name checking
                if self.isMailMessage:
                    d_name = "%s" % self.item.subject
                else:
                    d_name = "%s" % self.item.displayName
                if not value == d_name :
                    self.logger.report(False, name="Check_Object", comment="(On display name Checking)  || object title = %s ; expected title = %s" % (d_name, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On display name Checking)")
            elif field == "startDate": # start date checking
                startTime = self.item.startTime
                s_date = self.formatDate("%s/%s/%s" % (startTime.month, startTime.day, startTime.year) )
                dictDate = self.formatDate(value)
                if not dictDate == s_date :
                    self.logger.report(False, name="Check_Object", comment="(On start date Checking) || object start date = %s ; expected start date = %s" % (s_date, dictDate))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On start date Checking)")
            elif field == "startTime": # start time checking
                startTime = self.item.startTime
                s_time = getTime(startTime)
                if not value == s_time :
                    self.logger.report(False, name="Check_Object", comment="(On start time Checking) || object start time = %s ; expected start time = %s" % (s_time, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On start time Checking)")
            elif field == "endDate": # end date checking
                endTime = self.item.endTime
                e_date = self.formatDate("%s/%s/%s" % (endTime.month, endTime.day, endTime.year))
                dictDate = self.formatDate(value)
                if not dictDate == e_date :
                    self.logger.report(False, name="Check_Object", comment="(On end date Checking) || object end date = %s ; expected end date = %s" % (e_date, dictDate))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On end date Checking)")
            elif field == "endTime": # end time checking
                endTime = self.item.endTime
                e_time = getTime(endTime)
                if not value == e_time :
                    self.logger.report(False, name="Check_Object", comment="(On end time Checking) || object end time = %s ; expected end time = %s" % (e_time, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On end time Checking)")
            elif field == "location": # location checking
                loc = unicode(self.item.location)
                if not value == loc :
                    self.logger.report(False, name="Check_Object", comment="(On location Checking) || object location = %s ; expected location = %s" % (loc, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On location Checking)")
            elif field == "body": # body checking
                body = "%s" %self.item.body
                if not value == body :
                    self.logger.report(False, name="Check_Object", comment="(On body Checking) || object body = %s ; expected body = %s" % (body, value))
                else:
                     self.logger.report(True, name="Check_Object", comment="(On body Checking)")
            elif field == "fromAddress": # from address checking
                f = "%s" %self.item.fromAddress
                if not value == f :
                    self.logger.report(False, name="Check_Object", comment="(On from address Checking) || object from address = %s ; expected from address = %s" % (f, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On from address Checking)")
            elif field == "toAddress": # to address checking
                t = "%s" % self.item.toAddress
                if not value == t :
                    self.logger.report(False, name="Check_Object", comment="(On to address Checking) || object to address = %s ; expected to address = %s" % (t, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On to address Checking)")
            elif field == "status": # status checking
                status = "%s" % string.upper(self.item.transparency)
                if not value == status :
                    self.logger.report(False, name="Check_Object", comment="(On status Checking) || object status = %s ; expected status = %s" % (status, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On status Checking)")
            elif field == "timeZone": # time zone checking
                timeZone = "%s" % self.item.startTime.tzname()
                if not value == timeZone :
                    self.logger.report(False, name="Check_Object", comment="(On time zone Checking) || object time zone = %s ; expected time zone = %s" % (timeZone, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On time zone Checking)")
            elif field == "alarm": # status checking
                alarm = self.item.startTime - self.item.reminderTime
                field = timedelta(minutes = string.atoi(value))
                if not field == alarm :
                    self.logger.report(False, name="Check_Object", comment="(On alarm Checking) || object alarm = %s ; expected alarm = %s" % (alarm, field))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On alarm Checking)")
            elif field == "allDay": # status checking
                allDay = self.item.allDay
                if not value == allDay :
                    self.logger.report(False, name="Check_Object", comment="(On all Day Checking) || object all day = %s ; expected all day = %s" % (allDay, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On all Day Checking)")
            elif field == "stampMail": # Mail stamp checking
                if "MailMessage" in str(self.item.getKind()):
                    stampMail = True
                else:
                    stampMail = False
                if not value == stampMail :
                    self.logger.report(False, name="Check_Object", comment="(On Mail Stamp Checking) || object Mail Stamp = %s ; expected Mail Stamp = %s" % (stampMail, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On Mail Stamp Checking)")
            elif field == "stampTask": # Task stamp checking
                if "Task" in str(self.item.getKind()):
                    stampTask = True
                else:
                    stampTask = False
                if not value == stampTask :
                    self.logger.report(False, name="Check_Object", comment="(On Task Stamp Checking) || object Task Stamp = %s ; expected Task Stamp = %s" % (stampTask, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On Task Stamp Checking)")
            elif field == "stampEvent": # Event stamp checking
                if "CalendarEvent" in str(self.item.getKind()):
                    stampEvent = True
                else:
                    stampEvent = False
                if not value == stampEvent :
                    self.logger.report(False, name="Check_Object", comment="(On Event Stamp Checking) || object Event Stamp = %s ; expected Event Stamp = %s" % (stampEvent, value))
                else:
                    self.logger.report(True, name="Check_Object", comment="(On Event Stamp Checking)")
            else: # Wrong check => set the report state to unchecked
                self.logger.report(False, name="Check_Object", comment="unable to check field=%s value=%s" % (field, value))
        #report the checkings
        self.logger.addComment("Object state")

    def Check_CollectionExistence(self, expectedName=None, expectedResult=True):
        """
        Check if the collection exists/doesn't exist and has the expected display name (displayed in the sidebar)
        @type expectedName : string
        @param expectedName : The expected title of the collection
        @type expectedResult : boolean
        @param expectedResult : expected result of the method
        @return : True if result is the same as the expected
        """

        if self.isCollection:

            if self.item.isDeleted():
                if expectedResult is False:
                    self.logger.report(True, name="Check_CollectionExistence", comment="(On collection existence Checking)")
                    result = True
                else:
                    self.logger.report(False,  name="Check_CollectionExistence", comment="(On collection existence Checking)")
                    result = False
                self.logger.addComment("Collection existence")
            else:
                result = True
            return result

            if not expectedName:
                expectedName = self.item.displayName
            # check the changing values
            if not GetCollectionRow(self.item.displayName):
                exist = False
                description = "%s doesn't exist" % self.item.displayName
            else:
                exist = True
                description = "%s exists" % self.item.displayName
            #report the checkings
            if exist == expectedResult and self.item.displayName == expectedName:
                self.logger.report(True, name="Check_CollectionExistence", comment="(On collection existence Checking) - %s" % description)
                result = True
            elif not exist == expectedResult:
                self.logger.report(False, name="Check_CollectionExistence", comment="(On collection existence Checking) - %s" % description)
                result = False
            else:
                self.logger.report(False, name="Check_CollectionExistence", comment="(On collection name Checking) - current name = %s ; expected name = %s" % (self.item.displayName, expectedName))
                result = False
            self.logger.addComment("Collection existence")
            return result
        else:
            self.logger.addComment("Check_CollectionExistence is not available for this kind of item")
            return False


    def Check_ItemSelected(self, expectedResult=True, report=True):
        """
        Check if the item is displayed and selected, in the calendar view
        this means the item must be in the current display range.
        
        """
        if self.isCollection:
            selected = self.item in App_ns.sidebar.SelectedItems()
        else:
            if self.CalendarVisible():
                selected = self.item in chain(
                    App_ns.TimedEvents.widget.SelectedItems(),
                    App_ns.AllDayEvents.widget.SelectedItems()  )
            else:
                selected = self.item in App_ns.summary.widget.SelectedItems()
                
        if selected:
            description = u"item named %s is selected" % self.item.displayName
        else:
            description = u"item named %s is not selected" % self.item.displayName
        if selected == expectedResult:
            result = True
            if report:
                self.logger.report(True, name="Check_ItemSelected", comment="(On Selection Checking) - %s" % description)
        else:
            result = False
            if report:
                self.logger.report(False, name="Check_ItemSelected", comment="(On Selection Checking) - %s" % description)
        return result                 
        
        
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
            # for All, In, Out, Trash collection find by item rather than itemName
            pim_ns = scripting.schema.ns('osaf.pim', wx.GetApp().UIRepositoryView)
            chandler_collections = {"All":   pim_ns.allCollection,
                                    "Out":   pim_ns.outCollection,
                                    "In":    pim_ns.inCollection,
                                    "Trash": pim_ns.trashCollection}
            if collectionName in chandler_collections.keys():
                col = chandler_collections[collectionName]
            else:
                col = App_ns.item_named(pim.ContentCollection, collectionName)
            if col:
                if self.item in col:
                    value = True
                    description = "item named %s is in %s" % (self.item.displayName, collectionName)
                else:
                    value = False
                    description = "item named %s is not in %s" % (self.item.displayName, collectionName)
                if value == expectedResult:
                    result = True
                    if report:
                        self.logger.report(True, name="Check_ItemInCollection", comment="(On Collection Checking) - %s" % description)
                        self.logger.addComment("Item in collection")
                else:
                    result = False
                    if report:
                        self.logger.report(False, name="Check_ItemInCollection", comment="(On Collection Checking) - %s" % description)
                        self.logger.addComment("Item in collection")
            else:
                result = False
                if report:
                    self.logger.report(False, name="Check_ItemInCollection", comment="(On collection search)")
                    self.logger.addComment("Item in collection")
            return result 
        else:
            self.logger.addComment("Check_ItemInCollection is not available for this kind of item")
            return False 

    def Check_CalendarView(self, **attrs):

        item = self.item

        # go look up the screen item in the timed events canvas

        timedCanvas = App_ns.TimedEvents

        # find the canvas item for the given item:
        canvasItem = timedCanvas.widget.GetCanvasItems(item).next()

        # now check the strings:

        for attrName, attrValue in  attrs.iteritems():
            if getattr(canvasItem, attrName) == attrValue:
                self.logger.report(True, name="Check_CalendarView", comment="(On %s Checking)" % attrName)
            else:
                self.logger.report(False, name="Check_CalendarView", comment="(On %s Checking) || calendar view value = %s ; expected value = %s" % (attrName, getattr(canvasItem, attrName), attrValue))
                #if self.logger: self.logger.addComment("Calendar View")

    
class UITestAccounts:
    fieldMap = {
        'SMTP': {'displayName': 3, 'email': 5, 'host': 7,
                 'username': 17, 'password': 19, 'security': 9,
                 'port':13, 'authentication': 15},

        'IMAP': {'displayName': 3, 'email': 5,
                 'name': 7, 'host': 9, 'username': 11,
                 'password': 13, 'security': 15, 'port': 19,
                 'default': 21, 'server': 24},

        'POP': {'displayName': 3, 'email': 5,
                'name': 7, 'host': 9, 'username': 11,
                'password': 13, 'security': 15,'port': 19,
                'leave': 21, 'default': 23, 'server': 26},

        'WebDAV':{'displayName': 3, 'host':5, 'path': 7,
                  'username':9, 'password':11, 'port': 13, 'ssl': 14,
                  'default':16},
        }
    
    accountTypeIndex = {'SMTP': 3, 'IMAP': 1, 'POP': 2,
                        'WebDAV': 4}

    def __init__(self, logger):
        self.view = App_ns.itsView
        self.logger = logger
        self.window = None
        
        
    def Open(self):
        """
        Open the Account preferences dialog window in non-modal mode
        """
        # Have to do it the hard way since Account Preferences is modal by default
        import application
        self.window = application.dialogs.AccountPreferences.ShowAccountPreferencesDialog(wx.GetApp().mainFrame, rv=self.view, modal=False)
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
        else:
            self.logger.report(False, name="VerifyValues", comment="No such account: %s" % name)
            result = False
            account = None
        
        if account is not None:
            result = True
            for (key, value) in keys.items():
                if account._values[key] != value:
                    self.logger.report(False, name="VerifyValues", comment="Checking %s %s: expected %s, but got %s" % (type, key, value, account._values[key]))
                    result = False
                else:
                    self.logger.report(True, name="VerifyValues", comment="Checking %s %s" % (type, key))

        #report the checkings
        self.logger.addComment("%s values" % type)
        return result


class UITestView(object):
    def __init__(self, logger, environmentFile=None):
        self.logger = logger
        self.view = App_ns.itsView
        #get the current view state
        self.state = self.GetCurrentState()

        # setup the test environment if an environment file was specified
        if environmentFile is not None:
            path = os.path.join(os.getenv('CHANDLERHOME'),"tools/cats/DataFiles")
            #Upcast path to unicode since Sharing requires a unicode path
            path = unicode(path, sys.getfilesystemencoding())
            share = Sharing.Sharing.OneTimeFileSystemShare(path, 
                            environmentFile, 
                            ICalendar.ICalendarFormat, 
                            itsView=App_ns.itsView)
            try:
                self.collection = share.get()
            except:
                if logger: 
                    logger.endAction(False, name="UITestView", comment="Importing calendar: exception raised")
            else:
                App_ns.sidebarCollection.add(self.collection)
                scripting.User.idle()
                # do another idle and yield to make sure the calendar is up.
                scripting.User.idle()
                if logger: logger.report(True, name="UITestView", comment="Importing calendar")

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
        self.logger.startAction("Switch to %s" % viewName)
        #process the corresponding event
        App_ns.appbar.press(name=button)
        wx.GetApp().Yield()
        self.logger.endAction(True)
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
        if not self.state == self.GetCurrentState():
            self.logger.report(False, name="CheckView", comment="(On wiew checking) || expected current view = %s ; Correspondig button is switch off " % self.state)
        else:
            self.logger.report(True, name="CheckView", comment="(On view checking)")
        #report the checkings
        self.logger.addComment("View")

    def GoToDate(self, datestring):
        """
        Create a GoToDate event.  In the US locale, datestring should
        be of the form mm/dd/yy.
        
        """
        App_ns.root.GoToDate({'DateString' : datestring })

    def GoToToday(self):
        App_ns.root.GoToToday()
        
    def DoubleClickInCalView(self, x=100, y=100, gotoTestDate=True):
        """
        Emulate a double click in the calendar a the given position
        @type x : int
        @param x : the x coordinate
        @type y : int
        @param y : the y coordinate
        @param gotoTestDate: either True to go to a well known date,
                             or an actual date string, in the form
                             YYYY-mm-dd
        @type gotoTestDate: bool or datetime
        """
        if self.state == "CalendarView":
            # move to a known date, otherwise we'll just be operating
            #  on whatever shows up on Today's calendar
            if gotoTestDate:
                if gotoTestDate is True:
                    # True sends us to the default test date
                    gotoTestDate = "12/24/2005" # Dec has some free days
                self.GoToDate(gotoTestDate)

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
            pos.y += 1 # Work around a bug somewhere (appears with r8724)
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
        
                self.logger.startAction("Double click in the calendar view")
                self.timedCanvas.widget.ProcessEvent(click)
                wx.GetApp().Yield()
                self.logger.endAction(True)
                #work around : SelectAll() doesn't work
                wx.Window.FindFocus().Clear()
            else:
                self.logger.startAction("Double click in the calendar view")
                self.timedCanvas.widget.ProcessEvent(click)
                scripting.User.idle()
                self.logger.endAction(True)
            
            #it's a new event
            if not canvasItem :
                for elem in reversed(self.timedCanvas.widget.canvasItemList):
                # It's possible for the event to appear a few pixels
                # lower than pos, if pos is near a dividing line in
                # the calendar
                    if elem.isHit(pos) or elem.isHit(pos+(0,5)):
                            canvasItem = elem
                            self.logger.report(True, name="DoubleClickInCalView", comment="On double click in Calendar view checking (event creation)")
                            break
            else:
                self.logger.report(True, name="DoubleClickInCalView", comment="On double click in Calendar view checking (event selection)")

            #checking
            self.logger.addComment("Double click")
            if not canvasItem:
                self.logger.report(False, name="DoubleClickInCalView", comment="The event has not been created or selected")
                self.logger.Report()
                return
                   
            #create the corresponding UITestItem object
            TestItem = UITestItem(canvasItem.item, self.logger)
            return TestItem
        else:
            self.logger.addComment("DoubleClickInCalView is not available in the current view : %s" % self.state)
            return

    def Check_Equality(self, a, b, message):
        
        if a == b:
            self.logger.report(True, name="Check_Equality", comment=message)
        else:
            self.logger.report(False, name="Check_Equality", comment="%s || %s != %s" % (message, a, b))
    
