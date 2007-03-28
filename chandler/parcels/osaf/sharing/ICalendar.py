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


__parcel__ = "osaf.sharing"

__all__ = [
    'ICalendarFormat',
    'CalDAVFormat',
    'FreeBusyFileFormat',
]

import formats, errors, shares, utility
import application.Parcel
from osaf.pim import (ContentCollection, SmartCollection, Remindable,
                      EventStamp, CalendarEvent, TaskStamp, Note, has_stamp,
                      TriageEnum)
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
import md5
from application.dialogs.TurnOnTimezones import ShowTurnOnTimezonesDialog
import wx

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



attributesUsedWhenExporting = [EventStamp.location.name,
                               EventStamp.startTime.name,
                               EventStamp.duration.name,
                               EventStamp.anyTime.name,
                               EventStamp.allDay.name,
                               EventStamp.transparency.name,
                               'body', 'displayName',
                               Remindable.reminders.name,
                               Note.icalendarProperties.name,
                               Note.icalendarParameters.name]
                               

def itemsToVObject(view, items, cal=None, filters=None):
    """
    Iterate through items, add to cal, create a new vcalendar if needed.

    Consider only master events (then serialize all modifications).  For now,
    set all timezones to Pacific.

    """

    if filters is None:
        filters = () # we want filters to be iterable
    
    def makeDateTimeValue(dt, asDate=False):
        if asDate:
            return dt.date()
        elif dt.tzinfo is ICUtzinfo.floating:
            return dt.replace(tzinfo=None)
        else:
            return dt

    
    def populateCommon(comp, item):
        """
        Populate the given vevent or vtodo vobject with values for
        attributes common to Events or Tasks).
        """
        
        if item.getAttributeValue(Note.icalUID.name, default=None) is None:
            item.icalUID = unicode(item.itsUUID)
        comp.add('uid').value = item.icalUID

        # displayName --> SUMMARY
        try:
            summary = item.displayName
        except AttributeError:
            pass
        else:
            comp.add('summary').value = summary
            
        # body --> DESCRIPTION
        try:
            description = item.body
        except AttributeError:
            pass
        else:
            if description:
                comp.add('description').value = description
                
        # userReminder --> VALARM
        if Remindable.reminders.name not in filters:
            firstReminder = item.getUserReminder()
            if firstReminder is not None:
                if firstReminder.absoluteTime is not None:
                    value = firstReminder.absoluteTime
                else:
                    # @@@ For now, all relative reminders are relative to starttime
                    assert firstReminder.relativeTo == EventStamp.effectiveStartTime.name
                    value = firstReminder.delta
                comp.add('valarm').add('trigger').value = value
                
    def populateCustom(comp, item):
        # custom properties
        for name, value in item.icalendarProperties.iteritems():
            prop = comp.add(name)

            # for unrecognized properties, import stores strings, not
            # native types like datetimes.  So value should just be a
            # string, not a more complicated python data structure.  Don't
            # try to transform the value when serializing
            prop.isNative = False
            
            # encoding escapes characters like backslash and comma and
            # combines list values into a single string.  This was already
            # done when the icalendar was imported, so don't escape again
            prop.encoded = True
            
            prop.value = value
                
        for name, paramstring in item.icalendarParameters.iteritems():
            paramdict = comp.contents[name][0].params
            for paramlist in vobject.base.parseParams(paramstring):
                # parseParams gives a list of lists of parameters, with the
                # first element of each list being the name of the
                # parameter, followed by the parameter values, if any
                paramname = paramlist[0].upper()
                if paramname.lower() in parametersUnderstood:
                    # parameters understood by Chandler shouldn't be stored
                    # in icalendarParameters, but changes to which
                    # parameters Chandler understands can lead to spurious
                    # parameters, ignore them
                    continue
                paramvalues = paramdict.setdefault(paramname, [])
                paramvalues.extend(paramlist[1:])
        
        

    
    def populateEvent(comp, event):
        """Populate the given vobject vevent with data from event."""
        
        populateCommon(comp, event.itsItem)
        
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
            

        if EventStamp.transparency.name not in filters:
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
            comp.add('location').value = event.location.displayName
        except AttributeError:
            pass
        
        timestamp = datetime.datetime.utcnow()
        comp.add('dtstamp').value = timestamp.replace(tzinfo=utc)

        if event.modificationFor is not None:
            recurrenceid = comp.add('recurrence-id')
            masterEvent = event.getMaster()
            allDay = masterEvent.allDay or masterEvent.anyTime
            
            recurrenceid.value = makeDateTimeValue(event.recurrenceID, allDay)
        
        # logic for serializing rrules needs to move to vobject
        try: # hack, create RRULE line last, because it means running transformFromNative
            if event.getMaster() == event and event.rruleset is not None:
                # False because we don't want to ignore isCount for export
                # True because we don't want to use ICUtzinfo.floating
                cal.vevent_list[-1].rruleset = event.createDateUtilFromRule(False, True)
        except AttributeError:
            logger.error('Failed to export RRULE for %s' % event.itsItem.itsUUID)
        # end of populateEvent function
        
        populateCustom(comp, event.itsItem)


    def populateModifications(event, cal):
        for modification in itertools.imap(EventStamp, event.modifications):
            for attr, val in modification.itsItem.iterModifiedAttributes():
                if attr in attributesUsedWhenExporting and attr not in filters:
                    populateEvent(cal.add('vevent'), modification)
                    break
        #end helper functions
        
    def populateTask(comp, task):
        """Populate the given vobject vtodo with data from task."""
        populateCommon(comp, task.itsItem)

        # @@@ [grant] Once we start writing out Event+Tasks as
        # VTODO, write out DUE (or maybe DTSTART) here.

        if Note._triageStatus.name not in filters:
            triageStatus = task.itsItem._triageStatus
            
            # VTODO STATUS mapping:
            # ---------------------
            #
            #  [ICalendar]            [Triage Enum]
            #  <no value>/IN-PROCESS    now  (needsReply=False)
            #  NEEDS-ACTION             now  (needsReply=True)
            #  COMPLETED                done
            #  CANCELLED                later
            
            if triageStatus == TriageEnum.now:
                if task.itsItem.needsReply:
                    comp.add('status').value = 'needs-action'
                else:
                    comp.add('status').value = 'in-process'
            elif triageStatus == TriageEnum.later:
                comp.add('status').value = 'cancelled'
            else:
                comp.add('status').value = 'completed'
                
        populateCustom(comp, task.itsItem)

    if cal is None:
        cal = vobject.iCalendar()
    for item in items: # main loop
        try:
            # ignore any events that aren't masters
            #
            # Note: [grant]
            # At the moment, we allow Event-ness to take precedence over
            # Task-ness. So, we serialize Event+Task objects as VEVENTs.
            # Part of the reason for this is that recurring VTODOs aren't
            # so well-supported by other iCalendar clients. For RFC 2445
            # issues with VTODO+RRULE, see e.g.
            # <http://lists.osafoundation.org/pipermail/ietf-calsify/2006-August/001134.html>
            if has_stamp(item, EventStamp):
                event = EventStamp(item)
                if event.getMaster() == event:
                  populateEvent(cal.add('vevent'), event)
                populateModifications(event, cal)
            elif has_stamp(item, TaskStamp):
                  populateTask(cal.add('vtodo'), TaskStamp(item))
        except:
            logger.exception("Exception while exporting %s" % item)
            continue

    return cal

transparencyMap = { 'confirmed' : 'BUSY', 'tentative' : 'BUSY-TENTATIVE' }
reverseTransparencyMap = dict(itertools.imap(reversed,
                                             transparencyMap.iteritems()))


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

def makeNaiveteMatch(dt, tzinfo):
    if dt.tzinfo is None:
        if tzinfo is not None:
            dt = TimeZone.coerceTimeZone(dt, tzinfo)
    else:
        if tzinfo is None:
            dt = TimeZone.stripTimeZone(dt)
    return dt
    
def _importOneVObject(vobj, filters, coerceTzinfo, promptForTimezone, 
                      newItemParent):
    view = newItemParent.itsView
    
    itemIsNew = False
    newStamps = []

    # by default, we'll create a new item, not change existing items
    itemChangeCallback = None

    # store up all attributes in a dictionary ...
    changesDict = {}

    # ... and define a shorthand for updating it
    def change(attr, value):
        changesDict[attr.name] = value
        
    # rruleset and userReminderInterval/userReminderTime must
    # be set last....
    changeLast = []

    # values that apply to VEVENT and VTODO ...
    summary     = vobj.getChildValue('summary', u"")
    description = vobj.getChildValue('description')
    status      = vobj.getChildValue('status', "").lower()
    duration    = vobj.getChildValue('duration')
    uid         = vobj.getChildValue('uid')
    rruleset    = vobj.rruleset
    recurrenceID = vobj.getChildValue('recurrence_id') # ... uh, sorta
    completed = vobj.getChildValue('completed')


    def convertDatetime(dt):
        # coerce timezones based on coerceTzinfo
        if coerceTzinfo is not None:
            dt = TimeZone.coerceTimeZone(dt, coerceTzinfo)

        # ... and make sure we return something with an ICUtzinfo
        return convertToICUtzinfo(dt, view)

    reminderDelta = None
    reminderAbsoluteTime = None

    try:
        reminderValue = vobj.valarm.trigger.value
    except AttributeError:
        pass
    else:
        if type(reminderValue) is datetime.datetime:
            reminderAbsoluteTime = convertDatetime(reminderValue)
        else:
            assert type(reminderValue) is datetime.timedelta
            reminderDelta = reminderValue
            

    if vobj.name == "VEVENT":

        if DEBUG: logger.debug("got VEVENT %s", vobj)
        
        newStamps.append(EventStamp)
        dtstart = vobj.getChildValue('dtstart')

        if status in ('confirmed', 'tentative'):
            pass
        elif status == 'cancelled': #Chandler doesn't have CANCELLED
            status = 'fyi'
        else:
            status = 'confirmed'

        if EventStamp.transparency.name not in filters:
            change(EventStamp.transparency, status)

        location = vobj.getChildValue('location')
        if location:
            change(EventStamp.location,
                   Calendar.Location.getLocation(view, location))
        
    elif vobj.name == "VTODO":

        if DEBUG: logger.debug("got VEVENT %s", vobj)
        
        newStamps.append(TaskStamp)
        
        # VTODO with a DUE ==> EventTask
        due = vobj.getChildValue('due')
        if due is not None:
            newStamps.append(EventStamp)
            dtstart = due
            
    else:
        assert False, "vobj %s should always be VEVENT or VTODO" % (
                            vobj,)


    # Save changes applicable to both events & tasks ....

    # SUMMARY <-> {EventStamp,TaskStamp}.summary
    if summary is not None:
        change(newStamps[0].summary, summary)

    # DESCRIPTION <-> body  
    if description is not None:
        change(Note.body, description)
        
    # Absolute time reminders
    if (reminderAbsoluteTime is not None and
        Remindable.reminders.name not in filters):
        changeLast.append(lambda item: setattr(item,
                                               Remindable.userReminderTime.name, 
                                               reminderAbsoluteTime))
    # Custom properties/parameters                                           
    ignoredProperties = {}
    ignoredParameters = {}
    for line in vobj.lines():
        name = line.name.lower()
        if name not in attributesUnderstood:
            line.transformFromNative()
            if not line.encoded and line.behavior:
                line.behavior.encode(line)
            ignoredProperties[name] = line.value
        params=u''
        for key, paramvals in line.params.iteritems():
            if key.lower() not in parametersUnderstood:
                vals = map(vobject.base.dquoteEscape, paramvals)
                params += ';' + key + '=' + ','.join(vals)
        if len(params) > 0:
            ignoredParameters[name] = params

    change(Note.icalendarProperties, ignoredProperties)
    change(Note.icalendarParameters, ignoredParameters)


    # See if we have a corresponding item already
    item = formats.findUID(view, uid)

    if item is not None:
        if DEBUG: logger.debug("matched UID %s with %s", uid, item)
    else:
        try:
            # See if uid is a valid repository UUID, if so we'll
            # go ahead and use it for the new item's UUID.
            uuid = UUID(uid)
        except ValueError:
            # Not in valid UUID format, so hash the icaluid to
            # generate a 16-byte string we can use for uuid
            uuid = UUID(md5.new(uid).digest())
            logger.info("Converted icalUID '%s' to UUID '%s'", uid,
                str(uuid))

        # If there is already an item with this UUID, use it,
        # otherwise we'll create one later
        item = view.findUUID(uuid)
            
        if item is not None:
            item.icalUID = uuid

            
    if EventStamp in newStamps:
        dtend = vobj.getChildValue('dtend')

        isDate = type(dtstart) == date

        # RFC2445 allows VEVENTs without DTSTART, but it's hard to guess
        # what that would mean, so we won't catch an exception if there's no
        # dtstart.
        anyTime = (getattr(dtstart, 'x_osaf_anytime_param', None)
                      == 'TRUE')
        
        if duration is None:
        
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
                duration = oneDay
            else:
                duration = datetime.timedelta(0)

        if isDate:
            dtstart = TimeZone.forceToDateTime(dtstart)
            # convert to Chandler's notion of all day duration
            duration -= oneDay
        elif dtstart.tzinfo is not None and promptForTimezone:
            # got a timezoned event, prompt (non-modally) to turn on
            # timezones
            app = wx.GetApp()
            if app is not None:
                def ShowTimezoneDialogCallback():
                    ShowTurnOnTimezonesDialog(view=app.UIRepositoryView)
                app.PostAsyncEvent(ShowTimezoneDialogCallback)
            promptForTimezone = False

        dtstart = convertDatetime(dtstart)
        tzinfo = dtstart.tzinfo

        if anyTime:
            change(EventStamp.anyTime, True)
            change(EventStamp.allDay, False)
        elif isDate:
            # allDay events should have anyTime True, so if the user
            # unselects allDay, the time isn't set to midnight
            change(EventStamp.anyTime, True)
            change(EventStamp.allDay, True)
        else:
            change(EventStamp.allDay, False)
            change(EventStamp.anyTime, False)

        change(EventStamp.startTime, dtstart)
        change(EventStamp.duration, duration)

        if ((reminderDelta is not None) and
            (Remindable.reminders.name not in filters)):
                changeLast.append(
                    lambda item:setattr(item,
                                        EventStamp.userReminderInterval.name, 
                                        reminderDelta))
        if item is not None:
            event = EventStamp(item)

            if recurrenceID:
                if type(recurrenceID) == date:
                    recurrenceID = datetime.datetime.combine(
                                                recurrenceID,
                                                time(tzinfo=tzinfo))
                else:
                    recurrenceID = convertToICUtzinfo(
                                       makeNaiveteMatch(recurrenceID,
                                       tzinfo), view)
                
                masterEvent = EventStamp(item)    
                event = masterEvent.getRecurrenceID(recurrenceID)
                if event is None and hasattr(masterEvent, 'startTime'):
                    # Some calendars, notably Oracle, serialize
                    # recurrence-id as UTC, which wreaks havoc with 
                    # noTZ mode. So move recurrenceID to the same tzinfo
                    # as the master's dtstart, bug 6830
                    masterTzinfo = masterEvent.startTime.tzinfo
                    tweakedID = recurrenceID.astimezone(masterTzinfo)
                    event = masterEvent.getRecurrenceID(tweakedID)
                if event is None:
                    # just in case the previous didn't work
                    tweakedID = recurrenceID.astimezone(tzinfo)
                    event = masterEvent.getRecurrenceID(tweakedID)
                    
                if event is None:
                    # our recurrenceID didn't match an item we know
                    # about.  This may be because the item is created
                    # by a later modification, a case we're not dealing
                    # with.  For now, just skip it.
                    logger.info("RECURRENCE-ID '%s' didn't match rule.",
                                recurrenceID)
                    return (None, None, promptForTimezone)

                item = event.itsItem
                recurrenceLine = vobj.contents['recurrence-id'][0]
                range = recurrenceLine.params.get('RANGE', ['THIS'])[0]
                if range == 'THISANDPRIOR':
                    # ignore THISANDPRIOR changes for now
                    logger.info("RECURRENCE-ID RANGE of THISANDPRIOR " \
                                "not supported")
                    return (None, None, promptForTimezone)
                elif range == 'THIS':
                    itemChangeCallback = event.changeThis
                    # check if this is a modification to a master event
                    # if so, avoid changing the master's UUID when
                    # creating a modification
                    if event.getMaster() == event:
                        mod = event._cloneEvent()
                        mod.modificationFor = mod.occurrenceFor = event.itsItem
                        if item.hasLocalAttributeValue(
                                        EventStamp.occurrenceFor.name):
                            del event.occurrenceFor
                        event = mod
                        item = event.itsItem
                    
                elif range == 'THISANDFUTURE':
                    itemChangeCallback = event.changeThisAndFuture
                else:
                    logger.info("RECURRENCE-ID RANGE not recognized. " \
                                "RANGE = %s" % range)
                    return (None, None, promptForTimezone)
            else:
                if event.rruleset is not None:
                    # re-creating a recurring item from scratch, delete 
                    # old recurrence information
                    # item might not be the master, though, so
                    # get the master, or eventItem will be a deleted
                    # event
                    event = event.getMaster()
                    item = event.itsItem
                    # delete modifications the master has, to avoid
                    # changing the master to a modification with a
                    # different UUID
                    for mod in itertools.imap(EventStamp, event.modifications):
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

                    event.removeRecurrence()
                    
                itemChangeCallback = event.changeThis

            if DEBUG: logger.debug("Changing event: %s" % str(event))
            assert itemChangeCallback is not None, \
                   "Must set itemChangeCallback for EventStamp imports"
                

        if rruleset is not None:
            # fix for Bug 6994, exdate and rdate timezones need to be
            # converted to ICUtzinfo instances
            for typ in '_rdate', '_exdate':
                setattr(rruleset, typ, [convertDatetime(d) for d in
                                        getattr(rruleset, typ, [])  ])
            ruleSetItem = RecurrenceRuleSet(None, itsView=view)
            ruleSetItem.setRuleFromDateUtil(rruleset)
            changeLast.append(lambda item: setattr(item,
                                                   EventStamp.rruleset.name,
                                                   ruleSetItem))
        
    if TaskStamp in newStamps:
        
        if Note._triageStatus.name not in filters:
            # Translate status from iCalendar to TaskStamp/ContentItem
            triageStatus=TriageEnum.now
            
            if status == "completed":
                triageStatus = TriageEnum.done
            elif status == "needs-action":
                change(Note.needsReply, True)
            elif status in ("", "in-process"):
                change(Note.needsReply, False)
            elif status == "cancelled":
                triageStatus = TriageEnum.later

            # @@@ Jeffrey: This may not be right...
            # Set triageStatus and triageStatusChanged together.
            if completed is not None:
                if type(completed) == date:
                    completed = TimeZone.forceToDateTime(completed)
            changeLast.append(lambda item: item.setTriageStatus(triageStatus, 
                                                                when=completed))
            

    itemIsNew = (item is None)
            
    if itemIsNew:

        # create a new item
        change(Note.icalUID, uid)

        kind = Note.getKind(view)
        item = kind.instantiateItem(None, newItemParent, uuid,
                                    withInitialValues=True)
        itemChangeCallback = item.__setattr__
    else:
        if itemChangeCallback is None:
            itemChangeCallback = item.__setattr__
        
        # update an existing item
        if (rruleset is None and recurrenceID is None
           and EventStamp(item).rruleset is not None):
            # no recurrenceId or rruleset, but the existing item
            # may have recurrence, so delete it
            EventStamp(item).removeRecurrence()

    for attr, val in changesDict.iteritems():
    
        # Only change a datetime if it's really different
        # from what the item already has:
        if type(val) is datetime.datetime:
             oldValue = getattr(item, attr, None)
             if (oldValue is not None and 
                 oldValue == val and
                 oldValue.tzinfo == val.tzinfo):
                continue
    
        itemChangeCallback(attr, val)

    # ... make sure the stamps are right
    for stamp in EventStamp, TaskStamp:
        if not stamp in newStamps:
            if has_stamp(item, stamp):
                stamp(item).remove()
        else:
            if not has_stamp(item, stamp):
                stamp(item).add()

    # ... and do the final set of changes
    for cb in changeLast:
        cb(item)
        
            
    return item, itemIsNew, promptForTimezone



# attributes to avoid reusing when serializing events that were originally
# imported
attributesUnderstood = ['recurrence-id', 'summary', 'description', 'location',
                        'status', 'duration', 'dtstart', 'dtend', 'uid', 'due',
                        'valarm', 'dtstamp', 'rrule', 'exrule', 'rdate',
                        'exdate']

parametersUnderstood = ['tzid', 'x-vobj-original-tzid', 'x-osaf-anytime']

def itemsFromVObject(view, text, coerceTzinfo=None, filters=None,
                     monolithic=True, activity=None, stats=None,
                     silentFailure=False):
    """
    Take a string, create or update items from that stream.
    The filters argument is an optional sequence of attributes to not populate.
    
    monolithic is True for calendars that may contain multiple events, for
    CalDAV shares calendars will always contain one event (modulo recurrence) 
    so monolithic will be False for CalDAV.

    Return is a tuple (itemlist, calname).

    """
    if filters is None:
        filters = () # we want filters to be iterable
    tzprefs = schema.ns("osaf.pim", view).TimezonePrefs
    promptForTimezone = not tzprefs.showUI and tzprefs.showPrompt
    
    newItemParent = view.findPath("//userdata")
    
    countNew = 0
    countUpdated = 0
    
    itemlist = []
    
    calname = None

    # iterate over calendars, usually only one, but more are allowed
    for calendar in vobject.readComponents(text, validate=False,
                                           ignoreUnreadable=True):
        modificationQueue = []

        # just grab the first calendar name
        if calname is None:
            calname = calendar.getChildValue('x_wr_calname')

        vobjects = tuple((-1, obj) for obj in itertools.chain(
                            getattr(calendar, 'vevent_list', []),
                            getattr(calendar, 'vtodo_list', [])))

        numItems = len(vobjects)
        if activity and monolithic:
            activity.update(msg=_(u"Calendar contains %d items") % numItems,
                totalWork=numItems)
        
        for i, vobj in itertools.chain(vobjects, enumerate(modificationQueue)):
            # Queue modifications to recurring events so modifications are
            # processed after master events in the iCalendar stream.
            recurrenceID = vobj.getChildValue('recurrence_id')
            if recurrenceID is not None and i < 0:
                # only add to modificationQueue in initial processing
                modificationQueue.append(vobj)

            else:
                try:
                    item, isNew, promptForTimezone = _importOneVObject(vobj,
                        filters, coerceTzinfo, promptForTimezone, newItemParent)
                    
                    if item is None:
                        continue
                    
                    if DEBUG: logger.debug(u"Imported %s", item)
                    
                    if isNew:
                        countNew += 1
                        statsKey = 'added'
                    else:
                        countUpdated += 1
                        statsKey = 'modified'
                    if stats and item.itsUUID not in stats[statsKey]:
                        stats[statsKey].append(item.itsUUID)
        
                    if activity:
                        msg="'%s'" % (item.displayName,)
                        # the work parameter tells the callback whether progress
                        # should be tracked, this only makes sense if we might have
                        # more than one event.
                        activity.update(msg=msg, work=monolithic)
                
                    # finished creating the item
                    itemlist.append(item)
    
                except vobject.base.VObjectError, e:
                    icalendarLines = text.splitlines()
                    logger.error("Exception when importing icalendar, first 300 lines: \n%s"
                                 % "\n".join(icalendarLines[:300]))
                    logger.exception("import failed to import one event with exception: %s" % str(e))
                    if not silentFailure:
                        raise
    
    logger.info("...iCalendar import of %d new items, %d updated", countNew,
                countUpdated)
    
    return itemlist, calname


def updateFreebusyFromVObject(view, text, busyCollection, activity=None):
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
    for calendar in vobject.readComponents(text, validate=True,
                                           ignoreUnreadable=True):
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

    logger.info("...iCalendar import of %d new freebusy blocks, %d updated",
                countNew, countUpdated)
    
    return freebusystart, freebusyend, calname

class ICalendarFormat(formats.ImportExportFormat):

    def fileStyle(self):
        return formats.STYLE_SINGLE

    def extension(self, item):
        return "ics"

    def contentType(self, item):
        return "text/calendar"

    def acceptsItem(self, item):
        return (has_stamp(item, EventStamp) or
                has_stamp(item, TaskStamp) or
                isinstance(item, Sharing.Share))

    def importProcess(self, contentView, text, extension=None, item=None,
                      activity=None, stats=None):
        # the item parameter is so that a share item can be passed in for us
        # to populate.

        # An ICalendar file doesn't have any 'share' info, just the collection
        # of events, etc.  Therefore, we want to actually populate the share's
        # 'contents':

        view = contentView # Use the passed-in view for creating items
        filters = self.share.filterAttributes
        monolithic = self.fileStyle() == formats.STYLE_SINGLE
        coerceTzinfo = getattr(self, 'coerceTzinfo', None)

        events, calname = itemsFromVObject(view, text, coerceTzinfo, filters,
                                           monolithic, activity, stats,
                                           monolithic)

        def masterEventItem(obj):
            if has_stamp(obj, EventStamp):
                return EventStamp(obj).getMaster().itsItem
            else:
                return obj


        if monolithic:
            if calname is None:
                calname = _(u"Imported Calendar")

            if item is None:
                item = SmartCollection(itsView=view)
                shares.SharedItem(item).add()
            elif isinstance(item, shares.Share):                        
                if item.contents is None:
                    item.contents = \
                        SmartCollection(itsView=view)
                    shares.SharedItem(item.contents).add()
                item = item.contents

            if not isinstance(item, ContentCollection):
                print "Only a share or an item collection can be passed in"
                #@@@MOR Raise something

            if getattr(item, 'displayName', "") == "":
                item.displayName = unicode(calname)

            # finally, add each new event to the collection
            for event in events:
                item.add(masterEventItem(event))

            return item

        else:
            if len(events) == 0:
                logger.error("Got no events, icalendar: " + text)
            # if fileStyle isn't single, item must be a collection
            return masterEventItem(events[0])

    def exportProcess(self, share, depth=0):
        cal = itemsToVObject(self.itsView, share.contents,
                             filters=self.share.filterAttributes)
        if self.fileStyle() == formats.STYLE_SINGLE:
            # don't add a METHOD to CalDAV serializations, because CalDAV
            # forbids them, but do add one when serializing monolithic ics files
            # because Outlook requires them (bug 7121)
            cal.add('method').value="PUBLISH"
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
        return formats.STYLE_DIRECTORY
    
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
                      activity=None, stats=None):
        # the item parameter is so that a share item can be passed in for us
        # to populate.

        # An ICalendar file doesn't have any 'share' info, just the collection
        # of events, etc.  Therefore, we want to actually populate the share's
        # 'contents':

        view = contentView # Use the passed-in view for creating items

        if item is None:
            item = SmartCollection(itsView=view)
            shares.SharedItem(item).add()
        elif isinstance(item, shares.Share):
            if item.contents is None:
                item.contents = \
                    SmartCollection(itsView=view)
                shares.SharedItem(item.contents).add()
            item = item.contents

        # something should be done with start and end, eventually
        start, end, calname = updateFreebusyFromVObject(view, text, item, 
                                                        activity)

        if getattr(item, 'displayName', "") == "":
            if calname is None:
                calname = _(u"Imported Free-busy")
            item.displayName = unicode(calname)

        return item

class ICalendarImportError(Exception):
    pass

def importICalendarFile(fullpath, view, targetCollection = None,
                        filterAttributes = None, activity=None,
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
    
    share = shares.OneTimeFileSystemShare(itsView=view,
        filePath=dir, fileName=filename,
        formatClass=ICalendarFormat, contents=targetCollection
    )
    if tzinfo is not None:
        share.format.coerceTzinfo = tzinfo
    
    for key in filterAttributes:
        share.filterAttributes.append(key)
    
    before = epoch_time()
    
    try:
        collection = share.get(activity=activity)
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
