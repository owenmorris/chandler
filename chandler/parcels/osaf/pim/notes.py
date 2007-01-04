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
from osaf.pim.stamping import Stamp
from application import schema
from i18n import ChandlerMessageFactory as _

class Note(items.ContentItem):

    icalUID = schema.One(
        schema.Text,
        doc="iCalendar uses arbitrary strings for UIDs, not UUIDs.  We can "
            "set UID to a string representation of UUID, but we need to be "
            "able to import iCalendar events with arbitrary UIDs."
    )

    schema.addClouds(
        sharing = schema.Cloud(
            literal = [icalUID],
        )
    )

    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(Note, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        self.processingStatus = 'processing'

    def ExportItemData(self, clipboardHandler):
        # Create data for this kind of item in the clipboard handler
        # The data is used for Drag and Drop or Cut and Paste
        super(Note, self).ExportItemData (clipboardHandler)

        # Let the clipboard handler know we've got a Note to export
        clipboardHandler.ExportItemFormat(self, 'Note')
        
    def addDisplayDates(self, dates):
        super(Note, self).addDisplayDates(dates)
        
        for stampObject in Stamp(self).stamps:
            method = getattr(stampObject, 'addDisplayDates', lambda _: None)
            method(dates)

    def addDisplayWhos(self, whos):
        super(Note, self).addDisplayWhos(whos)
        
        for stampObject in Stamp(self).stamps:
            method = getattr(stampObject, 'addDisplayWhos', lambda _: None)
            method(whos)
