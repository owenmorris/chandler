#!bin/env python

"""EntityItem, common subclass for PersonItem, OrganizationItem, GroupItem
"""

__author__ = "Andy Hertzfeld"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF"

from persistence.dict import PersistentDict

from InformationItem import InformationItem

from RdfRestriction import RdfRestriction

from RdfNamespace import dc
from RdfNamespace import chandler

import ContactMethodAttributes

class ContactMethodItem(InformationItem):
    """ContactMethodItem"""

    rdfs = PersistentDict()
    
    rdfs[chandler.methodType] = RdfRestriction(str, 1)
    rdfs[chandler.methodDescription] = RdfRestriction(str, 1)
    rdfs[chandler.methodAddress] = RdfRestriction(ContactMethodAttributes.ContactMethodAttributes, 1)
    rdfs[chandler.methodComment] = RdfRestriction(str, 1)
   
    def __init__(self, methodType, methodDescription, attributes):
        InformationItem.__init__(self)
        
        self.SetMethodType(methodType)
        self.SetMethodDescription(methodDescription)
        self.InitMethodAddress(attributes)

    # methods to get and set all of the fields
    def GetMethodType(self):
        return self.getRdfAttribute(chandler.methodType, ContactMethodItem.rdfs)
    
    def SetMethodType(self, methodType):
        self.setRdfAttribute(chandler.methodType, methodType, ContactMethodItem.rdfs)
    
    def GetMethodDescription(self):
        return self.getRdfAttribute(chandler.methodDescription, ContactMethodItem.rdfs)
 
    # FIXME: for now, coerce unicode to string to pass the type validity check
    def SetMethodDescription(self, methodDescription):    
        self.setRdfAttribute(chandler.methodDescription, str(methodDescription), ContactMethodItem.rdfs)
        
    def GetMethodAddress(self):
        return self.getRdfAttribute(chandler.methodAddress, ContactMethodItem.rdfs)
    
    def SetMethodAddress(self, methodAddress):
        self.setRdfAttribute(chandler.methodAddress, methodAddress, ContactMethodItem.rdfs)
    
    def GetMethodComment(self):
        return self.getRdfAttribute(chandler.methodComment, ContactMethodItem.rdfs)
    
    def SetMethodComment(self, methodComment):
        self.setRdfAttribute(chandler.methodComment, methodComment, ContactMethodItem.rdfs)

    def HasComment(self):
        return self.methodComment != None
    
    def GetAttribute(self, attributeKey):
        if attributeKey == 'comment':
            return self.GetMethodComment()
        return self.methodAddress.GetAttribute(attributeKey)
    
    def SetAttribute(self, attributeKey, attributeValue):
        if attributeKey == 'comment':
            self.SetMethodComment(attributeValue)
        else:
            self.methodAddress.SetAttribute(attributeKey, attributeValue)

    # allocate the attributes object and initialize it from the passed in dictionary
    def InitMethodAddress(self, attributes):
        self.methodAddress = ContactMethodAttributes.CreateContactMethodAttributes(self.methodType)
        for key in attributes.keys():
            value = attributes[key]
            self.methodAddress.SetAttribute(key, value)
            
    # return the list of relevant attributes for this contact address, based
    # on it's type.
    # FIXME: should get these from introspection of the address object; right now, they
    # don't have RDF representations
    # FIXME: Eventually, users should be able to add attributes here,
    # but for now, it's hard-wired
    def GetAddressAttributes(self):
        addressType = self.GetMethodType()
        
        if addressType == 'phone':
            attributeList = ['phonenumber']
        elif addressType == 'email':
            attributeList = ['address']
        elif addressType == 'jabberID':
            attributeList = ['address']
        elif addressType == 'website':
            attributeList = ['url']
        elif addressType == 'note':
            attributeList = ['text']
        elif addressType == 'postal':
            attributeList = ['street', 'linebreak', 'city', 'state', 'zipcode']
        else:
            # the default for unknown types is 'address'
            attributeList = ['address']
            
        return attributeList
    
    # hook for formatting attributes in a type specific manner
    # unused for now
    def GetFormattedAttribute(self, attribute):
        attributeValue = self.GetAttribute(attribute)
        return attributeValue
    
    # return the formatted attribute for the first attribute associate with the address
    def GetFirstFormattedValue(self):
        attributes = self.GetAddressAttributes()
        return self.GetFormattedAttribute(attributes[0])
        
    # return an abbreviation for the location, used when space is at a premium
    def GetLocationAbbreviation(self):
        description = self.GetMethodDescription()
        return description[0]
    
    methodType = property(GetMethodType, SetMethodType)
    methodDescription = property(GetMethodDescription, SetMethodDescription)
    methodAddress = property(GetMethodAddress, SetMethodAddress)
    methodComment = property(GetMethodComment, SetMethodComment)

 