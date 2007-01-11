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


from QALogger import *
from datetime import datetime, timedelta, time
from time import mktime, strptime
from PyICU import ICUtzinfo
from osaf import pim, sharing
import osaf.pim.mail as Mail
import osaf.pim.collections as Collection
import application.Globals as Globals
import wx
import string
import osaf.framework.scripting as scripting
import os, sys
from itertools import chain
from i18n.tests import uw
from osaf.framework.blocks.Block import Block
from application.dialogs.PublishCollection import ShowPublishDialog
import application.dialogs.SubscribeCollection as SubscribeCollection
from repository.item.Item import MissingClass

#Global AppProxy instance
App_ns = scripting.app_ns()

def sidebarCollectionNamed(name):
    """
    Look for a sidebar collection with name, otherwise return None
    """
    sidebarWidget = App_ns.sidebar.widget
    for i in range(sidebarWidget.GetNumberRows()):
        collection = sidebarWidget.GetTable().GetValue(i,0)[0]
        if collection.displayName == name:
            return collection
    return None


def publishSubscribe(logger):
    """
    A function to publish and subscribe a collection.
    """
    # action
    # Webdav Account Setting
    ap = UITestAccounts(logger)
    ap.Open() # first, open the accounts dialog window
    ap.CreateAccount("WebDAV")
    ap.TypeValue("displayName", uw("Publish Test WebDAV"))
    ap.TypeValue("host", "osaf.us")
    ap.TypeValue("path", "cosmo/home/demo1")
    ap.TypeValue("username", "demo1")
    ap.TypeValue("password", "ad3leib5")
    ap.TypeValue("port", "443")
    ap.ToggleValue("ssl", True)
    ap.ToggleValue("default", True)
    ap.Ok()

    # verification
    ap.VerifyValues("WebDAV", uw("Publish Test WebDAV"), displayName = uw("Publish Test WebDAV"), host = "osaf.us", username = "demo1", password="ad3leib5", port=443)

    # import events so test will have something to share even when run by itself
    path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
    # Upcast path to unicode since Sharing requires a unicode path
    path = unicode(path, 'utf8')
    share = sharing.OneTimeFileSystemShare(path, u'testSharing.ics',
        sharing.ICalendarFormat, itsView=App_ns.itsView)

    collection = share.get()
    App_ns.sidebarCollection.add(collection)
    scripting.User.idle()

    # Collection selection
    sidebar = App_ns.sidebar
    scripting.User.emulate_sidebarClick(sidebar, "testSharing")

    # Sharing dialog
    collection = Block.findBlockByName("MainView").getSidebarSelectedCollection()
    if collection is not None:
        publishName = "TestSharing_%s" % str(collection.itsUUID)
        win = ShowPublishDialog(wx.GetApp().mainFrame, view=App_ns.itsView,
                                collection=collection,
                                modal=False,
                                name=publishName)
        #Share button call
        
        app = wx.GetApp()
        
        # We are interested in seeing how quickly we can upload the collection
        logger.Start('Publish')
        win.PublishCollection()
        while not win.done:
            app.Yield()
        logger.Stop()

        if not win.success:        
            logger.ReportFailure("(On publish collection)")
            win.OnCancel(None) # Close the window which should be showing a failure
            return
        
        # Get a read-write ticket to the published collection
        # XXX This is ripped from PublishCollection
        if win.publishType == 'freebusy':
            share = sharing.getFreeBusyShare(win.collection)
        else:
            share = sharing.getShare(win.collection)
        urls = sharing.getUrls(share)
        if len(urls) == 1:
            urlString = urls[0]
        elif win.publishType == 'freebusy':
            urlString = urls[1]
        else:
            urlString = urls[0] # read-write
        
        #Done button call
        win.OnPublishDone(None)
        app.Yield()

        # Unsubscribe and delete the (local) collection we just published so
        # that we can subscribe to it below.
        sharing.unsubscribe(collection)

        # Two clicks are required to select the collection (this is the second)
        scripting.User.emulate_sidebarClick(sidebar, "testSharing")
        App_ns.root.Remove({'testing' : True})
        scripting.User.idle()

        # Subscribe to the remote collection, forcing the subscribed name to
        # be "testSharing" because it was given a random name when published above.
        win = SubscribeCollection.Show(wx.GetApp().mainFrame,
            view=App_ns.itsView, modal=False, name="testSharing")
        url = win.toolPanel.GetChildren()[1]
        url.SetFocus()
        url.Clear()

        # Need to have this or first letter of URL is not
        # typed into control on Linux
        scripting.User.idle()
        
        scripting.User.emulate_typing(urlString)
        
        # We are interested in seeing how quickly we can download the collection
        logger.Start('Subscribe')
        win.OnSubscribe(None)
        try:
            while win.subscribing:
                app.Yield()
        except wx.PyDeadObjectError:
            # XXX The C++ part of the dialog was gone, so we are no longer
            # XXX supposed to touch any attributes of the dialog. In our
            # XXX case this is safe, so just ignore. This seems to be needed
            # XXX on Linux only.
            pass
        logger.Stop()
        
        scripting.User.idle()
    
        # verification
        if scripting.User.emulate_sidebarClick(App_ns.sidebar, "testSharing"):
            # We need to click twice to move the focus to the sidebar
            scripting.User.emulate_sidebarClick(App_ns.sidebar, "testSharing")
            # cleanup
            # cosmo can only handle so many shared calendars
            # so remove this one when done
            collection = sidebarCollectionNamed('testSharing')
            sharing.unpublish(collection)
            App_ns.root.Remove({'testing' : True})

            logger.ReportPass("(On Subscribe collection)")
        else:
            logger.ReportFailure("(On Subscribe collection)")
        
        logger.SetChecked(True)


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
        minute = u"%s" % minute
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
    item = App_ns.item_named(pim.Note, name)
    if pim.has_stamp(item, pim.EventStamp):
        master = pim.EventStamp(item).getMaster()
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
    def __init__(self, type, logger=None):
        for key in DataTypes.iterkeys():
            # set isTask, etc
            setattr(self, 'is' + key, False)
        
        if type not in DataTypes:
            # "Copy constructor"
            if pim.has_stamp(type, pim.EventStamp):
                self.isEvent = True
                self.view = App_ns.itsView
                self.logger = logger
                self.item = pim.EventStamp(type).itsItem
                self.recurring = hasattr(pim.EventStamp(type), 'recurrenceID')
            else:
                return
        else:
            self.allDay = self.recurring = False
            self.view = App_ns.itsView
            self.logger = logger
            if self.logger: self.logger.Start("%s creation" % type)
            
            setattr(self, 'is' + type, True)
            constructorName = DataTypes[type]
            constructor = getattr(App_ns.root, constructorName)
            item = constructor()
            # A cheesy hack for annotation classes
            self.item = getattr(item, 'itsItem', item)
            
            # Give the Yield
            scripting.User.idle()
            if self.logger: self.logger.Stop()
    
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
        if self.logger: self.logger.Start(msg)
        for param, method in methodOrder:
            if param in args:
                method(args[param], timeInfo=False)
        if self.logger: self.logger.Stop()
            
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

        if self.logger: self.logger.Start(msg)
        for (key, value) in argList:
            methodDict[key](value, timeInfo=False)
        if self.logger: self.logger.Stop()

    def CalendarVisible(self):
        """In the calendar view?"""
        return App_ns.ApplicationBarEventButton.widget.IsToggled()

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
            if self.logger: self.logger.Start("%s setting" % description)
        block = getattr(App_ns, blockName)
        # Emulate the mouse click in the display name block
        scripting.User.emulate_click(block)
        # Select the old text
        block.widget.SelectAll()
        # Emulate the keyboard events
        scripting.User.emulate_typing(value)
        scripting.User.emulate_return()
        if timeInfo:
            if self.logger: self.logger.Stop()

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
               if self.logger: self.logger.Start("%s setting" % menuName)
            # Emulate the mouse click in the menu
            scripting.User.emulate_click(block)
            block.widget.SetStringSelection(menuChoice)
            # Process the event corresponding to the selection
            selectionEvent = wx.CommandEvent(wx.wxEVT_COMMAND_CHOICE_SELECTED)
            selectionEvent.SetEventObject(block.widget)
            block.widget.ProcessEvent(selectionEvent)
            self.SelectItem()
            if timeInfo:
                if self.logger: self.logger.Stop()
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
                if self.logger: self.logger.Start("Collection title setting")
            # Type the new collection displayName
            scripting.User.emulate_typing(displayName)
            # work around : emulate_return doesn't work
            #scripting.User.emulate_return()
            scripting.User.emulate_sidebarClick(App_ns.sidebar, "Dashboard")
            #check this actually worked 
            #assert self.item.displayName == displayName, '%s != %s' % \
            #(self.item.displayName.encode('raw_unicode_escape'), displayName.encode('raw_unicode_escape'))
            if timeInfo:
                if self.logger: self.logger.Stop()

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
            if self.logger: self.logger.Print("SetStartTime is not available for this kind of item")
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
            if self.logger: self.logger.Print("SetStartDate is not available for this kind of item")

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
            if self.logger: self.logger.Print("SetEndTime is not available for this kind of item")
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
            if self.logger: self.logger.Print("SetEndDate is not available for this kind of item")
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
            if self.logger: self.logger.Print("SetLocation is not available for this kind of item")
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
            if self.allDay != allDay:
                if timeInfo:
                    if self.logger: self.logger.Start("All-day setting")
                allDayBlock = App_ns.detail.EditAllDay
                scripting.User.emulate_click(allDayBlock)
                if timeInfo:
                    if self.logger: self.logger.Stop()
                self.allDay = allDay
            elif self.logger: self.logger.Print("SetAllDay: allDay is already %s" % allDay)
        else:
            if self.logger: self.logger.Print("SetAllDay is not available for this kind of item")
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
            if self.logger: self.logger.Print("SetStatus is not available for this kind of item")
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
            if self.logger: self.logger.Print("SetAlarm is not available for this kind of item")
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
            if self.logger: self.logger.Print("SetBody is not available for this kind of item")
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
            if self.logger: self.logger.Print("SetToAddress is not available for this kind of item")
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
            if self.logger: self.logger.Print("SetCcAddress is not available for this kind of item")
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
            if self.logger: self.logger.Print("SetBccAddress is not available for this kind of item")
            return
        
    def SetFromAddress(self, fromAdd, timeInfo=True):
        """
        Set the from address (not available from UI)
        @type fromAdd : string
        @param fromAdd : the new from address value
        @type timeInfo: boolean
        """
        if self.isMailMessage:
            blockName = (pim.mail.MailStamp(self.item).isOutbound and
                         "EditMailOutboundFrom" 
                         or "EditMailInboundFrom")
            self.SetEditableBlock(blockName, "from address", fromAdd, 
                                  timeInfo=timeInfo)
        else:
            if self.logger: self.logger.Print("SetFromAddress is not available for this kind of item")
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
                    if self.logger: self.logger.Start("Change the %s stamp" % type)
                # markup bar tests disabled for now -- Reid
                buttonBlock = getattr(App_ns, type_states[type]['button'])
                scripting.User.emulate_click(buttonBlock, 10, 10)
                scripting.User.idle()
                if timeInfo:
                    if self.logger: self.logger.Stop()
        else:
            if self.logger: self.logger.Print("SetStamp is not available for this kind of item")
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
        if self.logger: self.logger.Start("Focusing in Detail View")
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
            if self.logger: self.logger.ReportPass("Focus set in Detail View")
        else:
            if self.logger: self.logger.ReportFailure("Detail View had no focusable blocks")
        wx.GetApp().Yield()
        if self.logger: self.logger.Stop()
        
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
            if self.logger: self.logger.Print("SetTimeZone is not available for this kind of item")
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
            if self.logger: self.logger.Print("SetRecurrence is not available for this kind of item")
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
            if self.logger: self.logger.Print("SetRecurrenceEnds is not available for this kind of item")
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
                if self.logger: self.logger.Start("Sending the message")
            App_ns.appbar.press(name="ApplicationBarSendButton")
            wx.GetApp().Yield()
            #checkings
            if self.logger: self.logger.SetChecked(True)
            sent = None
            #check if an SMTP account is defined
            account = Mail.getCurrentSMTPAccount(App_ns.itsView)[0]
            if account._values['host']=='':
                if self.logger: self.logger.ReportFailure("(On SMTP account) - Host not defined")
            else:
                if self.logger: self.logger.ReportPass("(On SMTP account)")
                # wait for mail delivery    
                mailMessage = pim.mail.MailStamp(self.item)
                while not sent:
                    wx.GetApp().Yield()
                    try:
                        sent = mailMessage.deliveryExtension.state
                    except AttributeError:
                        sent = None
            if timeInfo:
                if self.logger: self.logger.Stop()
            #check mail delivery
            if sent == "SENT":
                if self.logger: self.logger.ReportPass("(On sending message Checking)")
            else:
                if self.logger: self.logger.ReportFailure("(On sending message Checking)")
            if self.logger: self.logger.Report("Send Mail")
        else:
            if self.logger: self.logger.Print("SendMail is not available for this kind of item")
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
                if self.logger: self.logger.Start("Give a collection")
            if not col:
                if self.logger: self.logger.ReportFailure("(On collection search)")
                if timeInfo:
                    if self.logger: self.logger.Stop()
                if self.logger: self.logger.Report("Add collection")
                return
            col.add(self.item)
            if timeInfo:
                if self.logger: self.logger.Stop()
        else:
            if self.logger: self.logger.Print("SetCollection is not available for this kind of item")
            return

    def MoveToTrash(self, timeInfo=True):
        """
        Move the item into the trash collection
        @type timeInfo: boolean
        """
        if not self.isCollection:
            # Check if the item is not already in the Trash
            if self.Check_ItemInCollection("Trash", report=False):
                if self.logger: self.logger.Print("This item is already in the Trash")
                return
            # select the item
            if self.CalendarVisible():
                scripting.User.emulate_click(App_ns.AllDayEvents.widget)
            else:
                scripting.User.emulate_click(App_ns.summary.widget.GetGridWindow()) #work around for summary.select highlight bug
            self.SelectItem()
            if not self.Check_ItemSelected(report=False):
                if self.logger: self.logger.Print("Item could not be selected in the calendar")
                return
            
            if timeInfo:
                if self.logger: self.logger.Start("Move the item into the Trash")
            # Processing of the corresponding CPIA event
            App_ns.root.Delete()
            # give the Yield
            wx.GetApp().Yield()
            if timeInfo:
                if self.logger: self.logger.Stop()
        else:
            if self.logger: self.logger.Print("MoveToTrash is not available for this kind of item")
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
                if self.logger: self.logger.Start("Remove collection")
            # Processing of the corresponding CPIA event
            App_ns.root.Remove({'testing' : True})
            # give the Yield
            wx.GetApp().Yield()
            if timeInfo:
                if self.logger: self.logger.Stop()
        else:
            if self.logger: self.logger.Print("Remove is not available for this kind of item")
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
        
        if self.logger: 
            # Did we get what we wanted?
            if isVisible != shouldBeVisible:
                self.logger.ReportFailure("(On %s Visibility)  || detail view "
                                          "= %s ; expected value = %s" %
                                          (blockName, isVisible,
                                           shouldBeVisible))
            else:
                self.logger.ReportPass("(On %s Visibility)" % blockName)
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
            if self.logger: self.logger.ReportFailure("(On %s Checking)  || detail view value = %s ; expected value = %s" % (description, blockValue, value))
        else:
            if self.logger: self.logger.ReportPass("(On %s Checking)" % description)

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
            if self.logger: self.logger.ReportFailure("(On %s Checking)  || detail view value = %s ; expected value = %s" % (description, menuValue, value))
        else:
            if self.logger: self.logger.ReportPass("(On %s Checking)" % description)

    def formatDate(self, dateStr):
            """if year has 4 digits removes first 2
                 also removes leading zeros from month/ day
                 to resolve bug 5031"""
            month, day, year = dateStr.split('/')
            month = str(int(month)) # get rid of leading zeros
            day = str(int(day))
            if len(year) == 4:
                year = year[2:]
            return  u'%s/%s/%s' % (month, day, year)


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
            if self.logger: self.logger.ReportFailure("(On %s Checking) || detail view value = %s ; expected value = %s" % (description, state, value))
        else:
            if self.logger: self.logger.ReportPass("(On %s Checking)" % description)

    def CheckDisplayedValues(self, msg="Displayed Values", **dict):
        """
        Check that these blocks have the right values and visibility and values
        Argument names are block names; values are tuples containing a
          boolean visibility value and optionally a value to check. If the 
          value isn't present in the tuple, only the visibility will be tested.
        Example: item.CheckDisplayedValues(HeadlineBlock=(True, "My Title"),
                                           AllDayArea=(False,))
        """
        if self.logger: self.logger.SetChecked(True)
        self.SelectItem()
        for blockName, visValueTuple in dict.items():
            self.CheckBlockVisibility(blockName, visValueTuple[0])
            if len(visValueTuple) > 1:
                self.CheckEditableBlock(blockName, blockName, visValueTuple[1])

        #report the checkings
        if self.logger: self.logger.Report(msg)

    def Check_DetailView(self, dict):
        """
        Check expected values by comparation to the data diplayed in the detail view
        @type dict : dictionary
        @param dict : dictionary with expected item attributes values for checking {"attributeName":"expected value",...}
        """  
        if self.logger: self.logger.SetChecked(True)
        self.SelectItem()
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
                if self.logger: self.logger.SetChecked(False)
                
        #report the checkings
        if self.logger: self.logger.Report("Detail View")
    
    def Check_Object(self, dict):
        """
        Check expected value by comparison to the data contained in the object attributes
        @type dict : dictionary
        @param dict : dictionary with expected item attributes values for checking {"attributeName":"expected value",...}
        """
        if self.logger: self.logger.SetChecked(True)
        # check the changing values
        for field,value in dict.iteritems():
            if field == "displayName": # display name checking
                if self.isMailMessage:
                    d_name = pim.mail.MailStamp(self.item).subject
                else:
                    d_name = self.item.displayName
                if not value == d_name:
                    if self.logger: self.logger.ReportFailure("(On display name Checking)  || object title = %s ; expected title = %s" % (d_name, value))
                else:
                    if self.logger: self.logger.ReportPass("(On display name Checking)")
            elif field == "startDate": # start date checking
                startTime = pim.EventStamp(self.item).startTime
                s_date = self.formatDate("%s/%s/%s" % (startTime.month, startTime.day, startTime.year) )
                dictDate = self.formatDate(value)
                if not dictDate == s_date :
                    if self.logger: self.logger.ReportFailure("(On start date Checking) || object start date = %s ; expected start date = %s" % (s_date, dictDate))
                else:
                    if self.logger: self.logger.ReportPass("(On start date Checking)")
            elif field == "startTime": # start time checking
                startTime = pim.EventStamp(self.item).startTime
                s_time = getTime(startTime)
                if not value == s_time :
                    if self.logger: self.logger.ReportFailure("(On start time Checking) || object start time = %s ; expected start time = %s" % (s_time, value))
                else:
                    if self.logger: self.logger.ReportPass("(On start time Checking)")
            elif field == "endDate": # end date checking
                endTime = pim.EventStamp(self.item).endTime
                e_date = self.formatDate("%s/%s/%s" % (endTime.month, endTime.day, endTime.year))
                dictDate = self.formatDate(value)
                if not dictDate == e_date :
                    if self.logger: self.logger.ReportFailure("(On end date Checking) || object end date = %s ; expected end date = %s" % (e_date, dictDate))
                else:
                    if self.logger: self.logger.ReportPass("(On end date Checking)")
            elif field == "endTime": # end time checking
                endTime = pim.EventStamp(self.item).endTime
                e_time = getTime(endTime)
                if not value == e_time :
                    if self.logger: self.logger.ReportFailure("(On end time Checking) || object end time = %s ; expected end time = %s" % (e_time, value))
                else:
                    if self.logger: self.logger.ReportPass("(On end time Checking)")
            elif field == "location": # location checking
                #Convert the location item to a unicode string
                loc = unicode(pim.EventStamp(self.item).location)

                if not value == loc:
                    if self.logger: self.logger.ReportFailure("(On location Checking) || object location = %s ; expected location = %s" % (loc, value))
                else:
                    if self.logger: self.logger.ReportPass("(On location Checking)")
            elif field == "body": # body checking
                body = self.item.body
                if not value == body:
                    if self.logger: self.logger.ReportFailure("(On body Checking) || object body = %s ; expected body = %s" %(body, value))
                else:
                     if self.logger: self.logger.ReportPass("(On body Checking)")
            elif field == "fromAddress": # from address checking
                f = pim.mail.MailStamp(item).fromAddress
                if not value == f :
                    if self.logger: self.logger.ReportFailure("(On from address Checking) || object from address = %s ; expected from address = %s" % (f, value))
                else:
                    if self.logger: self.logger.ReportPass("(On from address Checking)")
            elif field == "toAddress": # to address checking
                t = pim.mail.MailStamp(item).toAddress
                if not value == t:
                    if self.logger: self.logger.ReportFailure("(On to address Checking) || object to address = %s ; expected to address = %s" % (t, value))
                else:
                    if self.logger: self.logger.ReportPass("(On to address Checking)")
            elif field == "status": # status checking
                status = pim.EventStamp(self.item).transparency.upper()
                if not value == status:
                    if self.logger: self.logger.ReportFailure("(On status Checking) || object status = %s ; expected status = %s" % (status, value))
                else:
                    if self.logger: self.logger.ReportPass("(On status Checking)")
            elif field == "timeZone": # time zone checking
                timeZone = pim.EventStamp(self.item).startTime.tzname()
                if not value == timeZone :
                    if self.logger: self.logger.ReportFailure("(On time zone Checking) || object time zone = %s ; expected time zone = %s" % (timeZone, value))
                else:
                    if self.logger: self.logger.ReportPass("(On time zone Checking)")
            elif field == "alarm": # status checking
                alarm = pim.EventStamp(self.item).startTime - pim.Remindable(self.item).reminderTime
                field = timedelta(minutes = string.atoi(value))
                if not field == alarm:
                    if self.logger: self.logger.ReportFailure("(On alarm Checking) || object alarm = %s ; expected alarm = %s" % (alarm, field))
                else:
                    if self.logger: self.logger.ReportPass("(On alarm Checking)")
            elif field == "allDay": # status checking
                allDay = pim.EventStamp(self.item).allDay
                if not value == allDay:
                    if self.logger: self.logger.ReportFailure("(On all Day Checking) || object all day = %s ; expected all day = %s" % (allDay, value))
                else:
                    if self.logger: self.logger.ReportPass("(On all Day Checking)")
            elif field == "stampMail": # Mail stamp checking
                stampMail = pim.has_stamp(self.item, pim.mail.MailStamp)
                if not value == stampMail:
                    if self.logger: self.logger.ReportFailure("(On Mail Stamp Checking) || object Mail Stamp = %s ; expected Mail Stamp = %s" % (stampMail, value))
                else:
                    if self.logger: self.logger.ReportPass("(On Mail Stamp Checking)")
            elif field == "stampTask": # Task stamp checking
                stampTask = pim.has_stamp(self.item, pim.TaskStamp)
                if not value == stampTask:
                    if self.logger: self.logger.ReportFailure("(On Task Stamp Checking) || object Task Stamp = %s ; expected Task Stamp = %s" % (stampTask, value))
                else:
                    if self.logger: self.logger.ReportPass("(On Task Stamp Checking)")
            elif field == "stampEvent": # Event stamp checking
                stampEvent = pim.has_stamp(self.item, pim.EventStamp)
                if not value == stampEvent:
                    if self.logger: self.logger.ReportFailure("(On Event Stamp Checking) || object Event Stamp = %s ; expected Event Stamp = %s" % (stampEvent, value))
                else:
                    if self.logger: self.logger.ReportPass("(On Event Stamp Checking)")
            else: # Wrong check => set the report state to unchecked
                if self.logger: self.logger.SetChecked(False)
        #report the checkings
        if self.logger: self.logger.Report("Object state")

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
                if self.logger:
                    self.logger.SetChecked(True)
                    if expectedResult is False:
                        self.logger.ReportPass("(On collection existence Checking)")
                        result = True
                    else:
                        self.logger.ReportFailure("(On collection existence Checking)")
                        result = False
                    self.logger.Report("Collection existence")
                else:
                    result = True
                return result

            if not expectedName:
                expectedName = self.item.displayName
            if self.logger: self.logger.SetChecked(True)
            # check the changing values
            if not GetCollectionRow(self.item.displayName):
                exist = False
                description = u"%s doesn't exist" % self.item.displayName
            else:
                exist = True
                description = u"%s exists" % self.item.displayName
            #report the checkings
            if exist == expectedResult and self.item.displayName == expectedName:
                if self.logger: self.logger.ReportPass("(On collection existence Checking) - %s" % description)
                result = True
            elif not exist == expectedResult:
                if self.logger: self.logger.ReportFailure("(On collection existence Checking) - %s" % description)
                result = False
            else:
                if self.logger: self.logger.ReportFailure("(On collection name Checking) - current name = %s ; expected name = %s" % (self.item.displayName, expectedName))
                result = False
            if self.logger: self.logger.Report("Collection existence")
            return result
        else:
            if self.logger: self.logger.Print("Check_CollectionExistence is not available for this kind of item")
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
                if self.logger: self.logger.ReportPass("(On Selection Checking) - %s" % description)
        else:
            result = False
            if report:
                if self.logger: self.logger.ReportFailure("(On Selection Checking) - %s" % description)
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
            if self.logger: self.logger.SetChecked(True)
            # for All, In, Out, Trash collection find by item rather than itemName
            pim_ns = scripting.schema.ns('osaf.pim', wx.GetApp().UIRepositoryView)
            chandler_collections = {"Dashboard": pim_ns.allCollection,
                                    "Out":       pim_ns.outCollection,
                                    "In":        pim_ns.inCollection,
                                    "Trash":     pim_ns.trashCollection}
            if collectionName in chandler_collections.keys():
                col = chandler_collections[collectionName]
            else:
                col = App_ns.item_named(pim.ContentCollection, collectionName)
            if col:
                if self.item in col:
                    value = True
                    description = u"item named %s is in %s" % (self.item.displayName, collectionName)
                else:
                    value = False
                    description = u"item named %s is not in %s" % (self.item.displayName, collectionName)
                if value == expectedResult:
                    result = True
                    if report:
                        if self.logger: self.logger.ReportPass("(On Collection Checking) - %s" % description)
                        if self.logger: self.logger.Report("Item in collection")
                else:
                    result = False
                    if report:
                        if self.logger: self.logger.ReportFailure("(On Collection Checking) - %s" % description)
                        if self.logger: self.logger.Report("Item in collection")
            else:
                result = False
                if report:
                    if self.logger: self.logger.ReportFailure("(On collection search)")
                    if self.logger: self.logger.Report("Item in collection")
            return result 
        else:
            if self.logger: self.logger.Print("Check_ItemInCollection is not available for this kind of item")
            return False 

    def Check_CalendarView(self, **attrs):

        item = self.item

        # go look up the screen item in the timed events canvas

        timedCanvas = App_ns.TimedEvents

        # find the canvas item for the given item:
        canvasItem = timedCanvas.widget.GetCanvasItems(item).next()

        # now check the strings:

        if self.logger: self.logger.SetChecked(True)
        for attrName, attrValue in  attrs.iteritems():
            if getattr(canvasItem, attrName) == attrValue:
                if self.logger: self.logger.ReportPass("(On %s Checking)" % attrName)
            else:
                if self.logger: self.logger.ReportFailure("(On %s Checking) || calendar view value = %s ; expected value = %s" % (attrName, getattr(canvasItem, attrName), attrValue))
        if self.logger: self.logger.SetChecked(False)
        if self.logger: self.logger.Report("Calendar View")

    
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

    def __init__(self, logger=None):
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
            iter = sharing.WebDAVAccount.iterItems(App_ns.itsView)
        elif type == "POP":
            iter = Mail.POPAccount.iterItems(App_ns.itsView)
        else:
            raise AttributeError

        for account in iter:
            if account.displayName == name:
                break
        else:
            if self.logger: self.logger.ReportFailure("No such account: %s" % name)
            result = False
            account = None

        if account is not None:
            if self.logger: self.logger.SetChecked(True)
            result = True
            for (key, value) in keys.items():
                if account._values[key] != value:
                    if self.logger: self.logger.ReportFailure("Checking %s %s: expected %s, but got %s" % (type, key, value, account._values[key]))
                    result = False
                else:
                    if self.logger: self.logger.ReportPass("Checking %s %s" % (type, key))

        #report the checkings
        if self.logger: self.logger.Report("%s values" %type)
        return result


class UITestView(object):
    def __init__(self, logger=None, environmentFile=None):
        self.logger = logger
        self.view = App_ns.itsView
        #get the current view state
        self.state = self.GetCurrentState()

        # setup the test environment if an environment file was specified
        if environmentFile is not None:
            path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
            #Upcast path to unicode since Sharing requires a unicode path
            path = unicode(path, sys.getfilesystemencoding())
            share = sharing.OneTimeFileSystemShare(path,
                            environmentFile,
                            sharing.ICalendarFormat,
                            itsView=App_ns.itsView)
            try:
                self.collection = share.get()
            except:
                if logger: 
                    logger.Stop()
                    logger.ReportFailure("Importing calendar: exception raised")
            else:
                App_ns.sidebarCollection.add(self.collection)
                scripting.User.idle()
                # do another idle and yield to make sure the calendar is up.
                scripting.User.idle()
                if logger: logger.ReportPass("Importing calendar")

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
        if self.logger: self.logger.Start("Switch to %s" % viewName)
        #process the corresponding event
        App_ns.appbar.press(name=button)
        wx.GetApp().Yield()
        if self.logger: self.logger.Stop()
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
        if self.logger: self.logger.SetChecked(True)
        if not self.state == self.GetCurrentState():
            if self.logger: self.logger.ReportFailure("(On wiew checking) || expected current view = %s ; Corresponding button is switch off " % self.state)
        else:
            if self.logger: self.logger.ReportPass("(On view checking)")
        #report the checkings
        if self.logger: self.logger.Report("View")

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
        
                if self.logger: self.logger.Start("Double click in the calendar view")
                self.timedCanvas.widget.ProcessEvent(click)
                wx.GetApp().Yield()
                if self.logger: self.logger.Stop()
                #work around : SelectAll() doesn't work
                wx.Window.FindFocus().Clear()
            else:
                if self.logger: self.logger.Start("Double click in the calendar view")
                self.timedCanvas.widget.ProcessEvent(click)
                scripting.User.idle()
                if self.logger: self.logger.Stop()
            
            #it's a new event
            if not canvasItem :
                for elem in reversed(self.timedCanvas.widget.canvasItemList):
                    # It's possible for the event to appear a few pixels
                    # lower than pos, if pos is near a dividing line in
                    # the calendar
                    if elem.isHit(pos) or elem.isHit(pos+(0,5)):
                        canvasItem = elem
                        if self.logger: self.logger.ReportPass("On double click in Calendar view checking (event creation)")
                        break
            else:
                if self.logger: self.logger.ReportPass("On double click in Calendar view checking (event selection)")

            #checking
            if self.logger: self.logger.SetChecked(True)
            if self.logger: self.logger.Report("Double click")
            if not canvasItem:
                if self.logger: self.logger.SetChecked(True)
                if self.logger: self.logger.ReportFailure("The event has not been created or selected")
                if self.logger: self.logger.Report()
                return
                   
            #create the corresponding UITestItem object
            TestItem = UITestItem(canvasItem.item, self.logger)
            return TestItem
        else:
            if self.logger: self.logger.Print("DoubleClickInCalView is not available in the current view : %s" % self.state)
            return

    def Check_Equality(self, a, b, message):
        if self.logger: self.logger.SetChecked(True)
        
        if a == b:
            if self.logger: self.logger.ReportPass(message)
        else:
            if self.logger: self.logger.ReportFailure("%s || %s != %s" % (message, a, b))
    
