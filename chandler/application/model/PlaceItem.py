#!bin/env python

"""Model object representing a Place in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from InformationItem import InformationItem
        
class PlaceItem(InformationItem):
    def __init__(self):
        InformationItem.__init__(self)
        self.address = None
        self.locationDescription = None
        self.name = None
        self.abbreviation = None


