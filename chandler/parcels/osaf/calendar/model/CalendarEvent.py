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
        self._kind = rep.find("//Schema/CalendarSchema/CalendarEvent")
        
    def NewItem(self):
        item = CalendarEvent(None, self._container, self._kind)
        item.setAttribute("startTime", DateTime.now())
        item.setAttribute("endTime", DateTime.now())

        return item

class CalendarEvent(Item):
    def __init__(self, name, parent, kind, **_kwds):
        super(CalendarEvent, self).__init__(name, parent, kind, **_kwds)

    def GetDuration(self):
        """Returns an mxDateTimeDelta, None if no startTime or endTime"""
        
        if (self.hasAttribute("startTime") and
            self.hasAttribute("endTime")):
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
        
    def IsRemote(self):
        return False


        
