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
from ICalendar import makeNaiveteMatch
import vobject
from datetime import datetime, timedelta, date
from PyICU import ICUtzinfo
import osaf.pim.calendar.TimeZone as TimeZone
from chandlerdb.util.c import UUID
import md5
import itertools

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
    

def readEventRecord(eventRecordSet, vevents):
    vevent = getVevent(eventRecordSet, vevents)

    uuid, recurrenceID = translator.splitUUID(eventRecordSet.uuid)
    if recurrenceID is not None:
        vevent.add('recurrence-id').value = recurrenceID
        
    if eventRecordSet.dtstart in translator.emptyValues:
        if recurrenceID is not None:
            vevent.add('dtstart').value = recurrenceID
    else:
        vevent.dtstart  = textLineToContentLine("DTSTART" +
                                                eventRecordSet.dtstart)
        tzid = getattr(vevent.dtstart, 'tzid_param', None)
        # add an appropriate tzinfo to vobject's tzid->tzinfo cache
        if tzid is not None and vobject.icalendar.getTzid(tzid) is None:
            vobject.icalendar.registerTzid(tzid, ICUtzinfo.getInstance(tzid))

    uppers = ['duration']

    for name in ['duration', 'status', 'location']:
        eimValue = getattr(eventRecordSet, name)
        if eimValue not in translator.emptyValues:
            line = vevent.add(name)
            if eimValue in uppers:
                eimValue = eimValue.upper()
            line.value = eimValue
            line.isNative = False
    
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
    uid = noteRecordSet.icalUid
    if uid in translator.emptyValues:
        uid, recurrenceID = translator.splitUUID(noteRecordSet.uuid)
    vevent.add('uid').value = uid
    # reminders?

def readItemRecord(itemRecordSet, vevents):
    vevent = getVevent(itemRecordSet, vevents)
    if itemRecordSet.title not in translator.emptyValues:
        vevent.add('summary').value = itemRecordSet.title

recordHandlers = {model.EventRecord : readEventRecord,
                  model.NoteRecord  : readNoteRecord,
                  model.ItemRecord  : readItemRecord,
                 }

class ICSSerializer(object):

    @classmethod
    def serialize(cls, recordSets, **extra):
        """ Convert a list of record sets to an ICalendar blob """
        vevent_mapping = {}
        for uuid, recordSet in recordSets.iteritems():
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
    
        for vobj in itertools.chain(
                                getattr(calendar, 'vevent_list', []),
                                #getattr(calendar, 'vtodo_list', []))
                            ):
            try:

                summary     = vobj.getChildValue('summary', u"")
                description = vobj.getChildValue('description')
                status      = vobj.getChildValue('status', "").upper()
                duration    = vobj.getChildValue('duration')
                uid         = vobj.getChildValue('uid')
                dtstart     = vobj.getChildValue('dtstart')
                location    = vobj.getChildValue('location')

                anyTime = (getattr(dtstart, 'x_osaf_anytime_param', '').upper()
                           == 'TRUE')

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
                                left = TimeZone.forceToDateTime(left)
                                
                        elif rightIsDate:
                            right = TimeZone.forceToDateTime(right)
        
                        return makeNaiveteMatch(left, right.tzinfo) - right
                        
                    if dtend is not None:
                        duration = getDifference(dtend, dtstart)
                    elif anyTime or isDate:
                        duration = timedelta(1)
                    else:
                        duration = timedelta(0)
                        
                if isDate:
                    dtstart = TimeZone.forceToDateTime(dtstart)
                    # originally, duration was converted to Chandler's notion of
                    # all day duration, but this step will be done by the
                    # translator
                    #duration -= oneDay

                    
                dtstart = TimeZone.convertToICUtzinfo(dtstart)

                # convert to EIM value
                duration = translator.toICalendarDuration(duration)                
                dtstart = translator.toICalendarDateTime(dtstart, allDay,
                                                         anyTime)

                uuid = UUIDFromICalUID(uid)

                # reminder code grabbed from ICalendar, not yet implemented
                            
                #reminderDelta = None
                #reminderAbsoluteTime = None
            
                #try:
                    #reminderValue = vobj.valarm.trigger.value
                #except AttributeError:
                    #pass
                #else:
                    #if type(reminderValue) is datetime:
                        #reminderAbsoluteTime = convertDatetime(reminderValue)
                    #else:
                        #assert type(reminderValue) is timedelta
                        #reminderDelta = reminderValue                    

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
                                             else None)
            
                for date_name in ('rdate', 'exdate'):
                    dates = []
                    for line in vobj.contents.get(date_name, []):
                        dates.extend(line.value)
                    if len(dates) > 0:
                        dates = [TimeZone.convertToICUtzinfo(dt)
                                 for dt in dates]
                        dt_value = translator.toICalendarDateTime(dates, allDay,
                                                                  anyTime)
                    else:
                        dt_value = None
                    recurrence[date_name] = dt_value
            

                recurrenceID = vobj.getChildValue('recurrence_id')
                if recurrenceID is not None:
                    recurrenceID = TimeZone.convertToICUtzinfo(recurrenceID)
                    rec_string = translator.toICalendarDateTime(recurrenceID,
                                                              allDay or anyTime)

                    uuid += ":" + rec_string

                records = [model.ItemRecord(uuid, 
                                            summary, # title
                                            None,    # triage
                                            None,    # createdOn
                                            None,    # hasBeenSent (TODO)
                                            None,    # needsReply (TODO)
                                            ),
                           model.NoteRecord(uuid,
                                            description, # body
                                            uid,         # icalUid
                                            None,        # icalProperties
                                            None,        # icalParameters
                                            ),
                           model.EventRecord(uuid,
                                             dtstart,
                                             duration,
                                             location,
                                             recurrence['rrule'],   # rrule
                                             recurrence['exrule'],   # exrule
                                             recurrence['rdate'],   # rdate
                                             recurrence['exdate'],  # exdate
                                             status, # status
                                             )]
                
                recordSets[uuid] = RecordSet(records)


            except vobject.base.VObjectError, e:
                icalendarLines = text.splitlines()
                logger.error("Exception when importing icalendar, first 300 lines: \n%s"
                             % "\n".join(icalendarLines[:300]))
                logger.exception("import failed to import one event with exception: %s" % str(e))
                if not silentFailure:
                    raise

        return recordSets, extra
