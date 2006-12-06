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
from osaf import sharing
from application import schema
import logging
logger = logging.getLogger(__name__)

# These may eventually live elsewhere, but checking them in here so we can
# collaborate on them

# We need to specify URIs for each of these record types:

class ItemRecord(sharing.Record):
    uuid = sharing.key(schema.UUID)
    title = sharing.field(sharing.TextType(size=256))
    triage_status = sharing.field(sharing.TextType(size=256))
    triage_status_changed = sharing.field(sharing.DecimalType(digits=11,
        decimal_places=2))
    last_modified_by = sharing.field(sharing.TextType(size=256)) # storing an email address
    created_on = sharing.field(sharing.DateType)

class NoteRecord(sharing.Record):
    uuid = sharing.key(schema.UUID)
    body = sharing.field(sharing.LobType())
    icaluid = sharing.field(sharing.TextType(size=256))

class TaskRecord(sharing.Record):
    uuid = sharing.key(schema.UUID)

class EventRecord(sharing.Record):
    uuid = sharing.key(schema.UUID)
    dtstart = sharing.field(sharing.TextType(size=20))
    dtend = sharing.field(sharing.TextType(size=20))
    location = sharing.field(sharing.TextType(size=256))
    rrule = sharing.field(sharing.TextType(size=1024))
    exrule = sharing.field(sharing.TextType(size=1024))
    rdate = sharing.field(sharing.TextType(size=1024))
    exdate = sharing.field(sharing.TextType(size=1024))
    recurrenceid = sharing.field(sharing.TextType(size=20))
    status = sharing.field(sharing.TextType(size=256))
    # anyTime -- may need for Apple iCal?
    # allDay


class MailMessageRecord(sharing.Record):
    uuid = sharing.key(schema.UUID)
    subject = sharing.field(sharing.TextType(size=256))
    to = sharing.field(sharing.TextType(size=256))
    cc = sharing.field(sharing.TextType(size=256))
    bcc = sharing.field(sharing.TextType(size=256))
    # other headers?

