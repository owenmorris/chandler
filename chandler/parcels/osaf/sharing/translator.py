#   Copyright (c) 2006-2007 Open Source Applications Foundation
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

from application import schema
from osaf import pim
from osaf.sharing import (
    eim, model, shares, utility, accounts, conduits, cosmo, webdav_conduit,
    recordset_conduit, eimml
)
from PyICU import ICUtzinfo
import time
import email
from email import Message, Utils
from datetime import datetime, date, timedelta
from decimal import Decimal

from vobject.base import textLineToContentLine, ContentLine
from vobject.icalendar import (DateOrDateTimeBehavior, MultiDateBehavior,
                               RecurringComponent, VEvent, timedeltaToString,
                               stringToDurations)
import osaf.pim.calendar.TimeZone as TimeZone
from osaf.pim.calendar.Calendar import Occurrence, EventStamp
from osaf.pim.calendar.Recurrence import RecurrenceRuleSet, RecurrenceRule
from dateutil.rrule import rrulestr
import dateutil
from chandlerdb.util.c import UUID
from osaf.pim.mail import EmailAddress
from osaf.usercollections import UserCollection
from osaf.mail.utils import getEmptyDate

__all__ = [
    'SharingTranslator',
    'DumpTranslator',
]


"""
Notes:

Cosmo likes None for empty bodies, and "" for empty locations
"""


utc = ICUtzinfo.getInstance('UTC')
du_utc = dateutil.tz.tzutc()
oneDay = timedelta(1)

noChangeOrInherit = (eim.NoChange, eim.Inherit)
emptyValues = (eim.NoChange, eim.Inherit, None)

def getEmailAddress(view, record):
    name, email = Utils.parseaddr(record)

    address = EmailAddress.findEmailAddress(view, email)

    if address is None:
        address = EmailAddress(itsView=view, emailAddress=email,
                                        fullName=name)

    return address


def addEmailAddresses(view, col, record):
    #, sep list
    addrs = record.split(u", ")

    for addr in addrs:
        name, email = Utils.parseaddr(addr)

        address = EmailAddress.findEmailAddress(view, email)

        if address is None:
            address = EmailAddress(itsView=view, emailAddress=email,
                                        fullName=name)

        col.append(address)


def with_nochange(value, converter, view=None):
    if value in (eim.NoChange, eim.Inherit):
        return value
    if value is None:  # TODO: think about how to handle None
        return eim.NoChange
    if view is None:
        return converter(value)
    else:
        return converter(value, view)


### Event field conversion functions
# incomplete

def fromTransparency(val):
    out = val.lower()
    if out == 'cancelled':
        out = 'fyi'
    elif out not in ('confirmed', 'tentative'):
        out = 'confirmed'
    return out

def fromLocation(val, view):
    if not val: # None or ""
        return None
    return pim.Location.getLocation(view, val)

def fromICalendarDateTime(text, multivalued=False):
    prefix = 'dtstart' # arbitrary
    if not text.startswith(';'):
        # no parameters
        prefix =+ ':'
    line = textLineToContentLine('dtstart' + text)
    if multivalued:
        line.behavior = MultiDateBehavior
    else:
        line.behavior = DateOrDateTimeBehavior
    line.transformToNative()
    anyTime = getattr(line, 'x_osaf_anytime_param', "").upper() == 'TRUE'
    allDay = False
    start = line.value
    if not multivalued:
        start = [start]
    if type(start[0]) == date:
        allDay = not anyTime
        start = [TimeZone.forceToDateTime(dt) for dt in start]
    else:
        # this parameter is broken, this should be fixed in vobject, at which
        # point this will break
        tzid = line.params.get('X-VOBJ-ORIGINAL-TZID')
        if tzid is None:
            # RDATEs and EXDATEs won't have an X-VOBJ-ORIGINAL-TZID
            tzid = getattr(line, 'tzid_param', None)
        if start[0].tzinfo == du_utc:
            tzinfo = utc
        elif tzid is None:
            tzinfo = ICUtzinfo.floating
        else:
            tzinfo = ICUtzinfo.getInstance(tzid)
        start = [dt.replace(tzinfo=tzinfo) for dt in start]
    if not multivalued:
        start = start[0]
    return (start, allDay, anyTime)

def fromICalendarDuration(text):
    return stringToDurations(text)[0]    

def getTimeValues(record):
    """
    Extract start time and allDay/anyTime from a record.
    """
    dtstart  = record.dtstart
    start = None
    if dtstart not in noChangeOrInherit:
        start, allDay, anyTime = fromICalendarDateTime(dtstart)
    else:
        allDay = anyTime = start = dtstart

    return (start, allDay, anyTime)

dateFormat = "%04d%02d%02d"
datetimeFormat = "%04d%02d%02dT%02d%02d%02d"
tzidFormat = ";TZID=%s"
allDayParameter = ";VALUE=DATE"
timedParameter  = ";VALUE=DATE-TIME"
anyTimeParameter = ";X-OSAF-ANYTIME=TRUE"

def formatDateTime(dt, allDay, anyTime):
    """Take a date or datetime, format it appropriately for EIM"""
    if allDay or anyTime:
        return dateFormat % dt.timetuple()[:3]
    else:
        base = datetimeFormat % dt.timetuple()[:6]
        if dt.tzinfo == utc:
            return base + 'Z'
        else:
            return base

def toICalendarDateTime(dt_or_dtlist, allDay, anyTime=False):
    if isinstance(dt_or_dtlist, datetime):
        dtlist = [dt_or_dtlist]
    else:
        dtlist = dt_or_dtlist

    output = ''
    if allDay or anyTime:
        if anyTime and not allDay:
            output += anyTimeParameter
        output += allDayParameter
    else:
        isUTC = dtlist[0].tzinfo == utc
        output += timedParameter
        if not isUTC and dtlist[0].tzinfo != ICUtzinfo.floating:
            output += tzidFormat % dtlist[0].tzinfo.tzid

    output += ':'
    output += ','.join(formatDateTime(dt, allDay, anyTime) for dt in dtlist)
    return output

def toICalendarDuration(delta, allDay=False):
    """
    The delta serialization format needs to match Cosmo exactly, so while
    vobject could do this, we'll want to be more picky about how exactly to
    serialize deltas.
    
    """
    if allDay:
        if delta.seconds > 0 or delta.microseconds > 0 or delta.days == 0:
            # all day events' actual duration always rounds up to the nearest
            # day, and zero length all day events are actually a full day
            delta = timedelta(delta.days + 1)
    # but, for now, just use vobject, since we don't know how ical4j serializes
    # deltas yet
    return timedeltaToString(delta)
    

def getDateUtilRRuleSet(field, value, dtstart):
    """
    Turn EIM recurrence fields into a dateutil rruleset.
    
    dtstart is required to deal with count successfully.
    """
    ical_string = ""
    if value.startswith(';'):
        # remove parameters, dateutil fails when it sees them
        value = value.partition(':')[2]
    # EIM uses a colon to concatenate RRULEs, which isn't iCalendar
    for element in value.split(':'):
        ical_string += field
        ical_string += ':'
        ical_string += element
        ical_string += "\r\n"
    # dateutil chokes on unicode, pass in a string
    return rrulestr(str(ical_string), forceset=True, dtstart=dtstart)

def getRecurrenceFields(event):
    """
    Take an event, return EIM strings for rrule, exrule, rdate, exdate, any
    or all of which may be None.
    
    """
    if event.rruleset is None or event.occurrenceFor is not None:
        return (None, None, None, None)
    
    vobject_event = RecurringComponent()
    vobject_event.behavior = VEvent
    start = event.startTime
    if event.allDay or event.anyTime:
        start = start.date()
    elif start.tzinfo is ICUtzinfo.floating:
        start = start.replace(tzinfo=None)
    vobject_event.add('dtstart').value = start
    vobject_event.rruleset = event.createDateUtilFromRule(False, True)
    
    if hasattr(vobject_event, 'rrule'):
        rrules = vobject_event.rrule_list
        rrule = ':'.join(obj.serialize(lineLength=1000)[6:].strip() for obj in rrules)
    else:
        rrule = None
        
    if hasattr(vobject_event, 'exrule'):
        exrules = vobject_event.exrule_list
        exrrule = ':'.join(obj.serialize(lineLength=1000)[7:].strip() for obj in exrules)
    else:
        exrule = None
        
    rdates = getattr(event.rruleset, 'rdates', [])
    if len(rdates) > 0:
        rdate = toICalendarDateTime(rdates, event.allDay, event.anyTime)
    else:
        rdate = None
    
    exdates = getattr(event.rruleset, 'exdates', [])
    if len(exdates) > 0:
        exdate = toICalendarDateTime(exdates, event.allDay, event.anyTime)
    else:
        exdate = None

    return rrule, exrule, rdate, exdate

def splitUUID(recurrence_aware_uuid):
    """
    Split an EIM recurrence UUID.
    
    Return the tuple (UUID, recurrenceID or None).  UUID will be a string,
    recurrenceID will be a datetime or None.
    """
    uuid, colon, recurrenceID = recurrence_aware_uuid.partition(":")
    if colon != ":":
        # a plain UUID
        return (uuid, None)
    else:
        return (uuid, fromICalendarDateTime(recurrenceID)[0])
        


def handleEmpty(item_or_stamp, attr):
    item = getattr(item_or_stamp, 'itsItem', item_or_stamp)
    if not isinstance(item_or_stamp, Occurrence):
        # type(some_Occurrence).attrname is a getter, not a descriptor, so
        # don't bother changing attr for stamps (it isn't needed anyway in
        # that case)
        attr = getattr(type(item_or_stamp), attr).name
    isOccurrence = isinstance(item, Occurrence)
    if not hasattr(item, attr):
        if not isOccurrence or hasattr(item.inheritFrom, attr):
            return None
        else:
            return eim.Inherit
    if not isOccurrence or item.hasLocalAttributeValue(attr):
        return getattr(item, attr)
    else:
        return eim.Inherit



def getAliasForItem(item_or_stamp):
    item = getattr(item_or_stamp, 'itsItem', item_or_stamp)
    if isinstance(item, Occurrence):
        event = EventStamp(item)
        master = item.inheritFrom
        recurrenceID = toICalendarDateTime(event.recurrenceID,
                                           event.allDay or event.anyTime)
        return master.itsUUID.str16() + ":" + recurrenceID
    else:
        return item.itsUUID.str16()


eim.add_converter(model.aliasableUUID, schema.Item, getAliasForItem)
eim.add_converter(model.aliasableUUID, pim.Stamp, getAliasForItem)


class SharingTranslator(eim.Translator):

    URI = "cid:pim-translator@osaf.us"
    version = 1
    description = u"Translator for Chandler PIM items"

    def getUUIDForAlias(self, alias):
        uuid, recurrenceID = splitUUID(alias)

        if recurrenceID is None:
            return uuid

        # find the occurrence and return itsUUID
        master = self.rv.findUUID(uuid)
        if master is not None and pim.has_stamp(master, pim.EventStamp):
            masterEvent = pim.EventStamp(master)
            occurrence = masterEvent.getExistingOccurrence(recurrenceID)
            if occurrence is not None:
                return occurrence.itsItem.itsUUID.str16()

        return None


    def getAliasForItem(self, item):
        return getAliasForItem(item)



    # ItemRecord -------------

    code_to_triagestatus = {
        "100" : pim.TriageEnum.now,
        "200" : pim.TriageEnum.later,
        "300" : pim.TriageEnum.done,
    }
    triagestatus_to_code = dict([[v, k] for k, v in code_to_triagestatus.items()])

    code_to_modaction = {
        100 : pim.Modification.edited,
        200 : pim.Modification.queued,
        300 : pim.Modification.sent,
        400 : pim.Modification.updated,
        500 : pim.Modification.created,
    }
    modaction_to_code = dict([[v, k] for k, v in code_to_modaction.items()])

    def getRealUUID(self, recurrence_aware_uuid):
        uuid, recurrenceID = splitUUID(recurrence_aware_uuid)
        if recurrenceID is not None:
            item = self.rv.findUUID(uuid)
            if item is None:
                uuid = UUID(uuid)
                item = pim.Note(itsView=self.rv, _uuid=uuid)
            master = EventStamp(item)
            if not pim.has_stamp(item, EventStamp):
                master.add()
            if getattr(master, 'rruleset', None) is None:
                # add a dummy RecurrenceRuleSet so event methods treat the event
                # as a master
                master.rruleset = RecurrenceRuleSet(None, itsView=self.rv)

            occurrence = master.getRecurrenceID(recurrenceID)
            if occurrence is None:
                occurrence = master._createOccurrence(recurrenceID)

            uuid = occurrence.itsItem.itsUUID.str16()
        return uuid

    def loadItemByUUID(self, recurrence_aware_uuid, *args, **kwargs):
        """
        Override to handle special recurrenceID:uuid uuids.
        """
        uuid = self.getRealUUID(recurrence_aware_uuid)
        return super(SharingTranslator, self).loadItemByUUID(uuid, *args, **kwargs)

    def withItemForUUID(self, recurrence_aware_uuid, *args, **kwargs):
        """
        Override to handle special recurrenceID:uuid uuids.
        """
        uuid = self.getRealUUID(recurrence_aware_uuid)
        return super(SharingTranslator, self).withItemForUUID(uuid, *args,
            **kwargs)

    @model.ItemRecord.importer
    def import_item(self, record):
        if record.createdOn not in emptyValues:
            # createdOn is a Decimal we need to change to datetime
            naive = datetime.utcfromtimestamp(float(record.createdOn))
            inUTC = naive.replace(tzinfo=utc)
            # Convert to user's tz:
            createdOn = inUTC.astimezone(ICUtzinfo.default)
        else:
            createdOn = eim.NoChange

        @self.withItemForUUID(
            record.uuid,
            pim.ContentItem,
            displayName=record.title,
            createdOn=createdOn
        )
        def do(item):
            if record.triage != "" and record.triage not in emptyValues:
                code, timestamp, auto = record.triage.split(" ")
                item._triageStatus = self.code_to_triagestatus[code]
                item._triageStatusChanged = float(timestamp)
                item.doAutoTriageOnDateChange = (auto == "1")

        # TODO: record.hasBeenSent --> item.modifiedFlags
        # TODO: record.needsReply

    @eim.exporter(pim.ContentItem)
    def export_item(self, item):

        # TODO: see why many items don't have createdOn
        if not hasattr(item, 'createdOn'):
            item.createdOn = datetime.now(ICUtzinfo.default)

        # createdOn = handleEmpty(item, 'createdOn')
        # elif createdOn not in noChangeOrInherit:
        createdOn = Decimal(int(time.mktime(item.createdOn.timetuple())))

        # For modifications, treat triage status as Inherit if it
        # matches its automatic state
        doATODC = getattr(item, "doAutoTriageOnDateChange", True)
        if (not isinstance(item, Occurrence) or not doATODC or 
            EventStamp(item).autoTriage() != item._triageStatus):

            tsCode = self.triagestatus_to_code.get(item._triageStatus, "100")
            tsChanged = item._triageStatusChanged or 0.0
            tsAuto = ("1" if doATODC else "0")
            triage = "%s %.2f %s" % (tsCode, tsChanged, tsAuto)
        else:
            triage = eim.Inherit

        title = handleEmpty(item, "displayName")
        if title is None:
            title = ""

        yield model.ItemRecord(
            item,                                       # uuid
            title,                                      # title
            triage,                                     # triage
            createdOn,                                  # createdOn
            0,                                          # hasBeenSent (TODO)
            0                                           # needsReply (TODO)
        )

        # Also export a ModifiedByRecord
        lastModifiedBy = ""
        if hasattr(item, "lastModifiedBy"):
            emailAddress = item.lastModifiedBy
            if emailAddress is not None and emailAddress.emailAddress:
                lastModifiedBy = emailAddress.emailAddress

        lastModified = getattr(item, "lastModified", None)
        if lastModified:
            lastModified = Decimal(
                int(time.mktime(lastModified.timetuple()))
            )
        else:
            lastModified = createdOn

        lastModification = item.lastModification

        yield model.ModifiedByRecord(
            item,
            lastModifiedBy,
            lastModified,
            action = self.modaction_to_code.get(lastModification, 500)
        )

        reminder = item.getUserReminder()

        if reminder is not None:

            if reminder.reminderItem is item: # this is our reminder

                trigger = None
                if reminder.hasLocalAttributeValue('delta'):
                    trigger = toICalendarDuration(reminder.delta)
                elif reminder.hasLocalAttributeValue('absoluteTime'):
                    trigger = toICalendarDateTime(reminder.absoluteTime, False)


                if reminder.duration:
                    duration = toICalendarDuration(reminder.duration, False)
                else:
                    duration = None

                if reminder.repeat:
                    repeat = reminder.repeat
                else:
                    repeat = None

                description = getattr(reminder, 'description', None)
                if description is None:
                    description = "Event Reminder"

            else: # we've inherited this reminder

                description = eim.Inherit
                trigger = eim.Inherit
                duration = eim.Inherit
                repeat = eim.Inherit

            yield model.DisplayAlarmRecord(
                item,
                description,
                trigger,
                duration,
                repeat,
            )



    # ModifiedByRecord  -------------

    @model.ModifiedByRecord.importer
    def import_modifiedBy(self, record):

        @self.withItemForUUID(record.uuid, pim.ContentItem)
        def do(item):
            # only apply a modifiedby record if timestamp is more recent than
            # what's on the item already

            existing = getattr(item, "lastModified", None)
            existing = (Decimal(int(time.mktime(existing.timetuple())))
                if existing else 0)

            if record.timestamp >= existing:

                # record.userid can never be NoChange.  "" == anonymous
                if not record.userid:
                    item.lastModifiedBy = None
                else:
                    item.lastModifiedBy = \
                        pim.EmailAddress.getEmailAddress(self.rv, record.userid)

                # record.timestamp can never be NoChange, nor None
                # timestamp is a Decimal we need to change to datetime
                naive = datetime.utcfromtimestamp(float(record.timestamp))
                inUTC = naive.replace(tzinfo=utc)
                # Convert to user's tz:
                item.lastModified = inUTC.astimezone(ICUtzinfo.default)

                if record.action is not eim.NoChange:
                    item.lastModification = \
                        self.code_to_modaction[record.action]

                #XXX Brian K: The modified flags were not getting set properly
                # without this addition.
                item.changeEditState(item.lastModification,
                                     item.lastModifiedBy,
                                     item.lastModified)


        # Note: ModifiedByRecords are exported by item



    # NoteRecord -------------

    @model.NoteRecord.importer
    def import_note(self, record):

        # TODO: REMOVE HACK: (Cosmo sends None for empty bodies)
        if record.body is None:
            body = ""
        else:
            body = record.body

        if record.icalUid is None:
            icalUID = eim.NoChange
        else:
            icalUID = record.icalUid

        self.withItemForUUID(
            record.uuid,
            pim.Note,
            icalUID=icalUID,
            body=body
        )

    @eim.exporter(pim.Note)
    def export_note(self, note):
        body = handleEmpty(note, 'body')
        # TODO: REMOVE HACK (Cosmo expects None for empty bodies)
        if body == '':
            body = None
            
        # when serializing iCalendar, modifications will incorrectly handle
        # a None value for icalUID if icalUID and UUID aren't the same, but in 
        # most cases, icalUID will be identical to UUID, just use None in that
        # case
        icalUID = getattr(note, 'icalUID', None)
        if icalUID == unicode(note.itsUUID):
            icalUID = None


        yield model.NoteRecord(
            note,                                       # uuid
            body,                                       # body
            icalUID,                                    # icalUid
            None,                                       # icalProperties
            None                                        # icalParameters
            
        )



    # TaskRecord -------------

    @model.TaskRecord.importer
    def import_task(self, record):
        self.withItemForUUID(
            record.uuid,
            pim.TaskStamp
        )

    @eim.exporter(pim.TaskStamp)
    def export_task(self, task):
        yield model.TaskRecord(
            task
        )


    @model.TaskRecord.deleter
    def delete_task(self, record):
        item = self.rv.findUUID(self.getRealUUID(record.uuid))
        if item is not None and item.isLive() and pim.has_stamp(item,
            pim.TaskStamp):
            pim.TaskStamp(item).remove()



    #MailMessageRecord
    @model.MailMessageRecord.importer
    def import_mail(self, record):
        #TODO: How to represent attachments?

        @self.withItemForUUID(
           record.uuid,
           pim.MailStamp,
           dateSentString=record.dateSent,
        )
        def do(mail):
            view = self.rv

            if record.messageId not in noChangeOrInherit:
                mail.messageId = record.messageId and \
                                 record.messageId or u""

            if record.inReplyTo not in noChangeOrInherit:
                mail.inReplyTo = record.inReplyTo and \
                                 record.inReplyTo or u""

            if record.headers not in noChangeOrInherit:
                mail.headers = {}

                if record.headers:
                    headers = record.headers.split(u"\n")

                    prevKey = None

                    for header in headers:
                        try:
                            key, val = header.split(u": ", 1)
                            mail.headers[key] = val

                            # Keep the last valid key around
                            prevKey = key
                        except:
                            if prevKey:
                                mail.headers[prevKey] = header

            if record.toAddress not in noChangeOrInherit:
                mail.toAddress = []
                if record.toAddress:
                    addEmailAddresses(view, mail.toAddress, record.toAddress)

            if record.ccAddress not in noChangeOrInherit:
                mail.ccAddress = []

                if record.ccAddress:
                    addEmailAddresses(view, mail.ccAddress, record.ccAddress)

            if record.bccAddress not in noChangeOrInherit:
                mail.bccAddress = []

                if record.bccAddress:
                    addEmailAddresses(view, mail.bccAddress, record.bccAddress)

            if record.fromAddress not in noChangeOrInherit:

               if record.fromAddress:
                    mail.fromAddress = getEmailAddress(view, record.fromAddress)
               else:
                   mail.fromAddress = None

            # text or email addresses in Chandler from field
            if record.originators not in noChangeOrInherit:
                if record.originators:
                    res = EmailAddress.parseEmailAddresses(view, record.originators)

                    mail.originators = [ea for ea in res[1]]
                else:
                    mail.originators = []

            # references mail message id list
            if record.references not in noChangeOrInherit:
                mail.referencesMID = []

                if record.references:
                    refs = record.references.split()

                    for ref in refs:
                        ref = ref.strip()

                        if ref: mail.referencesMID.append(ref)

            if record.dateSent not in noChangeOrInherit:
                if record.dateSent and record.dateSent.strip():
                    mail.dateSentString = record.dateSent

                    timestamp = Utils.parsedate_tz(record.dateSent)
                    mail.dateSent = datetime.fromtimestamp(Utils.mktime_tz(timestamp), \
                                                           ICUtzinfo.default)
                else:
                    mail.dateSent = getEmptyDate()
                    mail.dateSentString = u""


    @eim.exporter(pim.MailStamp)
    def export_mail(self, mail):
        headers = []

        for header in mail.headers:
            headers.append(u"%s: %s" % (header, mail.headers[header]))

        if headers:
            headers = u"\n".join(headers)
        else:
            headers = None

        toAddress = []

        for addr in mail.toAddress:
            toAddress.append(addr.format())

        if toAddress:
            toAddress = u", ".join(toAddress)
        else:
            toAddress = None

        ccAddress = []

        for addr in mail.ccAddress:
            ccAddress.append(addr.format())

        if ccAddress:
            ccAddress = u", ".join(ccAddress)
        else:
            ccAddress = None

        bccAddress = []

        for addr in mail.bccAddress:
            bccAddress.append(addr.format())

        if bccAddress:
            bccAddress = u", ".join(bccAddress)
        else:
            bccAddress = None

        originators = []

        if hasattr(mail, "originators"):
            for addr in mail.originators:
                originators.append(addr.format())


        if originators:
            originators = u", ".join(originators)
        else:
            originators = None

        if hasattr(mail, "fromAddress"):
            fromAddress = mail.fromAddress.format()
        else:
            fromAddress = None


        references = []

        for ref in mail.referencesMID:
            ref = ref.strip()

            if ref:
                references.append(ref)

        if references:
            references = u" ".join(references)
        else:
            references = None

        if hasattr(mail, "inReplyTo"):
            inReplyTo = mail.inReplyTo
        else:
            inReplyTo = None

        if hasattr(mail, "messageId"):
            messageId = mail.messageId
        else:
            messageId = None

        if hasattr(mail, "dateSentString"):
            dateSent = mail.dateSentString
        else:
            dateSent = None


        yield model.MailMessageRecord(
            mail,                  # uuid
            messageId,             # messageId
            headers,               # headers
            fromAddress,           # fromAddress
            toAddress,             # toAddress
            ccAddress,             # ccAddress
            bccAddress,            # bccAddress
            originators,           # originators
            dateSent,              # dateSent
            inReplyTo,             # inReplyTo
            references,            # references
        )


    @model.MailMessageRecord.deleter
    def delete_mail(self, record):
        item = self.rv.findUUID(record.uuid)
        if item is not None and item.isLive() and \
           pim.has_stamp(item, pim.MailStamp):
            pim.MailStamp(item).remove()


    # EventRecord -------------

    # TODO: EventRecord fields need work, for example: rfc3339 date strings

    @model.EventRecord.importer
    def import_event(self, record):

        start, allDay, anyTime = getTimeValues(record)

        @self.withItemForUUID(
            record.uuid,
            EventStamp,
            startTime=start,
            allDay=allDay,
            anyTime=anyTime,
            duration=with_nochange(record.duration, fromICalendarDuration),
            transparency=with_nochange(record.status, fromTransparency),
            location=with_nochange(record.location, fromLocation, self.rv),
        )
        def do(item):
            event = EventStamp(item)

            if event.occurrenceFor is not None:
                # modifications don't have recurrence rule information
                return

            # notify of recurrence changes once at the end
            if event.rruleset is not None:
                ignoreChanges = getattr(event.rruleset, '_ignoreValueChanges',
                    False)
                event.rruleset._ignoreValueChanges = True
            elif (record.rrule in emptyValues and
                  record.rdate in emptyValues):
                # since there's no recurrence currently, avoid creating a
                # rruleset if all the positive recurrence fields are None
                return

            if event.rruleset is not None:
                rruleset = event.rruleset
            else:
                rruleset = RecurrenceRuleSet(None, itsView=self.rv)

            for ruletype in 'rrule', 'exrule':
                record_field = getattr(record, ruletype)
                if record_field is not eim.NoChange:
                    if record_field in (None, eim.Inherit):
                        # this isn't the right way to delete the existing
                        # rules, what is?
                        setattr(rruleset, ruletype + 's', [])
                    else:
                        du_rruleset = getDateUtilRRuleSet(ruletype,
                            record_field, event.effectiveStartTime)
                        rules = getattr(du_rruleset, '_' + ruletype)
                        if rules is None:
                            rules = []
                        itemlist = []
                        for du_rule in rules:
                            ruleItem = RecurrenceRule(None, None, None, self.rv)
                            ruleItem.setRuleFromDateUtil(du_rule)
                            itemlist.append(ruleItem)
                        setattr(rruleset, ruletype + 's', itemlist)

            for datetype in 'rdate', 'exdate':
                record_field = getattr(record, datetype)
                if record_field is not eim.NoChange:
                    if record_field is None:
                        dates = []
                    else:
                        dates = fromICalendarDateTime(record_field,
                                                      multivalued=True)[0]
                    setattr(rruleset, datetype + 's', dates)

            if len(rruleset.rrules) == 0 and len(rruleset.rdates) == 0:
                event.removeRecurrence()
            elif event.rruleset is not None:
                # changed existing recurrence
                event.rruleset._ignoreValueChanges = ignoreChanges
                event.cleanRule()
            else:
                # new recurrence
                event.rruleset = rruleset


    @eim.exporter(EventStamp)
    def export_event(self, event):
        item = event.itsItem
        
        location = handleEmpty(event, 'location')
        if location not in emptyValues:
            location = location.displayName

        rrule, exrule, rdate, exdate = getRecurrenceFields(event)

        transparency = handleEmpty(event, 'transparency')
        if transparency not in emptyValues:
            transparency = str(event.transparency).upper()
            if transparency == "FYI":
                transparency = "CANCELLED"

        has_change = event.hasLocalAttributeValue


        # if recurring, dtstart has changed if allDay or anyTime has a local 
        # change, or if effectiveStartTime != recurrenceID.
        if (not isinstance(item, Occurrence) or
            has_change('allDay') or 
            has_change('anyTime') or 
            event.effectiveStartTime != event.recurrenceID):
            dtstart = toICalendarDateTime(event.effectiveStartTime, 
                                          event.allDay, event.anyTime)
        else:
            dtstart = eim.Inherit

        # if recurring, duration has changed if allDay, anyTime, or duration has
        # a local change
        if (not isinstance(item, Occurrence) or
            has_change('allDay') or 
            has_change('anyTime') or 
            has_change('duration')):
            duration = toICalendarDuration(event.duration, 
                                           event.allDay or event.anyTime)
        else:
            duration = eim.Inherit


        yield model.EventRecord(
            event,                                      # uuid
            dtstart,                                    # dtstart
            duration,                                   # duration
            location,                                   # location
            rrule,                                      # rrule
            exrule,                                     # exrule
            rdate,                                      # rdate
            exdate,                                     # exdate
            transparency,                               # status
        )

    @model.EventRecord.deleter
    def delete_event(self, record):
        item = self.rv.findUUID(record.uuid)
        if item is not None and item.isLive() and pim.has_stamp(item,
            EventStamp):
            EventStamp(item).remove()

    # DisplayAlarmRecord -------------

    @model.DisplayAlarmRecord.importer
    def import_alarm(self, record):

        @self.withItemForUUID(record.uuid, pim.ContentItem)
        def do(item):
            if record.trigger not in noChangeOrInherit:
                # trigger translates to either a pim.Reminder (if a date(time),
                # or a pim.RelativeReminder (if a timedelta).
                kw = dict(itsView=item.itsView)
                reminderFactory = None

                try:
                    val = fromICalendarDateTime(record.trigger)[0]
                except:
                    pass
                else:
                    reminderFactory = pim.Reminder
                    kw.update(absoluteTime=val)

                if reminderFactory is None:
                    try:
                        val = stringToDurations(record.trigger)[0]
                    except:
                        pass
                    else:
                        reminderFactory = pim.RelativeReminder
                        kw.update(delta=val)

                if reminderFactory is not None:
                    item.reminders = [reminderFactory(**kw)]


            reminder = item.getUserReminder()
            if reminder is not None:

                if record.description not in noChangeOrInherit:
                    reminder.description = record.description

                if record.duration not in noChangeOrInherit:
                    reminder.duration = stringToDurations(record.duration)[0]

                if record.repeat not in noChangeOrInherit:
                    reminder.repeat = record.repeat

    @model.DisplayAlarmRecord.deleter
    def delete_alarm(self, record):
        item = self.rv.findUUID(record.uuid)
        item.reminders = []

class DumpTranslator(SharingTranslator):

    URI = "cid:dump-translator@osaf.us"
    version = 1
    description = u"Translator for Chandler items (PIM and non-PIM)"


    # - - Collection  - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @model.CollectionRecord.importer
    def import_collection(self, record):

        @self.withItemForUUID(record.uuid,
            pim.SmartCollection
        )
        def do(collection):

            # Temporary hack to work aroud the fact that importers don't
            # properly call __init__ except in the base class. I think
            # __init__ hasn't been called if the following condition is True.

            if (collection.exclusionsCollection is None and
                not hasattr (collection, "collectionExclusions")):
                collection._setup()

            if record.mine == 1:
                schema.ns('osaf.pim', self.rv).mine.addSource(collection)


    @eim.exporter(pim.SmartCollection)
    def export_collection(self, collection):
        yield model.CollectionRecord(
            collection,
            int (collection in schema.ns('osaf.pim', self.rv).mine.sources)
        )
        for record in self.export_collection_memberships (collection):
            yield record


    def export_collection_memberships(self, collection):
        index = 0
        for item in collection:
            # By default we don't include items that are in
            # //parcels since they are not created by the user
            if not str(item.itsPath).startswith("//parcels"):
                yield model.CollectionMembershipRecord(
                    collection,
                    item.itsUUID,
                    index
                )
                index = index + 1

    if __debug__:
        def indexIsInSequence (self, collection, index):
            if not hasattr (self, "collectionToIndex"):
                self.collectionToIndex = {}
            expectedIndex = self.collectionToIndex.get (collection, 0)
            self.collectionToIndex[collection] = index + 1
            return expectedIndex == index


    @model.CollectionMembershipRecord.importer
    def import_collectionmembership(self, record):

        # Temporary work aroud for getting the right class of the sidebar since
        # loadItemByUUID with the default of SmartCollection throws an exception
        # in the case of the sidebar

        collection = self.rv.find (UUID (record.collectionUUID))
        if collection is None:
            collection = self.loadItemByUUID (record.collectionUUID, pim.SmartCollection)
        # We're preserving order of items in collections
        assert (self.indexIsInSequence (collection, record.index))

        @self.withItemForUUID(record.itemUUID, pim.ContentItem)
        def do(item):
            collection.add(item)



    # - - Sharing-related items - - - - - - - - - - - - - - - - - - - - - -

    @model.ShareRecord.importer
    def import_share(self, record):

        @self.withItemForUUID(record.uuid,
            shares.Share,
            established=True,
            error=record.error,
            mode=record.mode
        )
        def do(share):
            if record.lastSynced not in (eim.NoChange, None):
                # lastSynced is a Decimal we need to change to datetime
                naive = datetime.utcfromtimestamp(float(record.lastSynced))
                inUTC = naive.replace(tzinfo=utc)
                # Convert to user's tz:
                share.lastSynced = inUTC.astimezone(ICUtzinfo.default)

            if record.subscribed == 0:
                share.sharer = schema.ns('osaf.pim',
                    self.rv).currentContact.item

            if record.contents not in (eim.NoChange, None):
                # contents is the UUID of a SharedItem
                @self.withItemForUUID(record.contents, shares.SharedItem)
                def do_contents(sharedItem):
                    share.contents = sharedItem.itsItem

            if record.conduit not in (eim.NoChange, None):
                @self.withItemForUUID(record.conduit, conduits.Conduit)
                def do_conduit(conduit):
                    share.conduit = conduit



    @eim.exporter(shares.Share)
    def export_share(self, share):

        contents = share.contents.itsUUID

        conduit = share.conduit.itsUUID

        subscribed = 0 if utility.isSharedByMe(share) else 1

        error = getattr(share, "error", "")

        mode = share.mode

        if hasattr(share, "lastSynced"):
            lastSynced = Decimal(int(time.mktime(share.lastSynced.timetuple())))
        else:
            lastSynced = None

        yield model.ShareRecord(
            share,
            contents,
            conduit,
            subscribed,
            error,
            mode,
            lastSynced
        )





    @model.ShareConduitRecord.importer
    def import_shareconduit(self, record):
        self.withItemForUUID(record.uuid,
            conduits.BaseConduit,
            sharePath=record.path,
            shareName=record.name
        )

    @eim.exporter(conduits.BaseConduit)
    def export_conduit(self, conduit):

        path = conduit.sharePath
        name = conduit.shareName

        yield model.ShareConduitRecord(
            conduit,
            path,
            name
        )




    @model.ShareRecordSetConduitRecord.importer
    def import_sharerecordsetconduit(self, record):
        @self.withItemForUUID(record.uuid,
            recordset_conduit.RecordSetConduit,
        )
        def do(conduit):
            if record.serializer == "eimml":
                conduit.serializer = eimml.EIMMLSerializer
            if record.serializer == "eimml_lite":
                conduit.serializer = eimml.EIMMLSerializerLite

            if record.filters not in (None, eim.NoChange):
                for filter in record.filters.split(","):
                    if filter:
                        conduit.filters.add(filter)

    @eim.exporter(recordset_conduit.RecordSetConduit)
    def export_recordsetconduit(self, conduit):

        translator = None

        if conduit.serializer is eimml.EIMMLSerializer:
            serializer = 'eimml'
        elif conduit.serializer is eimml.EIMMLSerializerLite:
            serializer = 'eimml_lite'

        filters = ",".join(conduit.filters)

        yield model.ShareRecordSetConduitRecord(
            conduit,
            translator,
            serializer,
            filters
        )




    @model.ShareHTTPConduitRecord.importer
    def import_sharehttpconduit(self, record):

        @self.withItemForUUID(record.uuid, conduits.HTTPMixin)
        def do(conduit):
            if record.account is not eim.NoChange:
                if record.account:
                    @self.withItemForUUID(record.account,
                        accounts.SharingAccount)
                    def do_account(account):
                        conduit.account = account
                else:
                    conduit.account = None
                    if record.host is not eim.NoChange:
                        conduit.host = record.host
                    if record.port is not eim.NoChange:
                        conduit.port = record.port
                    if record.ssl is not eim.NoChange:
                        conduit.useSSL = True if record.ssl else False
                    if record.username is not eim.NoChange:
                        conduit.username = record.username
                    if record.password is not eim.NoChange:
                        conduit.password = record.password
        # TODO: url
        # TODO: ticket_rw
        # TODO: ticket_ro

    @eim.exporter(conduits.HTTPMixin)
    def export_httpmixin(self, conduit):

        url = conduit.getLocation()

        ticket_rw = None # TODO
        ticket_ro = None # TODO

        if conduit.account:
            account = conduit.account.itsUUID
            host = None
            port = None
            ssl = None
            username = None
            password = None
        else:
            account = None
            host = conduit.host
            port = conduit.port
            ssl = 1 if conduit.useSSL else 0
            username = conduit.username
            password = conduit.password

        yield model.ShareHTTPConduitRecord(
            conduit,
            url,
            ticket_rw,
            ticket_ro,
            account,
            host,
            port,
            ssl,
            username,
            password
        )




    @model.ShareCosmoConduitRecord.importer
    def import_sharecosmoconduit(self, record):

        self.withItemForUUID(record.uuid,
            cosmo.CosmoConduit,
            morsecodePath = record.morsecodepath
        )

    @eim.exporter(cosmo.CosmoConduit)
    def export_cosmoconduit(self, conduit):

        yield model.ShareCosmoConduitRecord(
            conduit,
            conduit.morsecodepath
        )



    @model.ShareWebDAVConduitRecord.importer
    def import_sharewebdavconduit(self, record):

        self.withItemForUUID(record.uuid,
            webdav_conduit.WebDAVRecordSetConduit
        )

    @eim.exporter(webdav_conduit.WebDAVRecordSetConduit)
    def export_webdavconduit(self, conduit):

        yield model.ShareWebDAVConduitRecord(
            conduit
        )




    @model.ShareStateRecord.importer
    def import_sharestate(self, record):

        @self.withItemForUUID(record.uuid,
            shares.State,
            itemUUID=record.item,
            peerRepoId=record.peerrepo,
            peerItemVersion=record.peerversion,
            itemUUID=record.item
        )
        def do(state):
            if record.peer not in (eim.NoChange, None):
                @self.withItemForUUID(record.peer, schema.Item)
                def do_peer(peer):
                    state.peer = peer

            if record.share not in (eim.NoChange, None):
                @self.withItemForUUID(record.share, shares.Share)
                def do_share(share):
                    if state not in share.states:
                        share.states.append(state, record.item)

        # TODO: agreed
        # TODO: pending

    @eim.exporter(shares.State)
    def export_state(self, state):

        peer = state.peer.itsUUID if getattr(state, "peer", None) else None
        peerrepo = state.peerRepoId
        peerversion = state.peerItemVersion
        share = state.share.itsUUID if getattr(state, "share", None) else None
        item = getattr(state, "itemUUID", None)
        agreed = None # TODO
        pending = None # TODO

        yield model.ShareStateRecord(
            state,
            peer,
            peerrepo,
            peerversion,
            share,
            item,
            agreed,
            pending
        )



    @model.ShareResourceStateRecord.importer
    def import_shareresourcestate(self, record):

        self.withItemForUUID(record.uuid,
            recordset_conduit.ResourceState,
            path=record.path,
            etag=record.etag
        )

    @eim.exporter(recordset_conduit.ResourceState)
    def export_resourcestate(self, state):

        path = getattr(state, "path", None)
        etag = getattr(state, "etag", None)

        yield model.ShareResourceStateRecord(
            state,
            path,
            etag
        )



    @model.ShareAccountRecord.importer
    def import_shareaccount(self, record):

        @self.withItemForUUID(record.uuid,
            accounts.SharingAccount,
            host=record.host,
            port=record.port,
            path=record.path,
            username=record.username,
            password=record.password,
        )
        def do(account):
            if record.ssl not in (eim.NoChange, None):
                account.useSSL = True if record.ssl else False

    @eim.exporter(accounts.SharingAccount)
    def export_shareaccount(self, account):

        yield model.ShareAccountRecord(
            account,
            account.host,
            account.port,
            1 if account.useSSL else 0,
            account.path,
            account.username,
            account.password
        )




    @model.ShareWebDAVAccountRecord.importer
    def import_sharewebdavaccount(self, record):

        self.withItemForUUID(record.uuid,
            accounts.WebDAVAccount
        )

    @eim.exporter(accounts.WebDAVAccount)
    def export_sharewebdavaccount(self, account):

        yield model.ShareWebDAVAccountRecord(account)



    @model.ShareCosmoAccountRecord.importer
    def import_sharecosmoaccount(self, record):

        self.withItemForUUID(record.uuid,
            cosmo.CosmoAccount,
            pimPath=record.pimpath,
            morsecodePath=record.morsecodepath,
            davPath=record.davpath
        )

    @eim.exporter(cosmo.CosmoAccount)
    def export_sharecosmoaccount(self, account):

        yield model.ShareCosmoAccountRecord(
            account,
            account.pimPath,
            account.morsecodePath,
            account.davPath
        )

    def finishExport(self):
        for record in super(DumpTranslator, self).finishExport():
            yield record

        # emit the CollectionMembership records for the sidebar collection
        for record in self.export_collection_memberships (schema.ns("osaf.app", self.rv).sidebarCollection):
            yield record


def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'Translator.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )

