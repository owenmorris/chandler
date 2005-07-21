""" Classes used for Calendar parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.contentmodel.calendar"

import application
import repository.query.Query as Query

from application import schema

from osaf.contentmodel import ContentModel
from osaf.contentmodel import Notes
from osaf.contentmodel.ContentModel import Calculated
from osaf.contentmodel.contacts import Contacts
from osaf.contentmodel.calendar import Recurrence

from repository.schema.Types import TimeZone

from datetime import datetime, time, timedelta

class TimeTransparencyEnum(schema.Enumeration):
    """Time Transparency Enum

    The iCalendar values for Time Transparency are slightly different. We should consider making our values match the iCalendar ones, or be a superset of them.  Mitch suggested that a 'cancelled' value would be a useful extension.

    It'd be nice to not maintain the transparency choices separately from the enum values"""
    
    schema.kindInfo(
        displayName="Time Transparency"
    )
    values="confirmed", "tentative", "fyi"

class ModificationEnum(schema.Enumeration):
    schema.kindInfo(displayName="Modification")
    values="this", "thisandfuture"

def _sortEvents(eventlist, reverse=False):
    """Helper function for working with events."""
    def cmpEventStarts(event1, event2):
        return cmp(event1.startTime, event2.startTime)
    eventlist = list(eventlist)
    eventlist.sort(cmp=cmpEventStarts)
    if reverse: eventlist.reverse()
    return eventlist

class CalendarEventMixin(ContentModel.ContentItem):
    """
    This is the set of CalendarEvent-specific attributes. This Kind is 'mixed
    in' to others kinds to create Kinds that can be instantiated.

      Calendar Event Mixin is the bag of Event-specific attributes.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    schema.kindInfo(
        displayName="Calendar Event Mixin Kind"
    )

    startTime = schema.One(
        schema.DateTime,
        displayName="Start-Time/Do-on",
        doc="For items that represent *only* Tasks, this attribute serves as "
            "the 'Do-on' attribute. For items that represent only Calendar "
            "Events, this attribute serves as the 'Start-time' attribute. "
            "I think this unified attribute may match the way iCalendar "
            "models these attributes, but we should check to make sure. "
            "- Brian"
    )

    recurrenceID = schema.One(
        schema.DateTime,
        displayName="Recurrence ID",
        defaultValue=None,
        doc="Date time this occurrence was originally scheduled. startTime and "
            "recurrenceID for everything but modifications"
    )

    endTime = schema.One(
        schema.DateTime,
        displayName="End-Time"
    )

    allDay = schema.One(
        schema.Boolean,
        displayName="All-Day",
        initialValue=False
    )

    anyTime = schema.One(
        schema.Boolean,
        displayName="Any-Time",
        initialValue=True
    )

    transparency = schema.One(
        TimeTransparencyEnum,
        displayName="Time Transparency",
        initialValue="confirmed"
    )

    location = schema.One(
        "Location",
        displayName="location",
        doc="We might want to think about having Location be just a 'String', "
            "rather than a reference to a 'Location' item."
     )

    reminderTime = schema.One(
        schema.DateTime,
        displayName="ReminderTime",
        doc="This may not be general enough"
    )

    rruleset = schema.One(
        Recurrence.RecurrenceRuleSet,
        displayName="Recurrence Rule Set",
        doc="Rule or rules for when future occurrences take place",
        inverse=Recurrence.RecurrenceRuleSet.events,
        defaultValue=None
    )

    organizer = schema.One(
        Contacts.Contact,
        displayName="Meeting Organizer",
        inverse=Contacts.Contact.organizedEvents
    )

    participants = schema.Sequence(
        Contacts.Contact,
        displayName="Participants",
        inverse=Contacts.Contact.participatingEvents
    )

    icalUID = schema.One(
        schema.String,
        displayName="UID",
        doc="iCalendar uses arbitrary strings for UIDs, not UUIDs.  We can "
            "set UID to a string representation of UUID, but we need to be "
            "able to import iCalendar events with arbitrary UIDs."
    )

    modifies = schema.One(
        ModificationEnum,
        displayName="Modifies how",
        defaultValue=None,
        doc = "Describes whether a modification applies to future events, or "
              "just one event"
    )
    
    modifications = schema.Sequence(
        "CalendarEventMixin",
        displayName="Events modifying recurrence",
        defaultValue=None,
        inverse="modificationFor"
    )
    
    modificationFor = schema.One(
        "CalendarEventMixin",
        displayName="Modification for",
        defaultValue=None,
        inverse="modifications"
    )

    modificationRecurrenceID = schema.One(
        schema.DateTime,
        displayName="Start-Time backup",
        defaultValue=None,
        doc="If a modification's startTime is changed, none of its generated"
            "occurrences will backup startTime, so modifications must persist"
            "a backup for startTime"
    )

    occurrences = schema.Sequence(
        "CalendarEventMixin",
        displayName="Occurrences",
        defaultValue=None,
        inverse="occurrenceFor"
    )
    
    occurrenceFor = schema.One(
        "CalendarEventMixin",
        displayName="Occurrence for",
        defaultValue=None,
        inverse="occurrences"
    )

    isGenerated = schema.One(
        schema.Boolean,
        displayName="Generated",
        defaultValue=False
    )
    
    calendar = schema.Sequence(
        "Calendar",
        displayName="Calendar",
        doc="Is this used?"
    )

    resources = schema.Sequence(
        schema.String,
        displayName="Resources",
        doc="Is this used?"
    )

    schema.addClouds(
        copying = schema.Cloud(organizer,location,rruleset,participants),
        sharing = schema.Cloud(
            startTime, endTime, allDay, location, anyTime,
            reminderTime, transparency,
            byCloud = [organizer,participants]
        )
    )

    # Redirections

    who = schema.One(redirectTo="participants")
    whoFrom = schema.One(redirectTo="organizer")
    about = schema.One(redirectTo="displayName")
    date = schema.One(redirectTo="startTime")

    def __init__(self, name=None, parent=None, kind=None, view=None, **kw):
        super(CalendarEventMixin, self).__init__(name, parent, kind, view, **kw)
        self.occurrenceFor = self

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
        
        self.occurrenceFor = self
        
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
            return self.getEffectiveEndTime() - self.getEffectiveStartTime()
        else:
            return None

    def SetDuration(self, timeDelta):
        """Set duration of event, expects value to be a timedelta
        
        endTime is updated based on the new duration, startTime remains fixed
        """
        if (self.startTime is not None):
            self.endTime = self.getEffectiveStartTime() + timeDelta

    duration = Calculated(schema.TimeDelta, displayName="duration",
                          fget=GetDuration, fset=SetDuration,
                          doc="Duration, computed from effective start & "
                              "end times. Observes all-day & any-time.")

    def getEffectiveStartTime(self):
        """ 
        Get the effective start time of this event: ignore the time
        component of the startTime attribute if this is an allDay 
        or anyTime event.
        """
        # If startTime's time is invalid, ignore it.
        if self.anyTime or self.allDay:
            result = datetime.combine(self.startTime, time(0))
        else:
            result = self.startTime
        return result
    
    def getEffectiveEndTime(self):
        """ 
        Get the effective end time of this event: ignore the time
        component of the endTime attribute if this is an allDay 
        or anyTime event.
        """
        # If endTime's time is invalid, ignore it.
        if self.anyTime or self.allDay:
            result = datetime.combine(self.endTime, time(0))
        else:
            result = self.endTime
        return result
        
    def GetReminderDelta(self):
        """ Returns the difference between startTime and reminderTime, a timedelta """
        try:
            return self.reminderTime - self.getEffectiveStartTime()
        except AttributeError:
            return None
   
    def SetReminderDelta(self, reminderDelta):
        effectiveStart = self.getEffectiveStartTime()
        if effectiveStart is not None:
            if reminderDelta is not None:
                self.reminderTime = effectiveStart + reminderDelta
            else:
                try:
                    del self.reminderTime
                except AttributeError:
                    pass

    reminderDelta = Calculated(schema.TimeDelta,
                               displayName="reminderDelta",
                               fget=GetReminderDelta, fset=SetReminderDelta,
                               doc="reminderDelta: the amount of time before " \
                                   "the event that we want a reminder")
    
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

    # begin recurrence related methods

    def getFirstInRule(self):
        """Return the nearest thisandfuture modifications or master."""
        if self.modificationFor != None:
            if self.modifies == 'thisandfuture':
                return self
            else:
                return self.modificationFor
        elif self.occurrenceFor in (self, None):
            # could be None if a master's first date has a "this" modification
            return self
        else:
            return self.occurrenceFor

    def getMaster(self):
        """Return the master event in modifications or occurrences."""
        if self.modificationFor is not None:
            return self.modificationFor.getMaster()
        elif self.occurrenceFor is not self:
            return self.occurrenceFor.getMaster()
        else:
            return self

    def createDateUtilFromRule(self):
        """Construct a dateutil.rrule.rruleset from self.rruleset.
        
        The resulting rruleset will apply only to the modification or master
        for which self is an occurrence or modification, for instance, if an
        event has a thisandfuture modification, and self is an occurrence for
        that modification, the returned rule will be the modification's rule,
        not the master's rule.
        
        """
        if self.getFirstInRule() != self:
            return self.getFirstInRule().createDateUtilFromRule()
        else:
            dtstart = self.getEffectiveStartTime()
            set = self.rruleset.createDateUtilFromRule(dtstart)
            return self.rruleset.createDateUtilFromRule(dtstart)

    def setRuleFromDateUtil(self, rule):
        """Set self.rruleset from rule.  Rule may be an rrule or rruleset."""
        if self.rruleset is None:
            ruleItem=Recurrence.RecurrenceRuleSet(None, view=self.itsView)
            ruleItem.setRuleFromDateUtil(rule)
            self.rruleset = ruleItem
        else:
            self.rruleset.setRuleFromDateUtil(rule)

    def _cloneEvent(self):
        new = self.copy()
        new._ignoreValueChanges = True
        first = self.getFirstInRule()
        
        #now get all reference attributes whose inverse has multiple cardinality 
        for attr, val in first.iterAttributeValues(referencesOnly=True):
            inversekind = first.getAttributeAspect(attr, 'type')
            inverse=first.getAttributeAspect(attr, 'otherName')
            if inversekind is not None:
                inverseAttr=inversekind.getAttribute(inverse)
                if inverseAttr.cardinality != 'single':
                    setattr(new, attr, val)
        del new._ignoreValueChanges
        return new

    def _createOccurrence(self, recurrenceID):
        """Generate an occurrence for recurrenceID, return it."""
        first = self.getFirstInRule()
        if first != self:
            return self.getFirstInRule()._createOccurrence(recurrenceID)
        new = self._cloneEvent()
        new._ignoreValueChanges = True
        
        new.isGenerated = True
        new.ChangeStart(recurrenceID)
        new.recurrenceID = new.startTime
        new.occurrenceFor = first        
        new.modificationFor = None
        new.modifies = 'this' # it doesn't work with the rep to make this None
        
        del new._ignoreValueChanges
        return new

    def getNextOccurrence(self, after=None):
        """Return the next occurrence for the recurring event self is part of.
        
        If self is the only occurrence, or last occurrence, return None.
        
        """
        if self.rruleset is None:
            return None
        else:
            after = after or self.startTime
            nextRecurrenceID=self.createDateUtilFromRule().after(after)
            if nextRecurrenceID == None: return None
            # TODO: deal with modifications
            # test if nextRecurrenceID matches a modification that actually
            # occurred before now, if so, get a new recurrenceID
            # find all modifications after startTime and before nextRecurrenceID
            # if any exist, return the first one
            firstInRule = self.getFirstInRule()
            for occurrence in firstInRule.occurrences:
                if occurrence.recurrenceID == nextRecurrenceID:
                    return occurrence
            return self._createOccurrence(nextRecurrenceID)

    def _generateRule(self):
        """Yield all occurrences in this rule."""
        event = first = self.getFirstInRule()
        while event is not None:
            yield event
            event = event.getNextOccurrence()
            if event is not None and event.occurrenceFor != first:
                event = None

    def _getFirstGeneratedOccurrence(self, create=False):
        """Return the first generated occurrence or None.
        
        If create is True, create an occurrence if possible.
        
        """
        if self.rruleset == None: return None
        
        first = self.getFirstInRule()
        if first != self: return first._getFirstGeneratedOccurrence(create)
        
        if create:
            iter = self._generateRule()
        else:
            if self.occurrences == None: return None
            iter = _sortEvents(self.occurrences)
        for occurrence in iter:
            if occurrence.isGenerated: return occurrence
        # no generated occurrences
        return None

    def getOccurrencesBetween(self, after, before):
        """Return a list of events ordered by startTime.
        
        Get events starting on or before "before", ending on or after "after".
        Generate any events needing generating. 
        
        """
        def isBetween(event):
            return event.startTime <= before and event.endTime >= after
                
        master = self.getMaster()

        if not master.hasLocalAttributeValue('rruleset'):
            if isBetween(master):
                return [master]
            else: return []

        mods = [master]
        if master.hasLocalAttributeValue('modifications'):
            mods.extend(mod for mod in master.modifications
                                    if mod.modifies == 'thisandfuture'
                                    and mod.startTime <= before)
        _sortEvents(mods)
        # cut out mods which end before "after"
        index = -1
        for i, mod in enumerate(mods):
            if mod.startTime >= after:
                index = i
                break
        if index == -1: mods = mods[-1:] # no mods start before after
        elif index == 0: pass
        else: mods = mods[index - 1:]
        
        return [e for mod in mods for e in mod._generateRule() if isBetween(e)]
    
    def changeThis(self, attr=None, value=None):
        """Make this event a modification, don't modify future events.
        
        Without arguments, change self appropriately to make it a THIS 
        modification.
        
        One edge case does have an effect on other events.  Moving an event's
        startTime so it begins in a different rule will ........FIXME
        
        """
        if self.modifies is 'this' and self.modificationFor is not None:
            pass
        elif self.rruleset is not None:
            first = self.getFirstInRule()
            if first == self:
                # self may have already been changed, find a backup to copy
                backup = self._getFirstGeneratedOccurrence()
                if backup is not None:
                    newmaster = backup._cloneEvent()
                    newmaster._ignoreValueChanges = True
                    newmaster.startTime = self.modificationRecurrenceID or \
                                          self.recurrenceID
                    if self.hasLocalAttributeValue('modifications'):
                        for mod in self.modifications:
                            mod.modificationFor = newmaster
                    if self.hasLocalAttributeValue('occurrences'):
                        for occ in self.occurrences:
                            occ.occurrenceFor = newmaster
                    newmaster.occurrenceFor = None #self overrides newmaster
                    self.occurrenceFor = newmaster
                    self.isGenerated = False
                    self.modifies = 'this'
                    self.recurrenceID = newmaster.startTime
                    del newmaster._ignoreValueChanges
                # if backup is None, allow the change to stand, applying just
                # to self.  This relies on _getFirstGeneratedOccurrence() always
                # being called.

            else:
                self.modificationFor = first
                self.isGenerated = False
                self.modifies = 'this'
                self._getFirstGeneratedOccurrence(True)
        if attr is not None:
            setattr(self, attr, value)

    def changeThisAndFuture(self, attr=None, value=None):
        """Modify this and all future events."""
        self._ignoreValueChanges = True
        self.modifies='thisandfuture'
        master = self.getMaster()
        self.occurrenceFor = self
        if attr is not 'rruleset':
            self.rruleset = self.rruleset.copy(cloudAlias='copying')
        self.isGenerated = False

        setattr(self, attr, value)
        
        # make sure the previous rule doesn't recreate self, and don't let
        # the previous rule overlap with this new rule
        previousRuleEnd = min(self.startTime, self.recurrenceID) - \
                          timedelta(minutes=1)

        previousMod = master # default value
        if master.hasLocalAttributeValue('modifications'):
            startBefore = min(self.startTime, self.getFirstInRule().startTime)
            for modification in _sortEvents(master.modifications, reverse=True):
                if modification.modifies == 'thisandfuture':
                    if modification.startTime < startBefore:
                        previousMod = modification
                        break
        
        for rule in previousMod.rruleset.getAttributeValue('rrules', default=[]):
            if not rule.hasLocalAttributeValue('until') or \
                                                 rule.until > previousRuleEnd:
                rule.until = previousRuleEnd
            previousMod.rruleset.rdates=[rdate for rdate in \
                   master.rruleset.getAttributeValue('rdates', default=[]) \
                   if rdate > previousRuleEnd]

        self.modificationFor = master
        self.modificationRecurrenceID = self.startTime
        
        if attr in ('duration', 'startTime', 'anyTime', 'allDay', 'rruleset'):
            self._cleanFuture()
        else:
            for modification in master.modifications:
                if modification.startTime > self.startTime:
                    if modification.modifies == 'this':
                        # some this modifications in master should move to self
                        modification.modificationFor = self
                    elif modification.modifies == 'thisandfuture':
                        modification.cleanRule()
                        for event in modification.occurrences:
                            event._ignoreValueChanges = True
                            # not clear what should be done with differently
                            # stamped items when applying THISANDFUTURE. Low
                            # priority edge case, ignoring non-matching changes.
                            if event.itsKind.hasAttribute(attr):
                                setattr(event, attr, value)
                            del event._ignoreValueChanges
                        for event in modification.occurrences:
                            event._ignoreValueChanges = True
                            if event.itsKind.hasAttribute(attr):
                                setattr(event, attr, value)
                            del event._ignoreValueChanges
                        modification._getFirstGeneratedOccurrence(True)
            # we may have invalidated some of master's occurrences
            master.cleanRule() 
            master._getFirstGeneratedOccurrence(True)

            self._getFirstGeneratedOccurrence(True)

        del self._ignoreValueChanges

    def onValueChanged(self, name):
        # allow initialization code to avoid triggering onValueChanged
        if getattr(self, '_ignoreValueChanges', False):
            return
        # avoid infinite loops
        if name == "rruleset": 
            self._getFirstGeneratedOccurrence(True)
        elif name not in """modifications modificationFor occurrences
                          occurrenceFor modifies isGenerated recurrenceID
                          _ignoreValueChanges""".split():
            self.changeThis()

    def cleanRule(self):
        """Delete generated occurrences and invalidated modifications.
        
        Only applies to the current rule, also see _cleanFuture.
                
        """
        first = self.getFirstInRule()
        rruleset = []
        if first.hasLocalAttributeValue('modifications'):
            rruleset = self.createDateUtilFromRule()
        for event in first.occurrences:
            if event.isGenerated:
                # don't let deletion result in spurious onValueChanged calls
                event._ignoreValueChanges = True
                event.delete()
            elif event.startTime > self.startTime: # modifications after self
                if event.recurrenceID not in rruleset:
                    event._ignoreValueChanges = True
                    event.delete()
                
        first._getFirstGeneratedOccurrence(True)
        

    def _cleanFuture(self):
        """Delete all future occurrences and modifications."""
        for event in self.getMaster().occurrences:
            if event.startTime > self.startTime:
                # don't let deletion result in spurious onValueChanged calls
                event._ignoreValueChanges = True
                event.delete()
        self._getFirstGeneratedOccurrence(True)
                
    def isCustomRule(self):
        """Determine if self.rruleset represents a custom rule.
        
        For the moment, simple daily, weekly, or monthly repeating events, 
        optionally with an UNTIL date, or the abscence of a rule, are the only
        rules which are not custom.
        
        """
        if self.hasLocalAttributeValue('rruleset'):
            return self.rruleset.isCustomRule()
        else: return False
    
    def getCustomDescription(self):
        """Return a string describing custom rules."""
        if self.hasLocalAttributeValue('rruleset'):
            return self.rruleset.getCustomDescription()
        else: return ''
        
    def isProxy(self):
        """Is this a proxy of an event?"""
        return False
    
def getProxy(obj):
    return OccurrenceProxy(obj)

class OccurrenceProxy(object):
    proxyAttributes = 'proxiedItem', 'currentlyModifying'
    
    def __init__(self, item):
        self.proxiedItem = item
        self.currentlyModifying = None
    
    def __eq__(self, other):
        return self.proxiedItem == other
        
    def __getattr__(self, name):
        return getattr(self.proxiedItem, name)
        
    def __setattr__(self, name, value):
        if name in self.proxyAttributes:
            object.__setattr__(self, name, value)
        else:
            setattr(self.proxiedItem, name, value)
    
    def isProxy(self):
        return True

class CalendarEvent(CalendarEventMixin, Notes.Note):
    """
    @note: CalendarEvent should maybe have a 'Timezone' attribute.
    @note: Do we want to have 'Duration' as a derived attribute on Calendar Event?
    @note: Do we want to have a Boolean 'AllDay' attribute, to indicate that an event is an all day event? Or should we instead have the 'startTime' and 'endTime' attributes be 'RelativeDateTime' instead of 'DateTime', so that they can store all day values like '14 June 2004' as well as specific time values like '4:05pm 14 June 2004'?
    """
    schema.kindInfo(displayName="Calendar Event")

    def __init__(self, name=None, parent=None, kind=None, view=None, **kw):
        kw.setdefault('participants',[])
        super (CalendarEvent, self).__init__(name, parent, kind, view, **kw)


class Calendar(ContentModel.ContentItem):
    """
    @note: Calendar should have an attribute that points to all the Calendar Events.
    @note: Calendar should maybe have a 'Timezone' attribute.
    """
    
    schema.kindInfo(displayName="Calendar", displayAttribute="displayName")


class Location(ContentModel.ContentItem):
    """
       @note: Location may not be calendar specific.
    """
    
    schema.kindInfo(displayName="Location", displayAttribute="displayName")

    eventsAtLocation = schema.Sequence(
        CalendarEventMixin,
        displayName="Calendar Events",
        inverse=CalendarEventMixin.location
    )

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
        its = Location.iterItems(view, exact=True)
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

class RecurrencePattern(ContentModel.ContentItem):
    """
    @note: RecurrencePattern is still a placeholder, and might be general enough to live with PimSchema. RecurrencePattern should have an attribute that points to a CalendarEvent.
    """
    
    schema.kindInfo(displayName="Recurrence Pattern")

