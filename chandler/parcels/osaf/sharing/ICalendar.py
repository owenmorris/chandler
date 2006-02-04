__parcel__ = "osaf.sharing"

__all__ = [
    'ICalendarFormat',
    'CalDAVFormat',
]

import Sharing
import application.Parcel
from osaf.pim import AbstractCollection, InclusionExclusionCollection, CalendarEventMixin
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
    Convert the given datetime into a date or datetime, depending on asDate.
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
            if item.allDay:
                # allDay-ness overrides anyTime-ness
                dtstartLine.value = dateForVObject(item.startTime, True)
            elif item.anyTime:
                dtstartLine.params['X-OSAF-ANYTIME']=['TRUE']
                # anyTime should be exported as allDay for non-Chandler apps
                dtstartLine.value = dateForVObject(item.startTime, True)
            else:
                dtstartLine.value = dateForVObject(item.startTime, False)

        except AttributeError:
            comp.dtstart = [] # delete the dtstart that was added
        
        try:
            if not (item.duration == datetime.timedelta(0) or (
                    (item.anyTime or item.allDay) and 
                    item.duration <= datetime.timedelta(days=1))):
                dtendLine = comp.add('dtend')
                #convert Chandler's notion of allDay duration to iCalendar's
                if item.allDay:
                    dtendLine.value = dateForVObject(item.endTime, True) + \
                                                     datetime.timedelta(days=1)
                elif item.anyTime:
                    dtendLine.params['X-OSAF-ANYTIME']=['TRUE']
                    # anyTime should be exported as allDay for non-Chandler apps
                    dtendLine.value = dateForVObject(item.endTime, True)
                else:
                    dtendLine.value = dateForVObject(item.endTime, False)

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
            firstReminder = item.reminders.first() or item.expiredReminders.first()
            if firstReminder is not None:
                comp.add('valarm').add('trigger').value = firstReminder.delta
        
        if item.getAttributeValue('modificationFor', default=None) is not None:
            recurrenceid = comp.add('recurrence-id')
            master = item.getMaster()
            allDay = master.allDay or master.anyTime
            recurrenceid.value = dateForVObject(item.recurrenceID, allDay)
        
        # logic for serializing rrules needs to move to vobject
        try: # hack, create RRULE line last, because it means running transformFromNative
            if item.modifies == 'thisandfuture' or item.getMaster() == item:
                # False because we don't want to ignore isCount for export
                cal.vevent[-1].rruleset = item.createDateUtilFromRule(False)
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

    def acceptsItem(self, item):
        return isinstance(item, (CalendarEventMixin, Sharing.Share))

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

    def importProcess(self, text, extension=None, item=None, changes=None,
        previousView=None, updateCallback=None):
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
                item = InclusionExclusionCollection(itsView=view).setup()
            elif isinstance(item, Sharing.Share):
                        
                if item.contents is None:
                    item.contents = \
                        InclusionExclusionCollection(itsView=view).setup()
                item = item.contents

            if not isinstance(item, AbstractCollection):
                print "Only a share or an item collection can be passed in"
                #@@@MOR Raise something


        else:
            caldavReturn = None

        input = StringIO.StringIO(text)
        calendar = list(vobject.readComponents(input, validate=True))
        if len(calendar) == 0:
            # an empty ics file, what to do?
            return
        else:
            calendar = calendar[0]
        

        if self.fileStyle() == self.STYLE_SINGLE:
            try:
                calName = calendar.contents[u'x-wr-calname'][0].value
            except:
                calName = u"Imported Calendar"
            if getattr(item, 'displayName', "") == "":
                item.displayName = unicode(calName)

        countNew = 0
        countUpdated = 0
        
        modificationQueue = []
        
        minusone = itertools.repeat(-1)
        # This is, essentially: [(-1, event) for event in calendar.vevent]
        rawVevents = getattr(calendar, 'vevent', [])
        numVevents = len(rawVevents)
        if updateCallback and self.fileStyle() == self.STYLE_SINGLE:
            updateCallback(msg=_(u"Calendar contains %d events") % numVevents,
                totalWork=numVevents)
            
        vevents = itertools.izip(minusone, rawVevents)
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

                # RFC2445 allows VEVENTs without DTSTART, but it's hard to guess
                # what that would mean, so we won't catch an exception if there's no
                # dtstart.
                dtstartLine = event.dtstart[0]
                dtstart = dtstartLine.value
                anyTime = dtstartLine.params.get('X-OSAF-ANYTIME', [None])[0] == 'TRUE'
                isDate = type(dtstart) == date

                try:
                    reminderDelta = event.valarm[0].trigger[0].value
                    if type(reminderDelta) is datetime.datetime:
                        reminderDelta = reminderDelta - dtstart
                except AttributeError:
                    reminderDelta = None

                try:
                    duration = event.duration[0].value
                except AttributeError:
                    # note that duration = dtend - dtstart isn't strictly correct
                    # throughout a recurrence set, 1 hour differences might happen
                    # around DST, but we'll ignore that corner case for now
                    try:
                        duration = event.dtend[0].value - dtstart
                    except AttributeError:
                        # FIXME Nesting try/excepts is ugly.
                        try:
                            duration = event.due[0].value - dtstart
                        except AttributeError:
                            if anyTime or isDate:
                                duration = datetime.timedelta(days=1)
                            else:
                                duration = datetime.timedelta(0)
                                
    
                if isDate:
                    dtstart = TimeZone.forceToDateTime(dtstart)
                    # convert to Chandler's notion of all day duration
                    duration -= datetime.timedelta(days=1)
                
                # coerce timezones based on coerceTzinfo
                coerceTzinfo = getattr(self, 'coerceTzinfo', None)
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
                uidMatchItem = self.findUID(event.uid[0].value)
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
                                mod.modificationFor = mod.occurenceFor = eventItem
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
                    change('body', textKind.makeValue(description))
                
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
                    #change('icalUID', event.uid[0].value)
                    eventItem = pickKind.newItem(None, newItemParent, **changesDict)
                    # set icalUID seperately to make sure uid_map gets set
                    eventItem.icalUID = event.uid[0].value
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

                if updateCallback and \
                    updateCallback(msg="'%s'" % eventItem.getItemDisplayName(),
                        work=(self.fileStyle() == self.STYLE_SINGLE)):
                    raise Sharing.SharingError(_(u"Cancelled by user"))

                allCollection = schema.ns("osaf.app", view).allCollection

                if self.fileStyle() == self.STYLE_SINGLE:
                    if item != allCollection:
                        item.add(eventItem.getMaster())
                else:
                    caldavReturn = eventItem.getMaster()

            except Sharing.SharingError:
                raise

            except Exception, e:
                if __debug__:
                    raise
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

    trash = schema.ns("osaf.app", view).TrashCollection
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