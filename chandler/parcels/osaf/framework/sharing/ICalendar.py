__parcel__ = "osaf.framework.sharing"

import Sharing
import application.Parcel
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.calendar.Recurrence as Recurrence
from chandlerdb.util.uuid import UUID
import StringIO
import vobject
import logging
import dateutil.tz
import datetime
from datetime import date
from datetime import time
import itertools
import repository.query.Query as Query
from application import schema

logger = logging.getLogger('ICalendar')
logger.setLevel(logging.INFO)

localtime = dateutil.tz.tzlocal()
utc = dateutil.tz.tzutc()

def dateForVObject(dt, asDate = False):
    """Convert the given datetime into a date or datetime with tzinfo=UTC."""
    if asDate:
        return dt.date()
    else:
        return dt.replace(tzinfo=localtime).astimezone(utc)

def itemsToVObject(view, items, cal=None, filters=None):
    """Iterate through items, add to cal, create a new vcalendar if needed.

    Chandler doesn't do recurrence yet, so for now we don't worry
    about timezones.

    """
    taskKind  = view.findPath(ICalendarFormat._taskPath)
    eventKind  = view.findPath(ICalendarFormat._calendarEventPath)
    if cal is None:
        cal = vobject.iCalendar()
    for item in items:
        if item.isItemOf(taskKind):
            taskorevent='TASK'
            comp = cal.add('vtodo')
        elif item.isItemOf(eventKind):
            taskorevent='EVENT'
            comp = cal.add('vevent')
        else:
            continue
        
        if item.getAttributeValue('icalUID', default=None) is None:
            item.icalUID = unicode(item.itsUUID)
        comp.add('uid').value = item.icalUID

        try:
            comp.add('summary').value = item.displayName
        except AttributeError:
            pass
        try:
            comp.add('dtstart').value = dateForVObject(item.startTime,item.allDay)
        except AttributeError:
            pass
        try:
            if taskorevent == 'TASK':
                comp.add('due').value = dateForVObject(item.dueDate,item.allDay)
            else:
                comp.add('dtend').value = dateForVObject(item.endTime,item.allDay)
        except AttributeError:
            pass

        if not filters or "transparency" not in filters:
            try:
                if taskorevent == 'EVENT':
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

    return cal

class ICalendarFormat(Sharing.ImportExportFormat):

    schema.kindInfo(displayName="iCalendar Import/Export Format Kind")

    _calendarEventPath = "//parcels/osaf/contentmodel/calendar/CalendarEvent"
    _taskPath = "//parcels/osaf/contentmodel/EventTask"
    _lobPath = "//Schema/Core/Lob"
    
    def fileStyle(self):
        return self.STYLE_SINGLE

    def extension(self, item):
        return "ics"

    def findUID(self, uid):
        view = self.itsView
        queryString='union(for i in "%s" where i.icalUID == $0, \
                           for i in "%s" where i.icalUID == $0)' % \
                           (self._calendarEventPath, self._taskPath)
        p = view.findPath('//Queries')
        k = view.findPath('//Schema/Core/Query')
        q = Query.Query(None, p, k, queryString)

        q.args["$0"] = ( uid, )
        for match in q:
            return match.getMaster()
        return None

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
                item = ItemCollection.ItemCollection(view=view)
            elif isinstance(item, Sharing.Share):
                if item.contents is None:
                    item.contents = ItemCollection.ItemCollection(view=view)
                item = item.contents

            if not isinstance(item, ItemCollection.ItemCollection):
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
            dtstart = Recurrence.stripTZ(dtstart)
            
            # See if we have a corresponding item already
            recurrenceID = None
            uidMatchItem = self.findUID(event.uid[0].value)
            if uidMatchItem is not None:
                logger.debug("matched UID")
                try:
                    recurrenceID = event.contents['recurrence-id'][0].value
                    if type(recurrenceID) == date:
                        recurrenceID = datetime.datetime.combine(recurrenceID,
                                                                 time(0))
                    else:
                        recurrenceID = Recurrence.stripTZ(recurrenceID)
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
            

            # vobject isn't meshing well with dateutil when dtstart isDate;
            # dtstart is converted to a datetime for dateutil, but rdate
            # isn't.  To make dateutil happy, convert rdates which are dates to
            # datetimes until vobject is fixed.
            for i, rdate in enumerate(event.rdate):
                if type(rdate) == date:
                    event.rdate[i] = datetime.datetime.combine(rdate, time(0))
                else:
                    event.rdate[i] = Recurrence.stripTZ(event.rdate[i])
                    
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
