""" Classes used for Calendar parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import application
import repository.item.Item as Item

import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.Notes as Notes

import mx.DateTime as DateTime


class CalendarParcel(application.Parcel.Parcel):

    def _setUUIDs(self):
        calendarEventKind = self['CalendarEvent']
        CalendarParcel.calendarEventKindID = calendarEventKind.itsUUID

        locationKind = self['Location']
        CalendarParcel.locationKindID = locationKind.itsUUID
        
        calendarKind = self['Calendar']
        CalendarParcel.calendarKindID = calendarKind.itsUUID
        
        recurrenceKind = self['RecurrencePattern']
        CalendarParcel.recurrencePatternKindID = recurrenceKind.itsUUID
        
        reminderKind = self['Reminder']
        CalendarParcel.reminderKindID = reminderKind.itsUUID

        calendarEventMixinKind = self['CalendarEventMixin']
        CalendarParcel.calendarEventMixinKindID = calendarEventMixinKind.itsUUID

    def onItemLoad(self):
        super(CalendarParcel, self).onItemLoad()
        self._setUUIDs()

    def startupParcel(self):
        super(CalendarParcel, self).startupParcel()
        self._setUUIDs()

    def getCalendarEventKind(cls):
        assert cls.calendarEventKindID, "CalendarParcel not yet loaded"
        return Globals.repository[cls.calendarEventKindID]

    getCalendarEventKind = classmethod(getCalendarEventKind)

    def getCalendarEventMixinKind(cls):
        assert cls.calendarEventMixinKindID, "CalendarParcel not yet loaded"
        return Globals.repository[cls.calendarEventMixinKindID]

    getCalendarEventMixinKind = classmethod(getCalendarEventMixinKind)

    def getLocationKind(cls):
        assert cls.locationKindID, "CalendarParcel not yet loaded"
        return Globals.repository[cls.locationKindID]

    getLocationKind = classmethod(getLocationKind)

    def getCalendarKind(cls):
        assert cls.calendarKindID, "CalendarParcel not yet loaded"
        return Globals.repository[cls.calendarKindID]

    getCalendarKind = classmethod(getCalendarKind)

    def getRecurrencePatternKind(cls):
        assert cls.recurrencePatternKindID, "CalendarParcel not yet loaded"
        return Globals.repository[cls.recurrencePatternKindID]

    getRecurrencePatternKind = classmethod(getRecurrencePatternKind)

    def getReminderKind(cls):
        assert cls.reminderKindID, "CalendarParcel not yet loaded"
        return Globals.repository[cls.reminderKindID]

    getReminderKind = classmethod(getReminderKind)


    # The parcel knows the UUIDs for the Kinds, once the parcel is loaded
    calendarEventKindID = None
    calendarEventMixinKindID = None
    locationKindID = None
    calendarKindID = None
    recurrencePatternKindID = None
    reminderKindID = None

class CalendarEventMixin(Item.Item):
    """
      Calendar Event Mixin is the bag of Event-specific attributes.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(CalendarEventMixin, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        # default the requestor to "me"
        self.organizer = self.getCurrentMeEmailAddress ()

        # start at the nearest half hour, duration of an hour
        now = DateTime.now()
        self.startTime = DateTime.DateTime(now.year, now.month, now.day,
                                           now.hour, int(now.minute/30) * 30)
        self.duration = DateTime.DateTimeDelta(0, 1)

        # give a starting display name
        self.displayName = "New Event"

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



class CalendarEvent(CalendarEventMixin, Notes.Note):

    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = Globals.repository.findPath("//parcels/osaf/contentmodel/calendar/CalendarEvent")
        super (CalendarEvent, self).__init__(name, parent, kind)
        self.participants = []

class Location(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = CalendarParcel.getLocationKind()
        super (Location, self).__init__(name, parent, kind)


class Calendar(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = CalendarParcel.getCalendarKind()
        super (Calendar, self).__init__(name, parent, kind)

class RecurrencePattern(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = CalendarParcel.getRecurrencePatternKind()
        super (RecurrencePattern, self).__init__(name, parent, kind)

class Reminder(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = CalendarParcel.getReminderKind()
        super (Reminder, self).__init__(name, parent, kind)
        
