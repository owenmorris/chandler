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

            reader = note.body.getReader()
            self.assertEqual(reader.read(),
                             "more elaborate sample note body")
            reader.close()

        # Test the globals
        notesPath = '//parcels/OSAF/contentmodel/notes/%s'

        self.assertEqual(Notes.NotesParcel.getNoteKind(),
                         self.rep.find(notesPath % 'Note'))
        self.assertEqual(Notes.NotesParcel.getConversationKind(),
                         self.rep.find(notesPath % 'Conversation'))

        # Construct sample items
        noteItem = Notes.Note("noteItem")
        conversationItem = Notes.Conversation("conversationItem")

        # Double check kinds
        self.assertEqual(noteItem.itsKind, Notes.NotesParcel.getNoteKind())
        self.assertEqual(conversationItem.itsKind,
                         Notes.NotesParcel.getConversationKind())

        # Literal properties
        noteItem.title = "sample note"

        # Text property
        textType = self.rep.find("//Schema/Core/Text")
        noteItem.body = textType.makeValue("more elaborate sample note body")

        _verifyNote(noteItem)

        self._reopenRepository()

        contentItemParent = self.rep.find("//userdata/contentitems")
        
        noteItem = contentItemParent.find("noteItem")
        conversationItem = contentItemParent.find("conversationItem")
        
        _verifyNote(noteItem)
        

if __name__ == "__main__":
    unittest.main()
