__parcel__ = "osaf.sharing"

import Sharing
import application.Parcel
from osaf.pim import AbstractCollection, ListCollection
import osaf.pim.calendar.Calendar as Calendar
import osaf.pim.calendar.TimeZone as TimeZone
from chandlerdb.util.uuid import UUID
import StringIO
import vobject
import logging
import dateutil.tz
import datetime
from datetime import date, time
from PyICU import ICUtzinfo
import itertools
from application import schema

logger = logging.getLogger(__name__)

localtime = dateutil.tz.tzlocal()
utc = dateutil.tz.tzutc()
    
def translateToTimezone(dt, tzinfo):
    if dt.tzinfo == None:
        return dt.replace(tzinfo=localtime).astimezone(tzinfo)
    else:
        return dt.astimezone(tzinfo)

class RecurrenceToVObject:
    """Temporary home for creating vobject objects that can be serialized.
    
    These functions currently force all recurrence into the US-Pacific, and
    only support a small subset of possible recurrence rules.  Eventually,
    all this functionality should move (in a more general form) to vobject.
    
    """
    def __init__(self):
        pacificVTimezoneString = """BEGIN:VTIMEZONE
TZID:US-Pacific
LAST-MODIFIED:19870101T000000Z
BEGIN:STANDARD
DTSTART:19671029T020000
RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10
TZOFFSETFROM:-0700
TZOFFSETTO:-0800
TZNAME:PST
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19870405T020000
RRULE:FREQ=YEARLY;BYDAY=1SU;BYMONTH=4
TZOFFSETFROM:-0800
TZOFFSETTO:-0700
TZNAME:PDT
END:DAYLIGHT
END:VTIMEZONE"""
        buffer = StringIO.StringIO(pacificVTimezoneString)
        buffer.seek(0)
        self.pacificTZ = dateutil.tz.tzical(buffer).get()
        buffer.seek(0)
        self.pacificVTimezone = vobject.readComponents(buffer).next()

    def addRRule(self, vevent, freq, count=None, until=None):
        """Adds an RRULE line to a Component.
        
        Because native vobject vevents are RecurringComponents, use the
        transformFromNative method before calling addRRule.
        
        """
        val = "FREQ=" + freq.upper()
        if count is not None:
            val += ";COUNT=" + str(count)
        elif until is not None: # you can't have both a count and until
            until = translateToTimezone(until, utc) # until must be in UTC
            val += ";UNTIL=" + vobject.serializing.dateTimeToString(until)
        vevent.add('RRULE').value = val

RecurrenceHelper = RecurrenceToVObject()

def dateForVObject(dt, asDate = False):
    """Convert the given datetime into a date or datetime in Pacific time."""
    if asDate:
        return dt.date()
    else:
        return translateToTimezone(dt, RecurrenceHelper.pacificTZ)

def preserveTimezone(dtContentLine):
    """Timezones in vobject lines are converted to UTC by default."""
    dtContentLine.params['X-VOBJ-PRESERVE-TZID'] = ['TRUE']

def itemsToVObject(view, items, cal=None, filters=None):
    """Iterate through items, add to cal, create a new vcalendar if needed.

    Consider only master events (then serialize all modifications).  For now,
    set all timezones to Pacific.

    """
    tzidsUsed = {'US-Pacific' : True }
    def populate(comp, item):
        """Populate the given vobject vevent with data from item."""
        if item.getAttributeValue('icalUID', default=None) is None:
            item.icalUID = unicode(item.itsUUID)
        comp.add('uid').value = item.icalUID

        try:
            comp.add('summary').value = item.displayName
        except AttributeError:
            pass
        
        try:
            dtstartLine = comp.add('dtstart')
            dtstartLine.value = dateForVObject(item.startTime, item.allDay)
            preserveTimezone(dtstartLine)
            # placeholder until we deal with different timezones
            tzidsUsed['US-Pacific'] = True 
        except AttributeError:
            pass
        
        try:
            dtendLine = comp.add('dtend')
            #convert Chandler's notion of allDay duration to iCalendar's
            if item.allDay:
                dtendLine.value = dateForVObject(item.endTime,item.allDay) + \
                                                 datetime.timedelta(days=1)
            else:
                dtendLine.value = dateForVObject(item.endTime,item.allDay)
            preserveTimezone(dtendLine)
            
            # placeholder until we deal with different timezones
            tzidsUsed['US-Pacific'] = True 
        except AttributeError:
            comp.dtend = [] # delete the dtend that was added
            

        if not filters or "transparency" not in filters:
            try:
                status = item.transparency.upper()
                if status == 'FYI': status = 'CANCELLED'
                comp.add('status').value = status
            except AttributeError:
                pass

        try:
            comp.add('description').value = item.body.getReader().read()
        except AttributeError:
            pass
        
        try:
            comp.add('location').value = item.location.displayName
        except AttributeError:
            pass

        if not filters or "reminderTime" not in filters:
            try:
                comp.add('valarm').add('trigger').value = \
                  dateForVObject(item.reminderTime) - \
                  dateForVObject(item.startTime)
            except AttributeError:
                pass
        
        if item.getAttributeValue('modificationFor', default=None) is not None:
            recurrenceid = comp.add('recurrence-id')
            recurrenceid.value = dateForVObject(item.recurrenceID,item.allDay)
            if item.modifies != 'this':
                recurrenceid.params['RANGE'] = [item.modifies.upper()]
            preserveTimezone(recurrenceid)
        
        # logic for serializing rrules needs to move to vobject
        try: # hack, create RRULE line last, because it means running transformFromNative
            if item.modifies == 'thisandfuture' or item.getMaster() == item:
                rule = item.rruleset.rrules.first() # only dealing with one rrule right now
                comp = cal.vevent[-1] = comp.transformFromNative()
                RecurrenceHelper.addRRule(comp, rule.freq, until=rule.calculatedUntil())
        except AttributeError:
            pass
        # end of populate function

    def populateModifications(item, cal):
        for modification in item.getAttributeValue('modifications', default=[]):
            populate(cal.add('vevent'), modification)
            if modification.modifies == 'thisandfuture':
                populateModifications(modification, cal)
        #end helper functions

    if cal is None:
        cal = vobject.iCalendar()
    for item in items: # main loop
        try:
            # ignore any events that aren't masters
            if item.getMaster() == item:
                populate(cal.add('vevent'), item)
            else:
                continue
        except:
            continue
        
        populateModifications(item, cal)

    # placeholder until we deal with different timezones
    if tzidsUsed.get('US-Pacific') == True:
        cal.vtimezone = [RecurrenceHelper.pacificVTimezone]

    return cal

def convertToICUtzinfo(dt):
    """
    This method returns a C{datetime} whose C{tzinfo} field
    (if any) is an instance of the ICUtzinfo class.
    
    @param dt: The C{datetime} whose C{tzinfo} field we want
               to convert to an ICUtzinfo instance.
    @type dt: C{datetime}
    """
    oldTzinfo = dt.tzinfo
    
    if oldTzinfo is not None:

        def getICUInstance(name):
            result = None
            
            if name is not None:
                result = ICUtzinfo.getInstance(name)
                
                if result is not None and \
                    result.timezone.getID() == 'GMT' and \
                    tzname != 'GMT':
                    
                    result = None
                    
            return result

    
        
        
        # First, for dateutil.tz._tzicalvtz, we check
        # _tzid, since that's the displayable timezone
        # we want to use. This is kind of cheesy, but
        # works for now. This means that we're preferring
        # a tz like 'America/Chicago' over 'CST' or 'CDT'.
        icuTzinfo = getICUInstance(getattr(oldTzinfo, '_tzid', None))
        
        # If that didn't work, get the name of the tz
        # at the value of dt
        if icuTzinfo is None:
            icuTzinfo = getICUInstance(oldTzinfo.tzname(dt))
            
        # Here, if we have an unknown timezone, we'll turn
        # it into a floating datetime, which is probably not right
        dt = dt.replace(tzinfo=icuTzinfo)
        
    return dt

class ICalendarFormat(Sharing.ImportExportFormat):

    schema.kindInfo(displayName="iCalendar Import/Export Format Kind")

    _calendarEventPath = "//parcels/osaf/pim/calendar/CalendarEvent"
    _taskPath = "//parcels/osaf/pim/EventTask"
    _lobPath = "//Schema/Core/Lob"
    
    def fileStyle(self):
        return self.STYLE_SINGLE

    def extension(self, item):
        return "ics"

    def findUID(self, uid):
        """Return the master event whose icalUID matched uid, or None."""
        uid_map = schema.ns('osaf.sharing', self.itsView).uid_map
        matches = uid_map.items.getByAlias(uid)
        if matches is None:
            return None
        else: 
            return uid_map.items.getByAlias(uid).getMaster()

    def importProcess(self, text, extension=None, item=None):
        # the item parameter is so that a share item can be passed in for us
        # to populate.

        # An ICalendar file doesn't have any 'share' info, just the collection
        # of events, etc.  Therefore, we want to actually populate the share's
        # 'contents':

        view = self.itsView
        filters = self.share.filterAttributes

        newItemParent = self.findPath("//userdata")
        eventKind = self.itsView.findPath(self._calendarEventPath)
        taskKind  = self.itsView.findPath(self._taskPath)
        textKind  = self.itsView.findPath(self._lobPath)

        if self.fileStyle() == self.STYLE_SINGLE:
            if item is None:
                item = ListCollection(view=view)
            elif isinstance(item, Sharing.Share):
                if item.contents is None:
                    item.contents = ListCollection(view=view)
                item = item.contents

            if not isinstance(item, AbstractCollection):
                print "Only a share or an item collection can be passed in"
                #@@@MOR Raise something

        input = StringIO.StringIO(text)
        calendar = vobject.readComponents(input, validate=True).next()

        if self.fileStyle() == self.STYLE_SINGLE:
            try:
                calName = calendar.contents[u'x-wr-calname'][0].value
            except:
                calName = "Imported Calendar"
            item.displayName = calName

        countNew = 0
        countUpdated = 0
        
        eventlist = getattr(calendar, 'vevent', [])
        todolist  = getattr(calendar, 'vtodo', [])
        
        # this is just a quick hack to get VTODO working, FIXME write
        # more readable table driven code to process VEVENTs and VTODOs
        for event in itertools.chain(eventlist, todolist):
            vtype = event.name
            if vtype == u'VEVENT':
                logger.debug("got VEVENT")
                pickKind = eventKind
            elif vtype == u'VTODO':
                logger.debug("got VTODO")
                pickKind = taskKind

            try:
                displayName = event.summary[0].value
            except AttributeError:
                displayName = ""

            try:
                description = event.description[0].value
            except AttributeError:
                description = None
                
            try:
                location = event.location[0].value
            except AttributeError:
                location = None            

            try:
                status = event.status[0].value.lower()
                if status in ('confirmed', 'tentative'):
                    pass
                elif status == 'cancelled': #Chandler doesn't have CANCELLED
                    status = 'fyi'
                else:
                    status = 'confirmed'
            except AttributeError:
                status = 'confirmed'

            try:
                # FIXME assumes DURATION, not DATE-TIME
                reminderDelta = event.valarm[0].trigger[0].value
            except AttributeError:
                reminderDelta = None

            # RFC2445 allows VEVENTs without DTSTART, but it's hard to guess
            # what that would mean, so we won't catch an exception if there's no
            # dtstart.
            dtstart  = event.dtstart[0].value 
            
            try:
                duration = event.duration[0].value
            except AttributeError:
                # note that duration = dtend - dtstart isn't strictly correct
                # throughout a recurrence set, 1 hour differences might happen
                # around DST, but we'll ignore that corner case for now
                try:
                    duration = event.dtend[0].value - dtstart
                # FIXME no end time or duration, Calendar UI doesn't seem to
                # like events with no duration, so for now we'll set a dummy
                # duration of 1 hour
                except AttributeError:
                    # FIXME Nesting try/excepts is ugly.  Also, we're assuming
                    # DATE-TIMEs, not DATEs.
                    try:
                        duration = event.due[0].value - dtstart
                    except AttributeError:
                        if vtype == u'VEVENT':
                            duration = datetime.timedelta(hours=1)
                        elif vtype == u'VTODO':
                            duration = None
                            
            isDate = type(dtstart) == date
            if isDate:
                dtstart = datetime.datetime.combine(dtstart, time(0))
                if duration: # convert to Chandler's notion of all day duration
                    duration -= datetime.timedelta(days=1)
                    
            # ignore timezones and recurrence till tzinfo -> PyICU is written
            # give the repository a naive datetime, no timezone
            dtstart = convertToICUtzinfo(dtstart)
            # Because of restrictions on dateutil.rrule, we're going
            # to have to make sure all the datetimes we create have
            # the same naivete as dtstart
            tzinfo = dtstart.tzinfo
            
            def makeNaiveteMatch(dt):
                if dt.tzinfo is None:
                    if tzinfo is not None:
                        dt = TimeZone.coerceTimeZone(dt, tzinfo)
                else:
                    if tzinfo is None:
                        dt = TimeZone.stripTimeZone(dt)
                return dt
 
            
            # See if we have a corresponding item already
            recurrenceID = None
            uidMatchItem = self.findUID(event.uid[0].value)
            if uidMatchItem is not None:
                logger.debug("matched UID")
                try:
                    recurrenceID = event.contents['recurrence-id'][0].value
                    if type(recurrenceID) == date:
                        recurrenceID = datetime.datetime.combine(
                                                    recurrenceID,
                                                    time(tzinfo=tzinfo))
                    else:
                        recurrenceID = makeNaiveteMatch(
                                              convertToICUtzinfo(recurrenceID))
                except:
                    pass
                if recurrenceID:
                    eventItem = uidMatchItem.getRecurrenceID(recurrenceID)
                    if eventItem == None:
                        raise Exception, "RECURRENCE-ID didn't match rule. " + \
                                         "RECURRENCE-ID = %s" % recurrenceID
                else:
                    eventItem = uidMatchItem
                    countUpdated += 1
            else:
                eventItem = pickKind.newItem(None, newItemParent)
                countNew += 1
                eventItem.icalUID = event.uid[0].value

                # Add this event to our UID map:
                uid_map = schema.ns('osaf.sharing', view).uid_map
                uid_map.items.append(eventItem, eventItem.icalUID)


            # vobject isn't meshing well with dateutil when dtstart isDate;
            # dtstart is converted to a datetime for dateutil, but rdate
            # isn't.  To make dateutil happy, convert rdates which are dates to
            # datetimes until vobject is fixed.
            for i, rdate in enumerate(event.rdate):
                if type(rdate) == date:
                    event.rdate[i] = datetime.datetime.combine(rdate,
                                                            time(tzinfo=tzinfo))
                else:
                    event.rdate[i] = makeNaiveteMatch(convertToICUtzinfo(
                                                      event.rdate[i]))
                    
                # get rid of RDATES that match dtstart, created by vobject to
                # deal with unusual RRULEs correctly
                if event.rdate[i] == dtstart:
                    del event.rdate[i]
                
            logger.debug("eventItem is %s" % str(eventItem))
            
            #Default to NOT any time
            eventItem.anyTime = False
            
            eventItem.displayName = displayName
            if isDate:
                eventItem.allDay = True
            eventItem.startTime   = dtstart
            if vtype == u'VEVENT':
                eventItem.endTime = dtstart + duration
            elif vtype == u'VTODO':
                if duration is not None:
                    eventItem.dueDate = dtstart + duration
            
            if not filters or "transparency" not in filters:
                eventItem.transparency = status
            
            # I think Item.description describes a Kind, not userdata, so
            # I'm using DESCRIPTION <-> body  
            if description is not None:
                eventItem.body = textKind.makeValue(description)
            
            if location:
                eventItem.location = Calendar.Location.getLocation(view,
                                                                   location)
            
            if not filters or "reminderTime" not in filters:
                if reminderDelta is not None:
                    eventItem.reminderTime = dtstart + reminderDelta

            if len(event.rdate) > 0 or len(event.rrule) > 0:
                eventItem.setRuleFromDateUtil(event.rruleset)
            elif recurrenceID is None: # delete any existing rule
                eventItem.removeRecurrence()

            logger.debug("Imported %s %s" % (eventItem.displayName,
             eventItem.startTime))

            if self.fileStyle() == self.STYLE_SINGLE:
                item.add(eventItem)
            else:
                return eventItem
                 
        logger.info("...iCalendar import of %d new items, %d updated" % \
         (countNew, countUpdated))

        return item

    def exportProcess(self, share, depth=0):
        cal = itemsToVObject(self.itsView, share.contents,
                             filters=self.share.filterAttributes)
        try:
            cal.add('x-wr-calname').value = share.contents.displayName
        except:
            pass
        return cal.serialize()


class CalDAVFormat(ICalendarFormat):
    """Treat multiple events as different resources."""
    
    def fileStyle(self):
        return self.STYLE_DIRECTORY

    def exportProcess(self, item, depth=0):
        """Item may be a Share or an individual Item, return None if Share."""
        if isinstance(item, Sharing.Share):
            return None
        cal = itemsToVObject(self.itsView, [item],
                             filters=self.share.filterAttributes)
        return cal.serialize()
