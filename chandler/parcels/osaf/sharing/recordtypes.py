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


text20 = sharing.TextType("http://osafoundation.org/xyzzy/text20", size=20)
text256 = sharing.TextType("http://osafoundation.org/xyzzy/text256", size=256)
text1024 = sharing.TextType("http://osafoundation.org/xyzzy/text1024",
    size=1024)

class ItemRecord(sharing.Record):
    URI = "http://osafoundation.org/eimml/item/"

    uuid = sharing.key(schema.UUID)
    title = sharing.field(text256)
    triage_status = sharing.field(text256)
    triage_status_changed = sharing.field(sharing.DecimalType(digits=11,
        decimal_places=2))
    last_modified_by = sharing.field(text256) # storing an email address
    created_on = sharing.field(sharing.DateType)

class NoteRecord(sharing.Record):
    URI = "http://osafoundation.org/eimml/note/"

    uuid = sharing.key(ItemRecord.uuid)
    body = sharing.field(sharing.LobType())
    icaluid = sharing.field(text256)

class TaskRecord(sharing.Record):
    URI = "http://osafoundation.org/eimml/task/"

    uuid = sharing.key(ItemRecord.uuid)

class EventRecord(sharing.Record):
    URI = "http://osafoundation.org/eimml/event/"

    uuid = sharing.key(ItemRecord.uuid)
    dtstart = sharing.field(text20)
    dtend = sharing.field(text20)
    location = sharing.field(text256)
    rrule = sharing.field(text1024)
    exrule = sharing.field(text1024)
    rdate = sharing.field(text1024)
    exdate = sharing.field(text1024)
    recurrenceid = sharing.field(text20)
    status = sharing.field(text256)
    # anyTime -- may need for Apple iCal?
    # allDay


class MailMessageRecord(sharing.Record):
    URI = "http://osafoundation.org/eimml/mail/"

    uuid = sharing.key(ItemRecord.uuid)
    subject = sharing.field(text256)
    to = sharing.field(text256)
    cc = sharing.field(text256)
    bcc = sharing.field(text256)
    # other headers?

