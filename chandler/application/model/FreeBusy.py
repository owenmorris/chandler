#!bin/env python

"""Model object representing availability for a slice of time. (free/busy)

Currently a placeholder, we haven't done the full schema yet for this class.
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from persistence.dict import PersistentDict

from RdfObject import RdfObject
from RdfRestriction import RdfRestriction

from RdfNamespace import chandler

class FreeBusy(RdfObject):
    """FreeBusy"""

    # Define the schema for FreeBusy
    # ----------------------------------

    rdfs = PersistentDict()

    def __init__(self):
        RdfObject.__init__(self)
