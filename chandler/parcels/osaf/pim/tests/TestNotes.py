#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
Unit tests for notes parcel
"""

import unittest, os

import osaf.pim.tests.TestDomainModel as TestDomainModel
from osaf import pim

from chandlerdb.util.Path import Path
from i18n.tests import uw


class NotesTest(TestDomainModel.DomainModelTestCase):
    """ Test Notes Domain Model """

    def testNotes(self):
        """ Simple test for creating instances of note related kinds """

        self.loadParcel("osaf.pim")

        def _verifyNote(note):
            self.assertEqual(note.displayName, uw("sample note"))

            self.assertEqual(note.body,
                             uw("more elaborate sample note body"))

        # Test the globals
        notesPath = Path('//parcels/osaf/pim')
        view = self.view

        self.assertEqual(pim.Note.getKind(view),
                         view.find(Path(notesPath, 'Note')))

        # Construct sample items
        noteItem = pim.Note("noteItem", itsView=view)

        # Double check kinds
        self.assertEqual(noteItem.itsKind, pim.Note.getKind(view))

        # Literal properties
        noteItem.displayName = uw("sample note")

        noteItem.body = uw("more elaborate sample note body")

        _verifyNote(noteItem)

        self._reopenRepository()
        view = self.view
        contentItemParent = view.findPath("//userdata")

        noteItem = contentItemParent.getItemChild("noteItem")

        _verifyNote(noteItem)


if __name__ == "__main__":
    unittest.main()
