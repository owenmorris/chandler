import os
import application.Globals as Globals
import mx.DateTime as DateTime
import datetime
import application.Globals as Globals
from repository.persistence.DBRepository import DBRepository
import vobject
import dateutil.tz
import StringIO
import itertools

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
cal = vobject.readComponents(StringIO.StringIO(icaltest)).next()
pacific = cal.vtimezone[0].tzinfo

localtime = dateutil.tz.tzlocal()
utc = dateutil.tz.tzutc()

def convertToMX(dt, tz=None):
    """Convert the given datetime into an mxDateTime.
    
    Convert dt to local time if it has a timezone.
    
    >>> import datetime, mx.DateTime
    >>> dt = datetime.datetime(2004, 12, 20, 18, tzinfo=utc)
    >>> mxdt = convertToMX(dt, pacific)
    >>> print mxdt
    2004-12-20 10:00:00.00
    >>> type(mxdt)
    <type 'DateTime'>
    
    """
    if not tz: tz = localtime
    if dt.tzinfo: dt = dt.astimezone(tz)
    return DateTime.mktime(dt.timetuple())
    
def convertToUTC(dt, tz = None):
    """Convert the given mxDateTime (without tz) into datetime with tzinfo=UTC.
    
    >>> import datetime, mx.DateTime
    >>> mxdt = mx.DateTime.DateTime(2004, 12, 20, 12)
    >>> dt = convertToUTC(mxdt, pacific)
    >>> print dt
    2004-12-20 20:00:00+00:00
    
    """
    if not tz: tz = localtime
    args = (dt.year, dt.month, dt.day, dt.hour, dt.minute, int(dt.second))
    return datetime.datetime(*args).replace(tzinfo=tz).astimezone(utc)
    

#only look at vcalendar roots
#setBehavior iCalendar, transformChildrenToNative

def newEvent(rep, name=None, parent = None):
    """Create a new CalendarEvent in the repository, return it."""

    eventkind = rep.findPath("//parcels/osaf/contentmodel/calendar/CalendarEvent")
    userdata = rep.findPath("//userdata")

    if parent is None: parent = userdata
    return eventkind.newItem(name, parent)

def importICalendar(cal, rep, parent=None):
    """Import the given vobject vcalendar into rep at the given parent.
    
    Currently only grabs vevents, ignores duration, ignores rdates with
    extra duration information.  Also, vobject 0.1 has a bug (argh) that
    completely ignores recurrence information.  Fortunately, this offsets a bug
    in parsing rrules that are unicode.
    
    """
    for event in cal.vevent:
        #vevent's should really have a calculated duration in vobject
        if not getattr(event, 'dtstart', None):
            continue #we don't know what to do with events without dtstarts
        if getattr(event, 'dtend', None):
            duration = event.dtend[0].value - event.dtstart[0].value
        elif getattr(event, 'duration', None):
            #duration hasn't quite been wired up yet in vobject
            continue
        else: duration = None
        #lets not go crazy with large recurrence sets
        for dt in itertools.islice(event.rruleset, 10):
            newevent = newEvent(rep)
            newevent.startTime = convertToMX(dt)
            if duration:
                newevent.endTime = convertToMX(dt + duration)
                
            # writing to body doesn't seem to work this way.
            #test = getattr(event, 'description', [])
            #if len(test) > 0:
            #    writer = newevent.body.getWriter()
            #    writer.write(test[0].value)
            #    writer.close()
            test = getattr(event, 'summary', [])
            if len(test) > 0:
                newevent.displayName = test[0].value
            test = getattr(event, 'dtstamp', [])
            if len(test) > 0:
                newevent.createdOn = convertToMX(test[0].value)
    return True

def exportICalendar(eventlist, stream):
    """Export all events in eventlist as iCalendar to stream."""
    pass

def importFile(filename, rep):
    #rep.logger.info("got to importFile") 
    f = file(filename)
    try:
        for vcal in vobject.readComponents(f): importICalendar(vcal, rep)
    except Exception, e:
        msg = "Failed vobject.readComponents, caught exception "
        rep.logger.info(msg + str(e))
    f.close()
    rep.commit()
    return True

def exportICalendar(events, out):
    """Export the list of Chandler CalendarEvents to one VCALENDAR in out."""
    pass


#------------------- Testing and running functions -----------------------------

def _test():
    import doctest, icalendar, datetime
    doctest.testmod(icalendar, verbose=0)
    
if __name__ == '__main__':
    _test()
