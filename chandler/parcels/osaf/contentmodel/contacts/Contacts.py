""" Classes used for Contacts parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.parcel.Parcel as Parcel
import repository.item.Item as Item
import OSAF.contentmodel.ContentModel as ContentModel
import mx.DateTime as DateTime

# Module globals for Kinds
# ContactKind ==> //parcels/OSAF/contentmodel/contacts/Contact
# ContactSectionKind ==> //parcels/OSAF/contentmodel/contacts/ContactSection
# ContactNameKind ==> //parcels/OSAF/contentmodel/contacts/ContactName
# StreetAddressKind ==> //parcels/OSAF/contentmodel/contacts/StreetAddress
# PhoneNumberKind ==> //parcels/OSAF/contentmodel/contacts/PhoneNumber

class ContactsParcel(Parcel.Parcel):
    def __init__(self, name, parent, kind):
        Parcel.Parcel.__init__(self, name, parent, kind)

    def startupParcel(self):
        Parcel.Parcel.startupParcel(self)

        global ContactKind
        ContactKind = self.find('Contact')
        assert ContactKind

        global ContactSectionKind
        ContactSectionKind = self.find('ContactSection')
        assert ContactSectionKind

        global ContactNameKind
        ContactNameKind = self.find('ContactName')
        assert ContactNameKind

        global StreetAddressKind
        StreetAddressKind = self.find('StreetAddress')
        assert StreetAddressKind

        global PhoneNumberKind
        PhoneNumberKind = self.find('PhoneNumber')
        assert PhoneNumberKind

class Contact(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = ContactKind
        ContentModel.ContentItem.__init__(self, name, parent, kind)

class ContactSection(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentItemParent
        if not kind:
            kind = ContactSectionKind
        Item.Item.__init__(self, name, parent, kind)

class ContactName(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentItemParent
        if not kind:
            kind = ContactNameKind
        Item.Item.__init__(self, name, parent, kind)

class StreetAddress(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentItemParent
        if not kind:
            kind = StreetAddressKind
        Item.Item.__init__(self, name, parent, kind)

class PhoneNumber(Item.Item):
    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentItemParent
        if not kind:
            kind = PhoneNumberKind
        Item.Item.__init__(self, name, parent, kind)


