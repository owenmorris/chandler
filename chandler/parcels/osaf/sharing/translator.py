from application import schema
from osaf import pim
from osaf.sharing import eim, model
from PyICU import ICUtzinfo
import time
from datetime import datetime, date, timedelta
from decimal import Decimal

from vobject.base import textLineToContentLine, ContentLine
from vobject.icalendar import (DateOrDateTimeBehavior, MultiDateBehavior,
                               RecurringComponent, VEvent)
import osaf.pim.calendar.TimeZone as TimeZone
from osaf.pim.calendar.Recurrence import RecurrenceRuleSet, RecurrenceRule
from dateutil.rrule import rrulestr

__all__ = [
    'PIMTranslator',
]


utc = ICUtzinfo.getInstance('UTC')
oneDay = timedelta(1)

def with_nochange(value, converter, view=None):
    if value is eim.NoChange:
        return value
    if value is None:  # TODO: think about how to handle None
        return eim.NoChange
    if view is None:
        return converter(value)
    else:
        return converter(value, view)


### Event field conversion functions
# incomplete

def transparency(val):
    out = val.lower()
    if out == 'cancelled':
        out = 'fyi'
    elif out not in ('confirmed', 'tentative'):
        out = 'confirmed'
    return out

def location(val, view):
    if val is None:
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
        if tzid is None:        
            tzinfo = ICUtzinfo.floating
        else:
            tzinfo = ICUtzinfo.getInstance(tzid)
        start = [dt.replace(tzinfo=tzinfo) for dt in start]
    if not multivalued:
        start = start[0]
    return (start, allDay, anyTime)

def getTimeValues(record):
    """
    Extract start time, end time, and allDay/anyTime from a record.
    """
    dtstart = record.dtstart
    dtend   = record.dtend
    if dtstart is not eim.NoChange:
        start, allDay, anyTime = fromICalendarDateTime(dtstart)
    else:
        allDay = anyTime = start = eim.NoChange

    if dtend is not eim.NoChange:
        end, end_allDay, end_anyTime = fromICalendarDateTime(dtend)
        if (end_allDay or end_anyTime) and end > start:
            # iCalendar syntax for serializing all day dtends is off by one day
            end -= oneDay
    else:
        end = eim.NoChange

    return (start, end, allDay, anyTime)

dateFormat = "%04d%02d%02d"
datetimeFormat = "%04d%02d%02dT%02d%02d%02d"
tzidFormat = ";TZID=%s"
allDayParameter = ";VALUE=DATE"
timedParameter  = ";VALUE=DATE-TIME"
anyTimeParameter = ";X-OSAF-ANYTIME=TRUE"

def formatDateTime(dt, allDay, anyTime):
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
    if event.rruleset is None:
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
    
    

class PIMTranslator(eim.Translator):

    URI = "cid:pim-translator@osaf.us"
    version = 1
    description = u"Translator for Chandler PIM items"


    # ItemRecord -------------

    # TODO: lastModifiedBy

    @model.ItemRecord.importer
    def import_item(self, record):

        if record.createdOn not in (eim.NoChange, None):
            # createdOn is a Decimal we need to change to datetime
            naive = datetime.utcfromtimestamp(float(record.createdOn))
            inUTC = naive.replace(tzinfo=utc)
            # Convert to user's tz:
            createdOn = inUTC.astimezone(ICUtzinfo.default)
        else:
            createdOn = eim.NoChange

        if record.triageStatus not in (eim.NoChange, None):
            # @@@MOR -- is this the right way to get an enum?  (it works)
            triageStatus = getattr(pim.TriageEnum, record.triageStatus)
        else:
            triageStatus = eim.NoChange

        if record.triageStatusChanged not in (eim.NoChange, None):
            tsc = float(record.triageStatusChanged)
        else:
            tsc = eim.NoChange

        self.loadItemByUUID(
            record.uuid,
            pim.ContentItem,
            displayName=record.title,
            triageStatus=triageStatus,
            triageStatusChanged=tsc,
            createdOn=createdOn
        ) # incomplete, missing lastModifiedBy


    @eim.exporter(pim.ContentItem)
    def export_item(self, item):
        yield model.ItemRecord(
            item.itsUUID,                               # uuid
            item.displayName,                           # title
            str(item.triageStatus),                     # triageStatus
            Decimal("%.2f" % item.triageStatusChanged), # t_s_changed
            None,                                       # lastModifiedBy
            Decimal(int(time.mktime(item.createdOn.timetuple()))) # createdOn
        )



    # NoteRecord -------------

    @model.NoteRecord.importer
    def import_note(self, record):
        # TODO: REMOVE HACK:
        if record.body is None:
            body = ""
        else:
            body = record.body

        if record.icalUid is None:
            icalUID = eim.NoChange
        else:
            icalUID = record.icalUid

        self.loadItemByUUID(
            record.uuid,
            pim.Note,
            icalUID=icalUID,
            body=body
        )

    @eim.exporter(pim.Note)
    def export_note(self, item):
        yield model.NoteRecord(
            item.itsUUID,                               # uuid
            item.body,                                  # body
            getattr(item, "icalUID", None),             # icalUid
            None                                        # reminderTime
        )



    # TaskRecord -------------

    @model.TaskRecord.importer
    def import_task(self, record):
        self.loadItemByUUID(
            record.uuid,
            pim.TaskStamp
        )

    @eim.exporter(pim.TaskStamp)
    def export_task(self, task):
        yield model.TaskRecord(
            task.itsItem.itsUUID                   # uuid
        )


    @model.TaskRecord.deleter
    def delete_task(self, record):
        item = self.rv.findUUID(record.uuid)
        if item is not None and item.isLive() and pim.has_stamp(item,
            pim.TaskStamp):
            pim.TaskStamp(item).remove()



    # EventRecord -------------

    # TODO: EventRecord fields need work, for example: rfc3339 date strings

    @model.EventRecord.importer
    def import_event(self, record):

        start, end, allDay, anyTime = getTimeValues(record)

        if start is not eim.NoChange and end is eim.NoChange:
            # odd case, Chandler's object model doesn't allow start to
            # change without changing end
            item = self.rv.findUUID(record.uuid)
            if item is not None:
                end = pim.EventStamp(item).endTime

        # start must be set before endTime, it'd be nice if we could just
        # serialize duration instead of endTime, avoiding this problem

        item = self.loadItemByUUID(
                   record.uuid,
                   pim.EventStamp,
                   startTime=start)

        self.loadItemByUUID(
            record.uuid,
            pim.EventStamp,
            endTime=end,
            allDay=allDay,
            anyTime=anyTime,
            transparency=with_nochange(record.status, transparency),
            location=with_nochange(record.location, location, self.rv),
        )
        
        event = pim.EventStamp(item)
        
        real_start = event.effectiveStartTime
        
        new_rruleset = []
        # notify of recurrence changes once at the end
        if event.rruleset is not None:
            ignoreChanges = getattr(event.rruleset, '_ignoreValueChanges', False)      
            event.rruleset._ignoreValueChanges = True
        elif (record.rrule in (None, eim.NoChange) and
              record.rdate in (None, eim.NoChange)):
            # since there's no recurrence currently, avoid creating a rruleset
            # if all the positive recurrence fields are None
            return
            

        def getRecordSet():
            if len(new_rruleset) > 0:
                return new_rruleset[0]
            elif event.rruleset is not None:
                return event.rruleset
            else:
                new_rruleset.append(RecurrenceRuleSet(None, itsView=self.rv))
                return new_rruleset[0]

        for ruletype in 'rrule', 'exrule':
            record_field = getattr(record, ruletype)
            if record_field is not eim.NoChange:
                rruleset = getRecordSet()
                if record_field is None:
                    # this isn't the right way to delete the existing rules, what is?
                    setattr(rruleset, ruletype + 's', [])
                else:
                    du_rruleset = getDateUtilRRuleSet(ruletype, record_field,
                                                      real_start)
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
                rruleset = getRecordSet()
                if record_field is None:
                    dates = []
                else:
                    dates = fromICalendarDateTime(record_field,
                                                  multivalued=True)[0]
                setattr(rruleset, datetype + 's', dates)

        if event.rruleset is not None:
            event.rruleset._ignoreValueChanges = ignoreChanges
            event.cleanRule()

        if len(new_rruleset) > 0:
            event.rruleset = new_rruleset[0]
        

    @eim.exporter(pim.EventStamp)
    def export_event(self, event):
        if getattr(event, 'location', None) is None:
            location = None
        else:
            location = event.location.displayName

        rrule, exrule, rdate, exdate = getRecurrenceFields(event)

        yield model.EventRecord(
            event.itsItem.itsUUID,                      # uuid
            toICalendarDateTime(event.startTime, event.allDay, event.anyTime),
            toICalendarDateTime(event.endTime, event.allDay or event.anyTime),
            location,                                   # location
            rrule,                                      # rrule
            exrule,                                     # exrule
            rdate,                                      # rdate
            exdate,                                     # exdate
            str(event.transparency)                     # status
        )


    @model.EventRecord.deleter
    def delete_event(self, record):
        item = self.rv.findUUID(record.uuid)
        if item is not None and item.isLive() and pim.has_stamp(item,
            pim.EventStamp):
            pim.EventStamp(item).remove()








def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'Translator.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )

