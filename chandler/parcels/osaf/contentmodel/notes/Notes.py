""" Classes used for Notes parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import repository.item.Item as Item
import osaf.contentmodel.ContentModel as ContentModel
import application.Globals as Globals

class NotesParcel(application.Parcel.Parcel):
    def startupParcel(self):
        super(NotesParcel, self).startupParcel()
        self._setUUIDs()

    def onItemLoad(self):
        super(NotesParcel, self).onItemLoad()
        self._setUUIDs()

    def _setUUIDs(self):
        noteKind = self['Note']
        NotesParcel.noteKindID = noteKind.itsUUID

        conversationKind = self['Conversation']
        NotesParcel.conversationKindID = conversationKind.itsUUID

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
        super (Note, self).__init__(name, parent, kind)

class Conversation(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = NotesParcel.getConversationKind()
        super (Conversation, self).__init__(name, parent, kind)





