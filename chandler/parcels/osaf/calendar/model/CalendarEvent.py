""" Class used for Items of Kind CalendarEvent
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from mx import DateTime

class CalendarEventFactory:
    def __init__(self, rep):
        self._container = rep.find("//Calendar")
        self._kind = rep.find("//Schema/CalendarEvent")
        
    def NewItem(self):
        item = CalendarEvent(None, self._container, self._kind)
        item.setAttribute("CalendarStartTime", DateTime.now())
        item.setAttribute("CalendarEndTime", DateTime.now())

        return item

class CalendarEvent(Item):
    def __init__(self, name, parent, kind, **_kwds):
        super(CalendarEvent, self).__init__(name, parent, kind, **_kwds)

    def GetDuration(self):
        """Returns an mxDateTimeDelta, None if no startTime or endTime"""
        
        if (self.hasAttribute('CalendarStartTime') and
            self.hasAttribute('CalendarEndTime')):
            return self.CalendarEndTime - self.CalendarStartTime
        else:
            return None

    def SetDuration(self, dateTimeDelta):
        """Set duration of event, expects value to be mxDateTimeDelta
        
        endTime is updated based on the new duration, startTime remains fixed
        """
        if (self.CalendarStartTime != None):
            self.CalendarEndTime = self.CalendarStartTime + dateTimeDelta

    CalendarDuration = property(GetDuration, SetDuration,
                                doc="mxDateTimeDelta: the length of an event")

    def ChangeStart(self, dateTime):
        """Change the start time without changing the duration.

        Setting startTime directly will effectively change the duration,
        because the endTime is not affected. This method changes the endTime"""

        duration = self.CalendarDuration
        self.CalendarStartTime = dateTime
        self.CalendarEndTime = self.CalendarStartTime + duration
        
    def IsRemote(self):
        return False


        
