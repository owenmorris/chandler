#!bin/env python

"""Model object representing a calendar event in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from application.persist import Persist

from InformationItem import InformationItem
from EntityItem import EntityItem

from RdfRestriction import RdfRestriction

from RdfNamespace import dc
from RdfNamespace import chandler

from mx.DateTime import *

_DateTimeType = type(now())
_DateTimeDurationType = type(now() - now())

class EventItem(InformationItem):

    # Define the schema for EventItem
    # -----------------------------------

    rdfs = Persist.Dict()
    
    rdfs[chandler.startTime] = RdfRestriction(_DateTimeType, 1)
    rdfs[chandler.endTime] = RdfRestriction(_DateTimeType, 1)
    rdfs[chandler.headline] = RdfRestriction(str, 1)
    rdfs[chandler.recurrence] = RdfRestriction(InformationItem) #RecurrencePattern
    rdfs[chandler.reminder] = RdfRestriction(InformationItem) #Reminder
    rdfs[chandler.timeTransparency] = RdfRestriction(InformationItem) #Freebusy
    rdfs[chandler.participant] = RdfRestriction(EntityItem)
    rdfs[chandler.invitee] = RdfRestriction(EntityItem)
    rdfs[chandler.location] = RdfRestriction(InformationItem) #PlaceItem
    rdfs[chandler.calendar] = RdfRestriction(InformationItem) #CalendarItem
    
    def __init__(self):
        InformationItem.__init__(self)

    def getStartTime(self):
        return self.getRdfAttribute(chandler.startTime,
                                    EventItem.rdfs)

    def setStartTime(self, time):
        self.setRdfAttribute(chandler.startTime, time,
                             EventItem.rdfs)

    def getEndTime(self):
        return self.getRdfAttribute(chandler.endTime,
                                    EventItem.rdfs)

    def setEndTime(self, time):
        self.setRdfAttribute(chandler.endTime, time,
                             EventItem.rdfs)

    def getHeadline(self):
        return self.getRdfAttribute(chandler.headline,
                                    EventItem.rdfs)

    def setHeadline(self, headline):
        self.setRdfAttribute(chandler.headline, headline,
                             EventItem.rdfs)

    startTime = property(getStartTime, setStartTime)
    endTime = property(getEndTime, setEndTime)
    headline = property(getHeadline, setHeadline)
    
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

    duration = property(getDuration, setDuration)

    def changeStart(self, dateTime):
        """Change the start time without changing the duration.

        Setting startTime directly will effectively change the duration,
        because the endTime is not affected. This method changes the endTime"""

        duration = self.duration
        self.startTime = dateTime
        self.endTime = self.startTime + duration



