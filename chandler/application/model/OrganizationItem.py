#!bin/env python

"""Model object for PersonItems in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from Persistence import PersistentDict

from EntityItem import EntityItem

class OrganizationItem(EntityItem):
    """OrganizationItem"""

    rdfs = PersistentDict.PersistentDict()

    rdfs[chandler.members] = RdfRestriction(EntityItem)
    
    def __init__(self):
        EntityItem.__init__(self)

    def getMembers(self):
        return self.getRdfAttribute(chandler.members,
                                    OrganizationItem.rdfs)

    def setMembers(self, members):
        return self.setRdfAttribute(chandler.members,
                                    members,
                                    OrganizationItem.rdfs)

    members = property(getMembers, setMembers)
