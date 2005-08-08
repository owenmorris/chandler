"""
Unit tests for contacts
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.pim.tests.TestContentModel as TestContentModel
import osaf.pim.tests.GenerateItems as GenerateItems
from osaf.pim.contacts import Contact, ContactName

from repository.util.Path import Path


class ContactsTest(TestContentModel.ContentModelTestCase):
    """ Test Contacts Content Model """

    def testContacts(self):
        """ Simple test for creating instances of contact related kinds """

        self.loadParcel("parcel:osaf.pim.contacts")
        def _verifyContactName(name):
            self.assertEqual(name.firstName, 'Sylvia')
            self.assertEqual(name.getAttributeValue('firstName'),'Sylvia')
            self.assertEqual(name.lastName, 'Plath')
            self.assertEqual(name.getAttributeValue('lastName'), 'Plath')

        # Test the globals
        contactsPath = Path('//parcels/osaf/pim/contacts')
        view = self.rep.view
        
        self.assertEqual(Contact.getKind(view),
                         view.find(Path(contactsPath, 'Contact')))
        self.assertEqual(ContactName.getKind(view),
                         view.find(Path(contactsPath, 'ContactName')))

        # Construct sample items
        contactItem = Contact("contactItem", view=view)
        contactNameItem = ContactName("contactNameItem", view=view)

        # Double check kinds
        self.assertEqual(contactItem.itsKind, Contact.getKind(view))
        self.assertEqual(contactNameItem.itsKind, ContactName.getKind(view))

        # Literal properties
        contactNameItem.firstName = "Sylvia"
        contactNameItem.lastName = "Plath"

        _verifyContactName(contactNameItem)

        self._reopenRepository()

        contentItemParent = self.rep.findPath("//userdata")

        contactNameItem = contentItemParent.getItemChild("contactNameItem")
        _verifyContactName(contactNameItem)
        
    def testGeneratedContacts(self):

        self.loadParcels(["parcel:osaf.pim.contacts", "parcel:osaf.pim.mail"])

        view = self.rep.view
        GenerateItems.GenerateItems(view, 100, GenerateItems.GenerateContact)
        view.commit()
        

if __name__ == "__main__":
    unittest.main()
