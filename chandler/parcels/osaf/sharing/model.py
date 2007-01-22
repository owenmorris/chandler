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

import eim
from application import schema
import logging
logger = logging.getLogger(__name__)

# TODO: MailMessage


text20 = eim.TextType(size=20)
text256 = eim.TextType(size=256)
text1024 = eim.TextType(size=1024)


triageFilter = eim.Filter('cid:triage-filter@osaf.us', u"Triage Status")

eventStatusFilter = eim.Filter('cid:event-status-filter@osaf.us',
    u"Event Status")

remindersFilter = eim.Filter('cid:reminders-filter@osaf.us', u"Reminders")


class ItemRecord(eim.Record):
    URI = "http://osafoundation.org/eim/item"

    uuid = eim.key(schema.UUID)
    title = eim.field(text256)
    triageStatus = eim.field(text256, [triageFilter])
    triageStatusChanged = eim.field(eim.DecimalType(digits=11, decimal_places=2), [triageFilter])
    lastModifiedBy = eim.field(text256) # storing an email address
    createdOn = eim.field(eim.DecimalType(digits=20, decimal_places=0))



class NoteRecord(eim.Record):
    URI = "http://osafoundation.org/eim/note"

    uuid = eim.key(ItemRecord.uuid)
    body = eim.field(eim.ClobType)
    icaluid = eim.field(text256)
    reminderTime = eim.field(eim.DecimalType(digits=20, decimal_places=0))



class TaskRecord(eim.Record):
    URI = "http://osafoundation.org/eim/task"

    uuid = eim.key(ItemRecord.uuid)



class TaskModificationRecord(eim.Record):
    URI = "http://osafoundation.org/eim/taskModification"

    masterUuid = eim.key(ItemRecord.uuid)
    recurrenceId = eim.key(text20)



class EventRecord(eim.Record):
    URI = "http://osafoundation.org/eim/event"

    uuid = eim.key(ItemRecord.uuid)
    dtstart = eim.field(text20)
    dtend = eim.field(text20)
    anytime = eim.field(eim.IntType)
    location = eim.field(text256)
    rrule = eim.field(text1024)
    exrule = eim.field(text1024)
    rdate = eim.field(text1024)
    exdate = eim.field(text1024)
    status = eim.field(text256, [eventStatusFilter])




class EventModificationRecord(eim.Record):
    URI = "http://osafoundation.org/eim/eventModification"

    masterUuid = eim.field(ItemRecord.uuid)
    recurrenceId = eim.key(text20)
    dtstart = eim.field(text20)
    dtend = eim.field(text20)
    anytime = eim.field(eim.IntType)
    location = eim.field(text256)
    status = eim.field(text256, [eventStatusFilter])
    title = eim.field(text256)
    body = eim.field(eim.ClobType)
    triageStatus = eim.field(text256, [triageFilter])
    triageStatusChanged = eim.field(eim.DecimalType(digits=11, decimal_places=2), [triageFilter])
    reminderTime = eim.field(eim.DecimalType(digits=20, decimal_places=0))






class DisplayAlarmRecord(eim.Record):
    URI = "http://osafoundation.org/eim/displayAlarm"

    uuid = eim.key(ItemRecord.uuid)
    description = eim.field(text1024)
    trigger = eim.field(text1024)
    duration = eim.field(text1024)
    repeat = eim.field(eim.IntType)




class MailMessageRecord(eim.Record):
    URI = "http://osafoundation.org/eim/mail"

    uuid = eim.key(ItemRecord.uuid)
    subject = eim.field(text256)
    to = eim.field(text256)
    cc = eim.field(text256)
    bcc = eim.field(text256)
    # other headers?



