"""
Unit tests for notes parcel
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import OSAF.contentmodel.tests.TestContentModel as TestContentModel
import OSAF.contentmodel.notes.Notes as Notes

import mx.DateTime as DateTime

class NotesTest(TestContentModel.ContentModelTestCase):
    """ Test Notes Content Model """

    def testNotes(self):
        """ Simple test for creating instances of note related kinds """

        self.loadParcel("OSAF/contentmodel/notes")

        def _verifyNote(note):
            self.assertEqual(note.title, "sample note")
            self.assertEqual(note.body, "more elaborate sample note body")

        # Test the globals
        notesPath = '//parcels/OSAF/contentmodel/notes/%s'

        self.assertEqual(Notes.NotesParcel.getNoteKind(),
                         self.rep.find(notesPath % 'Note'))

        # Construct sample items
        noteItem = Notes.Note("noteItem")

        # Double check kinds
        self.assertEqual(noteItem.kind, Notes.NotesParcel.getNoteKind())

        # Literal properties
        noteItem.title = "sample note"
        noteItem.body = "more elaborate sample note body"

        _verifyNote(noteItem)

        self._reopenRepository()

        contentItemParent = self.rep.find("//userdata/contentitems")
        
        noteItem = contentItemParent.find("noteItem")
        
        _verifyNote(noteItem)
        

if __name__ == "__main__":
    unittest.main()
