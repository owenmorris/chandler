"""Contact, the base class for contacts
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF"

from wxPython.wx import *
from application.repository.Thing import Thing
from application.repository.KindOfThing import AkoThingFactory
from application.repository.Namespace import chandler

from application.repository.Item import Item
from application.repository.ContactName import ContactName, AkoPersonNameFactory
from application.repository.ContactMethod import ContactMethod

# We're likely to handle ENUMs differently, but a simple strategy for now
_relationshipChoices = [_('friend'), _('coworker'), _('associate'), 
                        _('husband'), _('wife'), _('mother'), 
                        _('father'), _('son'), _('daughter'), 
                        _('aunt'), _('uncle'), _('brother'), _('sister')]
_genderChoices = [_('male'), _('female'), _('unknown')]
_sharingChoices = [_('private'), _('public')]
_reputationChoices = [_('trustworthy'), _('reliable'), _('honest'), 
                      _('secure'), _('unknown')]

_attributes = [{ chandler.uri : chandler.contactType,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Contact Type'),
                 chandler.default : '' },
               
               { chandler.uri : chandler.contactName,
                 chandler.range : ContactName,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Contact Name'),
                 chandler.default : '' },

               { chandler.uri : chandler.contactMethod,
                 chandler.range : ContactMethod,
                 chandler.cardinality : None,
                 chandler.required : False,
                 chandler.displayName : _('Contact Method'),
                 chandler.default : [] },           
               
               { chandler.uri : chandler.photoURL,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Photo URL'),
                 chandler.default : None },

               { chandler.uri : chandler.group,
                 chandler.range : 'string',
                 chandler.cardinality : None,
                 chandler.required : False,
                 chandler.displayName : _('Group'),
                 chandler.default : [] },
               
               # Lists of uris, for attribute formatting
               
               { chandler.uri : chandler.headerAttribute,
                 chandler.range : 'string',
                 chandler.cardinality : None,
                 chandler.required : False,
                 chandler.displayName : _('Header Attribute'),
                 chandler.default : [] },
               
               { chandler.uri : chandler.bodyAttribute,
                 chandler.range : 'string',
                 chandler.cardinality : None,
                 chandler.required : False,
                 chandler.displayName : _('Body Attribute'),
                 chandler.default : [] },
               
               # The laundry list of contact attributes...
               
               { chandler.uri : chandler.companyName,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Company'),
                 chandler.default : _('company name') },

               { chandler.uri : chandler.jobTitle,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Title'),
                 chandler.default : _('job title') },              
               
               { chandler.uri : chandler.occupation,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Occupation'),
                 chandler.default : _('occupation') },

               { chandler.uri : chandler.relationship,
                 chandler.range : _relationshipChoices,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Relationship'),
                 chandler.default : _('relationship') },

               { chandler.uri : chandler.age,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Age'),
                 chandler.default : _('age') },
               
               { chandler.uri : chandler.birthday,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Birthday'),
                 chandler.default : _('birthday') },

               { chandler.uri : chandler.gender,
                 chandler.range : _genderChoices,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Gender'),
                 chandler.default : _('gender') },
                                      
               { chandler.uri : chandler.sharing,
                 chandler.range : _sharingChoices,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Sharing Policy'),
                 chandler.default : _('public') },

               { chandler.uri : chandler.reputation,
                 chandler.range : _reputationChoices,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Reputation'),
                 chandler.default : _('unknown') },

               { chandler.uri : chandler.interests,
                 chandler.range : [],
                 chandler.cardinality : None,
                 chandler.required : False,
                 chandler.displayName : _('Interest'),
                 chandler.default : [] }
               ]

class AkoContactFactory(AkoThingFactory):
    def __init__(self):
        AkoThingFactory.__init__(self, chandler.Contact, _attributes)

class Contact(Item):

    def __init__(self, contactType):
        Item.__init__(self)
        self.SetAko(AkoContactFactory().GetAko())
        self.SetContactType(contactType)
        self.SetGroups([])
        self.SetContactMethods([])
        self.SetHeaderAttributes([])
        self.SetBodyAttributes([])
        self.SetContactName(ContactName(self))
    
    def GetAttribute(self, attribute):
        contactName = self.get(chandler.contactName)
        if (contactName != None):
            akoContactName =  contactName.GetAko()
            if (akoContactName.GetAttributeTemplate(attribute) != None):
                return contactName.GetAttribute(attribute)
            
        return Item.GetAttribute(self, attribute)
        
    def SetAttribute(self, attribute, value):
        contactName = self.get(chandler.contactName)
        if (contactName != None):
            akoContactName = contactName.GetAko()
            if (akoContactName.GetAttributeTemplate(attribute) != None):
                contactName.SetAttribute(attribute, value)
                return
        
        Item.SetAttribute(self, attribute, value)
        
    def GetContactType(self):
        return self.GetAttribute(chandler.contactType)
        
    def SetContactType(self, contactType):
        self.SetAttribute(chandler.contactType, contactType)

    contactType = property(GetContactType, SetContactType)

    def GetPhotoURL(self):
        return self.GetAttribute(chandler.photoURL)

    def SetPhotoURL(self, photoURL):
        self.SetAttribute(chandler.photoURL, photoURL)

    photoURL = property(GetPhotoURL, SetPhotoURL)
    
    def GetContactMethods(self):
        return self.GetAttribute(chandler.contactMethod)
    
    def SetContactMethods(self, value):
        self.SetAttribute(chandler.contactMethod, value)
        
    contactMethods = property(GetContactMethods)
    
    # Convenience methods for groups
    
    def GetGroups(self):
        return self.GetAttribute(chandler.group)
    
    def SetGroups(self, groupList):
        self.SetAttribute(chandler.group, groupList)
    
    groups = property(GetGroups)
    
    def HasGroup(self, group):
        return (self.groups.count(group) != 0)
    
    def AddGroup(self, group):
        if (self.groups.count(group) == 0):
            self.groups.append(group)

    def RemoveGroup(self, groupToRemove):
        try:
            index = self.groups.index(groupToRemove)
            del self.groups[index]
        except:
            pass
        #@@@ perhaps don't swallow this silently
        
    def HasContactMethod(self, contactType, contactValue):
        """ Return true if the contact has a specific contact method
        """
        for contactMethod in self.GetContactMethods():
            if contactMethod.GetMethodType() == contactType:
                for attributeUri in contactMethod.GetAllAttributes():
                    if (contactMethod.GetAttribute(attributeUri) == contactValue):
                        return true
        return false
    
    # Convenience methods for accessing a contact's name fields
    
    # @@@ Take the shortcut, dont' do validation
    def GetContactName(self):
        return self[chandler.contactName]
    
    def SetContactName(self, value):
        self.SetAttribute(chandler.contactName, value)
        
    name = property(GetContactName, SetContactName)
    
    def GetNameAttribute(self, attribute):
        return self.name.GetAttribute(attribute)
        
    def SetNameAttribute(self, attribute, value):
        self.name.SetAttribute(attribute, value)
        
    def GetFullName(self):
        return self.name.GetAttribute(chandler.fullname)
    
    def GetSortName(self):
        return self.name.GetAttribute(chandler.sortname)
    
    def GetShortName(self):
        return self.name.GetShortName()
    
    def SetFullName(self, value):
        self.name.SetAttribute(chandler.fullname, value)

    # delete a contact method
    def DeleteContactMethod(self, contactMethod):
        try:
            index = self.contactMethods.index(contactMethod)
            del self.contactMethods[index]
        except:
            pass

    # header and body attribute managerment routines
    def GetHeaderAttributes(self):
        return self.GetAttribute(chandler.headerAttribute)
 
    def SetHeaderAttributes(self, attributes):
         self.SetAttribute(chandler.headerAttribute, attributes)
        
    def HasHeaderAttribute(self, attribute):
        headerAttributes = self.GetHeaderAttributes()
        return headerAttributes.count(attribute) > 0
        
    def AddHeaderAttribute(self, attribute):
        headerAttributes = self.GetHeaderAttributes()
        if (headerAttributes.count(attribute) == 0):
            headerAttributes.append(attribute)
        
    def RemoveHeaderAttribute(self, attribute):
        try:
            headerAttributes = self.GetHeaderAttributes()
            index = headerAttributes.index(attribute)
            del headerAttributes[index]
        except:
           pass
        
    def GetBodyAttributes(self):
        return self.GetAttribute(chandler.bodyAttribute)
    
    def SetBodyAttributes(self, attributes):
        self.SetAttribute(chandler.bodyAttribute, attributes)
    
    def HasBodyAttribute(self, attribute):
        bodyAttributes = self.GetBodyAttributes()
        return bodyAttributes.count(attribute) > 0
        
    def AddBodyAttribute(self, attribute):
        bodyAttributes = self.GetBodyAttributes()
        if (bodyAttributes.count(attribute) == 0):
            bodyAttributes.append(attribute)
        
    def RemoveBodyAttribute(self, attribute):
       try:
           bodyAttributes = self.GetBodyAttributes()
           index = bodyAttributes.index(attribute)
           del bodyAttributes[index]
       except:
           pass

    # @@@ Depricated, use GetContactMethods
    def GetAddresses(self):
        return self.GetContactMethods()
    
    def AddAddress(self, addressType, addressDescription):
        newItem = ContactMethod(addressType, addressDescription)
        self.contactMethods.append(newItem)
        return newItem
    
    def GetContactValue(self, methodDescription, attributeName):
        for method in self.contactMethods:
            if method.GetMethodDescription() == methodDescription:
                return method.GetFormattedAttribute(attributeName)
        return ''

