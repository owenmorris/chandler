""" Item.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from application.repository.Thing import Thing
from application.repository.KindOfThing import KindOfThing
from application.repository.Repository import Repository
from application.repository.Namespace import chandler

_attributeTemplates = [{ chandler.uri : chandler.startTime,
                         chandler.type : dateTime,
                         chandler.cardinality : 1,
                         chandler.required : true,
                         chandler.default : None },
                       
                       { chandler.uri : chandler.endTime,
                         chandler.type : dateTime,
                         chandler.cardinality : 1,
                         chandler.required : false,
                         chandler.default : None }
                       
                       { chandler.uri : chandler.headline,
                         chandler.type : str,
                         chandler.cardinality : 1,
                         chandler.required : true,
                         chandler.default : None }
                       ]

_akoEvent = KindOfThing(chandler.Event, _attributeTemplates)
_repository = Repository()
_repository.AddThing(_akoEvent)

class Event(Item):
    def __init__(self):
        Item.__init__(self)
        self.SetAko(_akoEvent)
        
    def GetStartTime(self):
        """Returns the start date and time of the event, as an mxDateTime"""
        return self.GetAttribute(chandler.startTime)

    def SetStartTime(self, time):
        """Sets the start date and time of the event, as an mxDateTime.
        Changing the start time via this method will alter the duration
        of the event."""
        self.SetAttribute(chandler.startTime, time)

    # mxDateTime
    startTime = property(GetStartTime, SetStartTime,
                         doc='mxDateTime: event start time and date')

    def GetEndTime(self):
        """Returns the end date and time of the event, as an mxDateTime"""
        return self.GetAttribute(chandler.endTime)

    def SetEndTime(self, time):
        """Sets the end date and time of the event, as an mxDateTime.
        Changing the end time via this method will alter the duration
        of the event."""
        self.SetAttribute(chandler.endTime, time)

    # mxDateTime
    endTime = property(GetEndTime, SetEndTime,
                       doc='mxDateTime: event end time and date')


    def GetHeadline(self):
        """The information about an event the user wants to see in a glance.
        Returns a string."""
        return self.GetAttribute(chandler.headline)

    def SetHeadline(self, headline):
        """Sets the headline, the string representing the information the
        user wants to see about the event in a glance."""
        self.SetAttribute(chandler.headline, headline)

    # string
    headline = property(GetHeadline, SetHeadline,
                        doc='string: headline, or event summary')

    def GetRecurrence(self):
        """Get RecurrencePattern object.
        Describes recurring events."""
        return self.GetAttribute(chandler.recurrence)

    def SetRecurrence(self, recurrence):
        """Set the RecurrencePattern object, describing recurring events."""
        self.SetAttribute(chandler.recurrence, recurrence)

    # RecurrencePattern
    recurrence = property(getRecurrence, setRecurrence,
                          doc='RecurrencePattern')

    def getReminders(self):
        """List of ReminderItems associated with this event."""
        return self.GetAttribute(chandler.reminder)

    def setReminders(self, reminder):
        """Set the list of ReminderItems associated with this event.
        Expects a Persistent.List containing ReminderItems"""
        self.SetAttribute(chandler.reminder, reminder)

    # List of ReminderItems
    reminders = property(getReminders, setReminders,
                        doc='Persistent list of ReminderItems')

    def getTimeTransparency(self):
        """Get free busy time associated with this event, returns FreeBusy"""
        return self.GetAttribute(chandler.timeTransparency)

    def setTimeTransparency(self, freeBusy):
        """Set free busy time associated with this event, expects FreeBusy"""
        self.SetAttribute(chandler.timeTransparency, freeBusy)

    # FreeBusy
    timeTransparency = property(getTimeTransparency, setTimeTransparency,
                                doc='FreeBusy time associated with event')

    def getParticipants(self):
        """Get the list of participants associated with this event.
        Returns a list of EntityItems, which may be PersonItems, GroupItems."""
        return self.GetAttribute(chandler.participant)

    def setParticipants(self, participants):
        """Set a persistent list of participants assocated with this event.
        Expects a Persistent.List of EntityItems"""
        self.GetAttribute(chandler.participant, participants)

    # List of EntityItems
    participants = property(getParticipants, setParticipants,
                            doc='List of EntityItems: event participants')

    def getLocations(self):
        """Get list of PlaceItems related to this event"""
        return self.GetAttribute(chandler.location)

    def setLocations(self, locations):
        """Set persistent list of PlaceItems related to this event.
        Expects a Persistent.List of PlaceItems."""
        self.SetAttribute(chandler.location, locations)

    # List of PlaceItems
    locations = property(getLocations, setLocations,
                         doc='List of PlaceItems: event location')

    def getCalendars(self):
        """Get the list of calendars this event belongs to.
        Returns a list of CalendarItems"""
        return self.GetAttribute(chandler.calendar)

    def setCalendars(self, calendars):
        """Set a list of calendars this event belongs to.
        Expects a Persist.List of CalendarItems"""
        self.SetAttribute(chandler.calendar, calendars)

    # List of CalendarItems
    calendars = property(getCalendars, setCalendars,
                         doc='Persistent list of CalendarItems')
    
    def GetDuration(self):
        """Returns an mxDateTimeDelta, None if startTime or endTime is None"""

        if (self.endTime == None) or (self.startTime == None): return None
        return self.endTime - self.startTime
    
    def SetDuration(self, dateTimeDelta):
        """Set duration of event, expects value to be mxDateTimeDelta
        
        endTime is updated based on the new duration, startTime remains fixed
        """
    
        if (self.startTime != None) :
            self.endTime = self.startTime + dateTimeDelta

    # mxDateTimeDelta
    duration = property(GetDuration, SetDuration,
                        doc='mxDateTimeDelta: the length of an event')

    def ChangeStart(self, dateTime):
        """Change the start time without changing the duration.

        Setting startTime directly will effectively change the duration,
        because the endTime is not affected. This method changes the endTime"""

        duration = self.duration
        self.startTime = dateTime
        self.endTime = self.startTime + duration