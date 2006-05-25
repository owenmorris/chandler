__parcel__ = "osaf.sharing"

__all__ = [
    'ICalendarFormat',
    'CalDAVFormat',
    'FreeBusyFileFormat'
]

import Sharing
import application.Parcel
from osaf.pim import ContentCollection, SmartCollection, CalendarEventMixin
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.calendar.Recurrence import RecurrenceRuleSet
import osaf.pim.calendar.TimeZone as TimeZone
import StringIO
import vobject
import logging
import dateutil.tz
import datetime
from datetime import date, time
from time import time as epoch_time
from PyICU import ICUtzinfo
import PyICU
from osaf.pim.calendar.TimeZone import TimeZoneInfo
from application import schema
import itertools
from i18n import OSAFMessageFactory as _
import os, logging
import application.Globals as Globals
import bisect

FREEBUSY_WEEKS_EXPORTED = 26

logger = logging.getLogger(__name__)
DEBUG = logger.getEffectiveLevel() <= logging.DEBUG

localtime = dateutil.tz.tzlocal()
utc = dateutil.tz.tzutc()
oneDay = datetime.timedelta(1)

def translateToTimezone(dt, tzinfo):
    if dt.tzinfo == None:
        return dt.replace(tzinfo=localtime).astimezone(tzinfo)
    else:
        return dt.astimezone(tzinfo)

def itemsToVObject(view, items, cal=None, filters=None):
    """
    Iterate through items, add to cal, create a new vcalendar if needed.

    Consider only master events (then serialize all modifications).  For now,
    set all timezones to Pacific.

    """
    def populate(comp, item):
        """Populate the given vobject vevent with data from item."""
        
        def makeDateTimeValue(dt, asDate=False):
            if asDate:
                return dt.date()
            elif dt.tzinfo is ICUtzinfo.floating:
                return dt.replace(tzinfo=None)
            else:
                return dt
        
        if item.getAttributeValue('icalUID', default=None) is None:
            item.icalUID = unicode(item.itsUUID)
        comp.add('uid').value = item.icalUID

        try:
            comp.add('summary').value = item.displayName
        except AttributeError:
            pass
        
        try:
            dtstartLine = comp.add('dtstart')
            
            # allDay-ness overrides anyTime-ness
            if item.anyTime and not item.allDay:
                dtstartLine.x_osaf_anytime_param = 'TRUE'
                
            dtstartLine.value = makeDateTimeValue(item.startTime,
                                    item.anyTime or item.allDay)

        except AttributeError:
            comp.dtstart = [] # delete the dtstart that was added
        
        try:
            if not (item.duration == datetime.timedelta(0) or (
                    (item.anyTime or item.allDay) and 
                    item.duration <= oneDay)):
                dtendLine = comp.add('dtend')
                #convert Chandler's notion of allDay duration to iCalendar's
                if item.allDay:
                    dtendLine.value = item.endTime.date() + oneDay
                else:
                    if item.anyTime:
                        dtendLine.x_osaf_anytime_param = 'TRUE'

                    # anyTime should be exported as allDay for non-Chandler apps
                    dtendLine.value = makeDateTimeValue(item.endTime,
                                                        item.anyTime)

        except AttributeError:
            comp.dtend = [] # delete the dtend that was added
            

        if not filters or "transparency" not in filters:
            try:
                status = item.transparency.upper()
                # anytime events should be interpreted as not taking up time,
                # but all-day shouldn't
                if status == 'FYI' or (not item.allDay and item.anyTime):
                    status = 'CANCELLED'
                comp.add('status').value = status
            except AttributeError:
                pass

        try:
            comp.add('description').value = item.body
        except AttributeError:
            pass
        
        try:
            comp.add('location').value = item.location.displayName
        except AttributeError:
            pass

        if not filters or "reminders" not in filters:
            firstReminder = item.reminders.first() or item.expiredReminders.first()
            if firstReminder is not None:
                comp.add('valarm').add('trigger').value = firstReminder.delta
        
        if item.getAttributeValue('modificationFor', default=None) is not None:
            recurrenceid = comp.add('recurrence-id')
            master = item.getMaster()
            allDay = master.allDay or master.anyTime
            
            recurrenceid.value = makeDateTimeValue(item.recurrenceID, allDay)
        
        # logic for serializing rrules needs to move to vobject
        try: # hack, create RRULE line last, because it means running transformFromNative
            if item.getMaster() == item and item.rruleset is not None:
                # False because we don't want to ignore isCount for export
                # True because we don't want to use ICUtzinfo.floating
                cal.vevent_list[-1].rruleset = item.createDateUtilFromRule(False, True)
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

transparencyMap = { 'confirmed' : 'BUSY', 'tentative' : 'BUSY-TENTATIVE' }
reverseTransparencyMap = dict(zip(transparencyMap.values(), transparencyMap.keys()))


def itemsToFreeBusy(view, start, end, calname = None):
    """
    Create FREEBUSY components corresponding to all events between start and 
    end.
        
    """
    all = schema.ns("osaf.pim", view).allCollection
    normal    = Calendar.eventsInRange(view, start, end, all)
    recurring = Calendar.recurringEventsInRange(view, start, end, all)
    events = Calendar._sortEvents(itertools.chain(normal, recurring))
    
    
    def toUTC(dt):
        if dt < start: dt = start
        elif dt > end: dt = end
        return translateToTimezone(dt, utc)    
    
    cal = vobject.iCalendar()
    
    if calname is not None:
        cal.add('x-wr-calname').value = calname
    vfree = cal.add('vfreebusy')
    vfree.add('dtstart').value = toUTC(start)
    vfree.add('dtend').value   = toUTC(end)
    
    def addFB(event):
        free = vfree.add('freebusy')
        free.fbtype_param = transparencyMap[event.transparency]
        return free

    free = None
    for event in events:
        # ignore anytime events, events with no duration, and fyi events
        if (event.transparency == 'fyi' or
            ((event.anyTime or event.duration == datetime.timedelta(0)) and 
             not event.allDay)):
            continue
        if free is None or free.fbtype_param != \
                           transparencyMap[event.transparency]:
            free = addFB(event)
            free.value = [[toUTC(event.effectiveStartTime),
                           event.effectiveEndTime]]
        else:
            # compress freebusy blocks if possible
            if event.effectiveStartTime <= free.value[-1][1]:
                if event.effectiveEndTime > free.value[-1][1]:
                    free.value[-1][1] = event.effectiveEndTime
            else:
                free.value.append([toUTC(event.effectiveStartTime),
                                   event.effectiveEndTime])
                
    # change the freebusy periods to their canonical form, dt/period instead of
    # dt/dt
    vfree.serialize()
    
    return cal
                

tzid_mapping = {}

def convertToICUtzinfo(dt, view=None):
    """
    This method returns a C{datetime} whose C{tzinfo} field
    (if any) is an instance of the ICUtzinfo class.
    
    @param dt: The C{datetime} whose C{tzinfo} field we want
               to convert to an ICUtzinfo instance.
    @type dt: C{datetime}
    """
    oldTzinfo = dt.tzinfo
    
    if oldTzinfo is None:

        icuTzinfo = None # Will patch to floating at the end
        
    else:

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
        tzical_tzid = getattr(oldTzinfo, '_tzid', None)
        icuTzinfo = getICUInstance(tzical_tzid)
        
        if tzical_tzid is not None:
            if tzid_mapping.has_key(tzical_tzid):
                # we've already calculated a tzinfo for this tzid
                icuTzinfo = tzid_mapping[tzical_tzid]
        
        if icuTzinfo is None:
            # special case UTC, because dateutil.tz.tzutc() doesn't have a TZID
            # and a VTIMEZONE isn't used for UTC
            if vobject.icalendar.tzinfo_eq(utc, oldTzinfo):
                icuTzinfo = getICUInstance('UTC')
        
        # iterate over all PyICU timezones, return the first one whose
        # offsets and DST transitions match oldTzinfo.  This is painfully
        # inefficient, but we should do it only once per unrecognized timezone,
        # so optimization seems premature.
        
        if icuTzinfo is None:
            if view is not None:
                info = TimeZoneInfo.get(view)
                well_known = (t[1].tzid for t in info.iterTimeZones())
            else:
                well_known = []
                
            # canonicalTimeZone doesn't help us here, because our matching
            # criteria aren't as strict as PyICU's, so iterate over well known
            # timezones first
            for tzid in itertools.chain(well_known,
                                        PyICU.TimeZone.createEnumeration()):
                test_tzinfo = getICUInstance(tzid)
                # only test for the DST transitions for the year of the event
                # being converted.  This could be very wrong, but sadly it's
                # legal (and common practice) to serialize VTIMEZONEs with only
                # one year's DST transitions in it.  Some clients (notably iCal)
                # won't even bother to get that year's offset transitions right,
                # but in that case, we really can't pin down a timezone
                # definitively anyway (fortunately iCal uses standard zoneinfo
                # tzid strings, so getICUInstance above should just work)
                if vobject.icalendar.tzinfo_eq(test_tzinfo, oldTzinfo,
                                               dt.year, dt.year + 1):
                    icuTzinfo = test_tzinfo
                    if tzical_tzid is not None:
                        tzid_mapping[tzical_tzid] = icuTzinfo                    
                    break
        
    # Here, if we have an unknown timezone, we'll turn
    # it into a floating datetime
    if icuTzinfo is None:
        icuTzinfo = ICUtzinfo.floating

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

def itemsFromVObject(view, text, coerceTzinfo = None, filters = None,
                     monolithic = True, changes=None, previousView=None,
                     updateCallback=None):
    """
    Take a string, create or update items from that stream.

    The updating of items uses Sharing.importValue; changes, previousView and
    updateCallback are all optional pass-throughs to this function.

    The filters argument is an optional sequence of attributes to not populate.
    
    monolithic is True for calendars that may contain multiple events, for
    CalDAV shares calendars will always contain one event (modulo recurrence) 
    so monolithic will be False for CalDAV.

    Return is a tuple (itemlist, calname).

    """
    
    newItemParent = view.findPath("//userdata")
    
    eventKind = view.findPath(_calendarEventPath)
    taskKind  = view.findPath(_taskPath)
    textKind  = view.findPath(_lobPath)
    
    countNew = 0
    countUpdated = 0
    
    itemlist = []
    
    calname = None

    # iterate over calendars, usually only one, but more are allowed
    for calendar in vobject.readComponents(text, validate=True):
        modificationQueue = []

        # just grab the first calendar name
        if calname is None:
            calname = calendar.getChildValue('x_wr_calname')

        rawVevents = getattr(calendar, 'vevent_list', [])
        numVevents = len(rawVevents)
        if updateCallback and monolithic:
            updateCallback(msg=_(u"Calendar contains %d events") % numVevents,
                totalWork=numVevents)
        
        vevents = ((-1, event) for event in rawVevents)
        for i, event in itertools.chain(vevents, enumerate(modificationQueue)):
            # Queue modifications to recurring events so modifications are
            # processed after master events in the iCalendar stream.
            recurrenceID = event.getChildValue('recurrence_id')
            if recurrenceID is not None and i < 0:
                # only add to modificationQueue in initial processing
                modificationQueue.append(event)
                continue

            try:
                if DEBUG: logger.debug("got VEVENT")
                pickKind = eventKind

                displayName = event.getChildValue('summary', u"")
                description = event.getChildValue('description')
                location    = event.getChildValue('location')
                status      = event.getChildValue('status', "").lower()
                duration    = event.getChildValue('duration')
                dtstart     = event.getChildValue('dtstart')
                dtend       = event.getChildValue('dtend')
                due         = event.getChildValue('due')
                uid         = event.getChildValue('uid')

                if status in ('confirmed', 'tentative'):
                    pass
                elif status == 'cancelled': #Chandler doesn't have CANCELLED
                    status = 'fyi'
                else:
                    status = 'confirmed'

                isDate = type(dtstart) == date

                # RFC2445 allows VEVENTs without DTSTART, but it's hard to guess
                # what that would mean, so we won't catch an exception if there's no
                # dtstart.
                anyTime = getattr(event.dtstart, 'x_osaf_anytime_param', None) == 'TRUE'

                try:
                    reminderDelta = event.valarm.trigger.value
                    if type(reminderDelta) is datetime.datetime:
                        reminderDelta = reminderDelta - dtstart
                except AttributeError:
                    reminderDelta = None

                
                if duration is None:
                    if dtend is not None:
                        duration = dtend - dtstart
                    elif due is not None: #VTODO case
                        duration = due - dtstart
                    elif anyTime or isDate:
                        duration = oneDay
                    else:
                        duration = datetime.timedelta(0)
                                
    
                if isDate:
                    dtstart = TimeZone.forceToDateTime(dtstart)
                    # convert to Chandler's notion of all day duration
                    duration -= oneDay
                
                # coerce timezones based on coerceTzinfo

                if coerceTzinfo is not None:
                    dtstart = TimeZone.coerceTimeZone(dtstart, coerceTzinfo)
                    
                dtstart = convertToICUtzinfo(dtstart, view)
                # Because of restrictions on dateutil.rrule, we're going
                # to have to make sure all the datetimes we create have
                # the same naivete as dtstart
                tzinfo = dtstart.tzinfo
                
                # by default, we'll create a new item, not change existing items
                itemChangeCallback = None
               
                # See if we have a corresponding item already
                uidMatchItem = Calendar.findUID(view, uid)
                
                if uidMatchItem is not None:
                    if DEBUG: logger.debug("matched UID")

                    if recurrenceID:
                        if type(recurrenceID) == date:
                            recurrenceID = datetime.datetime.combine(
                                                        recurrenceID,
                                                        time(tzinfo=tzinfo))
                        else:
                            recurrenceID = convertToICUtzinfo(
                                               makeNaiveteMatch(recurrenceID,
                                               tzinfo), view)
                            
                        eventItem = uidMatchItem.getRecurrenceID(recurrenceID)
                        if eventItem == None:
                            # our recurrenceID didn't match an item we know
                            # about.  This may be because the item is created
                            # by a later modification, a case we're not dealing
                            # with.  For now, just skip it.
                            logger.info("RECURRENCE-ID didn't match rule. " \
                                        "RECURRENCE-ID = %s" % recurrenceID)
                            continue
                        recurrenceLine = event.contents['recurrence-id'][0]
                        range = recurrenceLine.params.get('RANGE', ['THIS'])[0]
                        if range == 'THISANDPRIOR':
                            # ignore THISANDPRIOR changes for now
                            logger.info("RECURRENCE-ID RANGE of THISANDPRIOR " \
                                        "not supported")
                            continue
                        elif range == 'THIS':
                            itemChangeCallback = CalendarEventMixin.changeThis
                            # check if this is a modification to a master event
                            # if so, avoid changing the master's UUID when
                            # creating a modification
                            if eventItem.getMaster() == eventItem:
                                mod = eventItem._cloneEvent()
                                mod.modificationFor = mod.occurrenceFor = eventItem
                                if eventItem.hasLocalAttributeValue('occurrenceFor'):
                                    del eventItem.occurrenceFor
                                eventItem = mod
                        elif range == 'THISANDFUTURE':
                            itemChangeCallback = CalendarEventMixin.changeThisAndFuture
                        else:
                            logger.info("RECURRENCE-ID RANGE not recognized. " \
                                        "RANGE = %s" % range)
                            continue
                        
                    else:
                        eventItem = uidMatchItem
                        if (eventItem.occurrenceFor is None and
                            eventItem.occurrences is None):
                                eventItem.occurrenceFor = eventItem
                        if eventItem.rruleset is not None:
                            # re-creating a recurring item from scratch, delete 
                            # old recurrence information
                            # uidMatchItem might not be the master, though, so
                            # get the master, or eventItem will be a deleted
                            # event
                            eventItem = eventItem.getMaster()
                            # delete modifications the master has, to avoid
                            # changing the master to a modification with a
                            # different UUID
                            if getattr(eventItem, 'modifications', None):
                                for mod in eventItem.modifications:
                                    mod.delete()
                            eventItem.removeRecurrence()
                            
                        itemChangeCallback = CalendarEventMixin.changeThis
                        countUpdated += 1
                    if DEBUG: logger.debug("Changing eventItem: %s" % str(eventItem))
                    
                changesDict = {}
                change = changesDict.__setitem__
                                
                change('displayName', displayName)

                if anyTime:
                    change('anyTime', True)
                    change('allDay', False)
                elif isDate:
                    # allDay events should have anyTime True, so if the user
                    # unselects allDay, the time isn't set to midnight
                    change('anyTime', True)
                    change('allDay', True)
                else:
                    change('allDay', False)
                    change('anyTime', False)

                change('startTime', dtstart)
                change('duration', duration)
                
                if not filters or "transparency" not in filters:
                    change('transparency', status)
                
                # DESCRIPTION <-> body  
                if description is not None:
                    change('body', description)
                
                if location:
                    change('location', Calendar.Location.getLocation(view,
                                                                     location))
                    
                # rruleset and reminderInterval need to be set last
                changeLast = []
                if not filters or "reminders" not in filters:
                    if reminderDelta is not None:
                        changeLast.append(('reminderInterval', reminderDelta))
                
                rruleset = event.rruleset
                if rruleset is not None:
                    ruleSetItem = RecurrenceRuleSet(None, itsView=view)
                    ruleSetItem.setRuleFromDateUtil(rruleset)
                    changeLast.append(('rruleset', ruleSetItem))
                
                if itemChangeCallback is None:
                    # create a new item
                    # setting icalUID in the constructor doesn't seem to work
                    #change('icalUID', uid)
                    eventItem = pickKind.newItem(None, newItemParent, **changesDict)
                    # set icalUID seperately to make sure uid_map gets set
                    # @@@MOR Needed anymore since we got rid of uid_map?
                    eventItem.icalUID = uid
                    for tup in changeLast:
                        eventItem.changeThis(*tup)
                    countNew += 1
                else:
                    # update an existing item
                    if rruleset is None and recurrenceID is None \
                       and eventItem.rruleset is not None:
                        # no recurrenceId or rruleset, but the existing item
                        # may have recurrence, so delete it
                        eventItem.removeRecurrence()

                    for attr, val in changesDict.iteritems():
                        Sharing.importValue(eventItem, changes, attr,
                            val, previousView, updateCallback,
                            itemChangeCallback)
                    for (attr, val) in changeLast:
                        Sharing.importValue(eventItem, changes, attr,
                            val, previousView, updateCallback,
                            itemChangeCallback)

                if DEBUG: logger.debug(u"Imported %s %s" % (eventItem.displayName,
                 eventItem.startTime))

                if updateCallback:
                    msg="'%s'" % eventItem.getItemDisplayName()
                    # the work parameter tells the callback whether progress
                    # should be tracked, this only makes sense if we might have
                    # more than one event.
                    cancelled = updateCallback(msg=msg, work=monolithic)
                    if cancelled:
                        raise Sharing.SharingError(_(u"Cancelled by user"))
                
                # finished creating the item
                itemlist.append(eventItem)

            except Sharing.SharingError:
                raise

            except Exception, e:
                if __debug__:
                    raise
                else:
                    logger.exception("import failed to import one event with \
                                     exception: %s" % str(e))

    else:
        # an empty ics file, what to do?
        pass

    logger.info("...iCalendar import of %d new items, %d updated" % \
     (countNew, countUpdated))
    
    return itemlist, calname

_calendarEventPath = "//parcels/osaf/pim/calendar/CalendarEvent"
_taskPath = "//parcels/osaf/pim/EventTask"
_lobPath = "//Schema/Core/Lob"

def updateFreebusyFromVObject(view, text, busyCollection, updateCallback=None):
    """
    Take a string, create or update freebusy events in busyCollection from that
    stream.

    Truncate differing existing freebusy events that overlap the start or end
    times.

    Returns (freebusystart, freebusyend, calname).

    """
    
    newItemParent = view.findPath("//userdata")
    eventKind = view.findPath(_calendarEventPath)
    
    countNew = 0
    countUpdated = 0

    freebusystart = freebusyend = None

    Calendar.ensureIndexed(busyCollection)
    
    # iterate over calendars, usually only one, but more are allowed
    for calendar in vobject.readComponents(text, validate=True):
        calname = calendar.getChildValue('x_wr_calname')
            
        for vfreebusy in calendar.vfreebusy_list:
            if vfreebusy.behavior is None:
                vfreebusy.behavior = vobject.icalendar.VFreeBusy
                vfreebusy.transformToNative()

            start = vfreebusy.getChildValue('dtstart')
            end   = vfreebusy.getChildValue('dtend')
            if freebusystart is None or freebusystart > start:
                freebusystart = start
            if freebusyend is None or freebusyend < end:
                freebusyend = end

            # create a list of busy blocks tuples sorted by start time
            busyblocks = []
            for fb in getattr(vfreebusy, 'freebusy_list', []):
                status = getattr(fb, 'fbtype_param', 'BUSY').upper()
                for blockstart, duration in fb.value:
                    blockstart = translateToTimezone(blockstart, ICUtzinfo.default)
                    bisect.insort(busyblocks, (blockstart, duration, status))
            
            # eventsInRange sorts by start time, recurring events aren't allowed
            # so we don't bother to fetch them
            existing = Calendar.eventsInRange(view, start, end, busyCollection)
            existing = itertools.chain(existing, [None])

            oldEvent = existing.next()
            for blockstart, duration, status in busyblocks:
                while oldEvent is not None and oldEvent.startTime < blockstart:
                    # this assumes no freebusy blocks overlap freebusystart
                    oldEvent.delete()
                    oldEvent = existing.next()
                if oldEvent is not None and oldEvent.startTime == blockstart:
                    oldEvent.transparency = reverseTransparencyMap[status]
                    oldEvent.duration = duration
                    countUpdated += 1
                    oldEvent = existing.next()
                else:
                    vals = { 'startTime'    : blockstart,
                             'transparency' : reverseTransparencyMap[status],
                             'duration'     : duration,
                             'isFreeBusy'   : True,
                             'anyTime'      : False,
                             'displayName'  : '' }
                    eventItem = eventKind.newItem(None, newItemParent, **vals)
                    busyCollection.add(eventItem)
                    countNew += 1

    logger.info("...iCalendar import of %d new freebusy blocks, %d updated" % \
     (countNew, countUpdated))
    
    return freebusystart, freebusyend, calname

class ICalendarFormat(Sharing.ImportExportFormat):

    schema.kindInfo(displayName=u"iCalendar Import/Export Format Kind")
    
    def fileStyle(self):
        return self.STYLE_SINGLE

    def extension(self, item):
        return "ics"

    def contentType(self, item):
        return "text/calendar"

    def acceptsItem(self, item):
        return isinstance(item, (CalendarEventMixin, Sharing.Share))

    def importProcess(self, text, extension=None, item=None, changes=None,
                      previousView=None, updateCallback=None):
        # the item parameter is so that a share item can be passed in for us
        # to populate.

        # An ICalendar file doesn't have any 'share' info, just the collection
        # of events, etc.  Therefore, we want to actually populate the share's
        # 'contents':

        view = self.itsView
        filters = self.share.filterAttributes
        monolithic = self.fileStyle() == self.STYLE_SINGLE
        coerceTzinfo = getattr(self, 'coerceTzinfo', None)

        events, calname = itemsFromVObject(view, text, coerceTzinfo, filters,
                                           monolithic, changes, previousView,
                                           updateCallback)

        if monolithic:
            if calname is None:
                calname = _(u"Imported Calendar")

            if item is None:
                item = SmartCollection(itsView=view)
            elif isinstance(item, Sharing.Share):                        
                if item.contents is None:
                    item.contents = \
                        SmartCollection(itsView=view)
                item = item.contents

            if not isinstance(item, ContentCollection):
                print "Only a share or an item collection can be passed in"
                #@@@MOR Raise something

            if getattr(item, 'displayName', "") == "":
                item.displayName = unicode(calname)

            # finally, add each new event to the collection
            for event in events:
                item.add(event.getMaster())

            return item

        else:
            # if fileStyle isn't single, item must be a collection
            return events[0].getMaster()

    def exportProcess(self, share, depth=0):
        cal = itemsToVObject(self.itsView, share.contents,
                             filters=self.share.filterAttributes)
        try:
            cal.add('x-wr-calname').value = share.contents.displayName
        except:
            pass
        return cal.serialize().encode('utf-8')

def beginningOfWeek():
    midnightToday = datetime.datetime.combine(datetime.date.today(), 
                                     datetime.time(0, tzinfo=ICUtzinfo.default))
    return midnightToday - midnightToday.weekday() * oneDay # Monday = 0


class CalDAVFormat(ICalendarFormat):
    """
    Treat multiple events as different resources.
    """

    def fileStyle(self):
        return self.STYLE_DIRECTORY
    def acceptsItem(self, item):
        return isinstance(item, CalendarEventMixin)

    def exportProcess(self, item, depth=0):
        """
        Item may be a Share or an individual Item, return None if Share.
        """
        if not isinstance(item, CalendarEventMixin):
            return None
        cal = itemsToVObject(self.itsView, [item],
                             filters=self.share.filterAttributes)
        return cal.serialize().encode('utf-8')

    
    
class FreeBusyFileFormat(ICalendarFormat):
    """Format for exporting/importing a monolithic freebusy file."""
    schema.kindInfo(displayName=u"iCalendar Free/Busy Format Kind")

    def extension(self, item):
        return "ifb"

    def exportProcess(self, item, depth=0):
        """
        Share and depth are ignored, always export freebusy associated
        with the all collection.
        """
        start = beginningOfWeek()
        cal = itemsToFreeBusy(self.itsView, start,
                              start + FREEBUSY_WEEKS_EXPORTED * 7 * oneDay,
                              calname = self.itsParent.displayName)
        return cal.serialize().encode('utf-8')

    def importProcess(self, text, extension=None, item=None, changes=None,
                      previousView=None, updateCallback=None):
        # the item parameter is so that a share item can be passed in for us
        # to populate.

        # An ICalendar file doesn't have any 'share' info, just the collection
        # of events, etc.  Therefore, we want to actually populate the share's
        # 'contents':

        view = self.itsView

        if item is None:
            item = SmartCollection(itsView=view)
        elif isinstance(item, Sharing.Share):
            if item.contents is None:
                item.contents = \
                    SmartCollection(itsView=view)
            item = item.contents

        # something should be done with start and end, eventually
        start, end, calname = updateFreebusyFromVObject(view, text, item, 
                                                        updateCallback)

        if getattr(item, 'displayName', "") == "":
            if calname is None:
                calname = _(u"Imported Free-busy")
            item.displayName = unicode(calname)

        return item

class ImportError(Exception):
    pass

def importICalendarFile(fullpath, view, targetCollection = None,
                        filterAttributes = None, updateCallback=None,
                        tzinfo = None, logger=None, selectedCollection = False):
    """Import ics file at fullpath into targetCollection.
    
    If selectedCollection is True, ignored targetCollection and import into
    the currently selected sidebar collection.
    If Trash is chosen as the target collection, a new collection will be 
    created instead.

    """
    import osaf.framework.blocks
    if selectedCollection:
        targetCollection = Globals.views[0].getSidebarSelectedCollection()

    trash = schema.ns("osaf.pim", view).trashCollection
    if targetCollection == trash:
        targetCollection = None
        
    if filterAttributes is None: filterAttributes = []
    # not dealing with tzinfo yet
    if not os.path.isfile(fullpath):
        raise ImportError(_(u"File does not exist, import cancelled."))
    (dir, filename) = os.path.split(fullpath)
    
    share = Sharing.OneTimeFileSystemShare(
        dir, filename, ICalendarFormat, itsView=view, contents = targetCollection
    )
    if tzinfo is not None:
        share.format.coerceTzinfo = tzinfo
    
    for key in filterAttributes:
        share.filterAttributes.append(key)
    
    before = epoch_time()
    
    try:
        collection = share.get(updateCallback)
    except:
        if logger:
            logger.exception("Failed importFile %s" % fullpath)
        raise ImportError(_(u"Problem with the file, import cancelled."))

    if targetCollection is None:
        name = "".join(filename.split('.')[0:-1]) or filename
        collection.displayName = name
        schema.ns("osaf.app", view).sidebarCollection.add(collection)
        sideBarBlock = osaf.framework.blocks.Block.Block.findBlockByName('Sidebar')
        sideBarBlock.postEventByName ("SelectItemsBroadcast",
                                      {'items':[collection]})
    if logger:
        logger.info("Imported collection in %s seconds" % (epoch_time()-before))
        
    return collection
