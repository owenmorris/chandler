#!bin/env python

"""EntityItem, common subclass for PersonItem, OrganizationItem, GroupItem
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item

class ContactMethodFactory:
    def __init__(self, rep):
        self._container = rep.find("//Contacts")
        self.repository = rep
        
    def NewItem(self, addressType):
        if addressType == 'phone':
            kind = "//Schema/ContactsSchema/PhoneContactMethod"
        elif addressType == 'email':
            kind = "//Schema/ContactsSchema/EmailContactMethod"         
        else:
            kind = "//Schema/ContactsSchema/ContactMethod"
        
        item = ContactMethod(None, self._container, self.repository.find(kind))
        item.setAttribute('methodType', addressType)
        
        return item

class ContactMethod(Item):
    def __init__(self, name, parent, kind, **_kwds):
        super(ContactMethod, self).__init__(name, parent, kind, **_kwds)
 
    # methods to get and set all of the attributes
    def GetMethodType(self):
        return self.getAttribute('methodType')
    
    def SetMethodType(self, methodType):
        self.setAttribute('methodType', methodType)
    
    def GetMethodDescription(self):
        return self.getAttribute('methodDescription')
 
    def SetMethodDescription(self, methodDescription):    
        self.setAttribute('methodDescription', methodDescription)
        
    def GetMethodValue(self):
        return self.methodValue
    
    def SetMethodValue(self, methodValue):
        self.setAttribute('methodValue', methodValue)
    
    def GetMethodComment(self):
        try:
            return self.getAttribute('methodComment')
        except:
            return None
        
    def SetMethodComment(self, methodComment):
        self.setAttribute('methodComment', methodComment)

    def HasComment(self):
        return self.methodComment != None
    
    def GetAttribute(self, attributeName):
        try:
            return self.getAttribute(attributeName)
        except:
            return ''
        
    def SetAttribute(self, attributeName, attributeValue):
        self.setAttribute(attributeName, attributeValue)
        
    # change the type of the address item, setting up the passed-in attributes
    # we actually need to change the class of the object here
    # FIXME: this isn't implemented properly yet
    def ChangeMethodType(self, newType):
        if self.GetMethodType() == newType:
            return

        self.SetMethodType(newType)

        #methodAttributes = self.GetMethodAddress()
        #for attributeData in newAttributes:
             #methodAttributes.SetAttribute(attributeData[0], attributeData[1])

            
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
            attributeList = ['emailaddress']
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
    
    # return the first attribute
    def GetFirstAttribute(self):
        attributes =  self.GetAddressAttributes()
        return attributes[0]
    
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
    methodComment = property(GetMethodComment, SetMethodComment)

 