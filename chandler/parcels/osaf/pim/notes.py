#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

from osaf.pim import items
from osaf.pim.stamping import Stamp
from application import schema
from chandlerdb.util.c import Empty

class Note(items.ContentItem):

    icalUID = schema.One(
        schema.Text,
        doc="iCalendar uses arbitrary strings for UIDs, not UUIDs.  We can "
            "set UID to a string representation of UUID, but we need to be "
            "able to import iCalendar events with arbitrary UIDs."
    )
    
    icalendarProperties = schema.Mapping(
        schema.Text,
        defaultValue=Empty,
        doc="Original icalendar property name/value pairs not understood "
            "by Chandler.  Subcomponents (notably VALARMS) aren't stored."
    )

    icalendarParameters = schema.Mapping(
        schema.Text,
        defaultValue=Empty,
        doc="property name/parameter pairs for parameters not understood by "
            "Chandler.  The parameter value is the concatenation of "
            "paramater key/value pairs, separated by semi-colons, like the "
            "iCalendar serialization of those parameters"
    )



    schema.addClouds(
        sharing = schema.Cloud(
            literal = [icalUID],
        )
    )
    
    schema.initialValues(
        icalUID=lambda self: unicode(self.itsUUID)
    )

    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """

        super(Note, self).InitOutgoingAttributes ()
        self.processingStatus = 'processing'

    def ExportItemData(self, clipboardHandler):
        # Create data for this kind of item in the clipboard handler
        # The data is used for Drag and Drop or Cut and Paste
        super(Note, self).ExportItemData (clipboardHandler)

        # Let the clipboard handler know we've got a Note to export
        clipboardHandler.ExportItemFormat(self, 'Note')
        
    def addDisplayDates(self, dates, now):
        super(Note, self).addDisplayDates(dates, now)
        
        for stampObject in Stamp(self).stamps:
            method = getattr(stampObject, 'addDisplayDates', lambda _,__: None)
            method(dates, now)

    def addDisplayWhos(self, whos):
        super(Note, self).addDisplayWhos(whos)
        
        for stampObject in Stamp(self).stamps:
            method = getattr(stampObject, 'addDisplayWhos', lambda _: None)
            method(whos)
        
        from osaf.pim.mail import CommunicationStatus
        CommunicationStatus(self).addDisplayWhos(whos)

