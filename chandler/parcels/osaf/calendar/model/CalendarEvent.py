""" Class used for Items of Kind CalendarEvent
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item

class CalendarEventFactory:
    def __init__(self, rep):
        self._container = rep.find("//Calendar")
        self._kind = rep.find("//Schema/CalendarEvent")
        
    def NewItem(self):
        return CalendarEvent(None, self._container, self._kind)

class CalendarEvent(Item):
    def __init__(self, name, parent, kind, **_kwds):
        super(CalendarEvent, self).__init__(name, parent, kind, **_kwds)

    def getDuration(self):
        if (self.hasAttribute('CalendarStartTime') and self.hasAttribute('CalendarEndTime')):
            return self.CalendarEndTime - self.CalendarStartTime
        else:
            return None
