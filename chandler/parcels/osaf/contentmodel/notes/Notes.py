""" Classes used for Notes parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.parcel.Parcel as Parcel
import repository.item.Item as Item
import OSAF.contentmodel.ContentModel as ContentModel
import application.Globals as Globals

class NotesParcel(Parcel.Parcel):
    def __init__(self, name, parent, kind):
        Parcel.Parcel.__init__(self, name, parent, kind)

    def startupParcel(self):
        Parcel.Parcel.startupParcel(self)
        self._setUUIDs()

    def onItemLoad(self):
        Parcel.Parcel.onItemLoad(self)
        self._setUUIDs()

    def _setUUIDs(self):
        noteKind = self.find('Note')
        NotesParcel.noteKindID = noteKind.getUUID()

        conversationKind = self.find('Conversation')
        NotesParcel.conversationKindID = conversationKind.getUUID()

    def getNoteKind(cls):
        assert cls.noteKindID, "Note parcel not yet loaded"
        return Globals.repository[cls.noteKindID]

    getNoteKind = classmethod(getNoteKind)

    def getConversationKind(cls):
        assert cls.conversationKindID, "Note parcel not yet loaded"
        return Globals.repository[cls.conversationKindID]

    getConversationKind = classmethod(getConversationKind)

    noteKindID = None
    conversationKindID = None

class Note(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = NotesParcel.getNoteKind()
        ContentModel.ContentItem.__init__(self, name, parent, kind)

class Conversation(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = NotesParcel.getConversationKind()
        ContentModel.ContentItem.__init__(self, name, parent, kind)





