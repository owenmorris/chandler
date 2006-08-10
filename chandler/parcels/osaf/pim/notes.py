#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


""" Classes used for notes parcel kinds
"""

__parcel__ = "osaf.pim"

import application
import repository.item.Item as Item
from osaf.pim import items
from application import schema
from i18n import ChandlerMessageFactory as _

class Note(items.ContentItem):

    ##
    ## Attribute declarations
    ##

    # temporarily make this a real attribute instead of a redirection,
    # because we don't want to redirect this anywhere
    who = schema.One(
        schema.Text,
        initialValue = u"",
        indexed = True,
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

