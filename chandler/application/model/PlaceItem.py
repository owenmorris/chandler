#!bin/env python

"""Model object representing a Place in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from application.persist import Persist

from RdfRestriction import RdfRestriction
from RdfNamespace import chandler

from InformationItem import InformationItem
from Address import Address
        
class PlaceItem(InformationItem):

    rdfs = Persist.Dict()

    rdfs[chandler.name] = RdfRestriction(str, 1)
    rdfs[chandler.address] = RdfRestriction(Address)
    rdfs[chandler.category] = RdfRestriction(str)

    def __init__(self):
        InformationItem.__init__(self)




