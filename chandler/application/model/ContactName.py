#!bin/env python

"""Model object representing a contact's nane.
"""

__author__ = "Andy Hertzfeld"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from persistence.dict import PersistentDict

from RdfObject import RdfObject
from RdfRestriction import RdfRestriction

from RdfNamespace import chandler

class ContactName(RdfObject):
    """ContactNAme"""

# many of these strings should really be enumerated types; we'll convert them
# to that when the infrastructure is ready.

    rdfs = PersistentDict()

    rdfs[chandler.fullname] = RdfRestriction(str, 1)
    rdfs[chandler.sortname] = RdfRestriction(str, 1)
    rdfs[chandler.firstname] = RdfRestriction(int, 1)
    rdfs[chandler.middlename] = RdfRestriction(str, 1)
    rdfs[chandler.lastname] = RdfRestriction(str, 1)
    rdfs[chandler.honorific] = RdfRestriction(str, 1)
    rdfs[chandler.suffix] = RdfRestriction(str, 1)
    
    def __init__(self, contactItem):
        RdfObject.__init__(self)

        self.contactItem = contactItem
 
    def GetNamePart(self, partName):
        if self.__dict__.has_key(partName):
            return self.__dict__[partName]
        return None
    
    def SetNamePart(self, partName, nameValue):
        self.__dict__[partName] = nameValue
        if partName == 'fullname':
            self.ParseFullName()
        else:
            self.CalcFullName()
        
        self.CalcSortName()

    def GetFullName(self):
        return self.GetNamePart('fullname')
    
    # return an abbreviated version of the name
    def GetShortName(self):
        if self.contactItem.contactType == 'Person':
            firstName = self.GetNamePart('firstname')
            lastName = self.GetNamePart('lastname')
            if lastName == None:
                return firstName
            return '%s. %s' % (firstName[0], lastName)
        else:
            return self.GetFullName()
           
    # a name part was changed, so recompute the full name
    # FIXME: this needs be internationalized eventually
    def CalcFullName(self):
         if self.contactItem.contactType == 'Person':
            if self.GetNamePart('lastname') == None:
                self.fullname = self.GetNamePart('firstname')
                return
            
            if self.GetNamePart('middlename') != None:
                self.fullname = self.firstname + ' ' + self.middlename + ' ' + self.lastname
            else:
               self.fullname = self.firstname + ' ' + self.lastname
    
    # the full name was set, so parse it into the constituent parts if appropriate
    def ParseFullName(self):
       if self.contactItem.contactType == 'Person': 
           nameList = self.fullname.split(' ')
           self.firstname = nameList[0]
           partCount = len(nameList)
           if partCount == 1:
               self.lastname = None
           else:
               if partCount > 2:
                   self.middlename = nameList[1]
               else:
                    self.middlename = None
               
               self.lastname = nameList[-1]
 
    # calculate the sort name from the parts
    # FIXME: this must be internationalized eventually
    def CalcSortName(self):
        if self.contactItem.contactType == 'Person':  
            if self.GetNamePart('lastname') == None:
                self.sortname = self.GetNamePart('firstname')
            else: 
                self.sortname = self.lastname + ', ' + self.firstname
        else:
            self.sortname = self.GetNamePart('fullname')
        