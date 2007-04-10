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
import time
from datetime import datetime, timedelta, date
from PyICU import ICUtzinfo
from osaf.pim.calendar.TimeZone import convertToICUtzinfo, forceToDateTime
from osaf.pim.triage import Triageable
from chandlerdb.util.c import UUID
import md5
from itertools import chain
import logging

from vobject.base import textLineToContentLine

__all__ = [
    'ICSSerializer',
]

logger = logging.getLogger(__name__)

utc = ICUtzinfo.getInstance('UTC')

def no_op(*args, **kwds):
    pass

class ICalendarExportError(Exception):
    pass

def prepareVobj(uuid, recordSet, vobjs):
    """
    Determine if a recordset is for a vtodo, or a vevent, then create it.
    
    Modifications may not have event records OR task records, so for
    modifications, check what was done for the master.  This relies on 
    recordsets for masters being processed before modifications.
    
    """
    master_uuid, recurrenceID = translator.splitUUID(uuid)
    if recurrenceID is None:
        task, event = hasTaskAndEvent(recordSet)
    else:
        if vobjs.get(master_uuid).name.lower() == 'vevent':
            task, event = False, True
        else:
            task, event = True, False
            
    if event:
        vevent = vobject.newFromBehavior('vevent')
        vevent.isNative = True
        vobjs[uuid] = vevent
    elif task:
        vtodo = vobject.newFromBehavior('vtodo')
        vtodo.isNative = True
        vobjs[uuid] = vtodo
    else:
        raise ICalendarExportError(_(u"Item isn't a task or an event."))

def getVobj(record, vobjs):
    uuid = record.uuid
    return vobjs.get(uuid)

"""
Translate data in recordsets into fields in a vevent.

vobjs should be a dictionary mapping UUIDs to vobject vobjs.  A
dictionary is needed to handle recurrence, which may generate new vobjs.
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

def pruneDateTimeParam(vobj):
    """
    Converting eim fields directly to vobject misses out on pruning defaults
    like DATE-TIME.
    """
    if getattr(vobj, 'value_param', '').upper() == 'DATE-TIME':
        del vobj.value_param
    

def registerTZID(vobj):
    tzid = getattr(vobj, 'tzid_param', None)
    # add an appropriate tzinfo to vobject's tzid->tzinfo cache
    if tzid is not None and vobject.icalendar.getTzid(tzid) is None:
        vobject.icalendar.registerTzid(tzid, ICUtzinfo.getInstance(tzid))

def readEventRecord(eventRecord, vobjs):
    vevent = getVobj(eventRecord, vobjs)
    master = None

    uuid, recurrenceID = translator.splitUUID(eventRecord.uuid)
    if recurrenceID is not None:
        master = vobjs[uuid]
        m_start = master.dtstart
        anyTime = False
        if getattr(m_start, 'value_param', '') == 'DATE':
            recurrenceID = recurrenceID.date()
            anyTime = (getattr(m_start, 'x_osaf_anytime_param', '') == 'TRUE')
        elif recurrenceID.tzinfo == ICUtzinfo.floating:
            recurrenceID = recurrenceID.replace(tzinfo=None)
        vevent.add('recurrence-id').value = recurrenceID
        
    if eventRecord.dtstart in translator.emptyValues:
        if recurrenceID is not None:
            dtstart = vevent.add('dtstart')
            dtstart.value = recurrenceID
            if anyTime:
                dtstart.x_osaf_anytime_param = "TRUE"
    else:
        vevent.dtstart = textLineToContentLine("DTSTART" +
                                               eventRecord.dtstart)
        pruneDateTimeParam(vevent.dtstart)
        registerTZID(vevent.dtstart)

    for name in ['duration', 'status', 'location']:
        eimValue = getattr(eventRecord, name)
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
        record_value = getattr(eventRecord, rule_name)
        if record_value not in translator.emptyValues:
            for rule_value in record_value.split(':'):
                # EIM concatenates multiple rules with :
                rules.append(textLineToContentLine(rule_name + ":" + rule_value))
        vevent.contents[rule_name] = rules

    for date_name in ('rdate', 'exdate'):
        record_value = getattr(eventRecord, date_name)
        if record_value not in translator.emptyValues:
            # multiple dates should always be on one line
            setattr(vevent, date_name, 
                    textLineToContentLine(date_name + record_value))
            pruneDateTimeParam(getattr(vevent, date_name))



def readNoteRecord(noteRecord, vobjs):
    vobj = getVobj(noteRecord, vobjs)
    if noteRecord.body not in translator.emptyValues:
        vobj.add('description').value = noteRecord.body
    icalUID = noteRecord.icalUid
    if icalUID in translator.emptyValues:
        # empty icalUID for a master means use uuid, for a modification it means
        # inherit icalUID
        uuid, recurrenceID = translator.splitUUID(noteRecord.uuid)
        if recurrenceID is None:
            icalUID = uuid
        else:
            icalUID = vobjs[uuid].uid.value
    vobj.add('uid').value = icalUID


triage_code_to_vtodo_status = {
    "100" : 'in-process',
    "200" : 'cancelled',
    "300" : 'completed',
}

vtodo_status_to_triage_code = dict((v, k) for 
                                   k, v in triage_code_to_vtodo_status.items())

def readItemRecord(itemRecord, vobjs):
    vobj = getVobj(itemRecord, vobjs)
    if itemRecord.title not in translator.emptyValues:
        vobj.add('summary').value = itemRecord.title

    if vobj.name.lower() == 'vtodo':
        # VTODO STATUS mapping:
        # ---------------------
        #
        #  [ICalendar]            [Triage Enum]
        #  <no value>/IN-PROCESS    now  (needsReply=False)
        #  NEEDS-ACTION             now  (needsReply=True)
        #  COMPLETED                done
        #  CANCELLED                later
        triage = itemRecord.triage
        if itemRecord.triage != "" and triage not in translator.emptyValues:
            code, timestamp, auto = triage.split(" ")
            status = triage_code_to_vtodo_status[code]
            if status == 'in-process' and itemRecord.needsReply:
                status = 'needs-action'
            status_obj = vobj.add('status')
            status_obj.value = status.upper()
            # rfc2445 allows a COMPLETED which would make sense for
            # triageStatusChanged if status is completed, but rather than
            # exporting triageStatusChanged for only DONE items, put it in a
            # custom parameter
            status_obj.x_osaf_changed_param = str(timestamp)
            status_obj.x_osaf_auto_param = ('TRUE' if auto == '1' else 'FALSE')

def readAlarmRecord(alarmRecord, vobjs):
    vobj = getVobj(alarmRecord, vobjs)
    if alarmRecord.trigger not in translator.emptyValues:
        valarm = vobj.add('valarm')
        try:
            val = translator.fromICalendarDateTime(alarmRecord.trigger)[0]
            valarm.add('trigger').value = val
        except:
            valarm.trigger = textLineToContentLine("TRIGGER:" + 
                                                   alarmRecord.trigger)
        if alarmRecord.description not in translator.emptyValues:
            valarm.add('description').value = alarmRecord.description
        if alarmRecord.repeat not in translator.emptyValues:
            valarm.add('repeat').value = str(alarmRecord.repeat)
        if alarmRecord.duration not in translator.emptyValues:
            valarm.add('repeat').value = str(alarmRecord.duration)
            valarm.repeat.isNative = False

recordHandlers = {model.EventRecord : readEventRecord,
                  model.NoteRecord  : readNoteRecord,
                  model.ItemRecord  : readItemRecord,
                  model.DisplayAlarmRecord : readAlarmRecord,
                 }


def hasTaskAndEvent(recordSet):
    task = event = False
    for rec in recordSet.inclusions:
        if type(rec) == model.EventRecord:
            event = True
        elif type(rec) == model.TaskRecord:
            task = True
        if task and event:
            break
    return task, event

class ICSSerializer(object):

    @classmethod
    def serialize(cls, recordSets, **extra):
        """ Convert a list of record sets to an ICalendar blob """
        vobj_mapping = {}

        masterRecordSets = []
        nonMasterRecordSets = []
        # masters need to be handled first, so modifications have access to them
        for uuid, recordSet in recordSets.iteritems():
            # skip over record sets with neither an EventRecord nor a TaskRecord
            task, event = hasTaskAndEvent(recordSet)
            if task or event:
                uid, recurrenceID = translator.splitUUID(uuid)
                if recurrenceID is None:
                    masterRecordSets.append( (uuid, recordSet) )
                else:
                    nonMasterRecordSets.append( (uuid, recordSet) )
        
        for uuid, recordSet in chain(masterRecordSets, nonMasterRecordSets):
            prepareVobj(uuid, recordSet, vobj_mapping)
            for record in recordSet.inclusions:
                recordHandlers.get(type(record), no_op)(record, vobj_mapping)
            
        cal = vobject.iCalendar()
        cal.vevent_list = [obj for obj in vobj_mapping.values() 
                           if obj.name.lower() == 'vevent']
        cal.vtodo_list = [obj for obj in vobj_mapping.values() 
                           if obj.name.lower() == 'vtodo']

        # add x-wr-calname
        #handle icalproperties and icalparameters and Method (for outlook)
        return cal.serialize().encode('utf-8')

    @classmethod
    def deserialize(cls, text, silentFailure=True, helperView=None):
        """
        Parse an ICalendar blob into a list of record sets
        
        helperView can be None or a view that will be used to find preferences
        like what timezones should be used in convertToICUtzinfo.
        """
        recordSets = {}
        extra = {}

        calname = None
    
        # iterate over calendars, usually only one, but more are allowed
        for calendar in vobject.readComponents(text, validate=False,
                                               ignoreUnreadable=True):
            if calname is None:
                calname = calendar.getChildValue('x_wr_calname')
                extra['name'] = calname
    
        masters = {}
        for vobj in getattr(calendar, 'vevent_list', []):
            uid = vobj.getChildValue('uid')
            if vobj.getChildValue('recurrence_id') is None:
                masters[uid] = vobj
        
        
        for vobj in chain(
                                getattr(calendar, 'vevent_list', []),
                                getattr(calendar, 'vtodo_list', [])
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

                start_obj = getattr(vobj, 'dtstart', None)

                emitTask = (vobj.name == 'VTODO')

                if dtstart is None or emitTask:
                    # due takes precedence over dtstart
                    due = vobj.getChildValue('due')
                    if due is not None:
                        dtstart = due
                        start_obj = getattr(vobj, 'due', None)
                    
                anyTime = False
                if dtstart is not None:
                    anyTimeParam = getattr(start_obj, 'x_osaf_anytime_param',
                                           '')
                    anyTime = anyTimeParam.upper() == 'TRUE'

                isDate = type(dtstart) == date
                allDay = isDate and not anyTime

                
                emitEvent = (dtstart is not None)
                
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
                        
                    if dtend is not None and dtstart is not None:
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

                if dtstart is not None:
                    dtstart = convertToICUtzinfo(dtstart, helperView)
                    dtstart = toICalendarDateTime(dtstart, allDay, anyTime)
    
                # convert to EIM value
                duration = toICalendarDuration(duration)                

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
                            icutzinfoValue = convertToICUtzinfo(remValue,
                                                                helperView)
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
                        dates = [convertToICUtzinfo(dt, helperView)
                                 for dt in dates]
                        dt_value = toICalendarDateTime(dates, allDay, anyTime)
                    else:
                        dt_value = eim.NoChange
                    recurrence[date_name] = dt_value
            

                if recurrenceID is not None:
                    range = getattr(vobj.recurrence_id, 'range_param', 'THIS')
                    if range != 'THIS':
                        logger.info("Skipping a THISANDFUTURE or "
                                    "THISANDPRIOR modification")
                        continue

                    recurrenceID = forceToDateTime(recurrenceID)
                    recurrenceID = convertToICUtzinfo(recurrenceID, helperView)
                    rec_string = toICalendarDateTime(recurrenceID,
                                                              allDay or anyTime)

                    uuid += "::" + rec_string
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

                triage = eim.NoChange
                needsReply = eim.NoChange
                
                if emitTask and status is not eim.NoChange:
                    status = status.lower()
                    code = vtodo_status_to_triage_code.get(status, "100")
                    completed = vobj.getChildValue('completed')
                    if completed is not None:
                        if type(completed) == date:
                            completed = TimeZone.forceToDateTime(completed)
                        timestamp = str(Triageable.makeTriageStatusChangedTime(
                                            completed))
                    else:
                        timestamp = getattr(vobj.status, 'x_osaf_changed_param',
                                            "0.0")
                    auto = getattr(vobj.status, 'x_osaf_auto_param', 'FALSE')
                    auto = ("1" if auto == 'TRUE' else "0")
                    triage =  code + " " + timestamp + " " + auto
                    
                    needsReply = (1 if status == 'needs-action' else 0)
                    
                    # VTODO's status doesn't correspond to EventRecord's status
                    status = eim.NoChange
                    

                records = [model.NoteRecord(uuid,
                                            description,  # body
                                            uid,          # icalUid
                                            eim.NoChange, # icalProperties
                                            eim.NoChange, # icalParameters
                                            ),
                           model.ItemRecord(uuid, 
                                            summary,        # title
                                            triage,         # triage
                                            eim.NoChange,   # createdOn
                                            eim.NoChange,   # hasBeenSent (TODO)
                                            needsReply,     # needsReply (TODO)
                                            )]
                if emitEvent:
                    records.append(model.EventRecord(uuid,
                                            dtstart,
                                            duration,
                                            location,
                                            recurrence['rrule'],   # rrule
                                            recurrence['exrule'],  # exrule
                                            recurrence['rdate'],   # rdate
                                            recurrence['exdate'],  # exdate
                                            status, # status
                                            ))
                if emitTask:
                    records.append(model.TaskRecord(uuid))
                           
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
