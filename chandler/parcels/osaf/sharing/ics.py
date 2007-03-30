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

from osaf.sharing import model, eim, RecordSet, translator
from osaf.sharing.translator import toICalendarDuration, toICalendarDateTime
from ICalendar import makeNaiveteMatch
import vobject
from datetime import datetime, timedelta, date
from PyICU import ICUtzinfo
from osaf.pim.calendar.TimeZone import convertToICUtzinfo, forceToDateTime
from chandlerdb.util.c import UUID
import md5
from itertools import chain

from vobject.base import textLineToContentLine

__all__ = [
    'ICSSerializer',
]

utc = ICUtzinfo.getInstance('UTC')

def no_op(*args, **kwds):
    pass

def getVevent(recordSet, vevents):
    uuid = recordSet.uuid
    vevent = vevents.get(uuid)
    if vevent is None:
        vevent = vobject.newFromBehavior('vevent')
        vevent.isNative = True
        vevents[uuid] = vevent
    return vevent

"""
Translate data in recordsets into fields in a vevent.

vevents should be a dictionary mapping UUIDs to vobject vevents.  A
dictionary is needed to handle recurrence, which may generate new vevents.
"""

def UUIDFromICalUID(uid):
    try:
        # See if uid is a valid repository UUID, if so we'll
        # go ahead and use it for the new item's UUID.
        uuid = UUID(uid)
    except ValueError:
        # Not in valid UUID format, so hash the icaluid to
        # generate a 16-byte string we can use for uuid
        uuid = UUID(md5.new(uid).digest())
    return str(uuid)
    
def registerTZID(vobj):
    tzid = getattr(vobj, 'tzid_param', None)
    # add an appropriate tzinfo to vobject's tzid->tzinfo cache
    if tzid is not None and vobject.icalendar.getTzid(tzid) is None:
        vobject.icalendar.registerTzid(tzid, ICUtzinfo.getInstance(tzid))

def readEventRecord(eventRecordSet, vevents):
    vevent = getVevent(eventRecordSet, vevents)
    master = None

    uuid, recurrenceID = translator.splitUUID(eventRecordSet.uuid)
    if recurrenceID is not None:
        master = vevents[uuid]
        m_start = master.dtstart
        anyTime = False
        if getattr(m_start, 'value_param', '') == 'DATE':
            recurrenceID = recurrenceID.date()
            anyTime = (getattr(m_start, 'x_osaf_anytime_param', '') == 'TRUE')
        elif recurrenceID.tzinfo == ICUtzinfo.floating:
            recurrenceID = recurrenceID.replace(tzinfo=None)
        vevent.add('recurrence-id').value = recurrenceID
        
    if eventRecordSet.dtstart in translator.emptyValues:
        if recurrenceID is not None:
            dtstart = vevent.add('dtstart')
            dtstart.value = recurrenceID
            if anyTime:
                dtstart.x_osaf_anytime_param = "TRUE"
    else:
        vevent.dtstart = textLineToContentLine("DTSTART" +
                                               eventRecordSet.dtstart)
        registerTZID(vevent.dtstart)

    for name in ['duration', 'status', 'location']:
        eimValue = getattr(eventRecordSet, name)
        if eimValue not in translator.emptyValues:
            line = vevent.add(name)
            line.value = eimValue
            line.isNative = False

    if hasattr(vevent, 'duration'):
        vevent.duration.value = vevent.duration.value.upper()
    elif recurrenceID:
        vevent.add('duration').value = master.duration.value
        vevent.duration.isNative = False
        
    timestamp = datetime.utcnow()
    vevent.add('dtstamp').value = timestamp.replace(tzinfo=utc)
    # rruleset
    for rule_name in ('rrule', 'exrule'):
        rules = []
        record_value = getattr(eventRecordSet, rule_name)
        if record_value not in translator.emptyValues:
            for rule_value in record_value.split(':'):
                # EIM concatenates multiple rules with :
                rules.append(textLineToContentLine(rule_name + ":" + rule_value))
        vevent.contents[rule_name] = rules

    for date_name in ('rdate', 'exdate'):
        record_value = getattr(eventRecordSet, date_name)
        if record_value not in translator.emptyValues:
            # multiple dates should always be on one line
            setattr(vevent, date_name, 
                    textLineToContentLine(date_name + record_value))

def readNoteRecord(noteRecordSet, vevents):
    vevent = getVevent(noteRecordSet, vevents)
    if noteRecordSet.body not in translator.emptyValues:
        vevent.add('description').value = noteRecordSet.body
    icalUID = noteRecordSet.icalUid
    if icalUID in translator.emptyValues:
        # empty icalUID for a master means use uuid, for a modification it means
        # inherit icalUID
        uuid, recurrenceID = translator.splitUUID(noteRecordSet.uuid)
        if recurrenceID is None:
            icalUID = uuid
        else:
            icalUID = vevents[uuid].uid.value
    vevent.add('uid').value = icalUID


def readItemRecord(itemRecordSet, vevents):
    vevent = getVevent(itemRecordSet, vevents)
    if itemRecordSet.title not in translator.emptyValues:
        vevent.add('summary').value = itemRecordSet.title

def readAlarmRecord(alarmRecordSet, vevents):
    vevent = getVevent(alarmRecordSet, vevents)
    if alarmRecordSet.trigger not in translator.emptyValues:
        valarm = vevent.add('valarm')
        try:
            val = translator.fromICalendarDateTime(alarmRecordSet.trigger)[0]
            valarm.add('trigger').value = val
        except:
            valarm.trigger = textLineToContentLine("TRIGGER:" + 
                                                   alarmRecordSet.trigger)
        if alarmRecordSet.description not in translator.emptyValues:
            valarm.add('description').value = alarmRecordSet.description
        if alarmRecordSet.repeat not in translator.emptyValues:
            valarm.add('repeat').value = str(alarmRecordSet.repeat)
        if alarmRecordSet.duration not in translator.emptyValues:
            valarm.add('repeat').value = str(alarmRecordSet.duration)
            valarm.repeat.isNative = False

recordHandlers = {model.EventRecord : readEventRecord,
                  model.NoteRecord  : readNoteRecord,
                  model.ItemRecord  : readItemRecord,
                  model.DisplayAlarmRecord : readAlarmRecord,
                 }

class ICSSerializer(object):

    @classmethod
    def serialize(cls, recordSets, **extra):
        """ Convert a list of record sets to an ICalendar blob """
        vevent_mapping = {}

        masterRecordSets = []
        nonMasterRecordSets = []
        # masters need to be handled first, so modifications have access to them
        for uuid, recordSet in recordSets.iteritems():
            uid, recurrenceID = translator.splitUUID(uuid)
            if recurrenceID is None:
                masterRecordSets.append( (uuid, recordSet) )
            else:
                nonMasterRecordSets.append( (uuid, recordSet) )
        
        for uuid, recordSet in chain(masterRecordSets, nonMasterRecordSets):
            for record in recordSet.inclusions:
                recordHandlers.get(type(record), no_op)(record, vevent_mapping)

        cal = vobject.iCalendar()
        cal.vevent_list = vevent_mapping.values()
        # add x-wr-calname
        #handle icalproperties and icalparameters and Method (for outlook)
        return cal.serialize().encode('utf-8')

    @classmethod
    def deserialize(cls, text, silentFailure=True):
        """ Parse an ICalendar blob into a list of record sets """

        recordSets = {}
        extra = {}

        calname = None
    
        # iterate over calendars, usually only one, but more are allowed
        for calendar in vobject.readComponents(text, validate=False,
                                               ignoreUnreadable=True):
            if calname is None:
                calname = calendar.getChildValue('x_wr_calname')
    
        masters = {}
        for vobj in getattr(calendar, 'vevent_list', []):
            uid = vobj.getChildValue('uid')
            if vobj.getChildValue('recurrence_id') is None:
                masters[uid] = vobj
        
    
        for vobj in chain(
                                getattr(calendar, 'vevent_list', []),
                                #getattr(calendar, 'vtodo_list', []))
                            ):
            try:
                recurrenceID = vobj.getChildValue('recurrence_id')
                summary      = vobj.getChildValue('summary', eim.NoChange)
                description  = vobj.getChildValue('description', eim.NoChange)
                status       = vobj.getChildValue('status', eim.NoChange)
                duration     = vobj.getChildValue('duration')
                uid          = vobj.getChildValue('uid')
                dtstart      = vobj.getChildValue('dtstart')
                location     = vobj.getChildValue('location', eim.NoChange)

                # can't just compare recurrenceID and dtstart, timezone could
                # have changed, and comparing floating to non-floating would
                # raise an exception
                if recurrenceID is None:
                    dtstart_changed = True
                elif type(recurrenceID) == date or type(dtstart) == date:
                    dtstart_changed = recurrenceID != dtstart
                else:
                    dtstart_changed = (dtstart.tzinfo != recurrenceID.tzinfo or
                                       dtstart != recurrenceID)
                    
                if status is not eim.NoChange:
                    status = status.upper()
                if dtstart is not None:
                    anyTimeParam = getattr(vobj.dtstart, 'x_osaf_anytime_param',
                                           '')
                    anyTime = anyTimeParam.upper() == 'TRUE'

                isDate = type(dtstart) == date
                allDay = isDate and not anyTime
                
                if duration is None:
                    dtend = vobj.getChildValue('dtend')
                
                    def getDifference(left, right):
                        leftIsDate = (type(left) == date)
                        rightIsDate = (type(right) == date)
                        
                        if leftIsDate:
                            if rightIsDate:
                                return left - right
                            else:
                                left = forceToDateTime(left)
                                
                        elif rightIsDate:
                            right = forceToDateTime(right)
        
                        return makeNaiveteMatch(left, right.tzinfo) - right
                        
                    if dtend is not None:
                        duration = getDifference(dtend, dtstart)
                    elif anyTime or isDate:
                        duration = timedelta(1)
                    else:
                        duration = timedelta(0)
                        
                if isDate:
                    dtstart = forceToDateTime(dtstart)
                    # originally, duration was converted to Chandler's notion of
                    # all day duration, but this step will be done by the
                    # translator
                    #duration -= oneDay

                    
                dtstart = convertToICUtzinfo(dtstart)

                # convert to EIM value
                duration = toICalendarDuration(duration)                
                dtstart = toICalendarDateTime(dtstart, allDay, anyTime)

                uuid = UUIDFromICalUID(uid)

                valarm = getattr(vobj, 'valarm', None)
                
                if valarm is not None:
                    remValue        = valarm.getChildValue('trigger')
                    remDuration     = valarm.getChildValue('duration')
                    remRepeat       = valarm.getChildValue('repeat')
                    remDescription  = valarm.getChildValue('description',
                                                           "Event Reminder")
                    trigger = None
                    
                    if remValue is not None:
                        if type(remValue) is datetime:
                            icutzinfoValue = convertToICUtzinfo(remValue)
                            trigger = toICalendarDateTime(icutzinfoValue, False)
                        else:
                            assert type(remValue) is timedelta
                            trigger = toICalendarDuration(remValue)
                
                ## Custom properties/parameters                                           
                #ignoredProperties = {}
                #ignoredParameters = {}
                #for line in vobj.lines():
                    #name = line.name.lower()
                    #if name not in attributesUnderstood:
                        #line.transformFromNative()
                        #if not line.encoded and line.behavior:
                            #line.behavior.encode(line)
                        #ignoredProperties[name] = line.value
                    #params=u''
                    #for key, paramvals in line.params.iteritems():
                        #if key.lower() not in parametersUnderstood:
                            #vals = map(vobject.base.dquoteEscape, paramvals)
                            #params += ';' + key + '=' + ','.join(vals)
                    #if len(params) > 0:
                        #ignoredParameters[name] = params

                recurrence = {}
            
                for rule_name in ('rrule', 'exrule'):
                    rules = []
                    for line in vobj.contents.get(rule_name, []):
                        rules.append(line.value)
                    recurrence[rule_name] = (":".join(rules) if len(rules) > 0 
                                             else eim.NoChange)
            
                for date_name in ('rdate', 'exdate'):
                    dates = []
                    for line in vobj.contents.get(date_name, []):
                        dates.extend(line.value)
                    if len(dates) > 0:
                        dates = [convertToICUtzinfo(dt) for dt in dates]
                        dt_value = toICalendarDateTime(dates, allDay, anyTime)
                    else:
                        dt_value = eim.NoChange
                    recurrence[date_name] = dt_value
            

                if recurrenceID is not None:
                    recurrenceID = convertToICUtzinfo(forceToDateTime(
                                                                  recurrenceID))
                    rec_string = toICalendarDateTime(recurrenceID,
                                                              allDay or anyTime)

                    uuid += ":" + rec_string
                    master = masters[uid]
                    uid = eim.Inherit
                    if (master.getChildValue('duration') == 
                          vobj.getChildValue('duration')):
                        duration = eim.Inherit
                    masterAnyTime = (getattr(master.dtstart, 
                                          'x_osaf_anytime_param', '') == 'TRUE')
                    
                    masterAllDay = (not masterAnyTime and 
                                    type(master.dtstart.value) == date)
                    
                    if (masterAllDay == allDay and masterAnyTime == anyTime and
                        not dtstart_changed):
                        dtstart = eim.Inherit
                
                if uid == uuid:
                    uid = None
                    
                    


                records = [model.ItemRecord(uuid, 
                                            summary,        # title
                                            eim.NoChange,   # triage
                                            eim.NoChange,   # createdOn
                                            eim.NoChange,   # hasBeenSent (TODO)
                                            eim.NoChange,   # needsReply (TODO)
                                            ),
                           model.NoteRecord(uuid,
                                            description,  # body
                                            uid,          # icalUid
                                            eim.NoChange, # icalProperties
                                            eim.NoChange, # icalParameters
                                            ),
                           model.EventRecord(uuid,
                                             dtstart,
                                             duration,
                                             location,
                                             recurrence['rrule'],   # rrule
                                             recurrence['exrule'],  # exrule
                                             recurrence['rdate'],   # rdate
                                             recurrence['exdate'],  # exdate
                                             status, # status
                                             )]
                if valarm is not None:
                    records.append(
                           model.DisplayAlarmRecord(
                                             uuid,
                                             remDescription,
                                             trigger,
                                             remDuration,
                                             remRepeat
                                             ))

                recordSets[uuid] = RecordSet(records)


            except vobject.base.VObjectError, e:
                icalendarLines = text.splitlines()
                logger.error("Exception when importing icalendar, first 300 lines: \n%s"
                             % "\n".join(icalendarLines[:300]))
                logger.exception("import failed to import one event with exception: %s" % str(e))
                if not silentFailure:
                    raise

        return recordSets, extra
