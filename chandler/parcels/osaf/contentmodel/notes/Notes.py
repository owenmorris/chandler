""" Classes used for Notes parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.parcel.Parcel as Parcel
import repository.item.Item as Item
import OSAF.contentmodel.ContentModel as ContentModel

# Module globals for Kinds
# NoteKind ==> //parcels/OSAF/contentmodel/notes/Note
# BookmarkKind ==> //parcels/OSAF/contentmodel/notes/Bookmark
# DocumentKind ==> //parcels/OSAF/contentmodel/notes/Document

class NotesParcel(Parcel.Parcel):
    def __init__(self, name, parent, kind):
        Parcel.Parcel.__init__(self, name, parent, kind)

    def startupParcel(self):
        Parcel.Parcel.startupParcel(self)

        global NoteKind
        NoteKind = self.find('Note')
        assert NoteKind

        global BookmarkKind
        BookmarkKind = self.find('Bookmark')
        assert BookmarkKind

        global DocumentKind
        DocumentKind = self.find('Document')
        assert DocumentKind

class Note(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = NoteKind
        ContentModel.ContentItem.__init__(self, name, parent, kind)

class Bookmark(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = BookmarkKind
        ContentModel.ContentItem.__init__(self, name, parent, kind)

class Document(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = DocumentKind
        ContentModel.ContentItem.__init__(self, name, parent, kind)




