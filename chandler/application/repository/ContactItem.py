"""ContactItem, the base class for contacts
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

_attributes = [{ chandler.uri : chandler.contactType,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.contactName,
                 chandler.range : ContactName,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },

                { chandler.uri : chandler.contactMethod,
                 chandler.range : ContactName,
                 chandler.cardinality : None,
                 chandler.required : False,
                 chandler.default : None },              
               
               { chandler.uri : chandler.photoURL,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },

               { chandler.uri : chandler.contactAttributes,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },

               { chandler.uri : chandler.contactFormat,
                 chandler.range : ContactFormat,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },

               { chandler.uri : chandler.group,
                 chandler.range : str,
                 chandler.cardinality : None,
                 chandler.required : False,
                 chandler.default : None }
               ]

class AkoContactItemFactory(AkoThingFactory):
    def __init__(self):
        AkoThingFactory.__init__(self, chandler.ContactItem, _attributes)

class ContactItem(Item):

    def __init__(self, contactType):
        Item.__init__(self)
        self.SetAko(AkoContactItemFactory().GetAko())
        self.SetContactType(contactType)

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

    def AddAddress(self, addressType, addressLocation, attributes):
        newItem = ContactMethodItem(addressType, addressLocation, attributes)
        self.contactMethods.append(newItem)
        self.SetContact
    


        
