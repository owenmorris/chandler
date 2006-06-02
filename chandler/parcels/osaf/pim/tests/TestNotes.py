"""
Unit tests for notes parcel
"""

__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.pim.tests.TestDomainModel as TestDomainModel
from osaf import pim

from repository.util.Path import Path
from i18n.tests import uw


class NotesTest(TestDomainModel.DomainModelTestCase):
    """ Test Notes Domain Model """

    def testNotes(self):
        """ Simple test for creating instances of note related kinds """

        self.loadParcel("osaf.pim")

        def _verifyNote(note):
            self.assertEqual(note.displayName, uw("sample note"))
            self.assertEqual(note.getBasedAttributes('about'), ('displayName',))

            self.assertEqual(note.body,
                             uw("more elaborate sample note body"))

        # Test the globals
        notesPath = Path('//parcels/osaf/pim')
        view = self.rep.view

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
        view = self.rep.view
        contentItemParent = view.findPath("//userdata")

        noteItem = contentItemParent.getItemChild("noteItem")

        _verifyNote(noteItem)


if __name__ == "__main__":
    unittest.main()
