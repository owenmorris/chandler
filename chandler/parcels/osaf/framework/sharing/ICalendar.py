import Sharing
import application.Parcel
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.calendar.Calendar as Calendar
from chandlerdb.util.uuid import UUID
import StringIO
import vobject
import logging
import dateutil.tz
import datetime
import itertools
import repository.query.Query as Query

logger = logging.getLogger('ICalendar')
logger.setLevel(logging.INFO)

localtime = dateutil.tz.tzlocal()
utc = dateutil.tz.tzutc()

MAXRECUR = 10

def dateForVObject(dt, asDate = False):
    """Convert the given datetime into a date or datetime with tzinfo=UTC."""
    if asDate:
        return dt.date()
    else:
        return dt.replace(tzinfo=localtime).astimezone(utc)

def itemsToVObject(view, items, cal=None):
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
        
        if item.getAttributeValue('uid', default=None) is None:
            item.uid = unicode(item.itsUUID)
        comp.add('uid').value = item.uid

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
        try:
            comp.add('valarm').add('trigger').value = \
              dateForVObject(item.reminderTime) - dateForVObject(item.startTime)
        except AttributeError:
            pass
    return cal

class ICalendarFormat(Sharing.ImportExportFormat):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/sharing/ICalendarFormat"

    _calendarEventPath = "//parcels/osaf/contentmodel/calendar/CalendarEvent"
    _taskPath = "//parcels/osaf/contentmodel/EventTask"
    _lobPath = "//Schema/Core/Lob"
    
    def fileStyle(self):
        return self.STYLE_SINGLE

    def extension(self, item):
        return "ics"

    def findUID(self, uid):
        view = self.itsView
        queryString='union(for i in "%s" where i.uid == $0, \
                           for i in "%s" where i.uid == $0)' % \
                           (self._calendarEventPath, self._taskPath)
        p = view.findPath('//Queries')
        k = view.findPath('//Schema/Core/Query')
        q = Query.Query(None, p, k, queryString)
        # See if we have a corresponding item already, or create one
        q.args["$0"] = ( uid, )
        for match in q:
            return match
        return None

    def importProcess(self, text, extension=None, item=None):
        # the item parameter is so that a share item can be passed in for us
        # to populate.

        # An ICalendar file doesn't have any 'share' info, just the collection
        # of events, etc.  Therefore, we want to actually populate the share's
        # 'contents':

        view = self.itsView
        
        newItemParent = self.findPath("//userdata")
        eventKind = self.itsView.findPath(self._calendarEventPath)
        taskKind  = self.itsView.findPath(self._taskPath)
        textKind  = self.itsView.findPath(self._lobPath)
        
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

            # For now we'll expand recurrence sets, first find attributes that
            # will be constant across the recurrence set.

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
            # Iterate through recurrence set.  Infinite recurrence sets are
            # common, something has to be done to avoid infinite loops.
            # We'll arbitrarily limit ourselves to MAXRECUR recurrences.

            # See if we have a corresponding item already
            uidMatchItem = self.findUID(event.uid[0].value)
            first = True
            
            # FIXME total hack to deal with the fact that dateutil.rrule doesn't
            # know how to deal with dates without time.
            # If DTSTART's VALUE parameter is set to DATE, don't use rruleset
            isDate = type(event.dtstart[0].value) == datetime.date
            if isDate:
                d = event.dtstart[0].value
                recurrenceIter = [datetime.datetime(d.year, d.month, d.day)]
            else:
                recurrenceIter = itertools.islice(event.rruleset, MAXRECUR)
            
            for dt in recurrenceIter:
                #give the repository a naive datetime, no timezone
                try:
                    dt = dt.astimezone(localtime).replace(tzinfo=None)
                except ValueError: # astimezone will fail for naive datetimes
                    pass
                if uidMatchItem is not None:
                    logger.debug("matched UID")
                    eventItem = uidMatchItem
                    uidMatchItem = None
                    countUpdated += 1
                else:
                    eventItem = pickKind.newItem(None, newItemParent)
                    countNew += 1
                    if first:
                        eventItem.uid = event.uid[0].value
                        first = False
                    else:
                        eventItem.uid = unicode(eventItem.itsUUID)
                    
                logger.debug("eventItem is %s" % str(eventItem))
                
                #Default to NOT any time
                eventItem.anyTime = False
                
                eventItem.displayName = displayName
                if isDate:
                    eventItem.allDay = True
                eventItem.startTime   = dt
                if vtype == u'VEVENT':
                    eventItem.endTime = dt + duration
                elif vtype == u'VTODO':
                    if duration is not None:
                        eventItem.dueDate = dt + duration
                
                eventItem.transparency = status
                
                # I think Item.description describes a Kind, not userdata, so
                # I'm using DESCRIPTION <-> body  
                if description is not None:
                    eventItem.body = textKind.makeValue(description)
                
                if location:
                    eventItem.location = Calendar.Location.getLocation(view,
                                                                       location)
                
                if reminderDelta is not None:
                    eventItem.reminderTime = dt + reminderDelta

                item.add(eventItem)
                logger.debug("Imported %s %s" % (eventItem.displayName,
                 eventItem.startTime))
                 
        logger.info("...iCalendar import of %d new items, %d updated" % \
         (countNew, countUpdated))

        return item

    def exportProcess(self, share, depth=0):
        cal = itemsToVObject(self.itsView, share.contents)
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
        cal = itemsToVObject(self.itsView, [item])
        return cal.serialize()
