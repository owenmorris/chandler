#!bin/env python

"""Model object for PersonItems in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"

from EntityItem import EntityItem

class PersonItem(EntityItem):
    def __init__(self):
        EntityItem.__init__(self)

        # name fields are strings
        self.firstName = None
        self.lastName = None
        self.abbreviation = None

        # ???
        self.address = None
        self.phone = None
    
    def getFullName(self):
        """Build a full name string based on other name fields"""
        return "%s %s" % (self.firstName, self.lastName)
    
    fullName = property(getFullName)


    
