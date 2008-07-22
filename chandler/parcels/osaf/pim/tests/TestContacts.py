#   Copyright (c) 2003-2008 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""
Unit tests for contacts
"""

import unittest, os

import osaf.pim.tests.TestDomainModel as TestDomainModel
from osaf.pim.contacts import Contact, ContactName

from chandlerdb.util.Path import Path
from i18n.tests import uw


class ContactsTest(TestDomainModel.DomainModelTestCase):
    """ Test Contacts Domain Model """

    def testContacts(self):
        """ Simple test for creating instances of contact related kinds """

        self.loadParcel("osaf.pim.contacts")
        def _verifyContactName(name):
            self.assertEqual(name.firstName, uw('Sylvia'))
            self.assertEqual(name.lastName, uw('Plath'))

        # Test the globals
        contactsPath = Path('//parcels/osaf/pim/contacts')
        view = self.view

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
        contactNameItem.firstName = uw("Sylvia")
        contactNameItem.lastName = uw("Plath")

        _verifyContactName(contactNameItem)

        self._reopenRepository()
        view = self.view

        contentItemParent = view.findPath("//userdata")

        contactNameItem = contentItemParent.getItemChild("contactNameItem")
        _verifyContactName(contactNameItem)

if __name__ == "__main__":
    unittest.main()
