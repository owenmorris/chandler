"""
Unit tests for contacts
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import OSAF.contentmodel.tests.TestContentModel as TestContentModel
import OSAF.contentmodel.contacts.Contacts as Contacts

import mx.DateTime as DateTime

class ContactsTest(TestContentModel.ContentModelTestCase):
    """ Test Contacts Content Model """

    def testContacts(self):
        """ Simple test for creating instances of contact related kinds """

        def _verifyContactName(name):
            self.assertEqual(name.firstName, 'Sylvia')
            self.assertEqual(name.getAttributeValue('firstName'),'Sylvia')
            self.assertEqual(name.lastName, 'Plath')
            self.assertEqual(name.getAttributeValue('lastName'), 'Plath')

        # Test the globals
        contactsPath = '//parcels/OSAF/contentmodel/contacts/%s'

        self.assertEqual(Contacts.ContactKind,
                         self.rep.find(contactsPath % 'Contact'))
        self.assertEqual(Contacts.ContactSectionKind,
                         self.rep.find(contactsPath % 'ContactSection'))
        self.assertEqual(Contacts.ContactNameKind,
                         self.rep.find(contactsPath % 'ContactName'))
        self.assertEqual(Contacts.StreetAddressKind,
                         self.rep.find(contactsPath % 'StreetAddress'))
        self.assertEqual(Contacts.PhoneNumberKind,
                         self.rep.find(contactsPath % 'PhoneNumber'))

        # Construct sample items
        contactItem = Contacts.Contact("contactItem")
        contactSectionItem = Contacts.ContactSection("contactSectionItem")
        contactNameItem = Contacts.ContactName("contactNameItem")
        streetAddressItem = Contacts.StreetAddress("streetAddressItem")
        phoneNumberItem = Contacts.PhoneNumber("phoneNumberItem")

        # Double check kinds
        self.assertEqual(contactItem.kind, Contacts.ContactKind)
        self.assertEqual(contactSectionItem.kind, Contacts.ContactSectionKind)
        self.assertEqual(contactNameItem.kind, Contacts.ContactNameKind)
        self.assertEqual(streetAddressItem.kind, Contacts.StreetAddressKind)
        self.assertEqual(phoneNumberItem.kind, Contacts.PhoneNumberKind)

        # Literal properties
        contactNameItem.firstName = "Sylvia"
        contactNameItem.lastName = "Plath"

        _verifyContactName(contactNameItem)

        self._reopenRepository()

        contentItemParent = self.rep.find("//userdata/contentitems")
        
        contactNameItem = contentItemParent.find("contactNameItem")
        _verifyContactName(contactNameItem)
        

if __name__ == "__main__":
    unittest.main()
