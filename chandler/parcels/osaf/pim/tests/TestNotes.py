"""
Unit tests for notes parcel
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.pim.tests.TestContentModel as TestContentModel
from osaf import pim

from repository.util.Path import Path


class NotesTest(TestContentModel.ContentModelTestCase):
    """ Test Notes Content Model """

    def testNotes(self):
        """ Simple test for creating instances of note related kinds """

        self.loadParcel("parcel:osaf.pim")

        def _verifyNote(note):
            self.assertEqual(note.displayName, "sample note")

            reader = note.body.getReader()
            self.assertEqual(reader.read(),
                             "more elaborate sample note body")
            reader.close()

        # Test the globals
        notesPath = Path('//parcels/osaf/pim')
        view = self.rep.view
        
        self.assertEqual(pim.Note.getKind(view),
                         view.find(Path(notesPath, 'Note')))

        # Construct sample items
        noteItem = pim.Note("noteItem", view=view)

        # Double check kinds
        self.assertEqual(noteItem.itsKind, pim.Note.getKind(view))

        # Literal properties
        noteItem.displayName = "sample note"

        # Lob property
        lobType = noteItem.getAttributeAspect('body', 'type')

        # when data is unicode, encoding defaults to utf-8
        noteItem.body = lobType.makeValue(u"more elaborate sample note body")

        _verifyNote(noteItem)

        self._reopenRepository()

        contentItemParent = self.rep.findPath("//userdata")
        
        noteItem = contentItemParent.getItemChild("noteItem")
        
        _verifyNote(noteItem)
        

if __name__ == "__main__":
    unittest.main()
