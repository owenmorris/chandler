""" Event.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application.repository.Thing import Thing
from application.repository.KindOfThing import AkoThingFactory
from application.repository.Repository import Repository
from application.repository.Namespace import chandler

from application.repository.Item import Item
from mx.DateTime import DateTimeFrom

_attributes = [{ chandler.url : chandler.startTime,
                 chandler.displayName : 'Start Time',
                 chandler.range : 'dateTime',
                 chandler.cardinality : 1,
                 chandler.required : True,
                 chandler.default : None },
               
               { chandler.url : chandler.endTime,
                 chandler.displayName : 'End Time',
                 chandler.range : 'dateTime',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
                       
               { chandler.url : chandler.headline,
                 chandler.displayName : 'Headline',
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : True,
                 chandler.default : None }
               ]

class AkoEventFactory(AkoThingFactory):
    def __init__(self):
        AkoThingFactory.__init__(self, chandler.Event, _attributes)

class Event(Item):
    def __init__(self):
        Item.__init__(self)
        self.SetAko(AkoEventFactory().GetAko())
    
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

    # override SetAttribute to allow DateTime values to be set as unicode strings
    def SetAttribute(self, url, value):
        if url == chandler.startTime or url == chandler.endTime:
            if isinstance(value, unicode) or isinstance(value, str):
                 value = DateTimeFrom(str(value))
        Thing.SetAttribute(self, url, value)
        
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