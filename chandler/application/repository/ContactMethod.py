"""Contact Method
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application.repository.Thing import Thing
from application.repository.KindOfThing import AkoThingFactory
from application.repository.Namespace import chandler

from application.repository.Item import Item
from application.repository.ContactName import ContactName

_attributes = [{ chandler.url : chandler.methodType,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Contact Method'),
                 chandler.default : '' },
               
               { chandler.url : chandler.methodDescription,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Description'),
                 chandler.default : '' },
               
               { chandler.url : chandler.methodComment,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Comment'),
                 chandler.default : None },
               
               { chandler.url : chandler.methodAttributes,
                 chandler.range : 'string',
                 chandler.cardinality : None,
                 chandler.required : False,
                 chandler.displayName : _('Method Attributes'),
                 chandler.default : [] }]
               
_phoneAttributes = [{ chandler.url : chandler.phonenumber,
                      chandler.range : 'string',
                      chandler.cardinality : 1,
                      chandler.required : False,
                      chandler.displayName : _('Phone Number'),
                      chandler.default : _('phone number') }]
                   
_emailAttributes = [{ chandler.url : chandler.emailAddress,
                      chandler.range : 'string',
                      chandler.cardinality : 1,
                      chandler.required : False,
                      chandler.displayName : _('Email Address'),
                      chandler.default : _('email address') }]

_jabberAttributes = [{ chandler.url : chandler.jabberAddress,
                       chandler.range : 'string',
                       chandler.cardinality : 1,
                       chandler.required : False,
                       chandler.displayName : _('Jabber ID'),
                       chandler.default : _('jabber id') }]

_websiteAttributes = [{ chandler.url : chandler.url,
                        chandler.range : 'string',
                        chandler.cardinality : 1,
                        chandler.required : False,
                        chandler.displayName : _('URL'),
                        chandler.default : _('URL') }]

_noteAttributes = [{ chandler.url : chandler.note,
                     chandler.range : 'string',
                     chandler.cardinality : 1,
                     chandler.required : False,
                     chandler.displayName : _('Note'),
                     chandler.default : _('') }]
                   
_postalAttributes = [{ chandler.url : chandler.street,
                       chandler.range : 'string',
                       chandler.cardinality : 1,
                       chandler.required : False,
                       chandler.displayName : _('Street'),
                       chandler.default : _('street address') },
                     
                     # hack!
                     { chandler.url : 'linebreak',
                       chandler.range : 'string',
                       chandler.cardinality : 1,
                       chandler.required : False,
                       chandler.displayName : _('linebreak'),
                       chandler.default : _('linebreak') },                     
                     
                     { chandler.url : chandler.city,
                       chandler.range : 'string',
                       chandler.cardinality : 1,
                       chandler.required : False,
                       chandler.displayName : _('City'),
                       chandler.default : _('city') },
                     
                     { chandler.url : chandler.state,
                       chandler.range : 'string',
                       chandler.cardinality : 1,
                       chandler.required : False,
                       chandler.displayName : _('State'),
                       chandler.default : _('state') },
                     
                     { chandler.url : chandler.zip,
                       chandler.range : 'string',
                       chandler.cardinality : 1,
                       chandler.required : False,
                       chandler.displayName : _('Zipcode'),
                       chandler.default : _('zip') }]

# @@@ Note, need to handle this in a more consistent way
_methodTypes = { 'phone' : (chandler.PhoneContactMethod, _phoneAttributes),
                 'email' : (chandler.EmailContactMethod, _emailAttributes),
                 'jabberID' : (chandler.JabberContactMethod, _jabberAttributes),
                 'website' : (chandler.WebsiteContactMethod, _websiteAttributes),
                 'note' : (chandler.NoteContactMethod, _noteAttributes),
                 'postal' : (chandler.PostalContactMethod, _postalAttributes) }

class AkoContactMethodFactory(AkoThingFactory):
    def __init__(self, type):
        url, typeAttributes = _methodTypes[type]
        AkoThingFactory.__init__(self, url,
                                 _attributes + typeAttributes)
        
class ContactMethod(Item):
    
    #@@@ Constructor might need to be more complicated
    def __init__(self, type, description):
        Item.__init__(self)
        self.SetMethodType(type)
        self.SetMethodDescription(description)
        self.SetAko(AkoContactMethodFactory(type).GetAko())
        self.InitMethodAttributes(type)
        
    def ChangeMethodType(self, type):
        self.SetAko(AkoContactMethodFactory(type).GetAko())
        self.InitMethodAttributes(type)
        
    # @@@ This method will need to change if we implement the
    #     meta-information as 'Thing's
    def InitMethodAttributes(self, type):
        attributes = []
        url, typeAttributes = _methodTypes[type]
        for typeAttribute in typeAttributes:
            attributeURL = typeAttribute[chandler.url]
            attributes.append(attributeURL)
        self.SetMethodAttributes(attributes)
        
    def GetLocationAbbreviation(self):
        description = self.GetAttribute(chandler.methodDescription)
        return description[0]
    
    def GetFirstFormattedValue(self):
        return self.GetFormattedAttribute(self.GetFirstAttribute())
    
    def GetFirstAttribute(self):
        attributes = self.GetAttribute(chandler.methodAttributes)
        return attributes[0]
    
    # @@@ Hook for formatting attributes in a type specific manner
    #     Unused for now, perhaps should be more general to
    #     'Things' or 'Items'.
    def GetFormattedAttribute(self, attribute):
        return self.GetAttribute(attribute)
    
    # Convenience methods to get and set the fields
    def GetMethodType(self):
        return self.GetAttribute(chandler.methodType)
    
    def SetMethodType(self, value):
        self.SetAttribute(chandler.methodType, value)
        
    def GetMethodDescription(self):
        return self.GetAttribute(chandler.methodDescription)

    # @@@ FIXME: for now, coerce unicode to string to pass
    #     type validity check
    def SetMethodDescription(self, value):
        self.SetAttribute(chandler.methodDescription, value)
        
    def GetMethodComment(self):
        return self.GetAttribute(chandler.methodComment)
    
    def SetMethodComment(self, value):
        self.SetAttribute(chandler.methodComment, value)
        
    def HasComment(self):
        return (self.GetAttribute(chandler.methodComment) != None)
        
    def GetMethodAttributes(self):
        return self.GetAttribute(chandler.methodAttributes)
        
    def SetMethodAttributes(self, value):
        self.SetAttribute(chandler.methodAttributes, value)
 
    # even though it's an item, a ContactMethod is not a toplevel object
    def IsTopLevel(self):
        return 0

    # @@@ Depricated, should use GetMethodAttributes
    def GetAddressAttributes(self):
        return self.GetMethodAttributes()
        
   
        
        
        
        