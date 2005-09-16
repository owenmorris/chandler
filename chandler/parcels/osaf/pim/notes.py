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
from i18n import OSAFMessageFactory as _

class Note(items.ContentItem):

    ##
    ## Attribute declarations
    ##

    # ensure that the displayName carries over
    schema.kindInfo(displayName=_(u"Note"))

    # temporarily make this a real attribute instead of a redirection,
    # because we don't want to redirect this anywhere
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

    """
    These "getAny" methods are used for Mixin attribute initialization.
    After stamping, we'd like to initialize attributes, like subject,
    with the "about" value defined by the rest of the classes in the item.
    But we can't just access the "about" attribute, because we've already
    stamped the item with our mixin and have applied our "about" attribute
    definition.  So getAnyXXX gets any significant defined value in any
    of the xxx attributes so we can initialize our own attribute
    appropriately. See initMixin above for an example usage.

    It's unclear if we really need this mechanism in the long run, because
    we may end up with one "to" field instead of separate "participants",
    "requestees", etc.
    """

    def getAnyAbout (self):
        """
        Get any non-empty definition for the "about" attribute.
        """
        return self.displayName

    def ExportItemData(self, clipboardHandler):
        # Create data for this kind of item in the clipboard handler
        # The data is used for Drag and Drop or Cut and Paste
        super(Note, self).ExportItemData (clipboardHandler)

        # Let the clipboard handler know we've got a Note to export
        clipboardHandler.ExportItemFormat(self, 'Note')

