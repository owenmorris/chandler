#!bin/env python

"""Model object defining the format of a contact (which attributes are
   displayed where).
"""

__author__ = "Andy Hertzfeld"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from persistence.dict import PersistentDict

from RdfObject import RdfObject
from RdfRestriction import RdfRestriction

from RdfNamespace import chandler

from wxPython.wx import *

class ContactFormat(RdfObject):
    """ContactFormat"""

    rdfs = PersistentDict()

    rdfs[chandler.headerAttributes] = RdfRestriction(str, 0)
    rdfs[chandler.bodyAttributes] = RdfRestriction(str, 0)
    
    def __init__(self):
        RdfObject.__init__(self)

        self.headerAttributes = []
        self.bodyAttributes = []
        
    def GetHeaderAttributes(self):
        return self.getRdfAttribute(chandler.headerAttributes, ContactFormat.rdfs)
    
    def SetHeaderAttributes(self, headerAttributes):
        self.setRdfAttribute(chandler.headerAttributes, headerAttributes, ContactFormat.rdfs)

    def HasHeaderAttribute(self, attribute):
        try:
            index = self.headerAttributes.index(attribute)
            return true
        except ValueError:
            return false

    def AddHeaderAttribute(self, attribute):
        if not self.HasHeaderAttribute(attribute):
            self.headerAttributes.append(attribute)
        
    def GetBodyAttributes(self):
        return self.getRdfAttribute(chandler.bodyAttributes, ContactFormat.rdfs)
    
    def SetBodyAttributes(self, bodyAttributes):
        self.setRdfAttribute(chandler.bodyAttributes, bodyAttributes, ContactFormat.rdfs)
    
    def HasBodyAttribute(self, attribute):
        try:
            index = self.bodyAttributes.index(attribute)
            return true
        except ValueError:
            return false
    
    def AddBodyAttribute(self, attribute):
        if not self.HasBodyAttribute(attribute):
            self.bodyAttributes.append(attribute)
    
    headerAttributes = property(GetHeaderAttributes, SetHeaderAttributes)
    bodyAttributes = property(GetBodyAttributes, SetBodyAttributes)
