#!bin/env python

"""Model object for PersonItems in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"

from InformationItem import InformationItem

class EntityItem(InformationItem):
    def __init__(self):
        InformationItem.__init__(self)
        self.name = None
