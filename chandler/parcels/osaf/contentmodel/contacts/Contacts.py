""" Classes used for Contacts parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import repository.item.Item as Item
import osaf.contentmodel.ContentModel as ContentModel
import application.Globals as Globals
import mx.DateTime as DateTime

class ContactsParcel(application.Parcel.Parcel):
    def onItemLoad(self):
        super(ContactsParcel, self).onItemLoad()
        self._setUUIDs()

    def startupParcel(self):
        super(ContactsParcel, self).startupParcel()
        self._setUUIDs()

    def _setUUIDs(self):
        contactKind = self['Contact']
        ContactsParcel.contactKindID = contactKind.itsUUID
        
        contactSectionKind = self['ContactSection']
        ContactsParcel.contactSectionKindID = contactSectionKind.itsUUID

        contactNameKind = self['ContactName']
        ContactsParcel.contactNameKindID = contactNameKind.itsUUID
        
        streetAddressKind = self['StreetAddress']
        ContactsParcel.streetAddressKindID = streetAddressKind.itsUUID
        
        phoneNumberKind = self['PhoneNumber']
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
        super (Contact, self).__init__(name, parent, kind)

    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(Contact, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        self.contactName = ContactName()
        self.contactName.firstName = ''
        self.contactName.lastName = ''
        self.homeSection = ContactSection()
        self.workSection = ContactSection()

class ContactSection(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = ContactsParcel.getContactSectionKind()
        super (ContactSection, self).__init__(name, parent, kind)

class ContactName(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = ContactsParcel.getContactNameKind()
        super (ContactName, self).__init__(name, parent, kind)

class StreetAddress(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = ContactsParcel.getStreetAddressKind()
        super (StreetAddress, self).__init__(name, parent, kind)

class PhoneNumber(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = ContactsParcel.getPhoneNumberKind()
        super (PhoneNumber, self).__init__(name, parent, kind)


