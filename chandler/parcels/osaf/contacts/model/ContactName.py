#!bin/env python

"""Model object representing a contact's nane.
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item

class ContactNameFactory:
    def __init__(self, rep):
        self._container = rep.find("//Contacts")
        self._kind = rep.find("//Schema/ContactsSchema/ContactName")
        
    def NewItem(self):
        item = ContactName(None, self._container, self._kind)
        return item

class ContactName(Item):

    # list of valid name parts - FIXME: get this from the schema
    validNameParts = ['fullname', 'sortname', 'firstname', 'lastname', 'middlename']
    
    def __init__(self, name, parent, kind, **_kwds):
        super(ContactName, self).__init__(name, parent, kind, **_kwds)
 
    def GetNamePart(self, partName):
        if self.hasAttribute(partName):
            return self.getAttribute(partName)        
        return None
 
    def IsNameAttribute(self, attributeName):
        '''
            return True if the passed-in attribute name is a valid name part.
            FIXME: eventually, ask the schema, but for now, just use a list
        '''
        try:
            index = ContactName.validNameParts.index(attributeName)
            return True
        except:
             return False
        
    def SetNamePart(self, partName, nameValue):
        self.setAttribute(partName, nameValue)
        if partName == 'fullname':
            self.ParseFullName()    
        else:
            self.CalcFullName()
        
        self.CalcSortName()
       
    def GetFullName(self):
        return self.GetNamePart('fullname')
    
    # return an abbreviated version of the name
    def GetShortName(self):
        if self.nameEntity.contactType == 'Person':
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
        if self.nameEntity.contactType == 'Person':
            if self.GetNamePart('lastname') == None:
                fullname = self.GetNamePart('firstname')
            else:
                if self.GetNamePart('middlename') != None:
                    fullname = self.firstname + ' ' + self.middlename + ' ' + self.lastname
                else:
                    fullname = self.firstname + ' ' + self.lastname
                    
            self.setAttribute('fullname', fullname)
            
        
    # the full name was set, so parse it into the constituent parts if appropriate
    def ParseFullName(self):
       if self.nameEntity.contactType == 'Person': 
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
        if self.nameEntity.contactType == 'Person':  
            if self.GetNamePart('lastname') == None:
                sortname = self.GetNamePart('firstname')
            else: 
                sortname = self.lastname + ', ' + self.firstname
        else:
            sortname = self.GetNamePart('fullname')
            
        self.setAttribute('sortname', sortname)
         