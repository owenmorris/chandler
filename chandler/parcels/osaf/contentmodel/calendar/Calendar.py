""" Class used for Items of Kind Calendar
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.parcel.Parcel as Parcel
import repository.item.Item as Item
import OSAF.contentmodel.ContentModel as ContentModel
import mx.DateTime as DateTime

# Module globals for Kinds
CalendarEventKind = None
LocationKind = None
CalendarKind = None
RecurrencePatternKind = None
ReminderKind = None

class CalendarParcel(Parcel.Parcel):
    def __init__(self, name, parent, kind):
        Parcel.Parcel.__init__(self, name, parent, kind)

    def startupParcel(self):
        Parcel.Parcel.startupParcel(self)
        repository = self.getRepository()

        calendarPathStr = '//parcels/OSAF/contentmodel/calendar/%s'

        global CalendarEventKind
        CalendarEventKind = repository.find(calendarPathStr % 'CalendarEvent')
        assert CalendarEventKind

        global LocationKind
        LocationKind = repository.find(calendarPathStr % 'Location')
        assert LocationKind

        global CalendarKind
        CalendarKind = repository.find(calendarPathStr % 'Calendar')
        assert CalendarKind

        global RecurrencePatternKind
        RecurrencePatternKind = repository.find(calendarPathStr % 'RecurrencePattern')
        assert RecurrencePatternKind

        global ReminderKind
        ReminderKind = repository.find(calendarPathStr % 'Reminder')
        assert ReminderKind

class CalendarEvent(ContentModel.ContentItem):

    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = CalendarEventKind
        ContentModel.ContentItem.__init__(self, name, parent, kind)
        self.startTime = DateTime.now()
        self.endTime = DateTime.now()

    def GetDuration(self):
        """Returns an mxDateTimeDelta, None if no startTime or endTime"""
        
        if (self.hasAttributeValue("startTime") and
            self.hasAttributeValue("endTime")):
            return self.endTime - self.startTime
        else:
            return None

    def SetDuration(self, dateTimeDelta):
        """Set duration of event, expects value to be mxDateTimeDelta
        
        endTime is updated based on the new duration, startTime remains fixed
        """
        if (self.startTime != None):
            self.endTime = self.startTime + dateTimeDelta

    duration = property(GetDuration, SetDuration,
                                doc="mxDateTimeDelta: the length of an event")

    def ChangeStart(self, dateTime):
        """Change the start time without changing the duration.

        Setting startTime directly will effectively change the duration,
        because the endTime is not affected. This method changes the endTime"""

        duration = self.duration
        self.startTime = dateTime
        self.endTime = self.startTime + duration


class Location(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentItemParent
        if not kind:
            kind = LocationKind
        Item.Item.__init__(self, name, parent, kind)
        

class Calendar(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentItemParent
        if not kind:
            kind = CalendarKind
        Item.Item.__init__(self, name, parent, kind)

class RecurrencePattern(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentItemParent
        if not kind:
            kind = RecurrencePatternKind
        Item.Item.__init__(self, name, parent, kind)

class Reminder(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentItemParent
        if not kind:
            kind = ReminderKind
        Item.Item.__init__(self, name, parent, kind)
