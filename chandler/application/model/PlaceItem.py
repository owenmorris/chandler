#!bin/env python

"""Model object representing a Place in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from application.persist import Persist

from InformationItem import InformationItem
        
class PlaceItem(InformationItem):

    rdfs = Persist.Dict()

    rdfs[chandler.name] = RdfRestriction(str, 1)
    rdfs[chandler.address1] = RdfRestriction(str, 1)
    rdfs[chandler.address2] = RdfRestriction(str, 1)
    rdfs[chandler.address3] = RdfRestriction(str, 1)
    rdfs[chandler.city] = RdfRestriction(str, 1)
    rdfs[chandler.state] = RdfRestriction(str, 1)
    rdfs[chandler.zip] = RdfRestriction(str, 1)
    rdfs[chandler.country] = RdfRestriction(str, 1)

    def __init__(self):
        InformationItem.__init__(self)




