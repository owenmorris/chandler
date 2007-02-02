from application import schema
from osaf import pim
from osaf.sharing import eim, model
from PyICU import ICUtzinfo
import time
from datetime import datetime, date, timedelta
from decimal import Decimal

from vobject.base import textLineToContentLine
from vobject.icalendar import DateOrDateTimeBehavior
import osaf.pim.calendar.TimeZone as TimeZone

__all__ = [
    'PIMTranslator',
]

COSMO_MODE = False

utc = ICUtzinfo.getInstance('UTC')
oneDay = timedelta(1)

def with_nochange(value, converter, view=None):
    if value is eim.NoChange:
        return value
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
    return pim.Location.getLocation(view, val)

def readICalendarDateTime(text):
    line = textLineToContentLine('dtstart' + text)
    native_line = DateOrDateTimeBehavior.transformToNative(line)
    anyTime = getattr(native_line, 'x_osaf_anytime_param', "").upper() == 'TRUE'
    allDay = False
    start = native_line.value
    if type(start) == date:
        allDay = not anyTime
        start = TimeZone.forceToDateTime(start)
    else:
        # this parameter is broken, this should be fixed in vobject, at which
        # point this will break
        tzid = native_line.params.get('X-VOBJ-ORIGINAL-TZID')
        if tzid is None:
            tzinfo = ICUtzinfo.floating
        else:
            tzinfo = ICUtzinfo.getInstance(tzid)
        start = start.replace(tzinfo=tzinfo)
    return (start, allDay, anyTime)

def getTimeValues(record):
    """
    Extract start time, end time, and allDay/anyTime from a record.
    """
    dtstart = record.dtstart
    dtend   = record.dtend
    if dtstart is not eim.NoChange:
        start, allDay, anyTime = readICalendarDateTime(dtstart)
    else:
        allDay = anyTime = start = eim.NoChange
        
    if dtend is not eim.NoChange:
        end, end_allDay, end_anyTime = readICalendarDateTime(dtend)
        if end_allDay or end_anyTime:
            # iCalendar syntax for serializing all day dtends is off by one day;
            end -= oneDay 
    else:
        end = eim.NoChange
    
    return (start, end, allDay, anyTime)

class PIMTranslator(eim.Translator):

    URI = "cid:pim-translator@osaf.us"
    version = 1
    description = u"Translator for Chandler PIM items"


    # ItemRecord -------------

    # TODO: lastModifiedBy

    @model.ItemRecord.importer
    def import_item(self, record):

        if COSMO_MODE:
            self.loadItemByUUID(
                record.uuid,
                pim.ContentItem,
                displayName=record.title,
            ) # incomplete
            return

        if record.createdOn is not eim.NoChange:
            # createdOn is a Decimal we need to change to datetime
            naive = datetime.utcfromtimestamp(float(record.createdOn))
            inUTC = naive.replace(tzinfo=utc)
            # Convert to user's tz:
            createdOn = inUTC.astimezone(ICUtzinfo.default)
        else:
            createdOn = eim.NoChange

        if record.triageStatus is not eim.NoChange:
            # @@@MOR -- is this the right way to get an enum?  (it works)
            triageStatus = getattr(pim.TriageEnum, record.triageStatus)
        else:
            triageStatus = eim.NoChange

        if record.triageStatusChanged is not eim.NoChange:
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
        self.loadItemByUUID(
            record.uuid,
            pim.Note,
            icaluid=record.icaluid,
            body=record.body
        )

    @eim.exporter(pim.Note)
    def export_note(self, item):
        yield model.NoteRecord(
            item.itsUUID,                               # uuid
            item.body,                                  # body
            getattr(item, "icaluid", None),             # icaluid
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

        if COSMO_MODE:
            self.loadItemByUUID(
                record.uuid,
                pim.EventStamp,
            ) # incomplete
            return
        
        start, end, allDay, anyTime = getTimeValues(record)
        if end is eim.NoChange and start is not eim.NoChange:
            # odd case, Chandler's object model doesn't allow start to change
            # without changing end, so explicitly set both start and end time
            # appropriately
            item = self.rv.findUUID(record.uuid)
            if item is not None:
                event = pim.EventStamp(item)
                end = event.endTime
                event.startTime = start
                event.endTime = end
                end = start = eim.NoChange
        
        self.loadItemByUUID(
            record.uuid,
            pim.EventStamp,
            startTime=start,
            endTime=end,
            allDay=allDay,
            anyTime=anyTime,
            transparency = with_nochange(record.status, transparency),
            location     = with_nochange(record.location, location, self.rv),
        ) # incomplete


    @eim.exporter(pim.EventStamp)
    def export_event(self, event):
        yield model.EventRecord(
            event.itsItem.itsUUID,                      # uuid
            str(event.startTime),                       # dstart
            None,                                       # dtend
            None,                                       # location
            None,                                       # rrule
            None,                                       # exrule
            None,                                       # rdate
            None,                                       # exdate
            None,                                       # recurrenceid
            str(event.transparency)                      # status
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

