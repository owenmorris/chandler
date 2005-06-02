""" Classes used for Notes parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import repository.item.Item as Item
import osaf.contentmodel.ContentModel as ContentModel

class Note(ContentModel.ContentItem):

    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/Note"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super (Note, self).__init__(name, parent, kind, view)

    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(Note, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        self.processingStatus = 'processing'

    def getAnyAbout (self):
        """
        Get any non-empty definition for the "about" attribute.
        """
        return self.displayName

    def getAnyDate (self):
        """
        Get any non-empty definition for the "date" attribute.
        """
        return self.createdOn

    def getAnyWho (self):
        """
        Get any non-empty definition for the "who" attribute.
        """
        raise AttributeError

    def getAnyWhoFrom (self):
        """
        Get any non-empty definition for the "whoFrom" attribute.
        """
        return self.creator

    def ExportItemData(self, clipboardHandler):
        # Create data for this kind of item in the clipboard handler
        # The data is used for Drag and Drop or Cut and Paste
        super(Note, self).ExportItemData (clipboardHandler)

        # Let the clipboard handler know we've got a Note to export
        clipboardHandler.ExportItemFormat(self, 'Note')

