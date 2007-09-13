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

from osaf.sharing import model, eim, RecordSet, translator, formats
from osaf.sharing.translator import toICalendarDuration, toICalendarDateTime
from ICalendar import (makeNaiveteMatch, attributesUnderstood,
                       parametersUnderstood)
import vobject
from datetime import datetime, timedelta, date, time
from osaf.pim.calendar.TimeZone import convertToICUtzinfo, forceToDateTime
from osaf.pim.triage import Triageable
from chandlerdb.util.c import UUID, Empty, Nil
from repository.persistence.RepositoryView import currentview
from i18n import ChandlerMessageFactory as _
import md5
from itertools import chain
import logging

from vobject.base import textLineToContentLine, Component, ContentLine

__all__ = [
    'ICSSerializer', 'VObjectSerializer'
]

logger = logging.getLogger(__name__)

midnight = time(0)

class ICalendarExportError(Exception):
    pass

def prepareVobj(view, uuid, recordSet, vobjs):
    """
    Determine if a recordset is for a vtodo, or a vevent, then create it.
    
    Modifications may not have event records OR task records, so for
    modifications, check what was done for the master.  This relies on 
    recordsets for masters being processed before modifications.
    
    """
    master_uuid, recurrenceID = translator.splitUUID(view, uuid)
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

def UUIDFromICalUID(view, uid_to_uuid_map, uid):
    """
    When importing iCalendar, match up events by their uid if an item with that
    icalUID or UUID exists.  Otherwise, randomize UUID, bug 9965.
    """
    uuid = uid_to_uuid_map.get(uid)
    if uuid is None:
        item = formats.findUID(view, uid)
        if item is None:
            try:
                # See if uid is a valid repository UUID, if it is, and that UUID
                # already exists, we'll use it
                item = view.findUUID(UUID(uid))
            except ValueError:
                pass
        
        if item is None:
            uuid = UUID()
        else:
            uuid = item.itsUUID
        uid_to_uuid_map[uid] = uuid        
        
    return str(uuid)

def pruneDateTimeParam(vobj):
    """
    Converting eim fields directly to vobject misses out on pruning defaults
    like DATE-TIME.
    """
    if getattr(vobj, 'value_param', '').upper() == 'DATE-TIME':
        del vobj.value_param
    

def registerTZID(view, vobj):
    tzid = getattr(vobj, 'tzid_param', None)
    # add an appropriate tzinfo to vobject's tzid->tzinfo cache
    if tzid is not None and vobject.icalendar.getTzid(tzid) is None:
        vobject.icalendar.registerTzid(tzid, view.tzinfo.getInstance(tzid))

def readEventRecord(view, eventRecord, vobjs):
    vevent = getVobj(eventRecord, vobjs)
    master = None
    
    uuid, recurrenceID = translator.splitUUID(view, eventRecord.uuid)
    if recurrenceID is not None:
        master = vobjs[uuid]
        m_start = master.dtstart
        anyTime = False
        if getattr(m_start, 'value_param', '') == 'DATE':
            recurrenceID = recurrenceID.date()
            anyTime = (getattr(m_start, 'x_osaf_anytime_param', '') == 'TRUE')
        elif recurrenceID.tzinfo == view.tzinfo.floating:
            recurrenceID = recurrenceID.replace(tzinfo=None)
        elif recurrenceID.tzinfo == view.tzinfo.UTC:
            # convert UTC recurrence-id (which is legal, but unusual in
            # iCalendar) to the master's dtstart timezone
            tzid = getattr(m_start, 'tzid_param', None)
            if tzid is not None:
                tzinfo = view.tzinfo.getInstance(tzid)
                recurrenceID = recurrenceID.astimezone(tzinfo)
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
        registerTZID(view, vevent.dtstart)

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
    vevent.add('dtstamp').value = timestamp.replace(tzinfo=view.tzinfo.UTC)
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



def readNoteRecord(view, noteRecord, vobjs):
    vobj = getVobj(noteRecord, vobjs)
    if noteRecord.body not in translator.emptyValues:
        vobj.add('description').value = noteRecord.body
    icalUID = noteRecord.icalUid
    if icalUID in translator.emptyValues:
        # empty icalUID for a master means use uuid, for a modification it means
        # inherit icalUID
        uuid, recurrenceID = translator.splitUUID(view, noteRecord.uuid)
        if recurrenceID is None:
            icalUID = uuid
        else:
            icalUID = vobjs[uuid].uid.value

    vobj.add('uid').value = icalUID

top_level_understood = ['vtimezone', 'version', 'calscale', 'x-wr-calname', 
                        'prodid', 'method', 'vevent', 'vtodo']

class unrecognizedData(object):
    """
    Avoid creating tons of empty vobjects since the common case is that they're
    not needed.
    
    Using a separate class to work around Python nested scope annoyance,
    instead of using nested functions.
    
    """
    __slots__ = 'newChild', 'newComponent', 'parent_component', 'child'
    def __init__(self, parent_component, child):
        self.newChild = None
        self.newComponent = None
        self.parent_component = parent_component
        self.child = child

    def getComponent(self):
        if self.newComponent is None:
            self.newComponent = Component(self.parent_component.name)
        return self.newComponent
    
    def getChild(self):
        newChild = self.newChild
        if newChild is None:
            newChild = self.newChild = Component(self.child.name)
            parent = self.getComponent()
            parent.contents.setdefault(self.child.name, []).append(newChild)
        return newChild


def extractUnrecognized(parent_component, child):
    """
    Extract unrecognized, content lines, and parameters from a vevent, also
    store top level components from the whole calendar in cases that look like
    CalDAV.
    
    If the object has more than one icalUID, it's not a CalDAV icalendar file,
    so don't waste space on potentially hundreds of items by storing top-level
    unrecognized data for each item.
    
    Return either None, or a vobject, which is a fragment of an icalendar file,
    containing lines and components that weren't recognized.  If a line is
    recognized but a parameter isn't, a line with parameters byt no value will
    be output.
    
    This strategy may fall on its face for duplicated lines that are recognized 
    but with different, unrecognized parameters, but that seems like an unlikely
    edge case.
    
    Tasks currently aren't handled for fear of oddities when vevents
    are converted into vtodos.
    
    """
    # don't create a new component unless it's needed
    out = unrecognizedData(parent_component, child)
    
    # only handle top level lines and components if child is a vevent, and
    # parent_component's vevent children's uids all match
    if child.name.lower() == 'vevent':
        uid = child.getChildValue('uid').upper()
        for vevent in parent_component.contents.get('vevent', Empty):
            if vevent.getChildValue('uid').upper() != uid:
                break
        else: # reminder: else-after-for executes if the for-loop wasn't broken
            for key, top_child in parent_component.contents.iteritems():
                if key.lower() not in top_level_understood:
                    out.getComponent().contents[key] = top_child
                else:
                    # not saving parameters of recognized top level lines
                    pass
                
    for line in child.lines():
        name = line.name.lower()
        if name not in attributesUnderstood:
            line.transformFromNative()
            out.getChild().contents.setdefault(name, []).append(line)
        else:
            paramPairs = []
            for key, paramvals in line.params.iteritems():
                if key.lower() not in parametersUnderstood:
                    paramPairs.append((key, paramvals))
            if paramPairs:
                newLine = ContentLine(line.name, [], '')
                newLine.params = dict(paramPairs)
                out.getChild().contents.setdefault(name, []).append(newLine)

    # we could recurse and process child's component children, which would get
    # things like custom lines in VALARMs, but for now, don't bother
    
    return out.newComponent

def injectUnrecognized(icalendarExtra, calendar, vevent):
    """Add unrecognized data from item.icalendarExtra to calendar and vevent."""
    if not icalendarExtra:
        # nothing to do
        return
    newCal = vobject.readOne(icalendarExtra, transform=False)
    for line in newCal.lines():
        calendar.contents.setdefault(line.name, []).append(line)
    for component in newCal.components():
        if component.name.lower() != 'vevent':
            calendar.contents.setdefault(component.name, []).append(component)
        else:
            for line in component.lines():
                name = line.name.lower()
                if name in attributesUnderstood:
                    if hasattr(vevent, name):
                        for key, paramvals in line.params.iteritems():
                            vevent.contents[name][0].params[key] = paramvals
                    # do nothing for parameters on, say dtend, since we
                    # serialize duration instead
                else:
                    vevent.contents.setdefault(name, []).append(line)
                    

triage_code_to_vtodo_status = {
    "100" : 'in-process',
    "200" : 'cancelled',
    "300" : 'completed',
}

vtodo_status_to_triage_code = dict((v, k) for 
                                   k, v in triage_code_to_vtodo_status.items())

def readItemRecord(view, itemRecord, vobjs):
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

def readAlarmRecord(view, alarmRecord, vobjs):
    vobj = getVobj(alarmRecord, vobjs)
    if alarmRecord.trigger not in translator.emptyValues:
        valarm = vobj.add('valarm')
        try:
            val = translator.fromICalendarDateTime(view, alarmRecord.trigger)[0]
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
                  model.ItemRecord  : readItemRecord,
                  model.DisplayAlarmRecord : readAlarmRecord,
                  model.NoteRecord  : readNoteRecord,
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
    def serialize(cls, view, recordSets, **extra):
        cal = cls.recordSetsToVObject(view, recordSets, **extra)
        return cal.serialize().encode('utf-8')
    
    @classmethod
    def recordSetsToVObject(cls, view, recordSets, **extra):
        """ Convert a list of record sets to an ICalendar blob """
        vobj_mapping = {}
        cal = vobject.iCalendar()

        masterRecordSets = []
        nonMasterRecordSets = []
        # masters need to be handled first, so modifications have access to them
        for uuid, recordSet in recordSets.iteritems():
            # skip over record sets with neither an EventRecord nor a TaskRecord
            task, event = hasTaskAndEvent(recordSet)
            if task or event:
                uid, recurrenceID = translator.splitUUID(view, uuid)
                if recurrenceID is None:
                    masterRecordSets.append( (uuid, recordSet) )
                else:
                    nonMasterRecordSets.append( (uuid, recordSet) )
        
        for uuid, recordSet in chain(masterRecordSets, nonMasterRecordSets):
            prepareVobj(view, uuid, recordSet, vobj_mapping)
            icalExtra = None
            for record in recordSet.inclusions:
                recordHandlers.get(type(record), Nil)(view, record,
                                                      vobj_mapping)
                if type(record) == model.NoteRecord:
                    icalExtra = record.icalExtra
            
            if icalExtra not in translator.emptyValues:
                injectUnrecognized(icalExtra, cal, vobj_mapping.get(uuid))
            
        cal.vevent_list = [obj for obj in vobj_mapping.values()
                           if obj.name.lower() == 'vevent']
        cal.vtodo_list = [obj for obj in vobj_mapping.values()
                           if obj.name.lower() == 'vtodo']

        name = extra.get('name')
        if name is not None:
            cal.add('x-wr-calname').value = name
            
        monolithic = extra.get('monolithic', False)
        if monolithic:
            # don't add a METHOD to CalDAV serializations, because CalDAV
            # forbids them, but do add one when serializing monolithic ics files
            # because Outlook requires them (bug 7121)
            cal.add('method').value = "PUBLISH"
            
        #handle icalendarExtra
        return cal

    @classmethod
    def deserialize(cls, view, text, silentFailure=True):
        """
        Parse an ICalendar blob into a list of record sets
        """

        recordSets = {}
        extra = {'forceDateTriage' : True}

        calname = None
    
        # iterate over calendars, usually only one, but more are allowed
        for calendar in vobject.readComponents(text, validate=False,
                                               ignoreUnreadable=True):
            if calname is None:
                calname = calendar.getChildValue('x_wr_calname')
                if calname is not None:
                    extra['name'] = calname
    
        masters = {}
        for vobj in getattr(calendar, 'vevent_list', []):
            uid = vobj.getChildValue('uid')
            if vobj.getChildValue('recurrence_id') is None:
                masters[uid] = vobj

        uid_to_uuid_map = {}
        
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
                
                # bug 10821, Google serializes modifications with no master;
                # treat these as normal events, not modifications
                if not masters.get(uid):
                    recurrenceID = None
                
                # can't just compare recurrenceID and dtstart, timezone could
                # have changed, and comparing floating to non-floating would
                # raise an exception
                if recurrenceID is None:
                    dtstart_changed = True
                elif dtstart is None:
                    dtstart_changed = False
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
                                left = forceToDateTime(view, left)
                                
                        elif rightIsDate:
                            right = forceToDateTime(view, right)
        
                        return makeNaiveteMatch(view,
                                                left, right.tzinfo) - right
                        
                    if dtend is not None and dtstart is not None:
                        duration = getDifference(dtend, dtstart)
                            
                    elif anyTime or isDate:
                        duration = timedelta(1)
                    else:
                        duration = timedelta(0)

                # handle the special case of a midnight-to-midnight floating
                # event, treat it as allDay, bug 9579
                if (not isDate and dtstart is not None and
                      dtstart.tzinfo is None and dtstart.time() == midnight and
                      duration.days >= 1 and
                      duration == timedelta(duration.days)):
                    allDay = True
                
                if isDate:
                    dtstart = forceToDateTime(view, dtstart)
                    # originally, duration was converted to Chandler's notion of
                    # all day duration, but this step will be done by the
                    # translator
                    #duration -= oneDay

                if dtstart is not None:
                    dtstart = convertToICUtzinfo(view, dtstart)
                    dtstart = toICalendarDateTime(view, dtstart, allDay, anyTime)
    
                # convert to EIM value
                duration = toICalendarDuration(duration)                

                uuid = UUIDFromICalUID(view, uid_to_uuid_map, uid)

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
                            icutzinfoValue = convertToICUtzinfo(view, remValue)
                            trigger = toICalendarDateTime(view, icutzinfoValue, False)
                        else:
                            assert type(remValue) is timedelta
                            trigger = toICalendarDuration(remValue)

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
                        if not (allDay or anyTime):
                            dates = [convertToICUtzinfo(view, dt)
                                     for dt in dates]
                        dt_value = toICalendarDateTime(view, dates, allDay, anyTime)
                    else:
                        dt_value = eim.NoChange
                    recurrence[date_name] = dt_value
            

                if recurrenceID is not None:
                    range = getattr(vobj.recurrence_id, 'range_param', 'THIS')
                    if range != 'THIS':
                        logger.info("Skipping a THISANDFUTURE or "
                                    "THISANDPRIOR modification")
                        continue
                    
                    dateValue = allDay or anyTime
                    recurrenceID = forceToDateTime(view, recurrenceID)
                    recurrenceID = convertToICUtzinfo(view, recurrenceID)
                    if recurrenceID.tzinfo != view.tzinfo.floating:
                        recurrenceID = recurrenceID.astimezone(view.tzinfo.UTC)
                    rec_string = translator.formatDateTime(view, recurrenceID,
                                                           dateValue, dateValue)

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
                
                triage = eim.NoChange
                needsReply = eim.NoChange
                
                if emitTask and status is not eim.NoChange:
                    status = status.lower()
                    code = vtodo_status_to_triage_code.get(status, "100")
                    completed = vobj.getChildValue('completed')
                    if completed is not None:
                        if type(completed) == date:
                            completed = TimeZone.forceToDateTime(view, completed)
                        timestamp = str(Triageable.makeTriageStatusChangedTime(view, completed))
                    else:
                        timestamp = getattr(vobj.status, 'x_osaf_changed_param',
                                            "0.0")
                    auto = getattr(vobj.status, 'x_osaf_auto_param', 'FALSE')
                    auto = ("1" if auto == 'TRUE' else "0")
                    triage =  code + " " + timestamp + " " + auto
                    
                    needsReply = (1 if status == 'needs-action' else 0)

                    # VTODO's status doesn't correspond to EventRecord's status
                    status = eim.NoChange
                
                icalExtra = eim.NoChange
                if not emitTask:
                    # not processing VTODOs
                    icalExtra = extractUnrecognized(calendar, vobj)
                    if icalExtra is None:
                        icalExtra = ''
                    else:
                        icalExtra = icalExtra.serialize()

                records = [model.NoteRecord(uuid,
                                            description,  # body
                                            uid,          # icalUid
                                            None,         # icalProperties
                                            None,         # icalParameters
                                            icalExtra,    # icalExtra
                                            ),
                           model.ItemRecord(uuid, 
                                            summary,        # title
                                            triage,         # triage
                                            eim.NoChange,   # createdOn
                                            eim.NoChange,   # hasBeenSent (TODO)
                                            needsReply,     # needsReply (TODO)
                                            eim.NoChange,   # read
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
                                            status,                # status
                                            eim.NoChange    # lastPastOccurrence
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

class VObjectSerializer(ICSSerializer):
    serialize = ICSSerializer.recordSetsToVObject
