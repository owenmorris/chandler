#!bin/env python

"""ContactEntityItem, the base class for contacts
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from model.item.Item import Item

from application.Application import app
from wxPython.wx import *

from ContactMethod import *
from ContactName import *
from ContactFormat import *

class ContactEntityFactory:
    def __init__(self, rep):
        self._container = rep.find("//Contacts")
        self._kind = rep.find("//Schema/ContactsSchema/ContactEntity")
        self.repository = rep
        
    def NewItem(self, contactType='Person'):
        item = ContactEntity(None, self._container, self._kind)
        item.setAttribute('contactType', contactType)
                
        nameFactory = ContactNameFactory(self.repository)
        name = nameFactory.NewItem()
        item.setAttribute('contactName', name)
        
        formatFactory = ContactFormatFactory(self.repository)
        format = formatFactory.NewItem()
        item.setAttribute('contactFormat', format)
              
        return item

class ContactEntity(Item):  
    def __init__(self, name, parent, kind, **_kwds):
        super(ContactEntity, self).__init__(name, parent, kind, **_kwds)
        
    # methods for various properties
    def GetName(self):
        return self.getAttribute('contactName')
    
    def SetName(self, name):
        self.setAttribute('contactName', name)

    def GetContactType(self):
        return self.getAttribute('contactType')
    
    def SetContactType(self, newType):
        self.setAttribute('contactType', newType)
   
    def GetContactMethods(self):
        try:
            refDict = self.getAttribute('contactMethods')
            return refDict.values()
        except AttributeError:
            return []
    
    def SetContactMethods(self, contactMethod):
        self.setAttribute('contactMethods', contactMethod)
        
    def GetPhotoURL(self):
        try:
            return self.getAttribute('contactPhotoURL')
        except AttributeError:
            return None
    
    def SetPhotoURL(self, photoURL):
        self.setAttribute('contactPhotoURL', photoURL)

    def GetContactFormat(self):
         return self.getAttribute('contactFormat')
    
    def SetContactFormat(self, format):
        self.setAttribute('contactFormat', format)
        
    def GetGroups(self):
        try:
            return self.getAttribute('contactGroups')
        except AttributeError:
             return []
    
    name = property(GetName, SetName)
    contactMethods = property(GetContactMethods, SetContactMethods)
    format = property(GetContactFormat, SetContactFormat)

    # create a new contact method and add it to the list
    def AddAddress(self, addressType, addressLocation):
        factory = ContactMethodFactory(app.repository)        
        newMethod = factory.NewItem(addressType)
        newMethod.SetMethodDescription(addressLocation)
                
        newMethod.methodEntity = self
        self.attach('contactMethods', newMethod)
                
        return newMethod
         
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
 
    # return true if the contact has a specific contact method
    def HasContactMethod(self, contactType, contactValue):
        for contactMethod in self.contactMethods:
            if contactMethod.GetMethodType() == contactType:
                methodAttributes = contactMethod.GetAddressAttributes()
                for attribute in methodAttributes:
                    if contactMethod.GetAttribute(attribute) == contactValue:
                        return True
        return False
   
   # group management routines
    def AddGroup(self, newGroup):
        try:
            groups = self.GetGroups()
            index = groups.index(newGroup)
        except ValueError:
            self.addValue('contactGroups', newGroup)
            
    def RemoveGroup(self, groupToRemove):
        try:
            groups = self.GetGroups()
            index = groups.index(groupToRemove)
            self.removeValue('contactGroups', index)
        except:
            pass
    
    def HasGroup(self, group):
        try:
            groups = self.GetGroups()
            index = groups.index(group)
            return True
        except:
            pass
        
        return False
    
    # addresses manipulation
                
    def HasAttribute(self, attributeKey):
        return self._attributes.has_key(attributeKey)
 
    # FIXME: this is kind of a mess after various transitions -
    # we should reorganize it
    def GetAttribute(self, attributeKey):
        # hack for names to be specified as attributes
        if self.name.IsNameAttribute(attributeKey):
            return self.GetNamePart(attributeKey)

        # also, allow type to be fetched as an attribute
        if attributeKey == 'type':
            return self.GetContactType()
        
        try:
            attributeValue = self.getAttribute(attributeKey)
        except:
            attributeValue = None
            
        # hack for sharing - default to public, since the views default to private
        if attributeKey == 'sharing' and attributeValue == None:
            attributeValue = 'public'
            
        return attributeValue
        
    def SetAttribute(self, attributeKey, attributeValue):
        # hack to allow name parts to be set via SetAttribute
        if self.name.IsNameAttribute(attributeKey):
            self.SetNamePart(attributeKey, attributeValue)
        else:
            self.setAttribute(attributeKey, attributeValue)
                        
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
    def DeleteContactMethod(self, item):
        self.detach('contactMethods', item)
                        
    # fetch attribute values from their location label
    def GetContactValue(self, contactLocation, attributeName):
        for method in self.contactMethods:
            if method.GetMethodDescription() == contactLocation:
                return method.GetFormattedAttribute(attributeName)
        return ''
        
