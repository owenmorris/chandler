#!bin/env python

"""Model object for PersonItems in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from application.persist import Persist

from EntityItem import EntityItem

class PersonItem(EntityItem):

    rdfs = Persist.Dict()

    def __init__(self):
        EntityItem.__init__(self)




    
