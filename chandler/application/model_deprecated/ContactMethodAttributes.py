#!bin/env python

"""Model objects for various types of contact method addresses
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import copy

from persistence.dict import PersistentDict

from RdfObject import RdfObject
from RdfRestriction import RdfRestriction

from RdfNamespace import chandler

class ContactMethodAttributes(RdfObject):
    """The base class for contact method attributes"""

    rdfs = PersistentDict()

    rdfs[chandler.addressType] = RdfRestriction(str, 1)

    def __init__(self):
        RdfObject.__init__(self)

    def GetAddressType(self):
        return self.getRdfAttribute(chandler.addressType, ContactMethodAttributes.rdfs)
    
    def SetAddressType(self, addressType):
        self.setRdfAttribute(chandler.addressType, addressType, ContactMethodAttributes.rdfs)
 
    def GetAttribute(self, attributeKey):
        if self.__dict__.has_key(attributeKey):
            return self.__dict__[attributeKey]
        return None
    
    def SetAttribute(self, attributeKey, attributeValue):
        self.__dict__[attributeKey] = attributeValue

    addressType = property(GetAddressType, SetAddressType)

# here are subclasses for particular types of contact methods
class ContactPhoneAttributes(ContactMethodAttributes):
    
    rdfs = PersistentDict()

    rdfs[chandler.phonenumber] = RdfRestriction(str, 1)
     
    def __init__(self):
        ContactMethodAttributes.__init__(self)
   
    def GetPhoneNumber(self):
        return self.getRdfAttribute(chandler.phonenumber, ContactPhoneAttributes.rdfs)
    
    def SetPhoneNumber(self, phonenumber):
        self.setRdfAttribute(chandler.phonenumber, phonenumber, ContactPhoneAttributes.rdfs)
    
    def GetAttribute(self, attributeKey):
        if attributeKey == 'phonenumber':
            return self.GetPhoneNumber()
        
        if self.__dict__.has_key(attributeKey):
            return self.__dict__[attributeKey]
        
        return None
    
    def SetAttribute(self, attributeKey, attributeValue):
        if attributeKey == 'phonenumber':
            self.SetPhoneNumber(attributeValue)
        else:
            self.__dict__[attributeKey] = attributeValue
    
    phonenumber = property(GetPhoneNumber, SetPhoneNumber)
 
class ContactEmailAttributes(ContactMethodAttributes):
    
    rdfs = PersistentDict()

    rdfs[chandler.address] = RdfRestriction(str, 1)
     
    def __init__(self):
         ContactMethodAttributes.__init__(self)
   
    def GetAddress(self):
        return self.getRdfAttribute(chandler.address, ContactEmailAttributes.rdfs)
    
    def SetAddress(self, address):
        self.setRdfAttribute(chandler.address, address, ContactEmailAttributes.rdfs)
    
    def GetAttribute(self, attributeKey):
        if attributeKey == 'address':
            return self.GetAddress()
        
        if self.__dict__.has_key(attributeKey):
            return self.__dict__[attributeKey]
        
        return None
    
    def SetAttribute(self, attributeKey, attributeValue):
        if attributeKey == 'address':
            self.SetAddress(attributeValue)
        else:
            self.__dict__[attributeKey] = attributeValue
    
    address = property(GetAddress, SetAddress)

class ContactIMAttributes(ContactMethodAttributes):
    
    rdfs = PersistentDict()

    rdfs[chandler.address] = RdfRestriction(str, 1)
     
    def __init__(self):
        ContactMethodAttributes.__init__(self)
   
    def GetAddress(self):
        return self.getRdfAttribute(chandler.address, ContactIMAttributes.rdfs)
    
    def SetAddress(self, address):
        self.setRdfAttribute(chandler.address, address, ContactIMAttributes.rdfs)
    
    def GetAttribute(self, attributeKey):
        if attributeKey == 'address':
            return self.GetAddress()
        
        if self.__dict__.has_key(attributeKey):
            return self.__dict__[attributeKey]
        
        return None
    
    def SetAttribute(self, attributeKey, attributeValue):
        if attributeKey == 'address':
            self.SetAddress(attributeValue)
        else:
            self.__dict__[attributeKey] = attributeValue
    
    address = property(GetAddress, SetAddress)

class ContactWebAttributes(ContactMethodAttributes):
    
    rdfs = PersistentDict()

    rdfs[chandler.url] = RdfRestriction(str, 1)
     
    def __init__(self):
        ContactMethodAttributes.__init__(self)
   
    def GetURL(self):
        return self.getRdfAttribute(chandler.url, ContactWebAttributes.rdfs)
    
    def SetURL(self, url):
        self.setRdfAttribute(chandler.url, url, ContactWebAttributes.rdfs)

    def GetAttribute(self, attributeKey):
        if attributeKey == 'url':
            return self.GetURL()
        
        if self.__dict__.has_key(attributeKey):
            return self.__dict__[attributeKey]
        
        return None
    
    def SetAttribute(self, attributeKey, attributeValue):
        if attributeKey == 'url':
            self.SetURL(attributeValue)
        else:
            self.__dict__[attributeKey] = attributeValue

    url = property(GetURL, SetURL)

class ContactNoteAttributes(ContactMethodAttributes):
    
    rdfs = PersistentDict()

    rdfs[chandler.text] = RdfRestriction(str, 1)
     
    def __init__(self):
        ContactMethodAttributes.__init__(self)
   
    def GetText(self):
        return self.getRdfAttribute(chandler.text, ContactNoteAttributes.rdfs)
    
    def SetText(self, text):
        self.setRdfAttribute(chandler.text, text, ContactNoteAttributes.rdfs)

    def GetAttribute(self, attributeKey):
        if attributeKey == 'text':
            return self.GetText()
        
        if self.__dict__.has_key(attributeKey):
            return self.__dict__[attributeKey]
        
        return None
    
    def SetAttribute(self, attributeKey, attributeValue):
        if attributeKey == 'text':
            self.SetText(attributeValue)
        else:
            self.__dict__[attributeKey] = attributeValue

    text = property(GetText, SetText)

class ContactPostalAttributes(ContactMethodAttributes):
    
    rdfs = PersistentDict()

    rdfs[chandler.street] = RdfRestriction(str, 1)
    rdfs[chandler.city] = RdfRestriction(str, 1)
    rdfs[chandler.state] = RdfRestriction(str, 1)
    rdfs[chandler.zipcode] = RdfRestriction(str, 1)
     
    def __init__(self):
        ContactMethodAttributes.__init__(self)
   
    def GetStreet(self):
        return self.getRdfAttribute(chandler.street, ContactPostalAttributes.rdfs)
    
    def SetStreet(self, street):
        self.setRdfAttribute(chandler.street, street, ContactPostalAttributes.rdfs)
    
    def GetCity(self):
        return self.getRdfAttribute(chandler.city, ContactPostalAttributes.rdfs)
    
    def SetCity(self, city):
        self.setRdfAttribute(chandler.city, city, ContactPostalAttributes.rdfs)
          
    def GetState(self):
        return self.getRdfAttribute(chandler.state, ContactPostalAttributes.rdfs)
    
    def SetState(self, state):
        self.setRdfAttribute(chandler.state, state, ContactPostalAttributes.rdfs)
          
    def GetZipcode(self):
        return self.getRdfAttribute(chandler.zipcode, ContactPostalAttributes.rdfs)
    
    def SetZipcode(self, zipcode):
        self.setRdfAttribute(chandler.zipcode, zipcode, ContactPostalAttributes.rdfs)

    def GetAttribute(self, attributeKey):
        url = chandler.__getattr__(attributeKey)
        return self.getRdfAttribute(url, ContactPostalAttributes.rdfs)
    
    def SetAttribute(self, attributeKey, attributeValue):
        url = chandler.__getattr__(attributeKey)
        self.setRdfAttribute(url, attributeValue, ContactPostalAttributes.rdfs)
       
    street = property(GetStreet, SetStreet)
    city = property(GetCity, SetCity)
    state = property(GetState, SetState)
    zipcode = property(GetZipcode, SetZipcode)
        
# package global to associate contact method types with attribute classes
# this allows new types of contact methods to be installed at runtime
# by installing new entries into the dictionary
contactMethodClasses = {}

# install built-in types in dictionary
contactMethodClasses['phone'] = ContactPhoneAttributes
contactMethodClasses['email'] = ContactEmailAttributes
contactMethodClasses['website'] = ContactWebAttributes
contactMethodClasses['jabberID'] = ContactIMAttributes
contactMethodClasses['postal'] = ContactPostalAttributes
contactMethodClasses['note'] = ContactNoteAttributes

# parcel method to return attributes corresponding to passed in type
def CreateContactMethodAttributes(contactMethodType):
    if contactMethodClasses.has_key(contactMethodType):
        whichClass = contactMethodClasses[contactMethodType]
        attributes = apply(whichClass, ())
        attributes.SetAddressType(contactMethodType)
        return attributes
    
    # use the base class for unknown types    
    return ContactMethodAttributes()

        
