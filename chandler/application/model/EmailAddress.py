#!bin/env python

"""Model object representing email addresses.
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

class EmailAddress(RdfObject):
    """EmailAddress"""

    # Define the schema for Addresses
    # ---------------------------------------

    rdfs = Persist.Dict()

    rdfs[chandler.name] = RdfRestriction(str, 1)
    rdfs[chandler.mbox] = RdfRestriction(str, 1)
    rdfs[chandler.category] = RdfRestriction(str)

    def __init__(self):
        RdfObject.__init__(self)

