"""
Unit tests for notes parcel
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.Notes as Notes
import osaf.contentmodel.ContentModel as ContentModel

import mx.DateTime as DateTime

from repository.util.Path import Path


class NotesTest(TestContentModel.ContentModelTestCase):
    """ Test Notes Content Model """

    def testNotes(self):
        """ Simple test for creating instances of note related kinds """

        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel")

        def _verifyNote(note):
            self.assertEqual(note.displayName, "sample note")

            reader = note.body.getReader()
            self.assertEqual(reader.read(),
                             "more elaborate sample note body")
            reader.close()

        # Test the globals
        notesPath = Path('//parcels/osaf/contentmodel')

        self.assertEqual(Notes.Note.getKind(),
                         self.rep.find(Path(notesPath, 'Note')))

        # Construct sample items
        noteItem = Notes.Note("noteItem")

        # Double check kinds
        self.assertEqual(noteItem.itsKind, Notes.Note.getKind())

        # Literal properties
        noteItem.displayName = "sample note"

        # Lob property
        lobType = noteItem.getAttributeAspect('body', 'type')

        # when data is unicode, encoding defaults to utf-8
        noteItem.body = lobType.makeValue(u"more elaborate sample note body")

        _verifyNote(noteItem)

        self._reopenRepository()

        contentItemParent = self.rep.findPath("//userdata/contentitems")
        
        noteItem = contentItemParent.getItemChild("noteItem")
        
        _verifyNote(noteItem)
        

if __name__ == "__main__":
    unittest.main()
