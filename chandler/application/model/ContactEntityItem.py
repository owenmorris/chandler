#!bin/env python

"""ContactEntityItem, the base class for contacts
"""

__author__ = "Andy Hertzfeld"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF"

from application.Application import app

from persistence.dict import PersistentDict

from InformationItem import InformationItem
from LocalRepository import LocalRepository

from ContactMethodItem import ContactMethodItem
from ContactName import ContactName
from ContactAttributes import ContactAttributes
from ContactFormat import ContactFormat

from RdfRestriction import RdfRestriction

from RdfNamespace import dc
from RdfNamespace import chandler

class ContactEntityItem(InformationItem):
    """EntityItem"""

    rdfs = PersistentDict()
    
    rdfs[chandler.contactType] = RdfRestriction(str, 1)
    rdfs[chandler.name] = RdfRestriction(ContactName, 1)
    rdfs[chandler.contactMethods] = RdfRestriction(ContactMethodItem, 0)
    rdfs[chandler.photoURL] = RdfRestriction(str, 1)
    rdfs[chandler.attributes] = RdfRestriction(ContactAttributes, 1)
    rdfs[chandler.format] = RdfRestriction(ContactFormat, 1)
    rdfs[chandler.groups] = RdfRestriction(str, 0)


    def __init__(self, contactType):
        InformationItem.__init__(self)

        self.contactType = contactType
 
        self.name = ContactName(self)
        self.contactMethods = []
        self.groups = []
        
        self.attributes = ContactAttributes()
        self.format = ContactFormat()
         
    # methods for various properties
    def GetName(self):
        return self.getRdfAttribute(chandler.name, ContactEntityItem.rdfs)
    
    def SetName(self, name):
        self.setRdfAttribute(chandler.name, name, ContactEntityItem.rdfs)

    def GetContactType(self):
        return self.getRdfAttribute(chandler.contactType, ContactEntityItem.rdfs)
    
    def SetContactType(self, newType):
        self.setRdfAttribute(chandler.contactType, str(newType), ContactEntityItem.rdfs)
   
    def GetContactMethods(self):
        return self.getRdfAttribute(chandler.contactMethods, ContactEntityItem.rdfs)
    
    def SetContactMethods(self, contactMethod):
        self.setRdfAttribute(chandler.contactMethods, contactMethod, ContactEntityItem.rdfs)
        
    def GetPhotoURL(self):
        return self.getRdfAttribute(chandler.photoURL, ContactEntityItem.rdfs)
    
    def SetPhotoURL(self, photoURL):
        self.setRdfAttribute(chandler.photoURL, photoURL, ContactEntityItem.rdfs)

    def GetContactFormat(self):
       return self.getRdfAttribute(chandler.format, ContactEntityItem.rdfs)
    
    def SetContactFormat(self, format):
        self.setRdfAttribute(chandler.format, format, ContactEntityItem.rdfs)
    
    def GetAttribute(self, attributeKey):
        return self.attributes.GetAttribute(attributeKey)
    
    def SetAttribute(self, attributeKey, attributeValue):
        return self.attributes.SetAttribute(attributeKey, attributeValue)
    
    def GetGroups(self):
        return self.getRdfAttribute(chandler.groups, ContactEntityItem.rdfs)
    
    def SetGroups(self, groups):
        self.setRdfAttribute(chandler.groups, groups, ContactEntityItem.rdfs)

    # create a new contact method and add it to the list
    def AddAddress(self, addressType, addressLocation, attributes):
        newItem = ContactMethodItem(addressType, addressLocation, attributes)
        self.contactMethods.append(newItem)
        self.SetContactMethods(self.contactMethods)

        return newItem
         
    # header and body attribute managerment routines
    def GetHeaderAttributes(self):
        return self.format.GetHeaderAttributes()
 
    def SetHeaderAttributes(self, attributes):
         self.format.SetHeaderAttributes(attributes)
        
    def HasHeaderAttribute(self, attribute):
        return self.format.HasHeaderAttribute(attribute)
        
    def AddHeaderAttribute(self, attribute):
        self.format.AddHeaderAttribute(attribute)
        
    def RemoveHeaderAttribute(self, attribute):
        try:
           index = self.format.headerAttributes.index(attribute)
           del self.format.headerAttributes[index]
        except:
           pass
        
    def GetBodyAttributes(self):
        return self.format.GetBodyAttributes()
    
    def SetBodyAttributes(self, attributes):
        self.format.SetBodyAttributes(attributes)
    
    def HasBodyAttribute(self, attribute):
        return self.format.HasBodyAttribute(attribute)
        
    def AddBodyAttribute(self, attribute):
        self.format.AddBodyAttribute(attribute)
        
    def RemoveBodyAttribute(self, attribute):
       try:
           index = self.format.bodyAttributes.index(attribute)
           del self.format.bodyAttributes[index]
       except:
           pass
     
   # group management routines
    def AddGroup(self, newGroup):
        try:
            index = self.groups.index(newGroup)
        except ValueError:
            self.groups.append(newGroup)
            
    def RemoveGroup(self, groupToRemove):
        try:
            index = self.groups.index(groupToRemove)
            del self.groups[index]
        except:
            pass
                
    # addresses manipulation
    # FIXME: GetAddresses is deprecated, use GetContactMethods instead
    def GetAddresses(self):
        return self.GetContactMethods()
                
    def HasAttribute(self, attributeKey):
        return self.attributes.has_key(attributeKey)
        
    def GetAttribute(self, attributeKey):
        # hack for names to be specified as attributes
        if attributeKey.startswith('name/'):
            parts = attributeKey.split('/')
            return self.GetNamePart(parts[1])	

        attributeValue = self.attributes.GetAttribute(attributeKey)
        
        # hack for sharing - return 'private' instead of none
        if attributeKey == 'sharing' and attributeValue == None:
            attributeValue = 'private'
            
        return attributeValue
        
    def SetAttribute(self, attributeKey, attributeValue):
        # hack to allow name parts to be set via SetAttribute
        if attributeKey.startswith('name/'):
            parts = attributeKey.split('/')
            self.SetNamePart(parts[1], attributeValue)
        else:
            self.attributes.SetAttribute(attributeKey, attributeValue)
                        
    def GetNamePart(self, partName):
        return self.name.GetNamePart(partName)
    
    def SetNamePart(self, partName, partValue):
        self.name.SetNamePart(partName, partValue)
                
    # derive the full name from the name parts
    def GetFullName(self):		
        return self.name.GetNamePart('fullname')
        
    def GetSortName(self):
        return self.name.GetNamePart('sortname')

    def SetFullName(self, newName):
        self.name.SetNamePart('fullname', newName)
        
    def GetShortName(self):
        return self.name.GetShortName()
        
    # delete the passed-in address item
    def DeleteAddressItem(self, item):
        try:
            index = self.contactMethods.index(item)
            del self.contactMethods[index]
        except:
            pass
                        
    # fetch attribute values from their location label
    def GetContactValue(self, contactLocation, attributeName):
        for method in self.contactMethods:
            if method.GetMethodDescription() == contactLocation:
                return method.GetFormattedAttribute(attributeName)
        return ''
    
    name = property(GetName, SetName)
    contactType = property(GetContactType, SetContactType)
    contactMethods = property(GetContactMethods, SetContactMethods)
    photoURL = property(GetPhotoURL, SetPhotoURL)
    contactFormat = property(GetContactFormat, SetContactFormat)
    groups = property(GetGroups, SetGroups)
    
