#!bin/env python

"""Model object representing a calendar.

Currently a placeholder, we haven't done the full schema yet for this class.
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from persistence.dict import PersistentDict

from RdfObject import RdfObject
from RdfRestriction import RdfRestriction
from RdfNamespace import chandler

from InformationItem import InformationItem

class CalendarItem(InformationItem):
    """CalendarItem"""

    # Define the schema for CalendarItem
    # ----------------------------------

    rdfs = PersistentDict()

    rdfs[chandler.name] = RdfRestriction(str, 1)

    def __init__(self):
        RdfObject.__init__(self)

    def getName(self):
        return self.getRdfAttribute(chandler.name, CalendarItem.rdfs)

    def setName(self, name):
        self.setRdfAttribute(chandler.name, name, CalendarItem.rdfs)

    name = property(getName, setName)
    
