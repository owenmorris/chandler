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

# TODO: Missing attribute, "error" (dump/reload only)
# TODO: Missing attribute, "read" (dump/reload only)

text20 = eim.TextType(size=20)
text256 = eim.TextType(size=256)
text512 = eim.TextType(size=512)
text1024 = eim.TextType(size=1024)

aliasableUUID = eim.subtype(eim.UUIDType, size=256)




# pim items -------------------------------------------------------------------

triageFilter = eim.Filter('cid:triage-filter@osaf.us', u"Triage Status")

needsReplyFilter = eim.Filter('cid:needs-reply-filter@osaf.us', u"Needs Reply")

eventStatusFilter = eim.Filter('cid:event-status-filter@osaf.us',
    u"Event Status")

remindersFilter = eim.Filter('cid:reminders-filter@osaf.us', u"Reminders")

nonStandardICalendarFilter = eim.Filter('cid:non-standard-ical-filter@osaf.us',
    u"Non-standard iCalendar values")

# MailStamp Filters
bccFilter = eim.Filter('cid:bcc-filter@osaf.us', u"Bcc Addresses")
headersFilter = eim.Filter('cid:headers-filter@osaf.us', u"Mail Headers")
dateSentFilter = eim.Filter('cid:dateSent-filter@osaf.us', u"Date Sent")
messageIdFilter = eim.Filter('cid:messageId-filter@osaf.us', u"MessageId")
inReplyToFilter = eim.Filter('cid:inReplyTo-filter@osaf.us', u"InReplyTo")
referencesFilter = eim.Filter('cid:references-filter@osaf.us', u"InReplyTo")


class ItemRecord(eim.Record):
    URI = "http://osafoundation.org/eim/item/0"

    uuid = eim.key(aliasableUUID)

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

    uuid = eim.key(ItemRecord.uuid)

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

    # Note.icalendarProperties
    icalProperties = eim.field(text1024, [nonStandardICalendarFilter])

    # Note.icalendarParameters
    icalParameters = eim.field(text1024, [nonStandardICalendarFilter])


class TaskRecord(eim.Record):
    URI = "http://osafoundation.org/eim/task/0"

    uuid = eim.key(ItemRecord.uuid)

    # Task stamp has no shared attributes, so nothing is shared other than the
    # fact that an item is stamped as a task or not

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

class DisplayAlarmRecord(eim.Record):
    URI = "http://osafoundation.org/eim/displayAlarm/0"

    uuid = eim.key(ItemRecord.uuid)
    description = eim.field(text1024, [remindersFilter])
    trigger = eim.field(text1024, [remindersFilter])
    duration = eim.field(text1024, [remindersFilter])
    repeat = eim.field(eim.IntType, [remindersFilter])

class MailMessageRecord(eim.Record):
    URI = "http://osafoundation.org/eim/mail/0"

    uuid = eim.key(ItemRecord.uuid)
    messageId = eim.field(text256, [messageIdFilter])
    headers = eim.field(eim.ClobType, [headersFilter])
    # Will contain the RFC 822 from address
    fromAddress = eim.field(text256)
    toAddress = eim.field(text1024)
    ccAddress = eim.field(text1024)
    bccAddress = eim.field(text1024, [bccFilter])

    # Can contain text or email addresses ie. from The Management Team
    originators = eim.field(text1024)

    # date sent is populated by MailStamp.dateSentString
    dateSent = eim.field(text256, [dateSentFilter])

    inReplyTo = eim.field(text256, [inReplyToFilter])

    #The list of message-id's a mail message references
    # can be quite long and can easily exceed 1024 characters
    references = eim.field(eim.ClobType, [referencesFilter])


# collection ------------------------------------------------------------------

class CollectionRecord(eim.Record):
    URI = "http://osafoundation.org/eim/pim/collection/0"

    uuid = eim.key(ItemRecord.uuid)
    mine = eim.field(eim.IntType)
    
    # We represent color as 4 values instead of 1 integer since eim.IntType is signed
    # and so far it doesn't seem worth adding a new type for color
    colorRed = eim.key(eim.IntType)
    colorGreen = eim.key(eim.IntType)
    colorBlue = eim.key(eim.IntType)
    colorAlpha = eim.key(eim.IntType)

class CollectionMembershipRecord(eim.Record):
    # A membership record for a collection that is not "out of the box"
    # i.e. created by the user
    URI = "http://osafoundation.org/eim/pim/collectionmembership/0"

    collectionUUID = eim.key(schema.UUID)
    itemUUID = eim.key(aliasableUUID)
    index = eim.key(eim.IntType)

# osaf.sharing ----------------------------------------------------------------


class ShareRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/share/0"

    uuid = eim.key(ItemRecord.uuid)

    contents = eim.field(schema.UUID)
    conduit = eim.field(schema.UUID)
    subscribed = eim.field(eim.IntType)
    error = eim.field(text1024)
    mode = eim.field(text20)
    lastSynced = eim.field(eim.DecimalType(digits=20, decimal_places=0))

class ShareConduitRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/conduit/0"

    uuid = eim.key(ItemRecord.uuid)
    path = eim.field(text1024)
    name = eim.field(text1024)

class ShareRecordSetConduitRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/rsconduit/0"

    uuid = eim.key(ItemRecord.uuid)
    translator = eim.field(text1024)
    serializer = eim.field(text1024)
    filters = eim.field(text1024)


class ShareHTTPConduitRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/httpconduit/0"

    uuid = eim.key(ItemRecord.uuid)
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

    uuid = eim.key(ItemRecord.uuid)
    morsecodepath = eim.field(text1024) # only if account is None

class ShareWebDAVConduitRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/webdavconduit/0"

    uuid = eim.key(ItemRecord.uuid)

class ShareStateRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/sharestate/0"

    uuid = eim.key(ItemRecord.uuid)
    peer = eim.field(schema.UUID)
    peerrepo = eim.field(text1024)
    peerversion = eim.field(eim.IntType)
    share = eim.field(schema.UUID)
    item = eim.field(text1024)
    agreed = eim.field(eim.BlobType)
    pending = eim.field(eim.BlobType)

class ShareResourceStateRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/resourcesharestate/0"

    uuid = eim.key(ItemRecord.uuid)
    path = eim.field(text1024)
    etag = eim.field(text1024)


class ShareAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/account/0"

    uuid = eim.key(ItemRecord.uuid)
    host = eim.field(text256)
    port = eim.field(eim.IntType)
    ssl = eim.field(eim.IntType)
    path = eim.field(text1024)
    username = eim.field(text256)
    password = eim.field(text256)

class ShareWebDAVAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/webdavaccount/0"

    uuid = eim.key(ItemRecord.uuid)

class ShareCosmoAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/cosmoaccount/0"

    uuid = eim.key(ItemRecord.uuid)
    pimpath = eim.field(text1024) # pim/collection
    morsecodepath = eim.field(text1024) # mc/collection
    davpath = eim.field(text1024) # dav/collection

# preferences ----------------------------------------------------------------

class PrefCalendarHourHeightRecord(eim.Record):
    URI = "http://osafoundation.org/eim/preferences/calendarhourheight/0"

    uuid = eim.key(ItemRecord.uuid)
    hourHeightMode = eim.field(text20)
    visibleHours = eim.key(eim.IntType)
    
class PrefTimezonesRecord(eim.Record):
    URI = "http://osafoundation.org/eim/preferences/timezones/0"

    uuid = eim.key(ItemRecord.uuid)
    showUI = eim.key(eim.IntType)
    showPrompt = eim.key(eim.IntType)
    default = eim.field(text256)
    wellKnownIDs = eim.field(text1024)
    