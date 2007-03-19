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

import eim
from application import schema
import logging
logger = logging.getLogger(__name__)

# TODO: MailMessage (bkirsch working on this)

# TODO: Missing attribute, "error" (dump/reload only)
# TODO: Missing attribute, "read" (dump/reload only)
# TODO: Missing attribute, "needsReply" (???)
# TODO: Missing attribute, "modifiedFlags" (???)


text20 = eim.TextType(size=20)
text256 = eim.TextType(size=256)
text1024 = eim.TextType(size=1024)




# pim items -------------------------------------------------------------------

triageFilter = eim.Filter('cid:triage-filter@osaf.us', u"Triage Status")

needsReplyFilter = eim.Filter('cid:needs-reply-filter@osaf.us', u"Needs Reply")

eventStatusFilter = eim.Filter('cid:event-status-filter@osaf.us',
    u"Event Status")

remindersFilter = eim.Filter('cid:reminders-filter@osaf.us', u"Reminders")

nonStandardICalendarFilter = eim.Filter('cid:non-standard-ical-filter@osaf.us',
    u"Non-standard iCalendar values")




class ItemRecord(eim.Record):
    URI = "http://osafoundation.org/eim/item/0"

    uuid = eim.key(schema.UUID)

    # ContentItem.displayName
    title = eim.field(text1024)

    # ContentItem.[triageStatus, triageStatusChanged, doAutoTriageOnDateChange]
    triage = eim.field(text256, [triageFilter])

    # ContentItem.createdOn
    createdOn = eim.field(eim.DecimalType(digits=20, decimal_places=0))

    # ContentItem.modifiedFlags
    hasBeenSent = eim.field(eim.IntType)

    # ContentItem.needsReply
    needsReply = eim.field(eim.IntType)


class ModifiedByRecord(eim.Record):
    URI = "http://osafoundation.org/eim/modifiedBy/0"

    uuid = eim.key(schema.UUID)

    # ContentItem.lastModifiedBy
    userid = eim.key(text256)

    # ContentItem.lastModified (time)
    timestamp = eim.key(eim.DecimalType(digits=12, decimal_places=2))

    # ContentItem.lastModification (action)
    action = eim.key(eim.IntType)


class NoteRecord(eim.Record):
    URI = "http://osafoundation.org/eim/note/0"

    uuid = eim.key(ItemRecord.uuid)

    # ContentItem.body
    body = eim.field(eim.ClobType)

    # Note.icalUid
    icalUid = eim.field(text256)

    # Note.reminders?  (Translator not implemented yet)
    reminderTime = eim.field(eim.DecimalType(digits=20, decimal_places=0))



class TaskRecord(eim.Record):
    URI = "http://osafoundation.org/eim/task/0"

    uuid = eim.key(ItemRecord.uuid)

    # Task stamp has no shared attributes, so nothing is shared other than the
    # fact that an item is stamped as a task or not


class TaskModificationRecord(eim.Record):
    URI = "http://osafoundation.org/eim/taskModification/0"

    masterUuid = eim.key(ItemRecord.uuid)
    recurrenceId = eim.key(text20)



class EventRecord(eim.Record):
    URI = "http://osafoundation.org/eim/event/0"

    uuid = eim.key(ItemRecord.uuid)

    # EventStamp.[allDay, anyTime, duration, startTime]
    dtstart = eim.field(text20)
    duration = eim.field(text20)

    # EventStamp.location
    location = eim.field(text256)

    # EventStamp.[recurrenceID, rruleset, etc.]
    rrule = eim.field(text1024)
    exrule = eim.field(text1024)
    rdate = eim.field(text1024)
    exdate = eim.field(text1024)

    # EventStamp.transparency
    status = eim.field(text256, [eventStatusFilter])

    # Note.icalendarParameters
    icalParameters = eim.field(text1024, [nonStandardICalendarFilter])

    # Note.icalendarProperties
    icalProperties = eim.field(text1024, [nonStandardICalendarFilter])




class EventModificationRecord(eim.Record):
    URI = "http://osafoundation.org/eim/eventModification/0"

    masterUuid = eim.field(ItemRecord.uuid)
    recurrenceId = eim.key(text20)
    dtstart = eim.field(text20)
    duration = eim.field(text20)
    location = eim.field(text256)
    status = eim.field(text256, [eventStatusFilter])
    title = eim.field(text256)
    body = eim.field(eim.ClobType)
    triage = eim.field(text256, [triageFilter])
    reminderTime = eim.field(eim.DecimalType(digits=20, decimal_places=0))
    icalParameters = eim.field(text1024, [nonStandardICalendarFilter])
    icalProperties = eim.field(text1024, [nonStandardICalendarFilter])






class DisplayAlarmRecord(eim.Record):
    URI = "http://osafoundation.org/eim/displayAlarm/0"

    uuid = eim.key(ItemRecord.uuid)
    description = eim.field(text1024)
    trigger = eim.field(text1024)
    duration = eim.field(text1024)
    repeat = eim.field(eim.IntType)




class MailMessageRecord(eim.Record):
    URI = "http://osafoundation.org/eim/mail/0"

    uuid = eim.key(ItemRecord.uuid)
    subject = eim.field(text256)
    to = eim.field(text256)
    cc = eim.field(text256)
    bcc = eim.field(text256)
    # other headers?






# collection ------------------------------------------------------------------

class CollectionRecord(eim.Record):
    URI = "http://osafoundation.org/eim/pim/collection/0"

    uuid = eim.key(schema.UUID)
    mine = eim.field(eim.IntType)

class CollectionMembershipRecord(eim.Record):
    URI = "http://osafoundation.org/eim/pim/collectionmembership/0"

    collection = eim.key(schema.UUID)
    item = eim.key(schema.UUID)


# osaf.sharing ----------------------------------------------------------------


class ShareRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/share/0"

    uuid = eim.key(schema.UUID)

    contents = eim.field(schema.UUID)
    conduit = eim.field(schema.UUID)
    subscribed = eim.field(eim.IntType)
    error = eim.field(text1024)
    mode = eim.field(text20)
    lastSynced = eim.field(eim.DecimalType(digits=20, decimal_places=0))

class ShareConduitRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/conduit/0"

    uuid = eim.key(schema.UUID)
    path = eim.field(text1024)
    name = eim.field(text1024)

class ShareRecordSetConduitRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/rsconduit/0"

    uuid = eim.key(schema.UUID)
    translator = eim.field(text1024)
    serializer = eim.field(text1024)
    filters = eim.field(text1024)


class ShareHTTPConduitRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/httpconduit/0"

    uuid = eim.key(schema.UUID)
    url = eim.field(text1024)
    ticket_rw = eim.field(text1024)
    ticket_ro = eim.field(text1024)

    account = eim.field(schema.UUID) # if provided, the following are ignored
    host = eim.field(text256)
    port = eim.field(eim.IntType)
    ssl = eim.field(eim.IntType)
    username = eim.field(text256)
    password = eim.field(text256)

class ShareCosmoConduitRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/cosmoconduit/0"

    uuid = eim.key(schema.UUID)
    morsecodepath = eim.field(text1024) # only if account is None

class ShareWebDAVConduitRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/webdavconduit/0"

    uuid = eim.key(schema.UUID)

class ShareStateRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/sharestate/0"

    uuid = eim.key(schema.UUID)
    peer = eim.field(schema.UUID)
    peerrepo = eim.field(text1024)
    peerversion = eim.field(eim.IntType)
    share = eim.field(schema.UUID)
    item = eim.field(text1024)
    agreed = eim.field(eim.BlobType)
    pending = eim.field(eim.BlobType)

class ShareResourceStateRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/resourcesharestate/0"

    uuid = eim.key(schema.UUID)
    path = eim.field(text1024)
    etag = eim.field(text1024)


class ShareAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/account/0"

    uuid = eim.key(schema.UUID)
    host = eim.field(text256)
    port = eim.field(eim.IntType)
    ssl = eim.field(eim.IntType)
    path = eim.field(text1024)
    username = eim.field(text256)
    password = eim.field(text256)

class ShareWebDAVAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/webdavaccount/0"

    uuid = eim.key(schema.UUID)

class ShareCosmoAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/cosmoaccount/0"

    uuid = eim.key(schema.UUID)
    pimpath = eim.field(text1024) # pim/collection
    morsecodepath = eim.field(text1024) # mc/collection
    davpath = eim.field(text1024) # dav/collection
