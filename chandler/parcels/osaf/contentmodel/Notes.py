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

class Note(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = ContentModel.ContentModel.getNoteKind()
        super (Note, self).__init__(name, parent, kind)

        self.aboutAttribute = "title"

class Conversation(ContentModel.ContentItem):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = ContentModel.ContentModel.getConversationKind()
        super (Conversation, self).__init__(name, parent, kind)





