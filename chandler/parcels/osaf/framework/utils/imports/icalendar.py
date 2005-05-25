import os
import application.Globals as Globals
import datetime
import application.Globals as Globals
from repository.persistence.DBRepository import DBRepository
import vobject
import dateutil.tz
import StringIO
import itertools
import osaf.contentmodel.calendar.Calendar as Calendar
from osaf.framework.sharing.ICalendar import eventsToVObject
from repository.item.Query import KindQuery

if not Globals.chandlerDirectory: Globals.chandlerDirectory = '.'

INFILE=os.path.join(Globals.chandlerDirectory, 'import.ics')
OUTFILE='export.ics'

icaltest="""BEGIN:VCALENDAR
CALSCALE:GREGORIAN
X-WR-TIMEZONE;VALUE=TEXT:US/Pacific
METHOD:PUBLISH
PRODID:-//Apple Computer\, Inc//iCal 1.0//EN
X-WR-CALNAME;VALUE=TEXT:Example
VERSION:2.0
BEGIN:VTIMEZONE
TZID:US/Pacific
LAST-MODIFIED:20041121T234620Z
BEGIN:DAYLIGHT
DTSTART:20040404T100000
TZOFFSETTO:-0700
TZOFFSETFROM:+0000
TZNAME:PDT
END:DAYLIGHT
BEGIN:STANDARD
DTSTART:20041031T020000
TZOFFSETTO:-0800
TZOFFSETFROM:-0700
TZNAME:PST
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:20050403T010000
TZOFFSETTO:-0700
TZOFFSETFROM:-0800
TZNAME:PDT
END:DAYLIGHT
END:VTIMEZONE
BEGIN:VEVENT
SEQUENCE:5
DTSTART;TZID=US/Pacific:20041221T140000
DTSTAMP:20021028T011706Z
SUMMARY:Coffee with Jason
UID:EC9439B1-FF65-11D6-9973-003065F99D04
DTEND;TZID=US/Pacific:20041221T150000
END:VEVENT
END:VCALENDAR"""


#Uncomment to run doctests
#cal = vobject.readComponents(StringIO.StringIO(icaltest)).next()
#pacific = cal.vtimezone[0].tzinfo

localtime = dateutil.tz.tzlocal()
utc = dateutil.tz.tzutc()

def convertToUTC(dt, tz = None):
    """Convert the given datetime (without tz) into datetime with tzinfo=UTC.
    
    >>> import datetime
    >>> dt = datetime.datetime(2004, 12, 20, 12)
    >>> dt = convertToUTC(dt, pacific)
    >>> print dt
    2004-12-20 20:00:00+00:00
    
    """
    if tz is None:
        tz = localtime

    return dt.replace(tzinfo=tz).astimezone(utc)

    
def importICalendar(cal, rep, parent=None):
    """Import the given vobject vcalendar into rep at the given parent.
    
    Currently only grabs vevents, ignores duration, ignores rdates with
    extra duration information.  Also, vobject 0.1 has a bug (argh) that
    completely ignores recurrence information.  Fortunately, this offsets a bug
    in parsing rrules that are unicode.
    
    """
    textkind = rep.findPath("//Schema/Core/Lob")
    for event in cal.vevent:
        #vevent's should really have a calculated duration in vobject
        #Note that the only functional difference between dtend and duration
        #is when duration crosses daylight savings time, that corner case
        #fails with the naive calculation below.
        if not getattr(event, 'dtstart', None):
            continue #we don't know what to do with events without dtstarts
        if getattr(event, 'dtend', None):
            duration = event.dtend[0].value - event.dtstart[0].value
        elif getattr(event, 'duration', None):
            duration = event.duration[0].value
        else: duration = None
        #lets not go crazy with large recurrence sets
        for dt in itertools.islice(event.rruleset, 10):
            newevent = Calendar.CalendarEvent(view=rep.view)
            newevent.startTime = dt
            if duration:
                newevent.endTime = dt + duration

            test = getattr(event, 'description', [])
            if len(test) > 0:
                newevent.body = textkind.makeValue(test[0].value)
            test = getattr(event, 'summary', [])
            if len(test) > 0:
                newevent.displayName = test[0].value
            test = getattr(event, 'dtstamp', [])
            if len(test) > 0:
                newevent.createdOn = test[0].value
            test = getattr(event, 'valarm', [])
            if len(test) > 0:
                #assume DURATION, not DATE-TIME
                newevent.reminderTime = dt + test[0].trigger[0].value
    return True

def importFile(filename, rep):
    success = True
    f = file(filename)
    try:
        for vcal in vobject.readComponents(f): importICalendar(vcal, rep)
    except Exception, e:
        msg = "Failed vobject.readComponents, caught exception "
        rep.logger.info(msg + str(e))
        success = False
    f.close()
    rep.commit()
    return success

def exportFile(filename, rep):
    f = file(filename, 'w')
    eventkind = rep.findPath('//parcels/osaf/contentmodel/calendar/CalendarEvent')
    cal = eventsToVObject(KindQuery().run([eventkind]))
    cal.serialize(f)
    return True

#------------------- Testing and running functions -----------------------------

def _test():
    import doctest, icalendar, datetime
    doctest.testmod(icalendar, verbose=0)
    
if __name__ == '__main__':
    _test()
