"""
Unit tests for contacts
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.tests.GenerateItems as GenerateItems
import osaf.contentmodel.contacts.Contacts as Contacts

import mx.DateTime as DateTime

from repository.util.Path import Path


class ContactsTest(TestContentModel.ContentModelTestCase):
    """ Test Contacts Content Model """

    def testContacts(self):
        """ Simple test for creating instances of contact related kinds """

        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/contacts")

        def _verifyContactName(name):
            self.assertEqual(name.firstName, 'Sylvia')
            self.assertEqual(name.getAttributeValue('firstName'),'Sylvia')
            self.assertEqual(name.lastName, 'Plath')
            self.assertEqual(name.getAttributeValue('lastName'), 'Plath')

        # Test the globals
        contactsPath = Path('//parcels/osaf/contentmodel/contacts')

        self.assertEqual(Contacts.ContactsParcel.getContactKind(),
                         self.rep.find(Path(contactsPath, 'Contact')))
        self.assertEqual(Contacts.ContactsParcel.getContactSectionKind(),
                         self.rep.find(Path(contactsPath, 'ContactSection')))
        self.assertEqual(Contacts.ContactsParcel.getContactNameKind(),
                         self.rep.find(Path(contactsPath, 'ContactName')))
        self.assertEqual(Contacts.ContactsParcel.getStreetAddressKind(),
                         self.rep.find(Path(contactsPath, 'StreetAddress')))
        self.assertEqual(Contacts.ContactsParcel.getPhoneNumberKind(),
                         self.rep.find(Path(contactsPath, 'PhoneNumber')))

        # Construct sample items
        contactItem = Contacts.Contact("contactItem")
        contactSectionItem = Contacts.ContactSection("contactSectionItem")
        contactNameItem = Contacts.ContactName("contactNameItem")
        streetAddressItem = Contacts.StreetAddress("streetAddressItem")
        phoneNumberItem = Contacts.PhoneNumber("phoneNumberItem")

        # Double check kinds
        self.assertEqual(contactItem.itsKind,
                         Contacts.ContactsParcel.getContactKind())
        self.assertEqual(contactSectionItem.itsKind,
                         Contacts.ContactsParcel.getContactSectionKind())
        self.assertEqual(contactNameItem.itsKind,
                         Contacts.ContactsParcel.getContactNameKind())
        self.assertEqual(streetAddressItem.itsKind,
                         Contacts.ContactsParcel.getStreetAddressKind())
        self.assertEqual(phoneNumberItem.itsKind,
                         Contacts.ContactsParcel.getPhoneNumberKind())

        # Literal properties
        contactNameItem.firstName = "Sylvia"
        contactNameItem.lastName = "Plath"

        _verifyContactName(contactNameItem)

        self._reopenRepository()

        contentItemParent = self.rep.findPath("//userdata/contentitems")
        
        contactNameItem = contentItemParent.getItemChild("contactNameItem")
        _verifyContactName(contactNameItem)

    def testGeneratedContacts(self):

        self.loadParcels(["http://osafoundation.org/parcels/osaf/contentmodel/contacts", "http://osafoundation.org/parcels/osaf/contentmodel/mail"])

        GenerateItems.GenerateContacts(100)
        self.rep.commit()
        

if __name__ == "__main__":
    unittest.main()
