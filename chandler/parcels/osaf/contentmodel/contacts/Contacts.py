""" Classes used for Contacts parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.parcel.Parcel as Parcel
import repository.item.Item as Item
import OSAF.contentmodel.ContentModel as ContentModel
import application.Globals as Globals
import mx.DateTime as DateTime

class ContactsParcel(Parcel.Parcel):
    def __init__(self, name, parent, kind):
        Parcel.Parcel.__init__(self, name, parent, kind)

    def onItemLoad(self):
        super(ContactsParcel, self).onItemLoad()
        self._setUUIDs()

    def startupParcel(self):
        Parcel.Parcel.startupParcel(self)
        self._setUUIDs()

    def _setUUIDs(self):
        contactKind = self.find('Contact')
        ContactsParcel.contactKindID = contactKind.itsUUID
        
        contactSectionKind = self.find('ContactSection')
        ContactsParcel.contactSectionKindID = contactSectionKind.itsUUID

        contactNameKind = self.find('ContactName')
        ContactsParcel.contactNameKindID = contactNameKind.itsUUID
        
        streetAddressKind = self.find('StreetAddress')
        ContactsParcel.streetAddressKindID = streetAddressKind.itsUUID
        
        phoneNumberKind = self.find('PhoneNumber')
        ContactsParcel.phoneNumberKindID = phoneNumberKind.itsUUID

    def getContactKind(cls):
        assert cls.contactKindID, "Contacts parcel not yet loaded"
        return Globals.repository[cls.contactKindID]

    getContactKind = classmethod(getContactKind)

    def getContactSectionKind(cls):
        assert cls.contactSectionKindID, "Contacts parcel not yet loaded"
        return Globals.repository[cls.contactSectionKindID]

    getContactSectionKind = classmethod(getContactSectionKind)

    def getContactNameKind(cls):
        assert cls.contactNameKindID, "Contacts parcel not yet loaded"
        return Globals.repository[cls.contactNameKindID]

    getContactNameKind = classmethod(getContactNameKind)

    def getStreetAddressKind(cls):
        assert cls.streetAddressKindID, "Contacts parcel not yet loaded"
        return Globals.repository[cls.streetAddressKindID]

    getStreetAddressKind = classmethod(getStreetAddressKind)

    def getPhoneNumberKind(cls):
        assert cls.phoneNumberKindID, "Contacts parcel not yet loaded"
        return Globals.repository[cls.phoneNumberKindID]

    getPhoneNumberKind = classmethod(getPhoneNumberKind)

    contactKindID = None
    contactSectionKindID = None
    contactNameKindID = None
    streetAddressKindID = None
    phoneNumberKindID = None

class Contact(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = ContactsParcel.getContactKind()
        ContentModel.ContentItem.__init__(self, name, parent, kind)

class ContactSection(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = ContactsParcel.getContactSectionKind()
        Item.Item.__init__(self, name, parent, kind)

class ContactName(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = ContactsParcel.getContactNameKind()
        Item.Item.__init__(self, name, parent, kind)

class StreetAddress(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = ContactsParcel.getStreetAddressKind()
        Item.Item.__init__(self, name, parent, kind)

class PhoneNumber(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = ContactsParcel.getPhoneNumberKind()
        Item.Item.__init__(self, name, parent, kind)


