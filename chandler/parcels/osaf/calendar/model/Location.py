""" Class used for Items of Kind Location
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item
from mx import DateTime

class LocationFactory:
    def __init__(self, rep):
        self._container = rep.find("//Calendar")
        self._kind = rep.find("//Schema/CalendarSchema/Location")
        
    def NewItem(self, name=""):
        item = Location(None, self._container, self._kind)
        item.name = name

        return item

class Location(Item):

    def IsRemote(self):
        return False
