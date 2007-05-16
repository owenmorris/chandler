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
from i18n import ChandlerMessageFactory as _
import logging
logger = logging.getLogger(__name__)


text20 = eim.TextType(size=20)
text256 = eim.TextType(size=256)
text512 = eim.TextType(size=512)
text1024 = eim.TextType(size=1024)
bytes32 = eim.BytesType(size=32)
bytes1024 = eim.BytesType(size=1024)

aliasableUUID = eim.subtype(eim.UUIDType, size=256)




# pim items -------------------------------------------------------------------

triageFilter = eim.Filter('cid:triage-filter@osaf.us', u"Triage Status")

needsReplyFilter = eim.Filter('cid:needs-reply-filter@osaf.us', u"Needs Reply")

readFilter = eim.Filter('cid:read-filter@osaf.us', u"Has Been Read")

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
mimeContentFilter = eim.Filter('cid:mimeContent-filter@osaf.us', u"MIME Content")
rfc2822MessageFilter = eim.Filter('cid:rfc2822Message-filter@osaf.us', u"rfc 2822 Message")
previousSenderFilter = eim.Filter('cid:previousSender-filter@osaf.us', u"Previous Sender")
replyToAddressFilter = eim.Filter('cid:replyToAddress-filter@osaf.us', u"ReplyTo Address")
messageStateFilter = eim.Filter('cid:messageState-filter@osaf.us', u"Message State")


class ItemRecord(eim.Record):
    URI = "http://osafoundation.org/eim/item/0"

    uuid = eim.key(aliasableUUID)

    # ContentItem.displayName
    title = eim.field(text1024, _(u"Title"))

    # ContentItem.[triageStatus, triageStatusChanged, doAutoTriageOnDateChange]
    triage = eim.field(text256, _(u"Triage status"), filters=[triageFilter])

    # ContentItem.createdOn
    createdOn = eim.field(eim.DecimalType(digits=20, decimal_places=0),
        _(u"Created on"))

    # ContentItem.modifiedFlags
    hasBeenSent = eim.field(eim.IntType, _(u"Has been sent"))

    # ContentItem.needsReply
    needsReply = eim.field(eim.IntType, _(u"Needs reply"))

    # ContentItem.read
    read = eim.field(eim.IntType, _(u"Has been read"), filters=[readFilter],
        default=0)



class ModifiedByRecord(eim.Record):
    URI = "http://osafoundation.org/eim/modifiedBy/0"

    uuid = eim.key(ItemRecord.uuid)

    # ContentItem.lastModifiedBy
    userid = eim.key(text256, _(u"User ID"))

    # ContentItem.lastModified (time)
    timestamp = eim.key(eim.DecimalType(digits=12, decimal_places=2), _(u"Last modified"))

    # ContentItem.lastModification (action)
    action = eim.key(eim.IntType, _(u"Action"))

class NoteRecord(eim.Record):
    URI = "http://osafoundation.org/eim/note/0"

    uuid = eim.key(ItemRecord.uuid)

    # ContentItem.body
    body = eim.field(eim.ClobType, _(u"Body"))

    # Note.icalUid
    icalUid = eim.field(text256, _(u"Icalendar UID"))

    # Note.icalendarProperties
    icalProperties = eim.field(text1024, filters=[nonStandardICalendarFilter])

    # Note.icalendarParameters
    icalParameters = eim.field(text1024, filters=[nonStandardICalendarFilter])


class TaskRecord(eim.Record):
    URI = "http://osafoundation.org/eim/task/0"

    uuid = eim.key(NoteRecord.uuid)

    # Task stamp has no shared attributes, so nothing is shared other than the
    # fact that an item is stamped as a task or not

class EventRecord(eim.Record):
    URI = "http://osafoundation.org/eim/event/0"

    uuid = eim.key(NoteRecord.uuid)

    # EventStamp.[allDay, anyTime, duration, startTime]
    dtstart = eim.field(text20, _(u"Start time"))
    duration = eim.field(text20, _(u"Duration"))

    # EventStamp.location
    location = eim.field(text256, _(u"Location"))

    # EventStamp.[recurrenceID, rruleset, etc.]
    rrule = eim.field(text1024)
    exrule = eim.field(text1024)
    rdate = eim.field(text1024)
    exdate = eim.field(text1024)

    # EventStamp.transparency
    status = eim.field(text256, _(u"Event status"), filters=[eventStatusFilter])




class DisplayAlarmRecord(eim.Record):
    URI = "http://osafoundation.org/eim/displayAlarm/0"

    uuid = eim.key(EventRecord.uuid)
    description = eim.field(text1024, _(u"Alarm description"), filters=[remindersFilter])
    trigger = eim.field(text1024, _(u"Alarm trigger"), filters=[remindersFilter])
    duration = eim.field(text1024, _(u"Alarm duration"), filters=[remindersFilter])
    repeat = eim.field(eim.IntType, _(u"Alarm repeat"), filters=[remindersFilter])


class MailMessageRecord(eim.Record):
    URI = "http://osafoundation.org/eim/mail/0"

    uuid = eim.key(NoteRecord.uuid)
    messageId = eim.field(text256, _(u"Message ID"), filters=[messageIdFilter])
    headers = eim.field(eim.ClobType, _(u"Message headers"), filters=[headersFilter])
    # Will contain the RFC 822 from address
    fromAddress = eim.field(text256, _(u"From:"))
    toAddress = eim.field(text1024, _(u"To:"))
    ccAddress = eim.field(text1024, _(u"CC:"))
    bccAddress = eim.field(text1024, _(u"BCC:"), filters=[bccFilter])

    # Can contain text or email addresses ie. from The Management Team
    originators = eim.field(text1024, _(u"Originators"))

    # date sent is populated by MailStamp.dateSentString
    dateSent = eim.field(text256, _(u"Date sent"), filters=[dateSentFilter])

    inReplyTo = eim.field(text256, _(u"In-Reply-To:"), filters=[inReplyToFilter])

    #The list of message-id's a mail message references
    # can be quite long and can easily exceed 1024 characters
    references = eim.field(eim.ClobType, _(u"References"), filters=[referencesFilter])

    # Values required for Dump and Reload
    mimeContent = eim.field(eim.ClobType, _(u"MIME content"), filters=[mimeContentFilter])
    rfc2822Message = eim.field(eim.ClobType, _(u"RFC2822 message"), filters=[rfc2822MessageFilter])
    previousSender = eim.field(text256, _(u"Previous sender"), filters=[previousSenderFilter])
    replyToAddress = eim.field(text256, _(u"Reply-To address"), filters=[replyToAddressFilter])

    # Contains bit wise flags indicating state.
    # A state integer was chosen over individual
    # boolean fields as a means of decoupling
    # Chandler mail specific flag requirements from
    # EIM.

    messageState = eim.field(eim.IntType, _(u"Message state"), filters=[messageStateFilter])





# From here on down, the record types are not shared with Cosmo  ----------

class PrivateItemRecord(eim.Record):
    URI = "http://osafoundation.org/eim/pim/private/0"
    uuid = eim.key(ItemRecord.uuid)


class PasswordRecord(eim.Record):
    URI = "http://osafoundation.org/eim/password/0"

    uuid = eim.key(ItemRecord.uuid)
    ciphertext = eim.field(bytes1024)
    iv = eim.field(bytes32)
    salt = eim.field(bytes32)


class PasswordPrefsRecord(eim.Record):
    URI = "http://osafoundation.org/eim/password/prefs/0"

    dummyPassword = eim.field(schema.UUID)
    masterPassword = eim.field(eim.IntType) # boolean
    timeout = eim.field(eim.IntType)


class MailAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/mailaccount/0"

    uuid = eim.key(ItemRecord.uuid)
    retries = eim.field(eim.IntType)
    username = eim.field(text256)
    host = eim.field(text256)

    # 0 = None, 1 = TLS, 2 = SSL
    connectionType = eim.field(eim.IntType)
    frequency = eim.field(eim.IntType)
    timeout = eim.field(eim.IntType)

    # 0 = Inactive 1 = Active
    active = eim.field(eim.IntType)


class IMAPAccountFoldersRecord(eim.Record):
    URI = "http://osafoundation.org/eim/pim/imapaccountfolders/0"

    imapAccountUUID = eim.key(schema.UUID)
    imapFolderUUID = eim.key(aliasableUUID)


class SMTPAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/smtpccount/0"

    uuid = eim.key(ItemRecord.uuid)
    password = eim.field(schema.UUID)
    fromAddress = eim.field(text256)
    useAuth = eim.field(eim.IntType)
    port = eim.field(eim.IntType)

    # 1 = isDefault
    isDefault = eim.field(eim.IntType)

class SMTPAccountQueueRecord(eim.Record):
    URI = "http://osafoundation.org/eim/pim/smtpaccountqueue/0"

    smtpAccountUUID = eim.key(schema.UUID)
    itemUUID = eim.key(aliasableUUID)

class IMAPAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/imapaccount/0"

    uuid = eim.key(ItemRecord.uuid)
    password = eim.field(schema.UUID)
    replyToAddress = eim.field(text256)
    port = eim.field(eim.IntType)

    # 1 = isDefault
    isDefault = eim.field(eim.IntType)


class POPAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/popaccount/0"

    uuid = eim.key(ItemRecord.uuid)
    password = eim.field(schema.UUID)
    replyToAddress = eim.field(text256)
    type = eim.field(eim.TextType(size=50))
    delete = eim.field(eim.IntType)
    downloaded = eim.field(eim.IntType)
    downloadMax = eim.field(eim.IntType)
    seenUIDS = eim.field(eim.ClobType)
    port = eim.field(eim.IntType)

    # 1 = isDefault
    isDefault = eim.field(eim.IntType)

class IMAPFolderRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/imapfolder/0"

    uuid = eim.key(ItemRecord.uuid)
    name = eim.field(text256)
    type = eim.field(eim.TextType(size=50))
    lastUID = eim.field(eim.IntType)
    delete = eim.field(eim.IntType)
    downloaded = eim.field(eim.IntType)
    downloadMax = eim.field(eim.IntType)


class MailPrefsRecord(eim.Record):
    URI = "http://osafoundation.org/eim/mail/prefs/0"

    # 1 = online
    isOnline = eim.field(eim.IntType)

    # Contains all current and old me email addresses
    # needed to calulate the MailStamp.fromMe and
    # MailStamp.toMe boolean flags
    meAddressHistory = eim.field(eim.ClobType)

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

class DashboardMembershipRecord(eim.Record):
    # A membership record for an item which is a direct member of the Dashboard
    # and not because it happens to be in a "Mine" collection
    URI = "http://osafoundation.org/eim/pim/dashboardmembership/0"
    itemUUID = eim.key(aliasableUUID)

# osaf.sharing ----------------------------------------------------------------


class ShareRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/share/0"

    uuid = eim.key(ItemRecord.uuid)
    contents = eim.field(schema.UUID)
    conduit = eim.field(schema.UUID)
    subscribed = eim.field(eim.IntType)
    error = eim.field(eim.ClobType)
    errorDetails = eim.field(eim.ClobType)
    mode = eim.field(text20)
    lastSuccess = eim.field(eim.DecimalType(digits=20, decimal_places=0))
    lastAttempt = eim.field(eim.DecimalType(digits=20, decimal_places=0))

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
    syncToken = eim.field(text256)


class ShareHTTPConduitRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/httpconduit/0"

    uuid = eim.key(ItemRecord.uuid)
    ticket = eim.field(text1024)
    ticket_rw = eim.field(text1024)
    ticket_ro = eim.field(text1024)

    account = eim.field(schema.UUID) # if provided, the following are ignored
    host = eim.field(text256)
    port = eim.field(eim.IntType)
    ssl = eim.field(eim.IntType)
    username = eim.field(text256)
    password = eim.field(schema.UUID)

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
    share = eim.field(schema.UUID)
    alias = eim.field(text1024)
    conflict_item = eim.field(schema.UUID)
    conflict_share = eim.field(schema.UUID)
    agreed = eim.field(eim.BlobType)
    pending = eim.field(eim.BlobType)

class SharePeerStateRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/peerstate/0"

    uuid = eim.key(ItemRecord.uuid)
    peer = eim.field(schema.UUID)
    item = eim.field(schema.UUID)
    peerrepo = eim.field(text1024)
    peerversion = eim.field(eim.IntType)

class ShareResourceStateRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/resourcesharestate/0"

    uuid = eim.key(ItemRecord.uuid)
    path = eim.field(text1024)
    etag = eim.field(text1024)

class ShareSharedInRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/sharedin/0"

    item = eim.key(schema.UUID)
    share = eim.key(schema.UUID)

class ShareAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/account/0"

    uuid = eim.key(ItemRecord.uuid)
    host = eim.field(text256)
    port = eim.field(eim.IntType)
    ssl = eim.field(eim.IntType)
    path = eim.field(text1024)
    username = eim.field(text256)
    password = eim.field(schema.UUID)

class ShareWebDAVAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/webdavaccount/0"

    uuid = eim.key(ItemRecord.uuid)

class ShareCosmoAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/cosmoaccount/0"

    uuid = eim.key(ItemRecord.uuid)
    pimpath = eim.field(text1024) # pim/collection
    morsecodepath = eim.field(text1024) # mc/collection
    davpath = eim.field(text1024) # dav/collection

class ShareHubAccountRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/hubaccount/0"

    uuid = eim.key(ItemRecord.uuid)

class SharePrefsRecord(eim.Record):
    URI = "http://osafoundation.org/eim/sharing/prefs/0"

    currentAccount = eim.field(schema.UUID) # empty string means no account

# preferences ----------------------------------------------------------------

class PrefCalendarHourHeightRecord(eim.Record):
    URI = "http://osafoundation.org/eim/preferences/calendarhourheight/0"

    hourHeightMode = eim.field(text20)
    visibleHours = eim.field(eim.IntType)

class PrefTimezonesRecord(eim.Record):
    URI = "http://osafoundation.org/eim/preferences/timezones/0"

    showUI = eim.field(eim.IntType)
    showPrompt = eim.field(eim.IntType)
    default = eim.field(text256)
    wellKnownIDs = eim.field(text1024)
