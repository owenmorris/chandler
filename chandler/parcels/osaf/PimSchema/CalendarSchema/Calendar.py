""" Class used for Items of Kind Calendar
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item
from mx import DateTime

class Calendar(Item):
    def __init__(self, repository, name=""):
        parent = repository.find("//Parcels/OSAF/PimSchema/CalendarSchema")
        kind = repository.find("//Schema/OSAF/PimSchema/CalendarSchema/Calendar")
        Item.__init__(self, None, parent, kind)
        self.name = name
        
