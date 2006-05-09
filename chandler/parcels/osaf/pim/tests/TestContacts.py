"""
Unit tests for contacts
"""

__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.pim.tests.TestContentModel as TestContentModel
import osaf.pim.generate as generate
from osaf.pim.contacts import Contact, ContactName

from repository.util.Path import Path


class ContactsTest(TestContentModel.ContentModelTestCase):
    """ Test Contacts Content Model """

    def testContacts(self):
        """ Simple test for creating instances of contact related kinds """

        self.loadParcel("osaf.pim.contacts")
        def _verifyContactName(name):
            self.assertEqual(name.firstName, u'\u00FCSylvia')
            self.assertEqual(name.getAttributeValue('firstName'),u'\u00FCSylvia')
            self.assertEqual(name.lastName, u'\u00FCPlath')
            self.assertEqual(name.getAttributeValue('lastName'), u'\u00FCPlath')

        # Test the globals
        contactsPath = Path('//parcels/osaf/pim/contacts')
        view = self.rep.view
        
        self.assertEqual(Contact.getKind(view),
                         view.find(Path(contactsPath, 'Contact')))
        self.assertEqual(ContactName.getKind(view),
                         view.find(Path(contactsPath, 'ContactName')))

        # Construct sample items
        contactItem = Contact("contactItem", itsView=view)
        contactNameItem = ContactName("contactNameItem", itsView=view)

        # Double check kinds
        self.assertEqual(contactItem.itsKind, Contact.getKind(view))
        self.assertEqual(contactNameItem.itsKind, ContactName.getKind(view))

        # Literal properties
        contactNameItem.firstName = u"\u00FCSylvia"
        contactNameItem.lastName = u"\u00FCPlath"

        _verifyContactName(contactNameItem)

        self._reopenRepository()
        view = self.rep.view

        contentItemParent = view.findPath("//userdata")

        contactNameItem = contentItemParent.getItemChild("contactNameItem")
        _verifyContactName(contactNameItem)
        
    def testGeneratedContacts(self):

        self.loadParcels(["osaf.pim.contacts", "osaf.pim.mail"])

        view = self.rep.view
        generate.GenerateItems(view, 100, generate.GenerateContact)
        view.commit()
        

if __name__ == "__main__":
    unittest.main()
