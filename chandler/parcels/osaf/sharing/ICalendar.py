__parcel__ = "osaf.sharing"

__all__ = [
    'ICalendarFormat',
    'CalDAVFormat',
]

import Sharing
import application.Parcel
from osaf.pim import AbstractCollection, ListCollection, CalendarEventMixin
import osaf.pim.calendar.Calendar as Calendar
import osaf.pim.calendar.TimeZone as TimeZone
import StringIO
import vobject
import logging
import dateutil.tz
import datetime
from datetime import date, time
from PyICU import ICUtzinfo
from application import schema
import itertools

logger = logging.getLogger(__name__)
DEBUG = logger.getEffectiveLevel() <= logging.DEBUG

localtime = dateutil.tz.tzlocal()
utc = dateutil.tz.tzutc()
    
def translateToTimezone(dt, tzinfo):
    if dt.tzinfo == None:
        return dt.replace(tzinfo=localtime).astimezone(tzinfo)
    else:
        return dt.astimezone(tzinfo)

def dateForVObject(dt, asDate = False):
    """
    Convert the given datetime into a date or datetime in Pacific time.
    """
    if asDate:
        return dt.date()
    else:
        return dt

def itemsToVObject(view, items, cal=None, filters=None):
    """
    Iterate through items, add to cal, create a new vcalendar if needed.

    Consider only master events (then serialize all modifications).  For now,
    set all timezones to Pacific.

    """
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

        if not filters or "reminders" not in filters:
            firstReminder = item.reminders.first()
            if firstReminder is not None:
                comp.add('valarm').add('trigger').value = firstReminder.delta
        
        if item.getAttributeValue('modificationFor', default=None) is not None:
            recurrenceid = comp.add('recurrence-id')
            recurrenceid.value = dateForVObject(item.recurrenceID,item.allDay)
            if item.modifies != 'this':
                recurrenceid.params['RANGE'] = [item.modifies.upper()]
        
        # logic for serializing rrules needs to move to vobject
        try: # hack, create RRULE line last, because it means running transformFromNative
            if item.modifies == 'thisandfuture' or item.getMaster() == item:
                x = item.createDateUtilFromRule()
                cal.vevent[-1].rruleset = item.createDateUtilFromRule()
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
                    result.tzid == 'GMT' and \
                    name != 'GMT':
                        
                    
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

def makeNaiveteMatch(dt, tzinfo):
    if dt.tzinfo is None:
        if tzinfo is not None:
            dt = TimeZone.coerceTimeZone(dt, tzinfo)
    else:
        if tzinfo is None:
            dt = TimeZone.stripTimeZone(dt)
    return dt


class ICalendarFormat(Sharing.ImportExportFormat):

    schema.kindInfo(displayName=u"iCalendar Import/Export Format Kind")

    _calendarEventPath = "//parcels/osaf/pim/calendar/CalendarEvent"
    _taskPath = "//parcels/osaf/pim/EventTask"
    _lobPath = "//Schema/Core/Lob"
    
    def fileStyle(self):
        return self.STYLE_SINGLE

    def extension(self, item):
        return "ics"

    def contentType(self, item):
        return "text/calendar"

    def findUID(self, uid):
        """
        Return the master event whose icalUID matched uid, or None.
        """
        uid_map = schema.ns('osaf.sharing', self.itsView).uid_map
        match = uid_map.items.getByAlias(uid)
        if match is None:
            return None
        else:
            return match.getMaster()

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
                item = ListCollection(view=view).setup()
            elif isinstance(item, Sharing.Share):
                if item.contents is None:
                    item.contents = ListCollection(view=view).setup()
                item = item.contents

            if not isinstance(item, AbstractCollection):
                print "Only a share or an item collection can be passed in"
                #@@@MOR Raise something
        else:
            caldavReturn = None

        input = StringIO.StringIO(text)
        calendar = vobject.readComponents(input, validate=True).next()

        if self.fileStyle() == self.STYLE_SINGLE:
            try:
                calName = calendar.contents[u'x-wr-calname'][0].value
            except:
                calName = u"Imported Calendar"
            item.displayName = unicode(calName)

        countNew = 0
        countUpdated = 0
        
        modificationQueue = []
        
        minusone = itertools.repeat(-1)
        # This is, essentially: [(-1, event) for event in calendar.vevent]
        vevents = itertools.izip(minusone, getattr(calendar, 'vevent', []))
        for i, event in itertools.chain(vevents, enumerate(modificationQueue)):
            # Queue modifications to recurring events so modifications are
            # processed after master events in the iCalendar stream.
            recurrenceID = None
            try:
                recurrenceID = event.contents['recurrence-id'][0].value
                if i < 0: # only add to modificationQueue in initial processing
                    modificationQueue.append(event)
                    continue
            except:
                pass

            try:
                if DEBUG: logger.debug("got VEVENT")
                pickKind = eventKind

                try:
                    displayName = event.summary[0].value
                except AttributeError:
                    displayName = u""

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
                isDate = type(dtstart) == date

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
                        # FIXME Nesting try/excepts is ugly.
                        try:
                            duration = event.due[0].value - dtstart
                        except AttributeError:
                            if isDate: 
                                # make it two days long, our conversion from 
                                # iCalendar to sane changes it to 2 days long later
                                duration = datetime.timedelta(days=2)
                            else:
                                duration = datetime.timedelta(0)
                                
    
                if isDate:
                    dtstart = TimeZone.forceToDateTime(dtstart)
                    # convert to Chandler's notion of all day duration
                    duration -= datetime.timedelta(days=1)
                        
                # ignore timezones and recurrence till tzinfo -> PyICU is written
                # give the repository a naive datetime, no timezone
                dtstart = convertToICUtzinfo(dtstart)
                # Because of restrictions on dateutil.rrule, we're going
                # to have to make sure all the datetimes we create have
                # the same naivete as dtstart
                tzinfo = dtstart.tzinfo
                
                # See if we have a corresponding item already
                uidMatchItem = self.findUID(event.uid[0].value)
                if uidMatchItem is not None:
                    if DEBUG: logger.debug("matched UID")

                    if recurrenceID:
                        if type(recurrenceID) == date:
                            recurrenceID = datetime.datetime.combine(
                                                        recurrenceID,
                                                        time(tzinfo=tzinfo))
                        else:
                            recurrenceID = makeNaiveteMatch(
                                               convertToICUtzinfo(recurrenceID),
                                               tzinfo)
                            
                        eventItem = uidMatchItem.getRecurrenceID(recurrenceID)
                        if eventItem == None:
                            # our recurrenceID didn't match an item we know
                            # about.  This may be because the item is created
                            # by a later modification, a case we're not dealing
                            # with.  For now, just skip it.
                            logger.info("RECURRENCE-ID didn't match rule. " \
                                        "RECURRENCE-ID = %s" % recurrenceID)
                            continue
                    else:
                        eventItem = uidMatchItem
                        if (eventItem.occurrenceFor is None and
                            eventItem.occurrences is None):
                                eventItem.occurrenceFor = eventItem
                        if eventItem.rruleset is not None:
                            # re-creating a recurring item from scratch, delete 
                            # old recurrence information
                            eventItem.removeRecurrence()

                        countUpdated += 1
                else:
                    eventItem = pickKind.newItem(None, newItemParent)
                    countNew += 1
                    eventItem.icalUID = event.uid[0].value
                    
                if DEBUG: logger.debug("eventItem is %s" % str(eventItem))
                
                #Default to NOT any time
                eventItem.anyTime = False
                
                eventItem.displayName = displayName
                if isDate:
                    eventItem.allDay = True
                eventItem.startTime   = dtstart
                eventItem.endTime = dtstart + duration
                
                if not filters or "transparency" not in filters:
                    eventItem.transparency = status
                
                # I think Item.description describes a Kind, not userdata, so
                # I'm using DESCRIPTION <-> body  
                if description is not None:
                    eventItem.body = textKind.makeValue(description)
                
                if location:
                    eventItem.location = Calendar.Location.getLocation(view,
                                                                       location)
                
                if not filters or "reminders" not in filters:
                    if reminderDelta is not None:
                        eventItem.makeReminder(reminderDelta)
                
                rruleset = event.rruleset
                if rruleset is not None:
                    eventItem.setRuleFromDateUtil(rruleset)
                elif recurrenceID is None: # delete any existing rule
                    eventItem.removeRecurrence()
    
                if DEBUG: logger.debug(u"Imported %s %s" % (eventItem.displayName,
                 eventItem.startTime))
    
                if self.fileStyle() == self.STYLE_SINGLE:
                    item.add(eventItem.getMaster())
                else:
                    caldavReturn = eventItem.getMaster()
            except Exception, e:
                if __debug__:
                    raise e
                else:
                    logger.exception("import failed to import one event with \
                                     exception: %s" % str(e))
                     
        logger.info("...iCalendar import of %d new items, %d updated" % \
         (countNew, countUpdated))

        if self.fileStyle() == self.STYLE_SINGLE:
            return item
        else:
            return caldavReturn


    def exportProcess(self, share, depth=0):
        cal = itemsToVObject(self.itsView, share.contents,
                             filters=self.share.filterAttributes)
        try:
            cal.add('x-wr-calname').value = share.contents.displayName
        except:
            pass
        return cal.serialize().encode('utf-8')


class CalDAVFormat(ICalendarFormat):
    """
    Treat multiple events as different resources.
    """
    
    def fileStyle(self):
        return self.STYLE_DIRECTORY

    def exportProcess(self, item, depth=0):
        """
        Item may be a Share or an individual Item, return None if Share.
        """
        if not isinstance(item, CalendarEventMixin):
            return None
        cal = itemsToVObject(self.itsView, [item],
                             filters=self.share.filterAttributes)
        return cal.serialize().encode('utf-8')
