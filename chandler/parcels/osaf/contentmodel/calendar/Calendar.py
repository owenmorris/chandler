""" Classes used for Calendar parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import repository.query.Query as Query

import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.Notes as Notes
import osaf.contentmodel.contacts.Contacts as Contacts

from datetime import datetime, timedelta


class CalendarEventMixin(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/calendar/CalendarEventMixin"

    """
      Calendar Event Mixin is the bag of Event-specific attributes.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    def __init__ (self, name=None, parent=None, kind=None, view=None):
        super (CalendarEventMixin, self).__init__(name, parent, kind, view)

    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(CalendarEventMixin, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        CalendarEventMixin._initMixin (self) # call our init, not the method of a subclass

        # New item initialization
        self.displayName = "New Event"

    def _initMixin (self):
        """ 
          Init only the attributes specific to this mixin.
        Called when stamping adds these attributes, and from __init__ above.
        """
        # start at the nearest half hour, duration of an hour
        now = datetime.now()
        self.startTime = datetime(now.year, now.month, now.day,
                                  now.hour, (now.minute/30) * 30)
        self.duration = timedelta(hours=1)

        # default the organizer to an existing value, or "me"
        try:
            whoFrom = self.getAnyWhoFrom ()

            # I only want a Contact
            if not isinstance(whoFrom, Contacts.Contact):
                whoFrom = self.getCurrentMeContact(self.itsView)

            self.organizer = whoFrom

        except AttributeError:
            self.organizer = self.getCurrentMeContact(self.itsView)

        # give a starting display name
        try:
            self.displayName = self.getAnyAbout ()
        except AttributeError:
            pass
        
        """ @@@ Commenting out this block

        participants can only accept Contact items.  At some point
        this code will need inspect the results of getAnyWho() and
        create Contact items for any EmailAddresses in the list

        # set participants to any existing "who"
        try:
            need to shallow copy the list
            self.participants = self.getAnyWho ()
        except AttributeError:
            pass # no participants yet

        @@@ End block comment """

    """
    These "getAny" methods are used for Mixin attribute initialization.
    After stamping, we'd like to initialize attributes, like participants,
    with the "who" value defined by the rest of the classes in the item.
    But we can't just access the "who" attribute, because we've already
    stamped the item with our mixin and have applied our "who" attribute
    definition.  So getAnyXXX gets any significant defined value in any
    of the "who" attributes so we can initialize our own attribute
    appropriately. See initMixin above for an example usage.

    It's unclear if we really need this mechanism in the long run, because
    we may end up with one "to" field instead of separate "participants",
    "requestees", etc.
    """
    def getAnyWho (self):
        """
        Get any non-empty definition for the "who" attribute.
        """
        try:
            return self.participants
        except AttributeError:
            pass
        return super (CalendarEventMixin, self).getAnyWho ()
    
    def getAnyWhoFrom (self):
        """
        Get any non-empty definition for the "whoFrom" attribute.
        """
        try:
            organizer = self.organizer
        except AttributeError:
            organizer = None
        if organizer is not None:
            return organizer
        return super (CalendarEventMixin, self).getAnyWhoFrom ()

    def GetDuration(self):
        """Returns a timedelta, None if no startTime or endTime"""
        
        if (self.hasLocalAttributeValue("startTime") and
            self.hasLocalAttributeValue("endTime")):
            return self.endTime - self.startTime
        else:
            return None

    def SetDuration(self, timeDelta):
        """Set duration of event, expects value to be a timedelta
        
        endTime is updated based on the new duration, startTime remains fixed
        """
        if (self.startTime is not None):
            self.endTime = self.startTime + timeDelta

    duration = property(GetDuration, SetDuration,
                        doc="timedelta: the length of an event")

    def GetReminderDelta(self):
        """ Returns the difference between startTime and reminderTime, a timedelta """
        try:
            return self.startTime - self.reminderTime
        except AttributeError:
            return None
   
    def SetReminderDelta(self, reminderDelta):
        if (self.startTime is not None):
            if reminderDelta is not None:
                self.reminderTime = self.startTime - reminderDelta
            else:
                
                try:
                    del self.reminderTime
                except AttributeError:
                    pass
    
    reminderDelta = property(GetReminderDelta, SetReminderDelta,
                             doc="reminderDelta: the amount of time in advance of the event that we want a reminder")
    
    def ChangeStart(self, dateTime):
        """Change the start time without changing the duration.

        Setting startTime directly will effectively change the duration,
        because the endTime is not affected. This method changes the endTime, 
        as well as the reminderTime if we have one."""

        # Adjust the reminder first, while we still have the old time.
        try:
            self.reminderTime = self.reminderTime - (self.startTime - dateTime)
        except AttributeError:
                pass

        duration = self.duration
        self.startTime = dateTime
        self.endTime = self.startTime + duration

class CalendarEvent(CalendarEventMixin, Notes.Note):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/calendar/CalendarEvent"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super (CalendarEvent, self).__init__(name, parent, kind, view)
        self.participants = []

class Location(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/calendar/Location"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super (Location, self).__init__(name, parent, kind, view)

    def __str__ (self):
        """
          User readable string version of this Location
        """
        if self.isStale():
            return super(Location, self).__str__()
            # Stale items can't access their attributes
        return self.getItemDisplayName ()

    def getLocation (cls, view, locationName):
        """
          Factory Method for getting a Location.

          Lookup or create a Location based on the supplied name string.
        If a matching Location object is found in the repository, it
        is returned.  If there is no match, then a new item is created
        and returned.  
        @param locationName: name of the Location
        @type locationName: C{String}
        @return: C{Location} created or found
        """
        # make sure the locationName looks reasonable
        assert locationName, "Invalid locationName passed to getLocation factory"

        # get all Location objects whose displayName match the param
        import repository.item.Query
        k = view.findPath(Location.myKindPath)
        its = repository.item.Query.KindQuery(recursive=False).run([k])
        locQuery = [ i for i in its if i.displayName == locationName ]

##         locQuery = view.findPath('//Queries/calendarLocationQuery')
##         if locQuery is None:
##             queryString = u'for i in "//parcels/osaf/contentmodel/calendar/Location" \
##                       where i.displayName == $0'
##             p = view.findPath('//Queries')
##             k = view.findPath('//Schema/Core/Query')
##             locQuery = Query.Query ('calendarLocationQuery', p, k, queryString)
##         locQuery.args["$0"] = ( locationName, )

        # return the first match found, if any
        for firstSpot in locQuery:
            return firstSpot

        # make a new Location
        newLocation = Location(view=view)
        newLocation.displayName = locationName
        return newLocation

    getLocation = classmethod (getLocation)

class Calendar(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/calendar/Calendar"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super (Calendar, self).__init__(name, parent, kind, view)

class RecurrencePattern(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/calendar/RecurrencePattern"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super (RecurrencePattern, self).__init__(name, parent, kind, view)
