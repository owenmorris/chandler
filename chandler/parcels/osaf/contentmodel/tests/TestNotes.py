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

        def _verifyKinds(note, bookmark, document):
            self.assertEqual(note.title, "sample note")
            self.assertEqual(note.body, "more elaborate sample note body")

            self.assertEqual(bookmark.name, "sample bookmark")
            self.assertEqual(bookmark.url, "http://www.osafoundation.org/")

            self.assertEqual(document.name, "sample document")
            self.assertEqual(document.filePath,
                             "c:/somedirectory/somefile.txt")

        # Test the globals
        notesPath = '//parcels/OSAF/contentmodel/notes/%s'

        self.assertEqual(Notes.NoteKind,
                         self.rep.find(notesPath % 'Note'))
        self.assertEqual(Notes.BookmarkKind,
                         self.rep.find(notesPath % 'Bookmark'))
        self.assertEqual(Notes.DocumentKind,
                         self.rep.find(notesPath % 'Document'))

        # Construct sample items
        noteItem = Notes.Note("noteItem")
        bookmarkItem = Notes.Bookmark("bookmarkItem")
        documentItem = Notes.Document("documentItem")

        # Double check kinds
        self.assertEqual(noteItem.kind, Notes.NoteKind)
        self.assertEqual(bookmarkItem.kind, Notes.BookmarkKind)
        self.assertEqual(documentItem.kind, Notes.DocumentKind)

        # Literal properties
        noteItem.title = "sample note"
        noteItem.body = "more elaborate sample note body"

        bookmarkItem.name = "sample bookmark"
        bookmarkItem.url = "http://www.osafoundation.org/"
        
        documentItem.name = "sample document"
        documentItem.filePath = "c:/somedirectory/somefile.txt"

        _verifyKinds(noteItem, bookmarkItem, documentItem)

        self._reopenRepository()

        contentItemParent = self.rep.find("//userdata/contentitems")
        
        noteItem = contentItemParent.find("noteItem")
        bookmarkItem = contentItemParent.find("bookmarkItem")
        documentItem = contentItemParent.find("documentItem")
        
        _verifyKinds(noteItem, bookmarkItem, documentItem)
        

if __name__ == "__main__":
    unittest.main()
