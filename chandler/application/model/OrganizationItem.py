#!bin/env python

"""Model object for PersonItems in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"

from EntityItem import EntityItem

class OrganizationItem(EntityItem):
    def __init__(self):
        EntityItem.__init__(self)
        self.address = None
        self.phone = None
