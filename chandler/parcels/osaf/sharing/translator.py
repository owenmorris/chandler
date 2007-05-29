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
from osaf.pim import mail
from osaf.sharing import (
    eim, model, shares, utility, accounts, conduits, cosmo, webdav_conduit,
    recordset_conduit, eimml, ootb
)
from PyICU import ICUtzinfo
import os
import calendar
from email import Utils
from datetime import datetime, date, timedelta
from decimal import Decimal

from vobject.base import textLineToContentLine
from vobject.icalendar import (DateOrDateTimeBehavior, MultiDateBehavior,
                               RecurringComponent, VEvent, timedeltaToString,
                               stringToDurations)
import osaf.pim.calendar.TimeZone as TimeZone
from osaf.pim.calendar.Calendar import Occurrence, EventStamp
from osaf.pim.calendar.Recurrence import RecurrenceRuleSet, RecurrenceRule
from dateutil.rrule import rrulestr
import dateutil
from osaf.framework.twisted import waitForDeferred
from osaf.pim.mail import EmailAddress
from osaf.usercollections import UserCollection
from osaf.mail.utils import getEmptyDate, dataToBinary, binaryToData
from osaf.pim.structs import ColorType
from osaf.framework.password import Password
from twisted.internet.defer import Deferred
import logging

__all__ = [
    'SharingTranslator',
    'DumpTranslator',
    'fromICalendarDateTime',
    'fromICalendarDuration',
]


logger = logging.getLogger(__name__)


utc = ICUtzinfo.getInstance('UTC')
du_utc = dateutil.tz.tzutc()
oneDay = timedelta(1)

noChangeOrInherit = (eim.NoChange, eim.Inherit)
emptyValues = (eim.NoChange, eim.Inherit, None)

class MessageState(object):
    FROM_ME, TO_ME, VIA_MAILSERVICE, IS_UPDATED, \
    FROM_EIMML, PREVIOUS_IN_RECIPIENTS = (1<<n for n in xrange(6))

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
    if view is None:
        return converter(value)
    else:
        return converter(value, view)

def datetimes_really_equal(dt1, dt2):
    return dt1.tzinfo == dt2.tzinfo and dt1 == dt2

def datetimeToDecimal(dt):
    
    tt = dt.utctimetuple()
    return Decimal(int(calendar.timegm(tt)))

def decimalToDatetime(decimal):
        naive = datetime.utcfromtimestamp(float(decimal))
        inUTC = naive.replace(tzinfo=utc)
        # Convert to user's tz:
        return inUTC.astimezone(ICUtzinfo.default)


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
        prefix += ':'
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
        # all day events' actual duration always rounds up to the nearest day
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
        exrule = ':'.join(obj.serialize(lineLength=1000)[7:].strip() for obj in exrules)
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

def fixTimezoneOnModification(modification, tzinfo=None):
    """
    Set timezone on occurrence equal to master to correct for inherited
    UTC timezone values.
    
    If a tzinfo is passed in, convert recurrenceID (and possibly startTime)
    to that tzinfo, otherwise use the master's timezone.
    
    """
    mod = EventStamp(modification)
    if tzinfo is None:
        master = mod.occurrenceFor
        assert master is not None
        tzinfo = EventStamp(master).effectiveStartTime.tzinfo
    if tzinfo != ICUtzinfo.floating and tzinfo != utc:
        recurrenceID = mod.recurrenceID
        if recurrenceID.tzinfo == utc:
            mod.recurrenceID = recurrenceID.astimezone(tzinfo)
        if (mod.startTime.tzinfo == utc and
            mod.startTime == recurrenceID):
            mod.startTime = mod.startTime.astimezone(tzinfo)    

def splitUUID(recurrence_aware_uuid):
    """
    Split an EIM recurrence UUID.
    
    Return the tuple (UUID, recurrenceID or None).  UUID will be a string,
    recurrenceID will be a datetime or None.
    """
    pseudo_uuid = str(recurrence_aware_uuid)
    # tolerate old-style, double-colon pseudo-uuids
    position = pseudo_uuid.find('::')
    if position != -1:
        return (pseudo_uuid[:position],
                fromICalendarDateTime(pseudo_uuid[position + 2:])[0])
    position = pseudo_uuid.find(':')
    if position != -1:
        return (pseudo_uuid[:position],
                fromICalendarDateTime(pseudo_uuid[position:])[0])
        
    return (pseudo_uuid, None)


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
        dateValue = event.allDay or event.anyTime
        recurrenceID = event.recurrenceID
        if recurrenceID.tzinfo != ICUtzinfo.floating and not dateValue:
            recurrenceID = recurrenceID.astimezone(utc)
        recurrenceID = formatDateTime(recurrenceID, dateValue, dateValue)
        return master.itsUUID.str16() + ":" + recurrenceID
    else:
        return item.itsUUID.str16()


eim.add_converter(model.aliasableUUID, schema.Item, getAliasForItem)
eim.add_converter(model.aliasableUUID, pim.Stamp, getAliasForItem)






# Hopefully someday we will be able to remove the following converters:

# Cosmo will generate a value of None even if Chandler hasn't provided a
# value for event status, so treat None as NoChange
eim.add_converter(model.EventRecord.status, type(None), lambda x: eim.NoChange)

eim.add_converter(model.DisplayAlarmRecord.description, type(None),
    lambda x: eim.NoChange)

# Cosmo will generate a value of empty string even if Chandler hasn't provided
# a value for triage, so treat empty string as NoChange
def emptyToNoChange(s):
    return s if s else eim.NoChange
eim.add_converter(model.ItemRecord.triage, str, emptyToNoChange)
eim.add_converter(model.ItemRecord.triage, unicode, emptyToNoChange)






class SharingTranslator(eim.Translator):

    URI = "cid:pim-translator@osaf.us"
    version = 1
    description = u"Translator for Chandler PIM items"

    obfuscation = False

    def startImport(self):
        super(SharingTranslator, self).startImport()
        tzprefs = schema.ns("osaf.pim", self.rv).TimezonePrefs
        self.promptForTimezone = not tzprefs.showUI and tzprefs.showPrompt


    def resolveConflicts(self, conflicts):
        for conflict in conflicts:

            if len(conflict.change.inclusions) == 1:
                record = list(conflict.change.inclusions)[0]

                if isinstance(record, model.ItemRecord):

                    item = conflict.item


                    if record.triage is not eim.NoChange:

                        if record.triage is eim.Inherit:
                            conflict.discard()

                        else:
                            codeIn, tscIn, autoIn = record.triage.split(" ")

                            if self.code_to_triagestatus[codeIn] == \
                                item.triageStatus:
                                # The triage status is not in conflict, so we
                                # are going to auto resolve any conflicts on
                                # either triageStatusChanged or
                                # doAutoTriageOnDateChange:

                                tscIn = float(tscIn)
                                if tscIn < item._triageStatusChanged:
                                    # inbound tsc is more recent
                                    item._triageStatusChanged = tscIn

                                if autoIn == "0":
                                    # an inbound auto of False always gets
                                    # applied
                                    item.doAutoTriageOnDateChange = False

                                conflict.discard()

                    if record.createdOn is not eim.NoChange:
                        # Instead of having conflicts for createdOn, apply the
                        # oldest value

                        if record.createdOn not in emptyValues:
                            createdOn = decimalToDatetime(record.createdOn)
                            if createdOn < item.createdOn:
                                item.createdOn = createdOn

                        conflict.discard()




    def obfuscate(self, text):
        if text in (eim.Inherit, eim.NoChange):
            return text

        if text and getattr(self, "obfuscation", False):
            def lipsum(length):
                # Return some text that has properties real text would have.
                corpus = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum." 
                if length <= len(corpus):
                    return corpus[:length]
                # Need to generate some additional stuff...
                ret = corpus
                words = corpus.split()
                import random
                shuffler = random.Random(1) # fixed seed on purpose
                while True:
                    shuffler.shuffle(words)
                    ret += os.linesep + ' '.join(words)
                    if len(ret) >= length:
                        return ret[:length]
                
            return lipsum(len(text)) 
        else:
            return text

    def getUUIDForAlias(self, alias):
        if ':' not in alias:
            return alias

        uuid, recurrenceID = splitUUID(alias)

        # find the occurrence and return itsUUID
        master = self.rv.findUUID(uuid)
        if master is not None and pim.has_stamp(master, pim.EventStamp):
            masterEvent = pim.EventStamp(master)
            occurrence = masterEvent.getExistingOccurrence(recurrenceID)
            if occurrence is not None:
                if self.getAliasForItem(occurrence) != alias:
                    # don't get fooled by getExistingOccurrence( ) which
                    # thinks that a floating tz matches a non-floater
                    # (related to bug 9207)
                    return None
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

    def deferredUUID(self, recurrence_aware_uuid, create=True):
        master_uuid, recurrenceID = splitUUID(recurrence_aware_uuid)
        if recurrenceID is not None:
            d = self.deferredItem(master_uuid, EventStamp)
            @d.addCallback
            def get_occurrence(master):           
                if getattr(master, 'rruleset', None) is None:
                    # add a dummy RecurrenceRuleSet so event methods treat
                    # the event as a master
                    master.rruleset = RecurrenceRuleSet(None, itsView=self.rv)
                    # Some event methods won't work if a master doesn't have
                    # a rruleset, but import_event's modification fixing needs
                    # to know if the real master's event has been processed
                    master.itsItem._fake = True
                occurrence = master.getRecurrenceID(recurrenceID)
                if occurrence is None:
                    if create:
                        occurrence = master._createOccurrence(recurrenceID)
                    else:
                        return None
                return occurrence.itsItem.itsUUID.str16()
            return d
        d = Deferred()
        d.callback(master_uuid)
        return d

    def deferredItem(self, uuid, *args, **kwargs):
        """
        Override to handle special recurrenceID:uuid uuids.
        """
        if isinstance(uuid, basestring) and ':' in uuid:
            uuid = self.deferredUUID(uuid)
        return super(SharingTranslator, self).deferredItem(uuid, *args, **kwargs)

    @model.ItemRecord.importer
    def import_item(self, record):

        if record.title is None:
            title = eim.Inherit # to delete the attribute
        else:
            title = record.title

        if record.createdOn not in emptyValues:
            # createdOn is a Decimal we need to change to datetime
            createdOn = decimalToDatetime(record.createdOn)
        else:
            createdOn = eim.NoChange

        @self.withItemForUUID(
            record.uuid,
            pim.ContentItem,
            displayName=title,
            createdOn=createdOn,
            needsReply=with_nochange(record.needsReply, bool),
            read=with_nochange(record.read, bool)
        )
        def do(item):
            if record.triage != "" and record.triage not in emptyValues:
                code, timestamp, auto = record.triage.split(" ")
                item._triageStatus = self.code_to_triagestatus[code]
                item._triageStatusChanged = float(timestamp)
                item.doAutoTriageOnDateChange = (auto == "1")

        # TODO: record.hasBeenSent --> item.modifiedFlags

    @eim.exporter(pim.ContentItem)
    def export_item(self, item):

        # TODO: see why many items don't have createdOn
        if not hasattr(item, 'createdOn'):
            item.createdOn = datetime.now(ICUtzinfo.default)

        # createdOn = handleEmpty(item, 'createdOn')
        # elif createdOn not in noChangeOrInherit:
        createdOn = datetimeToDecimal(item.createdOn)

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

        if item.hasLocalAttributeValue('displayName'):
            title = item.displayName
        else:
            if isinstance(item, Occurrence):
                title = eim.Inherit
            else:
                title = None

        yield model.ItemRecord(
            item,                                       # uuid
            self.obfuscate(title),                      # title
            triage,                                     # triage
            createdOn,                                  # createdOn
            0,                                          # hasBeenSent (TODO)
            handleEmpty(item, "needsReply"),            # needsReply
            handleEmpty(item, "read"),                  # read
        )

        # Also export a ModifiedByRecord
        lastModifiedBy = ""
        if hasattr(item, "lastModifiedBy"):
            emailAddress = item.lastModifiedBy
            if emailAddress is not None and emailAddress.emailAddress:
                lastModifiedBy = emailAddress.emailAddress

        lastModified = getattr(item, "lastModified", None)
        if lastModified:
            lastModified = datetimeToDecimal(lastModified)
        else:
            lastModified = createdOn

        lastModification = item.lastModification

        yield model.ModifiedByRecord(
            item,
            self.obfuscate(lastModifiedBy),
            lastModified,
            action = self.modaction_to_code.get(lastModification, 500)
        )

        reminder = item.getUserReminder()

        if reminder is None:
            description = None
            trigger = None
            duration = None
            repeat = None

        elif reminder.reminderItem is item: # this is our reminder
            trigger = None
            if reminder.hasLocalAttributeValue('delta'):
                trigger = toICalendarDuration(reminder.delta)
            elif reminder.hasLocalAttributeValue('absoluteTime'):
                # iCalendar Triggers are supposed to be expressed in UTC;
                # EIM may not require that but might as well be consistent
                reminderTime = reminder.absoluteTime.astimezone(utc)
                trigger = toICalendarDateTime(reminderTime, False)

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

        if item.private:
            yield model.PrivateItemRecord(item)



    @model.PrivateItemRecord.importer
    def import_privateItem(self, record):
        self.withItemForUUID(record.uuid, pim.ContentItem, private=True)


    # ModifiedByRecord  -------------

    @model.ModifiedByRecord.importer
    def import_modifiedBy(self, record):

        @self.withItemForUUID(record.uuid, pim.ContentItem)
        def do(item):
            # only apply a modifiedby record if timestamp is more recent than
            # what's on the item already

            logger.debug("Examining ModifiedByRecord: %s", record)

            existing = getattr(item, "lastModified", None)
            existing = datetimeToDecimal(existing) if existing else 0

            if record.timestamp >= existing:

                # record.userid can never be NoChange.  "" == anonymous
                if not record.userid:
                    item.lastModifiedBy = None
                else:
                    item.lastModifiedBy = \
                        pim.EmailAddress.getEmailAddress(self.rv, record.userid)

                # record.timestamp can never be NoChange, nor None
                # timestamp is a Decimal we need to change to datetime
                item.lastModified = decimalToDatetime(record.timestamp)

                if record.action is not eim.NoChange:
                    item.lastModification = \
                        self.code_to_modaction[record.action]

                #XXX Brian K: The modified flags were not getting set properly
                # without this addition.
                item.changeEditState(item.lastModification,
                                     item.lastModifiedBy,
                                     item.lastModified)

                logger.debug("Applied ModifiedByRecord: %s", record)
                logger.debug("Now lastModifiedBy is %s", item.lastModifiedBy)
            else:
                logger.debug("Skipped ModifiedByRecord: record %s vs local %s",
                    record.timestamp, existing)


        # Note: ModifiedByRecords are exported by item



    # NoteRecord -------------

    @model.NoteRecord.importer
    def import_note(self, record):

        if record.body is None:
            body = eim.Inherit # to delete the attribute
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

        if note.hasLocalAttributeValue('body'):
            body = note.body
        else:
            if isinstance(note, Occurrence):
                body = eim.Inherit
            else:
                body = None

        # when serializing iCalendar, modifications will incorrectly handle
        # a None value for icalUID if icalUID and UUID aren't the same, but in 
        # most cases, icalUID will be identical to UUID, just use None in that
        # case
        icalUID = handleEmpty(note, 'icalUID')
        if icalUID == unicode(note.itsUUID):
            icalUID = None


        yield model.NoteRecord(
            note,                                       # uuid
            self.obfuscate(body),                       # body
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
        d = self.deferredUUID(record.uuid, create=False)
        @d.addCallback
        def do_delete(uuid):
            if uuid is not None:
                item = self.rv.findUUID(uuid)
                if item is not None and item.isLive() and pim.has_stamp(
                    item, pim.TaskStamp
                ):
                    pim.TaskStamp(item).remove()

    @model.PasswordRecord.importer
    def import_password(self, record):
        self.withItemForUUID(
            record.uuid,
            Password,
            ciphertext=record.ciphertext,
            iv=record.iv,
            salt=record.salt,
        )

    @eim.exporter(Password)
    def export_password(self, password):

        if self.obfuscation: return

        ciphertext, iv, salt = waitForDeferred(password.recordTuple())
        yield model.PasswordRecord(password, ciphertext, iv, salt)

    @model.PasswordPrefsRecord.importer
    def import_password_prefs(self, record):
        # Hard coded UUID so this is enough for the dummyPassword
        self.withItemForUUID(record.dummyPassword, Password)

        prefs = schema.ns("osaf.framework.MasterPassword",
                  self.rv).masterPasswordPrefs
        prefs.masterPassword = bool(record.masterPassword)
        prefs.timeout = record.timeout
        protect = getattr(record, "protect", 0)
        if protect == 1:
            prefs.protect = True
        elif protect == 2:
            prefs.protect = False

    # Called from finishExport()
    def export_password_prefs(self):

        if self.obfuscation: return

        prefs = schema.ns("osaf.framework.password", self.rv).passwordPrefs
        dummyPassword = prefs.dummyPassword

        prefs = schema.ns("osaf.framework.MasterPassword",
                  self.rv).masterPasswordPrefs
        masterPassword = prefs.masterPassword
        timeout = prefs.timeout
        protect = getattr(prefs, "protect", None)
        if protect is None:
            protect = 0
        elif protect == True:
            protect = 1
        elif protect == False:
            protect = 2

        yield model.PasswordPrefsRecord(dummyPassword,
                                        1 if masterPassword else 0,
                                        timeout,
                                        protect)
        for record in self.export_password(dummyPassword):
            yield record

    #MailMessageRecord
    @model.MailMessageRecord.importer
    def import_mail(self, record):
        @self.withItemForUUID(
           record.uuid,
           pim.MailStamp,
           dateSentString=record.dateSent,
        )
        def do(mail):
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
                                mail.headers[prevKey] += "\n" + header

            if record.toAddress not in noChangeOrInherit:
                mail.toAddress = []
                if record.toAddress:
                    addEmailAddresses(self.rv, mail.toAddress, record.toAddress)

            if record.ccAddress not in noChangeOrInherit:
                mail.ccAddress = []

                if record.ccAddress:
                    addEmailAddresses(self.rv, mail.ccAddress, record.ccAddress)

            if record.bccAddress not in noChangeOrInherit:
                mail.bccAddress = []

                if record.bccAddress:
                    addEmailAddresses(self.rv, mail.bccAddress, record.bccAddress)

            if record.fromAddress not in noChangeOrInherit:
               if record.fromAddress:
                    mail.fromAddress = getEmailAddress(self.rv, record.fromAddress)
               else:
                   mail.fromAddress = None

            # text or email addresses in Chandler from field
            if record.originators not in noChangeOrInherit:
                if record.originators:
                    res = EmailAddress.parseEmailAddresses(self.rv, record.originators)

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

            if record.mimeContent not in noChangeOrInherit:
                if record.mimeContent:
                    # There is no attachment support for
                    # Preview. This is a place holder for
                    # future enhancements
                    pass

            if record.rfc2822Message not in noChangeOrInherit:
                if record.rfc2822Message:
                    mail.rfc2822Message = dataToBinary(mail, "rfc2822Message",
                                                       record.rfc2822Message,
                                                      'message/rfc822', 'bz2',
                                                       False)

            if record.previousSender not in noChangeOrInherit:
               if record.previousSender:
                    mail.previousSender = getEmailAddress(self.rv, record.previousSender)
               else:
                   mail.previousSender = None

            if record.replyToAddress not in noChangeOrInherit:
               if record.replyToAddress:
                    mail.replyToAddress = getEmailAddress(self.rv, record.replyToAddress)
               else:
                   mail.replyToAddress = None

            if record.messageState not in noChangeOrInherit:
                if record.messageState & MessageState.FROM_ME:
                    mail.fromMe = True
                else:
                    mail.fromMe = False

                if record.messageState & MessageState.TO_ME:
                    mail.toMe = True
                else:
                    mail.toMe = False

                if record.messageState & MessageState.VIA_MAILSERVICE:
                    mail.viaMailService = True
                else:
                    mail.viaMailService = False

                if record.messageState & MessageState.IS_UPDATED:
                    mail.isUpdated = True
                else:
                    mail.isUpdated = False

                if record.messageState & MessageState.FROM_EIMML:
                    mail.fromEIMML = True
                else:
                    mail.fromEIMML = False

                if record.messageState & MessageState.PREVIOUS_IN_RECIPIENTS:
                    mail.previousInRecipients = True
                else:
                    mail.previousInRecipients = False


    @eim.exporter(pim.MailStamp)
    def export_mail(self, mail):
        # Move to a local variable for a slight performance increase
        obf = self.obfuscation

        def format(ea):
            if obf:
                return u"%s@example.com" % ea.itsUUID

            return ea.format()


        headers = []


        for header in mail.headers:
            if obf:
                headers.append(u"%s: %s" % (header, self.obfuscate(mail.headers[header])))

            else:
                headers.append(u"%s: %s" % (header, mail.headers[header]))

        if headers:
            headers = u"\n".join(headers)
        else:
            headers = None

        toAddress = []

        for addr in mail.toAddress:
            toAddress.append(format(addr))

        if toAddress:
            toAddress = u", ".join(toAddress)
        else:
            toAddress = None

        ccAddress = []

        for addr in mail.ccAddress:
            ccAddress.append(format(addr))

        if ccAddress:
            ccAddress = u", ".join(ccAddress)
        else:
            ccAddress = None

        bccAddress = []

        for addr in mail.bccAddress:
            bccAddress.append(format(addr))

        if bccAddress:
            bccAddress = u", ".join(bccAddress)
        else:
            bccAddress = None

        originators = []

        if getattr(mail, "originators", None) is not None:
            for addr in mail.originators:
                originators.append(format(addr))


        if originators:
            originators = u", ".join(originators)
        else:
            originators = None

        fromAddress = None

        if getattr(mail, "fromAddress", None) is not None:
            fromAddress = format(mail.fromAddress)


        references = []

        for ref in mail.referencesMID:
            ref = ref.strip()

            if ref:
                if obf:
                    references.append(self.obfuscate(ref))

                else:
                    references.append(ref)

        if references:
            references = u" ".join(references)
        else:
            references = None

        inReplyTo = None
        if getattr(mail, "inReplyTo", None) is not None:
            if obf:
                 inReplyTo = self.obfuscate(mail.inReplyTo)
            else:
                inReplyTo = mail.inReplyTo

        messageId = None
        if getattr(mail, "messageId", None) is not None:
            if obf:
                messageId = self.obfuscate(mail.messageId)
            else:
                messageId = mail.messageId

        dateSent = None
        if getattr(mail, "dateSentString", None) is not None:
            dateSent = mail.dateSentString

        # Place holder for attachment support
        mimeContent = None
        rfc2822Message = None

        rfc2822Message = None
        if getattr(mail, "rfc2822Message", None) is not None:
            if obf:
                rfc2822Message = self.obfuscate(binaryToData(mail.rfc2822Message))
            else:
                rfc2822Message = binaryToData(mail.rfc2822Message)

        previousSender = None
        if getattr(mail, "previousSender", None) is not None:
            previousSender = format(mail.previousSender)

        replyToAddress = None
        if getattr(mail, "replyToAddress", None) is not None:
            replyToAddress = format(mail.replyToAddress)

        messageState = 0

        if mail.fromMe:
            messageState |= MessageState.FROM_ME

        if mail.toMe:
            messageState |= MessageState.TO_ME

        if mail.viaMailService:
            messageState |= MessageState.VIA_MAILSERVICE

        if mail.isUpdated:
            messageState |= MessageState.IS_UPDATED

        if mail.fromEIMML:
            messageState |= MessageState.FROM_EIMML

        if mail.previousInRecipients:
            messageState |= MessageState.PREVIOUS_IN_RECIPIENTS


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
            mimeContent,           #mimeContent
            rfc2822Message,        #rfc2822Message
            previousSender,        #previousSender
            replyToAddress,        #replyToAddress
            messageState,          #messageState
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
        duration = with_nochange(record.duration, fromICalendarDuration)
        if (allDay == True or anyTime == True) and duration not in emptyValues:
            # convert to Chandler's notion of all day duration
            duration -= oneDay
    
        uuid, recurrenceID = splitUUID(record.uuid)
        if recurrenceID and start in emptyValues:
            start = recurrenceID

        if (self.promptForTimezone and start not in emptyValues
            and start.tzinfo not in (ICUtzinfo.floating, None)):
            # got a timezoned event, prompt (non-modally) to turn on
            # timezones
            import wx
            app = wx.GetApp()
            if app is not None:
                from application.dialogs.TurnOnTimezones import ShowTurnOnTimezonesDialog
                def ShowTimezoneDialogCallback():
                    ShowTurnOnTimezonesDialog(view=app.UIRepositoryView)
                app.PostAsyncEvent(ShowTimezoneDialogCallback)
            self.promptForTimezone = False


        @self.withItemForUUID(
            record.uuid,
            EventStamp,
            startTime=start,
            duration=duration,
            transparency=with_nochange(record.status, fromTransparency),
            location=with_nochange(record.location, fromLocation, self.rv),
        )
        def do(item):
            event = EventStamp(item)

            # allDay and anyTime shouldn't be set if they match the master
            master = event.getMaster()
            if master == event:
                if hasattr(master.itsItem, '_fake'):
                    del master.itsItem._fake
                if allDay in (True, False):
                    event.allDay = allDay
                    # modifications may have been created before the master, so
                    # they may have unnecessarily set allDay
                    for mod in master.modifications:
                        modEvent = EventStamp(mod)
                        if modEvent.allDay == allDay:
                            delattr(modEvent, 'allDay')

                if anyTime in (True, False):
                    event.anyTime = anyTime
                    # modifications may have been created before the master, so
                    # they may have unnecessarily set anyTime
                    for mod in master.modifications:
                        modEvent = EventStamp(mod)
                        if modEvent.anyTime == anyTime:
                            delattr(modEvent, 'anyTime')
                            
            else:
                # a modification
                fakeMaster = getattr(master.itsItem, '_fake', False)

                # set attributes that may want to be inherited.
                if allDay in (True, False) and (fakeMaster or
                                                allDay != master.allDay):
                    event.allDay = allDay
                elif allDay == eim.Inherit:
                    delattr(event, 'allDay')
    
                if anyTime in (True, False) and (fakeMaster or
                                                 anyTime != master.anyTime):
                    event.anyTime = anyTime
                elif anyTime == eim.Inherit:
                    delattr(event, 'anyTime')
                        
                if not fakeMaster:
                    fixTimezoneOnModification(event)
                # modifications don't have recurrence rule information, so stop
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
            else:
                if event.rruleset is not None:
                    # changed existing recurrence
                    event.rruleset._ignoreValueChanges = ignoreChanges
                    event.cleanRule()
                else:
                    # new recurrence
                    event.rruleset = rruleset
                # search through modifications in case they were created before
                # the master, if they're timezoned they'll have recurrenceID in
                # UTC, worse, if they inherit startTime it'll be in UTC
                tzinfo = event.effectiveStartTime.tzinfo
                if tzinfo != ICUtzinfo.floating:
                    for mod in event.modifications:
                        fixTimezoneOnModification(mod, tzinfo)

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
            not datetimes_really_equal(event.effectiveStartTime,
                                       event.recurrenceID)):
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
            self.obfuscate(location),                   # location
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
            # Rather than simply leaving out a DisplayAlarmRecord, we're using
            # a trigger value of None to indicate there is no alarm:
            if record.trigger is None:
                item.reminders = []

            elif record.trigger not in noChangeOrInherit:
                # trigger translates to either a pim.Reminder (if a date(time),
                # or a pim.RelativeReminder (if a timedelta).
                kw = dict(itsView=item.itsView)
                reminderFactory = None

                try:
                    val = fromICalendarDateTime(record.trigger)[0]
                    val = val.astimezone(ICUtzinfo.default)
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
                    if record.duration is None:
                        delattr(reminder, 'duration') # has a defaultValue
                    else:
                        reminder.duration = stringToDurations(record.duration)[0]

                if record.repeat not in noChangeOrInherit:
                    if record.repeat is None:
                        reminder.repeat = 0
                    else:
                        reminder.repeat = record.repeat

    @model.DisplayAlarmRecord.deleter
    def delete_alarm(self, record):
        item = self.rv.findUUID(self.getUUIDForAlias(record.uuid))
        item.reminders = []






class DumpTranslator(SharingTranslator):

    URI = "cid:dump-translator@osaf.us"
    version = 1
    description = u"Translator for Chandler items (PIM and non-PIM)"


    # Mapping for well-known names to/from their current repository path
    path_to_name = {
        "//parcels/osaf/app/sidebarCollection" : "@sidebar",
    }
    name_to_path = dict([[v, k] for k, v in path_to_name.items()])


    approvedClasses = (
        pim.Note, Password, pim.SmartCollection, shares.Share,
        conduits.BaseConduit, shares.State, accounts.SharingAccount,
        mail.AccountBase, mail.IMAPFolder
    )

    def exportItem(self, item):
        """
        Export an item and its stamps, if any.

        Recurrence changes:
        - Avoid exporting occurrences unless they're modifications.
        - Don't serialize recurrence rule items

        """

        if not isinstance(item, self.approvedClasses):
            return

        elif isinstance(item, Occurrence):
            if not EventStamp(item).modificationFor:
                return

        for record in super(DumpTranslator, self).exportItem(item):
            yield record


    # - - Collection  - - - - - - - - - - - - - - - - - - - - - - - - - - -
    @model.CollectionRecord.importer
    def import_collection(self, record):
        @self.withItemForUUID(record.uuid, pim.SmartCollection)
        def add_source(collection):
            if record.mine == 1:
                schema.ns('osaf.pim', self.rv).mine.addSource(collection)
            if record.colorRed is not None:
                UserCollection(collection).color = ColorType(
                    record.colorRed, record.colorGreen, record.colorBlue,
                    record.colorAlpha
                )

    @eim.exporter(pim.SmartCollection)
    def export_collection(self, collection):
        try:
            color = UserCollection (collection).color
            red = color.red
            green = color.green
            blue = color.blue
            alpha = color.alpha
        except AttributeError: # collection has no color
            red = green = blue = alpha = None

        yield model.CollectionRecord(
            collection,
            int (collection in schema.ns('osaf.pim', self.rv).mine.sources),
            red,
            green,
            blue,
            alpha
        )
        for record in self.export_collection_memberships (collection):
            yield record


    def export_collection_memberships(self, collection):
        index = 0

        # For well-known collections, use their well-known name rather than
        # their UUID
        collectionID = self.path_to_name.get(str(collection.itsPath),
            collection.itsUUID.str16())

        for item in collection:
            # By default we don't include items that are in
            # //parcels since they are not created by the user

            if (not str(item.itsPath).startswith("//parcels") and
                not isinstance(item, Occurrence)):
                yield model.CollectionMembershipRecord(
                    collectionID,
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

        id = record.collectionID

        # Map old hard-coded sidebar UUID to its well-known name
        if id == "3c58ae62-d8d6-11db-86bb-0017f2ca1708":
            id = "@sidebar"

        id = self.name_to_path.get(id, id)

        if id.startswith("//"):
            collection = self.rv.findPath(id)
            # We're preserving order of items in collections
            # assert (self.indexIsInSequence (collection, record.index))
            @self.withItemForUUID(record.itemUUID, pim.ContentItem)
            def do(item):
                collection.add(item)

        else:
            # Assume that non-existent collections should be created as
            # SmartCollections; otherwise don't upgrade from ContentCollection
            # base
            collectionType = (
                pim.SmartCollection if self.rv.findUUID(id) is None
                else pim.ContentCollection
            )
            @self.withItemForUUID(id, collectionType)
            def do(collection):
                # We're preserving order of items in collections
                # assert (self.indexIsInSequence (collection, record.index))
                @self.withItemForUUID(record.itemUUID, pim.ContentItem)
                def do(item):
                    collection.add(item)


    @model.DashboardMembershipRecord.importer
    def import_dashboard_membership(self, record):
        @self.withItemForUUID(record.itemUUID, pim.ContentItem)
        def do(item):
            dashboard = schema.ns("osaf.pim", self.rv).allCollection
            dashboard.add(item)




    # - - Sharing-related items - - - - - - - - - - - - - - - - - - - - - -

    @model.ShareRecord.importer
    def import_sharing_share(self, record):

        @self.withItemForUUID(record.uuid,
            shares.Share,
            established=True,
            error=record.error,
            errorDetails=record.errorDetails,
            mode=record.mode
        )
        def do(share):
            if record.lastSuccess not in (eim.NoChange, None):
                # lastSuccess is a Decimal we need to change to datetime
                share.lastSuccess = decimalToDatetime(record.lastSuccess)

            if record.lastAttempt not in (eim.NoChange, None):
                # lastAttempt is a Decimal we need to change to datetime
                share.lastAttempt = decimalToDatetime(record.lastAttempt)

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
    def export_sharing_share(self, share):

        if self.obfuscation: return

        contents = share.contents.itsUUID

        conduit = share.conduit.itsUUID

        subscribed = 0 if utility.isSharedByMe(share) else 1

        error = getattr(share, "error", "")

        errorDetails = getattr(share, "errorDetails", "")

        mode = share.mode

        if hasattr(share, "lastSuccess"):
            lastSuccess = datetimeToDecimal(share.lastSuccess)
        else:
            lastSuccess = None

        if hasattr(share, "lastAttempt"):
            lastAttempt = datetimeToDecimal(share.lastSuccess)
        else:
            lastAttempt = None

        yield model.ShareRecord(
            share,
            contents,
            conduit,
            subscribed,
            error,
            errorDetails,
            mode,
            lastSuccess,
            lastAttempt
        )



    @model.ShareConduitRecord.importer
    def import_sharing_conduit(self, record):
        self.withItemForUUID(record.uuid,
            conduits.BaseConduit,
            sharePath=record.path,
            shareName=record.name
        )

    @eim.exporter(conduits.BaseConduit)
    def export_sharing_conduit(self, conduit):

        if self.obfuscation: return

        path = conduit.sharePath
        name = conduit.shareName

        yield model.ShareConduitRecord(
            conduit,
            path,
            name
        )




    @model.ShareRecordSetConduitRecord.importer
    def import_sharing_recordset_conduit(self, record):
        @self.withItemForUUID(record.uuid,
            recordset_conduit.RecordSetConduit,
            syncToken=record.syncToken
        )
        def do(conduit):
            if record.serializer == "eimml":
                conduit.serializer = eimml.EIMMLSerializer
            if record.serializer == "eimml_lite":
                conduit.serializer = eimml.EIMMLSerializerLite

            # if record.translator == "sharing":
            conduit.translator = SharingTranslator

            if record.filters not in (None, eim.NoChange):
                for filter in record.filters.split(","):
                    if filter:
                        conduit.filters.add(filter)

    @eim.exporter(recordset_conduit.RecordSetConduit)
    def export_sharing_recordset_conduit(self, conduit):

        if self.obfuscation: return

        translator = "sharing"

        if conduit.serializer is eimml.EIMMLSerializer:
            serializer = 'eimml'
        elif conduit.serializer is eimml.EIMMLSerializerLite:
            serializer = 'eimml_lite'

        filters = ",".join(conduit.filters)

        syncToken = conduit.syncToken

        yield model.ShareRecordSetConduitRecord(
            conduit,
            translator,
            serializer,
            filters,
            syncToken
        )




    @model.ShareHTTPConduitRecord.importer
    def import_sharing_http_conduit(self, record):

        @self.withItemForUUID(record.uuid, conduits.HTTPMixin,
            ticket=record.ticket,
            ticketReadWrite=record.ticket_rw,
            ticketReadOnly=record.ticket_ro)
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
                    if record.password not in (eim.NoChange, None):
                        @self.withItemForUUID(record.password, Password)
                        def do_password(password):
                            if hasattr(conduit, 'password'):
                                conduit.password.delete()
                            conduit.password = password

    @eim.exporter(conduits.HTTPMixin)
    def export_sharing_http_mixin(self, conduit):

        if self.obfuscation: return

        ticket = conduit.ticket
        ticket_rw = conduit.ticketReadWrite
        ticket_ro = conduit.ticketReadOnly

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
            password = getattr(conduit, "password", None)

        yield model.ShareHTTPConduitRecord(
            conduit,
            ticket,
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
    def import_sharing_cosmo_conduit(self, record):

        self.withItemForUUID(record.uuid,
            cosmo.CosmoConduit,
            morsecodePath = record.morsecodepath
        )

    @eim.exporter(cosmo.CosmoConduit)
    def export_sharing_cosmo_conduit(self, conduit):

        if self.obfuscation: return

        yield model.ShareCosmoConduitRecord(
            conduit,
            conduit.morsecodePath
        )



    @model.ShareWebDAVConduitRecord.importer
    def import_sharing_webdav_conduit(self, record):

        self.withItemForUUID(record.uuid,
            webdav_conduit.WebDAVRecordSetConduit
        )

    @eim.exporter(webdav_conduit.WebDAVRecordSetConduit)
    def export_sharing_webdav_conduit(self, conduit):

        if self.obfuscation: return

        yield model.ShareWebDAVConduitRecord(
            conduit
        )




    @model.ShareStateRecord.importer
    def import_sharing_state(self, record):

        if record.agreed is None:
            agreed = eim.Inherit # perhaps Inherit was better as Missing; I'm
                                 # using it here to delete the attribute
        else:
            agreed = record.agreed

        if record.pending is None:
            pending = eim.Inherit # perhaps Inherit was better as Missing; I'm
                                  # using it here to delete the attribute
        else:
            pending = record.pending

        @self.withItemForUUID(record.uuid,
            shares.State,
            _agreed=agreed,
            _pending=pending,
        )
        def do(state):
            if record.share not in (eim.NoChange, None):

                @self.withItemForUUID(record.share, shares.Share)
                def do_share(share):

                    if state not in share.states:
                        share.states.append(state, record.alias)
                    state.peer = share

                    if record.conflict_share:
                        state.conflictingShare = share

            if record.conflict_item:
                @self.withItemForUUID(record.conflict_item, shares.SharedItem)
                def do_item(sharedItem):
                    state.conflictFor = sharedItem.itsItem

    @eim.exporter(shares.State)
    def export_sharing_state(self, state):

        if self.obfuscation: return

        share = state.share.itsUUID if getattr(state, "share", None) else None
        if share is not None:
            alias = state.share.states.getAlias(state)
        else:
            alias = None

        conflict_item = getattr(state, "conflictFor", None)
        conflict_share = getattr(state, "conflictingShare", None)

        agreed = getattr(state, "_agreed", None)
        pending = getattr(state, "_pending", None)

        yield model.ShareStateRecord(
            state,
            share,
            alias,
            conflict_item,
            conflict_share,
            agreed,
            pending
        )



    @model.SharePeerStateRecord.importer
    def import_sharing_peer_state(self, record):

        @self.withItemForUUID(record.uuid, shares.State,
            peerRepoId=record.peerrepo,
            peerItemVersion=record.peerversion
        )
        def do(state):
            if record.peer not in (eim.NoChange, None):
                @self.withItemForUUID(record.peer, schema.Item)
                def do_peer(peer):
                    state.peer = peer

            if record.item not in (eim.NoChange, None):
                @self.withItemForUUID(record.item, shares.SharedItem)
                def do_item(sharedItem):
                    if hasattr(sharedItem, 'peerStates') and \
                       state not in sharedItem.peerStates:
                        sharedItem.peerStates.append(state, record.peer)

    # SharePeerStateRecords are generated in SharedItem's exporter


    @model.ShareSharedInRecord.importer
    def import_sharing_shared_in(self, record):

        @self.withItemForUUID(record.item, shares.SharedItem)
        def do_item(sharedItem):
            @self.withItemForUUID(record.share, shares.Share)
            def do_share(share):
                sharedItem.sharedIn.append(share)


    @eim.exporter(shares.SharedItem)
    def export_sharing_shared_item(self, sharedItem):

        if self.obfuscation: return

        for share in sharedItem.sharedIn:
            yield model.ShareSharedInRecord(
                sharedItem.itsItem,
                share
            )

        for state in getattr(sharedItem, "peerStates", []):
            alias = sharedItem.peerStates.getAlias(state)
            uuid = state
            peer = state.peer
            item = sharedItem.itsItem
            peerrepo = state.peerRepoId
            peerversion = state.peerItemVersion

            yield model.SharePeerStateRecord(
                uuid,
                peer,
                item,
                peerrepo,
                peerversion
            )




    @model.ShareResourceStateRecord.importer
    def import_sharing_resource_state(self, record):

        self.withItemForUUID(record.uuid,
            recordset_conduit.ResourceState,
            path=record.path,
            etag=record.etag
        )

    @eim.exporter(recordset_conduit.ResourceState)
    def export_sharing_resource_state(self, state):

        if self.obfuscation: return

        path = getattr(state, "path", None)
        etag = getattr(state, "etag", None)

        yield model.ShareResourceStateRecord(
            state,
            path,
            etag
        )



    @model.ShareAccountRecord.importer
    def import_sharing_account(self, record):

        @self.withItemForUUID(record.uuid,
            accounts.SharingAccount,
            host=record.host,
            port=record.port,
            path=record.path,
            username=record.username
        )
        def do(account):
            if record.ssl not in (eim.NoChange, None):
                account.useSSL = True if record.ssl else False
            if record.password not in (eim.NoChange, None):
                @self.withItemForUUID(record.password, Password)
                def do_password(password):
                    if hasattr(account, 'password'):
                        account.password.delete()
                    account.password = password


    @eim.exporter(accounts.SharingAccount)
    def export_sharing_account(self, account):

        if self.obfuscation: return

        yield model.ShareAccountRecord(
            account,
            account.host,
            account.port,
            1 if account.useSSL else 0,
            account.path,
            account.username,
            getattr(account, "password", None)
        )




    @model.ShareWebDAVAccountRecord.importer
    def import_sharing_webdav_account(self, record):

        self.withItemForUUID(record.uuid,
            accounts.WebDAVAccount
        )

    @eim.exporter(accounts.WebDAVAccount)
    def export_sharing_webdav_account(self, account):

        if self.obfuscation: return

        yield model.ShareWebDAVAccountRecord(account)



    @model.ShareCosmoAccountRecord.importer
    def import_sharing_cosmo_account(self, record):

        self.withItemForUUID(record.uuid,
            cosmo.CosmoAccount,
            pimPath=record.pimpath,
            morsecodePath=record.morsecodepath,
            davPath=record.davpath
        )

    @eim.exporter(cosmo.CosmoAccount)
    def export_sharing_cosmo_account(self, account):

        if self.obfuscation: return

        yield model.ShareCosmoAccountRecord(
            account,
            account.pimPath,
            account.morsecodePath,
            account.davPath
        )



    @model.ShareHubAccountRecord.importer
    def import_sharing_hub_account(self, record):

        self.withItemForUUID(record.uuid, cosmo.HubAccount)

    @eim.exporter(cosmo.HubAccount)
    def export_sharing_hub_account(self, account):

        if self.obfuscation: return

        yield model.ShareHubAccountRecord(account)







    # - - Mail-related items - - - - - - - - - - - - - - - - - - - - - -


    @model.MailAccountRecord.importer
    def import_mail_account(self, record):
        @self.withItemForUUID(record.uuid,
            mail.AccountBase,
            host=record.host,
            username=record.username,
            numRetries=record.retries,
            pollingFrequency=record.frequency,
            #Timeout removed from MailStamp schema
            #timeout=record.timeout,
        )
        def do(account):
            if record.connectionType not in (eim.NoChange, None):
                account.connectionSecurity = record.connectionType == 0 and 'NONE' or \
                                             record.connectionType == 1 and 'TLS' or 'SSL'

            if record.active not in (eim.NoChange, None):
                account.isActive = record.active == 1

    @eim.exporter(mail.AccountBase)
    def export_mail_account(self, account):

        if self.obfuscation: return

        connectionType = 0

        if account.connectionSecurity == "TLS":
            connectionType = 1
        elif account.connectionSecurity == "SSL":
            connectionType = 2

        yield model.MailAccountRecord(
            account,
            account.numRetries,
            account.username,
            account.host,
            connectionType,
            account.pollingFrequency,
            #Timeout removed from MailStamp schema
            None,
            account.isActive and 1 or 0,)


    @model.SMTPAccountRecord.importer
    def import_smtp_account(self, record):
        @self.withItemForUUID(record.uuid, mail.SMTPAccount)
        def do(account):
            if record.password not in (eim.NoChange, None):
                @self.withItemForUUID(record.password, Password)
                def do_password(password):
                    if hasattr(account, 'password'):                    
                        account.password.delete()
                    account.password = password

            if record.useAuth not in (eim.NoChange, None):
                account.useAuth = record.useAuth == 1

            if record.fromAddress not in (eim.NoChange, None):
                account.fromAddress = getEmailAddress(self.rv, record.fromAddress)

            if record.port not in (eim.NoChange, None):
                account.port = record.port

            if record.isDefault not in (eim.NoChange, None) and \
                record.isDefault:
                ns = schema.ns("osaf.pim", self.rv)

                oldAccount = ns.currentOutgoingAccount.item

                if oldAccount and not oldAccount.host.strip():
                    # The current account is empty
                    oldAccount.isActive = False

                ns.currentOutgoingAccount.item = account

    @eim.exporter(mail.SMTPAccount)
    def export_smtp_account(self, account):

        if self.obfuscation: return

        ns = schema.ns("osaf.pim", self.rv)

        if hasattr(account, "fromAddress") and account.fromAddress:
            fromAddress = account.fromAddress.format()
        else:
            fromAddress = None

        isDefault = ns.currentOutgoingAccount.item == account and 1 or 0

        yield model.SMTPAccountRecord(
            account,
            getattr(account, 'password', None),
            fromAddress,
            account.useAuth and 1 or 0,
            account.port,
            isDefault)

        for record in self.export_smtp_account_queue(account):
            yield record

    def export_smtp_account_queue(self, account):
        for msg in account.messageQueue:
            yield model.SMTPAccountQueueRecord(
                    account,
                    msg.itsUUID,)

    @model.SMTPAccountQueueRecord.importer
    def import_smtp_account_queue(self, record):
        @self.withItemForUUID(record.smtpAccountUUID)
        def do(account):
            @self.withItemForUUID(record.itemUUID, pim.ContentItem)
            def do(item):
                account.messageQueue.append(item)

    @model.IMAPAccountRecord.importer
    def import_imap_account(self, record):
        @self.withItemForUUID(record.uuid, mail.IMAPAccount)
        def do(account):
            #The Inbox is created by default so clear it out
            inbox = account.folders.first()
            account.folders = []
            inbox.delete()

            if record.password not in (eim.NoChange, None):
                @self.withItemForUUID(record.password, Password)
                def do_password(password):
                    if hasattr(account, 'password'):
                        account.password.delete()
                    account.password = password

            if record.replyToAddress not in (eim.NoChange, None):
                account.replyToAddress = getEmailAddress(self.rv, record.replyToAddress)

            if record.port not in (eim.NoChange, None):
                account.port = record.port

            if record.isDefault not in (eim.NoChange, None) and \
                record.isDefault:
                ns = schema.ns("osaf.pim", self.rv)

                oldAccount = ns.currentIncomingAccount.item

                if oldAccount and not oldAccount.host.strip():
                    # The current account is empty
                    oldAccount.isActive = False

                ns.currentIncomingAccount.item = account


    @eim.exporter(mail.IMAPAccount)
    def export_imap_account(self, account):

        if self.obfuscation: return

        ns = schema.ns("osaf.pim", self.rv)

        if hasattr(account, "replyToAddress") and account.replyToAddress:
            replyToAddress = account.replyToAddress.format()
        else:
            replyToAddress = None

        isDefault = ns.currentIncomingAccount.item == account and 1 or 0

        yield model.IMAPAccountRecord(
            account,
            getattr(account, 'password', None),
            replyToAddress,
            account.port,
            isDefault)

        for record in self.export_imap_account_folders(account):
            yield record

    def export_imap_account_folders(self, account):
        for folder in account.folders:
            yield model.IMAPAccountFoldersRecord(
                    account,
                    folder.itsUUID,)

    @model.IMAPAccountFoldersRecord.importer
    def import_imap_account_folders(self, record):
        @self.withItemForUUID(record.imapAccountUUID)
        def do(account):
            @self.withItemForUUID(record.imapFolderUUID, mail.IMAPFolder)
            def do(folder):
                account.folders.append(folder)


    @model.IMAPFolderRecord.importer
    def import_imap_folder(self, record):
        @self.withItemForUUID(record.uuid, mail.IMAPFolder,
                              folderName=record.name,
                              folderType=record.type,
                              lastMessageUID=record.lastUID,
                              downloaded=record.downloaded,
                              downloadMax=record.downloadMax)
        def do(folder):
            folder.deleteOnDownload = record.delete == 1


    @eim.exporter(mail.IMAPFolder)
    def export_imap_folder(self, folder):

        if self.obfuscation: return

        yield model.IMAPFolderRecord(
            folder,
            folder.folderName,
            folder.folderType,
            folder.lastMessageUID,
            folder.deleteOnDownload and 1 or 0,
            folder.downloaded,
            folder.downloadMax,
        )

    @model.POPAccountRecord.importer
    def import_pop_account(self, record):
        @self.withItemForUUID(record.uuid, mail.POPAccount,
                              actionType=record.type,
                              downloaded=record.downloaded,
                              downloadMax=record.downloadMax)
        def do(account):
            if record.password not in (eim.NoChange, None):
                @self.withItemForUUID(record.password, Password)
                def do_password(password):
                    if hasattr(account, 'password'):
                        account.password.delete()
                    account.password = password

            if record.replyToAddress not in (eim.NoChange, None):
                account.replyToAddress = getEmailAddress(self.rv, record.replyToAddress)

            if record.delete not in (eim.NoChange, None):
                account.deleteOnDownload = record.delete == 1

            account.seenMessageUIDS = {}

            if record.seenUIDS not in (eim.NoChange, None):
                uids = record.seenUIDS.split("\n")

                for uid in uids:
                    account.seenMessageUIDS[uid] = "True"

            if record.port not in (eim.NoChange, None):
                account.port = record.port

            if record.isDefault not in (eim.NoChange, None) and \
                record.isDefault:
                ns = schema.ns("osaf.pim", self.rv)

                oldAccount = ns.currentIncomingAccount.item

                if oldAccount and not oldAccount.host.strip():
                    # The current account is empty
                    oldAccount.isActive = False

                ns.currentIncomingAccount.item = account


    @eim.exporter(mail.POPAccount)
    def export_pop_account(self, account):

        if self.obfuscation: return

        ns = schema.ns("osaf.pim", self.rv)

        if hasattr(account, "replyToAddress") and account.replyToAddress:
            replyToAddress = account.replyToAddress.format()
        else:
            replyToAddress = None

        seenUIDS = []

        for uid in account.seenMessageUIDS:
            seenUIDS.append(uid)

        if seenUIDS:
            seenUIDS = "\n".join(seenUIDS)
        else:
            seenUIDS = None

        isDefault = ns.currentIncomingAccount.item == account and 1 or 0

        yield model.POPAccountRecord(
            account,
            getattr(account, 'password', None),
            replyToAddress,
            account.actionType,
            account.deleteOnDownload and 1 or 0,
            account.downloaded,
            account.downloadMax,
            seenUIDS,
            account.port,
            isDefault,
        )



    @model.MailPrefsRecord.importer
    def import_mail_prefs(self, record):
        if record.isOnline not in (eim.NoChange, None):
            isOnline = record.isOnline == 1
            schema.ns("osaf.pim", self.rv).MailPrefs.isOnline = isOnline


        if record.meAddressHistory not in (eim.NoChange, None):
            col = schema.ns("osaf.pim", self.rv).meEmailAddressCollection
            addresses = record.meAddressHistory.split("\n")

            for address in addresses:
                col.append(getEmailAddress(self.rv, address))

    # Called from finishExport()
    def export_mail_prefs(self):
        isOnline = schema.ns("osaf.pim", self.rv).MailPrefs.isOnline and 1 or 0
        col = schema.ns("osaf.pim", self.rv).meEmailAddressCollection

        meAddressHistory = []

        for ea in col:
            meAddressHistory.append(ea.format())

        if meAddressHistory:
            meAddressHistory = "\n".join(meAddressHistory)
        else:
            meAddressHistory = None

        yield model.MailPrefsRecord(isOnline, meAddressHistory)


    # - - Preference items - - - - - - - - - - - - - - - - - - - - - - - - - -

    @model.PrefCalendarHourHeightRecord.importer
    def import_prefcalendarhourheight(self, record):
        pref = schema.ns('osaf.framework.blocks.calendar',
            self.rv).calendarPrefs
        pref.hourHeightMode = record.hourHeightMode
        pref.visibleHours = record.visibleHours

    # Called from finishExport( )
    def export_prefcalendarhourheight(self):
        pref = schema.ns('osaf.framework.blocks.calendar',
            self.rv).calendarPrefs

        yield model.PrefCalendarHourHeightRecord(
            pref.hourHeightMode,
            pref.visibleHours
        )

    @model.PrefTimezonesRecord.importer
    def import_preftimezones(self, record):

        pref = schema.ns('osaf.pim', self.rv).TimezonePrefs
        pref.showUI = bool(record.showUI)
        pref.showPrompt = bool(record.showPrompt)

        tzitem = TimeZone.TimeZoneInfo.get(self.rv)
        tzitem.default = ICUtzinfo.getInstance(record.default)
        tzitem.wellKnownIDs = record.wellKnownIDs.split(',')

    # Called from finishExport( )
    def export_preftimezones(self):

        pref = schema.ns('osaf.pim', self.rv).TimezonePrefs
        tzitem = TimeZone.TimeZoneInfo.get(self.rv)
        yield model.PrefTimezonesRecord(
            pref.showUI,
            pref.showPrompt,
            tzitem.default.tzid,
            ",".join(tzitem.wellKnownIDs)
        )








    # - - Finishing up - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def finishImport(self):
        super(DumpTranslator, self).finishImport()
        ootb.prepareAccounts(self.rv)


    def finishExport(self):
        for record in super(DumpTranslator, self).finishExport():
            yield record

        # emit the CollectionMembership records for the sidebar collection
        for record in self.export_collection_memberships(schema.ns("osaf.app",
            self.rv).sidebarCollection):
            yield record

        # emit the DashboardMembership records
        for item in schema.ns("osaf.pim", self.rv).allCollection.inclusions:
            if not str(item.itsPath).startswith("//parcels"):
                yield model.DashboardMembershipRecord(item)


        if not self.obfuscation:

            # mail
            for record in self.export_mail_prefs():
                yield record

            # calendar prefs
            for record in self.export_prefcalendarhourheight():
                yield record
            for record in self.export_preftimezones():
                yield record

            # passwords prefs
            for record in self.export_password_prefs():
                yield record


def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'Translator.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )

