#!bin/env python

"""Model object representing addresses.
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from application.persist import Persist

from RdfObject import RdfObject
from RdfRestriction import RdfRestriction

from RdfNamespace import chandler

class Address(RdfObject):
    """Address"""

    # Define the schema for Addresses
    # ---------------------------------------

    rdfs = Persist.Dict()
    rdfs[chandler.address1] = RdfRestriction(str, 1)
    rdfs[chandler.address2] = RdfRestriction(str, 1)
    rdfs[chandler.address3] = RdfRestriction(str, 1)
    rdfs[chandler.city] = RdfRestriction(str, 1)
    rdfs[chandler.state] = RdfRestriction(str, 1)
    rdfs[chandler.zip] = RdfRestriction(str, 1)
    rdfs[chandler.country] = RdfRestriction(str, 1)

    def __init__(self):
        RdfObject.__init__(self)

