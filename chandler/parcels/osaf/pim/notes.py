""" Classes used for notes parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.pim"

import application
import repository.item.Item as Item
from osaf.pim import items
from application import schema

class Note(items.ContentItem):

    ##
    ## Attribute declarations
    ##

    # ensure that the displayName carries over
    schema.kindInfo(displayName="Note")

    # temporarily make this a real attribute instead of a redirection,
    # because we want don't want to redirect this anywhere
    who = schema.One(
        schema.String,
        initialValue = ""
    )

    # redirections
    about = schema.One(redirectTo = "displayName")

    date = schema.One(redirectTo = "createdOn")


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

