""" Class used for Items of Kind Calendar
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from mx import DateTime

class CalendarFactory:
    def __init__(self, rep):
        self._container = rep.find("//Calendar")
        self._kind = rep.find("//Schema/CalendarSchema/Calendar")
        
    def NewItem(self, name=""):
        item = Location(None, self._container, self._kind)
        item.setAttributeValue("name", name)

        return item

class Calendar(Item):
    def __init__(self, name, parent, kind, **_kwds):
        super(Location, self).__init__(name, parent, kind, **_kwds)

    def IsRemote(self):
        return False
