#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


__parcel__ = "osaf.sharing"

__all__ = [
    'ICalendarFormat',
    'CalDAVFormat',
    'FreeBusyFileFormat'
]

import Sharing
import application.Parcel
from osaf.pim import (ContentCollection, SmartCollection, Remindable,
                      EventStamp, CalendarEvent, has_stamp, Note)
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
from osaf.pim.calendar.TimeZone import TimeZoneInfo, convertToICUtzinfo
from application import schema
import itertools
from i18n import ChandlerMessageFactory as _
import os, logging
import bisect
from chandlerdb.util.c import UUID

FREEBUSY_WEEKS_EXPORTED = 26

logger = logging.getLogger(__name__)
DEBUG = logger.getEffectiveLevel() <= logging.DEBUG

localtime = dateutil.tz.tzlocal()
utc = ICUtzinfo.getInstance('UTC')
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

    def populateEvent(comp, event):
        """Populate the given vobject vevent with data from event."""
        
        def makeDateTimeValue(dt, asDate=False):
            if asDate:
                return dt.date()
            elif dt.tzinfo is ICUtzinfo.floating:
                return dt.replace(tzinfo=None)
            else:
                return dt
        
        item = event.itsItem
        
        if item.getAttributeValue(EventStamp.icalUID.name, default=None) is None:
            item.icalUID = unicode(item.itsUUID)
        comp.add('uid').value = event.icalUID

        try:
            comp.add('summary').value = item.displayName
        except AttributeError:
            pass
        
        try:
            dtstartLine = comp.add('dtstart')
            
            # allDay-ness overrides anyTime-ness
            if event.anyTime and not event.allDay:
                dtstartLine.x_osaf_anytime_param = 'TRUE'
                
            dtstartLine.value = makeDateTimeValue(event.startTime,
                                    event.anyTime or event.allDay)

        except AttributeError:
            comp.dtstart = [] # delete the dtstart that was added
        
        try:
            if not (event.duration == datetime.timedelta(0) or (
                    (event.anyTime or event.allDay) and 
                    event.duration <= oneDay)):
                dtendLine = comp.add('dtend')
                #convert Chandler's notion of allDay duration to iCalendar's
                if event.allDay:
                    dtendLine.value = event.endTime.date() + oneDay
                else:
                    if event.anyTime:
                        dtendLine.x_osaf_anytime_param = 'TRUE'

                    # anyTime should be exported as allDay for non-Chandler apps
                    dtendLine.value = makeDateTimeValue(event.endTime,
                                                        event.anyTime)

        except AttributeError:
            comp.dtend = [] # delete the dtend that was added
            

        if not filters or EventStamp.transparency.name not in filters:
            try:
                status = event.transparency.upper()
                # anytime events should be interpreted as not taking up time,
                # but all-day shouldn't
                if status == 'FYI' or (not event.allDay and event.anyTime):
                    status = 'CANCELLED'
                comp.add('status').value = status
            except AttributeError:
                pass

        try:
            comp.add('description').value = item.body
        except AttributeError:
            pass
        
        try:
            comp.add('location').value = event.location.displayName
        except AttributeError:
            pass

        if not filters or Remindable.reminders.name not in filters:
            firstReminder = Remindable(item).getUserReminder()
            if firstReminder is not None:
                if firstReminder.absoluteTime is not None:
                    value = firstReminder.absoluteTime
                else:
                    # @@@ For now, all relative reminders are relative to starttime
                    assert firstReminder.relativeTo == EventStamp.effectiveStartTime.name
                    value = firstReminder.delta
                comp.add('valarm').add('trigger').value = value
        
        if event.modificationFor is not None:
            recurrenceid = comp.add('recurrence-id')
            masterEvent = event.getMaster()
            allDay = masterEvent.allDay or masterEvent.anyTime
            
            recurrenceid.value = makeDateTimeValue(event.recurrenceID, allDay)
        
        # logic for serializing rrules needs to move to vobject
        try: # hack, create RRULE line last, because it means running transformFromNative
            if event.getMaster().itsItem is event.itsItem and event.rruleset is not None:
                # False because we don't want to ignore isCount for export
                # True because we don't want to use ICUtzinfo.floating
                cal.vevent_list[-1].rruleset = event.createDateUtilFromRule(False, True)
        except AttributeError:
            pass
        # end of populateEvent function

    def populateModifications(event, cal):
        for modification in itertools.imap(EventStamp,
                                           event.modifications or []):
            populateEvent(cal.add('vevent'), modification)
            if modification.modifies == 'thisandfuture':
                populateModifications(modification, cal)
        #end helper functions

    if cal is None:
        cal = vobject.iCalendar()
    for item in items: # main loop
        try:
            # ignore any events that aren't masters
            event = EventStamp(item)
            if event.getMaster() == event:
                populateEvent(cal.add('vevent'), event)
            else:
                continue
        except:
            continue
        
        populateModifications(event, cal)

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
    events = Calendar._sortEvents(itertools.chain(normal, recurring),
                                  attrName='effectiveStartTime')
    
    
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

    if isinstance(oldTzinfo, ICUtzinfo):
        return dt
    
    elif oldTzinfo is None:
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
                     monolithic = True, updateCallback=None, stats=None):
    """
    Take a string, create or update items from that stream.

    The filters argument is an optional sequence of attributes to not populate.
    
    monolithic is True for calendars that may contain multiple events, for
    CalDAV shares calendars will always contain one event (modulo recurrence) 
    so monolithic will be False for CalDAV.

    Return is a tuple (itemlist, calname).

    """
    newItemParent = view.findPath("//userdata")
    
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

                summary     = event.getChildValue('summary', u"")
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

                reminderDelta = None
                reminderAbsoluteTime = None
                try:
                    reminderValue = event.valarm.trigger.value
                except AttributeError:
                    pass
                else:
                    if type(reminderValue) is datetime.datetime:
                        reminderAbsoluteTime = reminderValue
                    else:
                        assert type(reminderValue) is datetime.timedelta
                        reminderDelta = reminderValue
                
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
                def convertDatetime(dt):
                    if coerceTzinfo is not None:
                        dt = TimeZone.coerceTimeZone(dt, coerceTzinfo)
                    
                    return convertToICUtzinfo(dt, view)
                    
                dtstart = convertDatetime(dtstart)
                if reminderAbsoluteTime is not None:
                    reminderAbsoluteTime = convertDatetime(reminderAbsoluteTime)

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
                            itemChangeCallback = EventStamp.changeThis
                            # check if this is a modification to a master event
                            # if so, avoid changing the master's UUID when
                            # creating a modification
                            if eventItem.getMaster() == eventItem:
                                mod = eventItem._cloneEvent()
                                mod.modificationFor = mod.occurrenceFor = eventItem.itsItem
                                if eventItem.itsItem.hasLocalAttributeValue(
                                                EventStamp.occurrenceFor.name):
                                    del eventItem.occurrenceFor
                                eventItem = mod
                        elif range == 'THISANDFUTURE':
                            itemChangeCallback = EventStamp.changeThisAndFuture
                        else:
                            logger.info("RECURRENCE-ID RANGE not recognized. " \
                                        "RANGE = %s" % range)
                            continue
                        
                    else:
                        eventItem = uidMatchItem
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
                            for mod in itertools.imap(EventStamp,
                                                eventItem.modifications or []):
                                # [Bug 7019]
                                # We need to del these because, in the deferred
                                # delete case, we would have deferred items
                                # living on, in the manner of the undead, in
                                # master.modifications (and occurrences). This
                                # would ultimately cause .getNextOccurrence()
                                # to terminate prematurely.
                                del mod.modificationFor
                                del mod.occurrenceFor
                                mod.itsItem.delete()

                            eventItem.removeRecurrence(deleteOccurrences=False)
                            
                        itemChangeCallback = EventStamp.changeThis

                    # Mark this event as an update (modified)
                    countUpdated += 1
                    uuid = eventItem.itsItem.itsUUID
                    if stats and uuid not in stats['modified']:
                        stats['modified'].append(uuid)

                    if DEBUG: logger.debug("Changing eventItem: %s" % str(eventItem))
                    
                changesDict = {}
                def change(key, value):
                    try:
                        key = getattr(EventStamp, key).name
                    except AttributeError:
                        pass
                    changesDict[key] = value
                                
                change('summary', summary)

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
                
                if not filters or EventStamp.transparency.name not in filters:
                    change('transparency', status)
                
                # DESCRIPTION <-> body  
                if description is not None:
                    change('body', description)
                
                if location:
                    change('location', Calendar.Location.getLocation(view,
                                                                     location))
                    
                # rruleset and userReminderInterval/userReminderTime must be set last
                changeLast = []
                # Need to update this for Remindable
                if not filters or Remindable.reminders.name not in filters:
                    if reminderDelta is not None:
                        changeLast.append((Remindable.userReminderInterval.name, 
                                           reminderDelta))
                    elif reminderAbsoluteTime is not None:
                        changeLast.append((Remindable.userReminderTime.name, 
                                           reminderAbsoluteTime))
                
                rruleset = event.rruleset
                if rruleset is not None:
                    # fix for Bug 6994, exdate and rdate timezones need to be
                    # converted to ICUtzinfo instances
                    for typ in '_rdate', '_exdate':
                        setattr(rruleset, typ, [convertDatetime(d) for d in
                                                getattr(rruleset, typ, [])  ])
                    ruleSetItem = RecurrenceRuleSet(None, itsView=view)
                    ruleSetItem.setRuleFromDateUtil(rruleset)
                    changeLast.append((EventStamp.rruleset.name, ruleSetItem))
                    
                if itemChangeCallback is None:
                    # create a new item

                    try:
                        # See if uid is a valid repository UUID, if so we'll
                        # go ahead and use it for the new item's UUID.
                        uuid = UUID(uid)
                    except ValueError:
                        # Not in valid UUID format, so just create a new UUID
                        uuid = UUID()
                        logger.info("iCalendar UID not in UUID form (%s)", uid)

                    parent = schema.Item.getDefaultParent(view)
                    kind = Note.getKind(view)

                    # If there is already an item with this UUID, use it,
                    # otherwise create one.
                    item = view.findUUID(uuid)
                    if item is None:
                        
                        item = kind.instantiateItem(None, parent, uuid,
                            withInitialValues=True, **changesDict)
                        countNew += 1
                        if stats and item.itsUUID not in stats['added']:
                            stats['added'].append(item.itsUUID)
                    else:
                        countUpdated += 1
                        if stats and item.itsUUID not in stats['modified']:
                            stats['modified'].append(item.itsUUID)
                    eventItem = EventStamp(item)
                    eventItem.add()
                    eventItem.icalUID = uid

                    for tup in changeLast:
                        eventItem.changeThis(*tup)
                else:
                    # update an existing item
                    if rruleset is None and recurrenceID is None \
                       and eventItem.rruleset is not None:
                        # no recurrenceId or rruleset, but the existing item
                        # may have recurrence, so delete it
                        eventItem.removeRecurrence()

                    for attr, val in changesDict.iteritems():

                        # Only change a datetime if it's really different
                        # from what the item already has:
                        if type(val) is datetime.datetime:
                             oldValue = getattr(eventItem.itsItem, attr, None)
                             if (oldValue is not None and 
                                 oldValue == val and
                                 oldValue.tzinfo == val.tzinfo):
                                continue

                        itemChangeCallback(eventItem, attr, val)


                    for (attr, val) in changeLast:
                        itemChangeCallback(eventItem, attr, val)



                if DEBUG: logger.debug(u"Imported %s %s" % (eventItem.summary,
                 eventItem.startTime))

                if updateCallback:
                    msg="'%s'" % eventItem.itsItem.getItemDisplayName()
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
    
    countNew = 0
    countUpdated = 0

    freebusystart = freebusyend = None

    Calendar.ensureIndexed(busyCollection)
    
    # iterate over calendars, usually only one, but more are allowed
    for calendar in vobject.readComponents(text, validate=True):
        calname = calendar.getChildValue('x_wr_calname')
            
        for vfreebusy in calendar.vfreebusy_list:
            # RPI's server originally didn't put a VERSION:2.0 line in its
            # freebusy response.  vobject's behavior is set when a VERSION is
            # found.  Tolerate servers that export technically illegal but still 
            # readable vfreebusy components
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
                             'summary'  : '' }
                    eventItem = CalendarEvent(None, newItemParent, **vals)
                    busyCollection.add(eventItem.itsItem)
                    countNew += 1

    logger.info("...iCalendar import of %d new freebusy blocks, %d updated" % \
     (countNew, countUpdated))
    
    return freebusystart, freebusyend, calname

class ICalendarFormat(Sharing.ImportExportFormat):

    def fileStyle(self):
        return self.STYLE_SINGLE

    def extension(self, item):
        return "ics"

    def contentType(self, item):
        return "text/calendar"

    def acceptsItem(self, item):
        has_stamp(item, EventStamp) or isinstance(item, Sharing.Share)

    def importProcess(self, contentView, text, extension=None, item=None,
                      updateCallback=None, stats=None):
        # the item parameter is so that a share item can be passed in for us
        # to populate.

        # An ICalendar file doesn't have any 'share' info, just the collection
        # of events, etc.  Therefore, we want to actually populate the share's
        # 'contents':

        view = contentView # Use the passed-in view for creating items
        filters = self.share.filterAttributes
        monolithic = self.fileStyle() == self.STYLE_SINGLE
        coerceTzinfo = getattr(self, 'coerceTzinfo', None)

        events, calname = itemsFromVObject(view, text, coerceTzinfo, filters,
                                           monolithic, updateCallback, stats)

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
                item.add(event.getMaster().itsItem)

            return item

        else:
            # if fileStyle isn't single, item must be a collection
            return events[0].getMaster().itsItem

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
        return has_stamp(item, EventStamp)

    def exportProcess(self, item, depth=0):
        """
        Item may be a Share or an individual Item, return None if Share.
        """
        if has_stamp(item, EventStamp):
            cal = itemsToVObject(self.itsView, [item],
                                 filters=self.share.filterAttributes)
            return cal.serialize().encode('utf-8')

    
    
class FreeBusyFileFormat(ICalendarFormat):
    """Format for exporting/importing a monolithic freebusy file."""
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

    def importProcess(self, contentView, text, extension=None, item=None,
                      updateCallback=None, stats=None):
        # the item parameter is so that a share item can be passed in for us
        # to populate.

        # An ICalendar file doesn't have any 'share' info, just the collection
        # of events, etc.  Therefore, we want to actually populate the share's
        # 'contents':

        view = contentView # Use the passed-in view for creating items

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

class ICalendarImportError(Exception):
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
    from osaf.framework.blocks.Block import Block

    if selectedCollection:
        targetCollection = Block.findBlockByName("MainView").getSidebarSelectedCollection()

    trash = schema.ns("osaf.pim", view).trashCollection
    if targetCollection == trash:
        targetCollection = None
        
    if filterAttributes is None: filterAttributes = []
    # not dealing with tzinfo yet
    if not os.path.isfile(fullpath):
        raise ICalendarImportError(_(u"File does not exist, import cancelled."))
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
        raise ICalendarImportError(_(u"Problem with the file, import cancelled."))

    if targetCollection is None:
        name = "".join(filename.split('.')[0:-1]) or filename
        collection.displayName = name
        schema.ns("osaf.app", view).sidebarCollection.add(collection)
        sideBarBlock = Block.findBlockByName('Sidebar')
        sideBarBlock.postEventByName ("SelectItemsBroadcast",
                                      {'items':[collection]})
    if logger:
        logger.info("Imported collection in %s seconds" % (epoch_time()-before))
        
    return collection
