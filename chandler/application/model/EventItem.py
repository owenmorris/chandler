#!bin/env python

"""Model object representing a calendar event in Chandler.

Caveats with current implementation:
* We may need to consider start/end time more carefully. Particular
concerns: 'all day' or banner events apply to the day, timezone concerns.
* Headline is currently a separate property, we may want to collapse this with
'subject' or 'title'.
* duration should probably be a property, do we store derived properties?
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from persistence.dict import PersistentDict

from RdfRestriction import RdfRestriction
from RdfNamespace import dc
from RdfNamespace import chandler

from InformationItem import InformationItem
from EntityItem import EntityItem
from RecurrencePattern import RecurrencePattern
from ReminderItem import ReminderItem
from FreeBusy import FreeBusy
from PlaceItem import PlaceItem
from CalendarItem import CalendarItem

from mx.DateTime import *

_DateTimeType = type(now())
_DateTimeDurationType = type(now() - now())

class EventItem(InformationItem):

    # Define the schema for EventItem
    # -----------------------------------

    rdfs = PersistentDict()
    
    rdfs[chandler.startTime] = RdfRestriction(_DateTimeType, 1)
    rdfs[chandler.endTime] = RdfRestriction(_DateTimeType, 1)
    rdfs[chandler.headline] = RdfRestriction(str, 1)
    rdfs[chandler.recurrence] = RdfRestriction(RecurrencePattern) 
    rdfs[chandler.reminder] = RdfRestriction(InformationItem) 
    rdfs[chandler.timeTransparency] = RdfRestriction(FreeBusy)
    rdfs[chandler.participant] = RdfRestriction(EntityItem)
    rdfs[chandler.invitee] = RdfRestriction(EntityItem)
    rdfs[chandler.location] = RdfRestriction(PlaceItem) 
    rdfs[chandler.calendar] = RdfRestriction(CalendarItem)
    
    def __init__(self):
        InformationItem.__init__(self)

    def getStartTime(self):
        """Returns the start date and time of the event, as an mxDateTime"""
        return self.getRdfAttribute(chandler.startTime,
                                    EventItem.rdfs)

    def setStartTime(self, time):
        """Sets the start date and time of the event, as an mxDateTime.
        Changing the start time via this method will alter the duration
        of the event."""
        self.setRdfAttribute(chandler.startTime, time,
                             EventItem.rdfs)

    # mxDateTime
    startTime = property(getStartTime, setStartTime,
                         doc='mxDateTime: event start time and date')

    def getEndTime(self):
        """Returns the end date and time of the event, as an mxDateTime"""
        return self.getRdfAttribute(chandler.endTime,
                                    EventItem.rdfs)

    def setEndTime(self, time):
        """Sets the end date and time of the event, as an mxDateTime.
        Changing the end time via this method will alter the duration
        of the event."""
        self.setRdfAttribute(chandler.endTime, time,
                             EventItem.rdfs)

    # mxDateTime
    endTime = property(getEndTime, setEndTime,
                       doc='mxDateTime: event end time and date')


    def getHeadline(self):
        """The information about an event the user wants to see in a glance.
        Returns a string."""
        return self.getRdfAttribute(chandler.headline,
                                    EventItem.rdfs)

    def setHeadline(self, headline):
        """Sets the headline, the string representing the information the
        user wants to see about the event in a glance."""
        self.setRdfAttribute(chandler.headline, headline,
                             EventItem.rdfs)

    # string
    headline = property(getHeadline, setHeadline,
                        doc='string: headline, or event summary')

    def getRecurrence(self):
        """Get RecurrencePattern object.
        Describes recurring events."""
        return self.getRdfAttribute(chandler.recurrence, EventItem.rdfs)

    def setRecurrence(self, recurrence):
        """Set the RecurrencePattern object, describing recurring events."""
        self.setRdfAttribute(chandler.recurrence, recurrence, EventItem.rdfs)

    # RecurrencePattern
    recurrence = property(getRecurrence, setRecurrence,
                          doc='RecurrencePattern')

    def getReminders(self):
        """List of ReminderItems associated with this event."""
        return self.getRdfAttribute(chandler.reminder, EventItem.rdfs)

    def setReminders(self, reminder):
        """Set the list of ReminderItems associated with this event.
        Expects a Persistent.List containing ReminderItems"""
        self.setRdfAttribute(chandler.reminder, reminder, EventItem.rdfs)

    # List of ReminderItems
    reminders = property(getReminders, setReminders,
                        doc='Persistent list of ReminderItems')

    def getTimeTransparency(self):
        """Get free busy time associated with this event, returns FreeBusy"""
        return self.getRdfAttribute(chandler.timeTransparency, EventItem.rdfs)

    def setTimeTransparency(self, freeBusy):
        """Set free busy time associated with this event, expects FreeBusy"""
        self.setRdfAttribute(chandler.timeTransparency, freeBusy,
                             EventItem.rdfs)

    # FreeBusy
    timeTransparency = property(getTimeTransparency, setTimeTransparency,
                                doc='FreeBusy time associated with event')

    def getParticipants(self):
        """Get the list of participants associated with this event.
        Returns a list of EntityItems, which may be PersonItems, GroupItems."""
        return self.getRdfAttribute(chandler.participant, EventItem.rdfs)

    def setParticipants(self, participants):
        """Set a persistent list of participants assocated with this event.
        Expects a Persistent.List of EntityItems"""
        self.getRdfAttribute(chandler.participant, participants,
                             EventItem.rdfs)

    # List of EntityItems
    participants = property(getParticipants, setParticipants,
                            doc='List of EntityItems: event participants')

    def getLocations(self):
        """Get list of PlaceItems related to this event"""
        return self.getRdfAttribute(chandler.location, EventItem.rdfs)

    def setLocations(self, locations):
        """Set persistent list of PlaceItems related to this event.
        Expects a Persistent.List of PlaceItems."""
        self.setRdfAttribute(chandler.location, locations, EventItem.rdfs)

    # List of PlaceItems
    locations = property(getLocations, setLocations,
                         doc='List of PlaceItems: event location')

    def getCalendars(self):
        """Get the list of calendars this event belongs to.
        Returns a list of CalendarItems"""
        return self.getRdfAttribute(chandler.calendar, EventItem.rdfs)

    def setCalendars(self, calendars):
        """Set a list of calendars this event belongs to.
        Expects a Persist.List of CalendarItems"""
        self.setRdfAttribute(chandler.calendar, calendars, EventItem.rdfs)

    # List of CalendarItems
    calendars = property(getCalendars, setCalendars,
                         doc='Persistent list of CalendarItems')
    
    def getDuration(self):
        """Returns an mxDateTimeDelta, None if startTime or endTime is None"""

        if (self.endTime == None) or (self.startTime == None): return None
        return self.endTime - self.startTime
    
    def setDuration(self, dateTimeDelta):
        """Set duration of event, expects value to be mxDateTimeDelta
        
        endTime is updated based on the new duration, startTime remains fixed
        """
    
        if (self.startTime != None) :
            self.endTime = self.startTime + dateTimeDelta

    # mxDateTimeDelta
    duration = property(getDuration, setDuration,
                        doc='mxDateTimeDelta: the length of an event')

    def changeStart(self, dateTime):
        """Change the start time without changing the duration.

        Setting startTime directly will effectively change the duration,
        because the endTime is not affected. This method changes the endTime"""

        duration = self.duration
        self.startTime = dateTime
        self.endTime = self.startTime + duration



