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

# TODO: MailMessage


text20 = sharing.TextType(size=20)
text256 = sharing.TextType(size=256)
text1024 = sharing.TextType(size=1024)


triageFilter = sharing.Filter('cid:triage-filter@osaf.us', u"Triage Status")

eventStatusFilter = sharing.Filter('cid:event-status-filter@osaf.us',
    u"Event Status")

remindersFilter = sharing.Filter('cid:reminders-filter@osaf.us', u"Reminders")





class CollectionRecord(sharing.Record):
    URI = "http://osafoundation.org/eim/collection"

    uuid = sharing.key(schema.UUID)





class ItemRecord(sharing.Record):
    URI = "http://osafoundation.org/eim/item"

    uuid = sharing.key(schema.UUID)
    title = sharing.field(text256)
    triageStatus = sharing.field(text256, [triageFilter])
    triageStatusChanged = sharing.field(sharing.DecimalType(digits=11,
        decimal_places=2), [triageFilter])
    lastModifiedBy = sharing.field(text256) # storing an email address
    createdOn = sharing.field(sharing.TimestampType)

class NoteRecord(sharing.Record):
    URI = "http://osafoundation.org/eim/note"

    uuid = sharing.key(ItemRecord.uuid)
    body = sharing.field(sharing.ClobType)
    icaluid = sharing.field(text256)

class TaskRecord(sharing.Record):
    URI = "http://osafoundation.org/eim/task"

    uuid = sharing.key(ItemRecord.uuid)

class EventRecord(sharing.Record):
    URI = "http://osafoundation.org/eim/event"

    uuid = sharing.key(ItemRecord.uuid)
    dtstart = sharing.field(text20)
    dtend = sharing.field(text20)
    location = sharing.field(text256)
    rrule = sharing.field(text1024)
    exrule = sharing.field(text1024)
    rdate = sharing.field(text1024)
    exdate = sharing.field(text1024)
    recurrenceid = sharing.field(text20)
    status = sharing.field(text256, [eventStatusFilter])

    # anyTime -- may need for Apple iCal?
    # allDay


class ICalExtensionRecord(sharing.Record):
    URI = "http://osafoundation.org/eim/icalext"

    uuid = sharing.key(ItemRecord.uuid)
    name = sharing.key(text256)
    value = sharing.field(text1024)



class MailMessageRecord(sharing.Record):
    URI = "http://osafoundation.org/eim/mail"

    uuid = sharing.key(ItemRecord.uuid)
    subject = sharing.field(text256)
    to = sharing.field(text256)
    cc = sharing.field(text256)
    bcc = sharing.field(text256)
    # other headers?

