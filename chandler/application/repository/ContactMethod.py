"""Contact Method
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF"

from application.repository.Thing import Thing
from application.repository.KindOfThing import AkoThingFactory
from application.repository.Namespace import chandler

from application.repository.Item import Item
from application.repository.ContactName import ContactName

_attributes = [{ chandler.uri : chandler.methodType,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Contact Method'),
                 chandler.default : '' },
               
               { chandler.uri : chandler.methodDescription,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Description'),
                 chandler.default : '' },
               
               { chandler.uri : chandler.methodComment,
                 chandler.range : 'string',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.displayName : _('Comment'),
                 chandler.default : None },
               
               { chandler.uri : chandler.methodAttributes,
                 chandler.range : 'string',
                 chandler.cardinality : None,
                 chandler.required : False,
                 chandler.displayName : _('Method Attributes'),
                 chandler.default : [] }]
               
_phoneAttributes = [{ chandler.uri : chandler.phonenumber,
                      chandler.range : 'string',
                      chandler.cardinality : 1,
                      chandler.required : False,
                      chandler.displayName : _('Phone Number'),
                      chandler.default : _('phone number') }]
                   
_emailAttributes = [{ chandler.uri : chandler.emailAddress,
                      chandler.range : 'string',
                      chandler.cardinality : 1,
                      chandler.required : False,
                      chandler.displayName : _('Email Address'),
                      chandler.default : _('email address') }]

_jabberAttributes = [{ chandler.uri : chandler.jabberAddress,
                       chandler.range : 'string',
                       chandler.cardinality : 1,
                       chandler.required : False,
                       chandler.displayName : _('Jabber ID'),
                       chandler.default : _('jabber id') }]

_websiteAttributes = [{ chandler.uri : chandler.url,
                        chandler.range : 'string',
                        chandler.cardinality : 1,
                        chandler.required : False,
                        chandler.displayName : _('URL'),
                        chandler.default : _('URL') }]

_noteAttributes = [{ chandler.uri : chandler.note,
                     chandler.range : 'string',
                     chandler.cardinality : 1,
                     chandler.required : False,
                     chandler.displayName : _('Note'),
                     chandler.default : _('') }]
                   
_postalAttributes = [{ chandler.uri : chandler.street,
                       chandler.range : 'string',
                       chandler.cardinality : 1,
                       chandler.required : False,
                       chandler.displayName : _('Street'),
                       chandler.default : _('street address') },
                     
                     # hack!
                     { chandler.uri : 'linebreak',
                       chandler.range : 'string',
                       chandler.cardinality : 1,
                       chandler.required : False,
                       chandler.displayName : _('linebreak'),
                       chandler.default : _('linebreak') },                     
                     
                     { chandler.uri : chandler.city,
                       chandler.range : 'string',
                       chandler.cardinality : 1,
                       chandler.required : False,
                       chandler.displayName : _('City'),
                       chandler.default : _('city') },
                     
                     { chandler.uri : chandler.state,
                       chandler.range : 'string',
                       chandler.cardinality : 1,
                       chandler.required : False,
                       chandler.displayName : _('State'),
                       chandler.default : _('state') },
                     
                     { chandler.uri : chandler.zip,
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
        uri, typeAttributes = _methodTypes[type]
        AkoThingFactory.__init__(self, uri,
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
        uri, typeAttributes = _methodTypes[type]
        for typeAttribute in typeAttributes:
            attributeUri = typeAttribute[chandler.uri]
            attributes.append(attributeUri)
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
        
    # @@@ Depricated, should use GetMethodAttributes
    def GetAddressAttributes(self):
        return self.GetMethodAttributes()
        
   
        
        
        
        