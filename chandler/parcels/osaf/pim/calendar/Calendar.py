""" Classes used for Calendar parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.pim.calendar"

import application
import repository.query.Query as Query

from application import schema
from osaf.pim.contacts import Contact
from osaf.pim.items import Calculated, ContentItem
from osaf.pim.notes import Note
from osaf.pim.calendar import Recurrence

from repository.schema.Types import TimeZone

from datetime import datetime, time, timedelta
import itertools
import StringIO
import logging

logger = logging.getLogger(__name__)

TIMECHANGES = ('duration', 'startTime', 'anyTime', 'allDay', 'rruleset')

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

class CalendarEventMixin(ContentItem):
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
        Contact,
        displayName="Meeting Organizer",
        inverse=Contact.organizedEvents
    )

    participants = schema.Sequence(
        Contact,
        displayName="Participants",
        inverse=Contact.participatingEvents
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
        self.icalUID = str(self.itsUUID)

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
            if not isinstance(whoFrom, Contact):
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
        elif self.occurrenceFor in (self, None):
            return self
        else:
            return self.occurrenceFor.getMaster()

    def isBetween(self, after=None, before=None):
        #TODO: deal with different sorts of events
        return (before is None or self.startTime <= before) and \
               (after is None or self.endTime >= after)

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
            if self.getFirstInRule() != self:
                rruleset = Recurrence.RecurrenceRuleSet(None, view=self.itsView)
                rruleset.setRuleFromDateUtil(rule)
                self.changeThisAndFuture('rruleset', rruleset)
            else:
                self.rruleset.setRuleFromDateUtil(rule)

    def _cloneEvent(self):
        new = self.copy()
        new._ignoreValueChanges = True
        
        #now get all reference attributes whose inverse has multiple cardinality 
        for attr, val in self.iterAttributeValues(referencesOnly=True):
            # exclude itemCollectionInclusions so generated occurrences don't
            # appear in the collection
            if attr is 'itemCollectionInclusions':
                continue
            inversekind = self.getAttributeAspect(attr, 'type')
            inverse = self.getAttributeAspect(attr, 'otherName')
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

    def getNextOccurrence(self, after=None, before=None):
        """Return the next occurrence for the recurring event self is part of.
        
        If self is the only occurrence, or last occurrence, return None.  Note
        that getNextOccurrence does not have logic to deal with the duration
        of events.
        
        """
        # helper function
        def checkModifications(first, before, nextEvent = None):
            """Look for mods before nextEvent and before, and after "after"."""
            if after is None:
                # isBetween isn't quite what we want if after is None
                def test(mod):
                    return self.startTime < mod.startTime and \
                           (before is None or mod.startTime < before)
            else:
                def test(mod):
                    return mod.isBetween(after, before)
            for mod in first.modifications or []:
                if test(mod):
                    if nextEvent==None:
                        nextEvent = mod
                        # finally, well-ordering requires that we sort by
                        # recurrenceID if startTimes are equal
                    elif mod.startTime <= nextEvent.startTime:
                        if mod.startTime == nextEvent.startTime and \
                           mod.recurrenceID >= nextEvent.recurrenceID:
                            pass #this 
                        else:
                            # check to make sure mod isn't self, wacky things
                            # like that happen when modifications are out of 
                            # order.
                            if after is None and mod == self:
                                pass
                            else:
                                nextEvent = mod
            return nextEvent
        
        # main getNextOccurrence logic
        if self.rruleset is None:
            return None
        else:
            first = self.getFirstInRule()
            # take duration into account if after is set
            if after is not None:
                earliest = after - first.duration
                inc = True
            elif first == self: #recurrenceID means a different thing for first
                earliest = self.startTime 
                inc = False
            else:
                earliest = min(self.recurrenceID, self.startTime)
                inc = False
            while True:
                nextRecurrenceID = self.createDateUtilFromRule().after(earliest,
                                                                       inc)
                if nextRecurrenceID == None or \
                   (before != None and nextRecurrenceID > before):
                    # no more generated occurrences, make sure no modifications
                    # match
                    return checkModifications(first, before)
                                
                # First, see if an occurrence for nextRecurrenceID exists.
                calculated = None
                for occurrence in first.occurrences:
                    if occurrence.recurrenceID == nextRecurrenceID:
                        calculated = occurrence
                        break
                    
                # If no occurrence already exists, create one
                if calculated is None:
                    calculated = self._createOccurrence(nextRecurrenceID)

                # now we have an event calculated from nextRecurrenceID.  It's
                # actual startTime may be too early, or there may be a
                # modification which is even earlier.
                
                if (after == None and calculated.startTime < self.startTime) or\
                   (after != None and not calculated.isBetween(after, before)):
                        # too early, but there may be a later modification
                        mod = checkModifications(first, nextRecurrenceID)
                        if mod is None:
                            earliest = nextRecurrenceID
                            continue
                        else:
                            return mod
                else:
                    final = checkModifications(first, before, calculated)
                    if after is None and final == self:
                        earliest = nextRecurrenceID
                        continue
                    else:
                        return final



    def _generateRule(self, after=None, before=None, onlyGenerated = False):
        """Yield all occurrences in this rule."""
        event = first = self.getFirstInRule()
        if not first.isBetween(after, before):
            event = first.getNextOccurrence(after, before)        
        while event is not None:
            if event.isBetween(after, before):
                if event.isGenerated or not onlyGenerated:
                    yield event
            # isBetween really means AFTER here
            elif event.isBetween(after=before):
                break
            
            event = event.getNextOccurrence()

            # does this ever happen?
            if event is not None and event.occurrenceFor != first:
                break

    def _getFirstGeneratedOccurrence(self, create=False):
        """Return the first generated occurrence or None.
        
        If create is True, create an occurrence if possible.
        
        """
        if self.rruleset == None: return None
        
        first = self.getFirstInRule()
        if first != self: return first._getFirstGeneratedOccurrence(create)

        # make sure recurrenceID gets set for all masters
        if self.recurrenceID is None:
            self.recurrenceID = self.startTime

        if create:
            iter = self._generateRule()
        else:
            if self.occurrences == None:
                return None
            iter = _sortEvents(self.occurrences)
        for occurrence in iter:
            if occurrence.isGenerated:
                return occurrence
        # no generated occurrences
        return None

    def getOccurrencesBetween(self, after, before, onlyGenerated = False):
        """Return a list of events ordered by startTime.
        
        Get events starting on or before "before", ending on or after "after".
        Generate any events needing generating.
                
        """     
        master = self.getMaster()

        if not master.hasLocalAttributeValue('rruleset'):
            if onlyGenerated:
                return[]
            if master.isBetween(after, before):
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
        if index == -1:
            mods = mods[-1:] # no mods start before after
        elif index == 0:
            pass
        else:
            mods = mods[index - 1:]
##        logger.debug("generating occurrences for %s, after: %s, "
##                     "before: %s, mods: %s" % (self, after,before,mods))
        occurrences = []
        for mod in mods:
            occurrences.extend(mod._generateRule(after, before, onlyGenerated))
        return occurrences

    def getRecurrenceID(self, recurrenceID):
        """Get or create the item matching recurrenceID, or None."""
        # first look through modifications and occurrences
        for mod in self.getMaster().modifications or []:
            if mod.modifies == 'this':
                if mod.recurrenceID == recurrenceID:
                    return mod
            elif mod.modifies == 'thisandfuture':
                for occurrence in mod.occurrences or []:
                    if occurrence.recurrenceID == recurrenceID:
                        return occurrence

        # look through master's occurrences
        for occurrence in self.getMaster().occurrences:
            if occurrence.recurrenceID == recurrenceID:
                return occurrence

        # no existing matches, see if one can be generated:
        for occurrence in self.getOccurrencesBetween(recurrenceID,recurrenceID):
            if occurrence.recurrenceID == recurrenceID:
                return occurrence

        # no match
        return None

    def _movePreviousRuleEnd(self):
        """Make sure the previous rule doesn't recreate or overlap with self."""
        newend = min(self.startTime, self.recurrenceID) - timedelta(minutes=1)
        master = self.getMaster()
        
        # determine previousMod
        previousMod = master# default value
        if master.hasLocalAttributeValue('modifications'):
            startBefore = min(self.startTime, self.getFirstInRule().startTime)
            
            for modification in _sortEvents(master.modifications, reverse=True):
                if modification.modifies == 'thisandfuture':
                    if modification.startTime < startBefore:
                        previousMod = modification
                        break
        
        #change the rule, onValueChanged will trigger cleanRule for previouMod
        for rule in previousMod.rruleset.getAttributeValue('rrules',default=[]):
            if not rule.hasLocalAttributeValue('until') or \
               rule.calculatedUntil() > newend:
                rule.until = newend
                rule.untilIsDate = False
            previousMod.rruleset.rdates = [rdate for rdate in \
                   previousMod.rruleset.getAttributeValue('rdates', default=[])\
                   if rdate > newend]

    def _makeGeneralChange(self):
        """Do everything that should happen for any change call."""
        master = self.getMaster()
        if master.hasLocalAttributeValue('itemCollectionInclusions'):
            self.itemCollectionInclusions = master.itemCollectionInclusions
        self.isGenerated = False
                           
    def changeThisAndFuture(self, attr=None, value=None):
        """Modify this and all future events."""

        master = self.getMaster()
        first = self.getFirstInRule()
        self._ignoreValueChanges = True
        
        setattr(self, attr, value)
        
        def makeThisAndFutureMod():
            self.modifies='thisandfuture'
            self.occurrenceFor = self
            if attr is not 'rruleset':
                self.rruleset = self.rruleset.copy(cloudAlias='copying')
            self._makeGeneralChange()
            self.modificationFor = master
            self.modificationRecurrenceID = self.startTime
            
        def propagateChange(modification, changer=None):
            changer = changer or self
            if modification.startTime >= changer.startTime:
                # future 'this' modifications in master should move to self
                if modification.modifies == 'this':
                    modification.modificationFor = changer
                    modification.occurrenceFor = changer
                # future 'thisandfuture' mods should have setattr called
                elif modification.modifies == 'thisandfuture':
                    modification._deleteGeneratedOccurrences()
                    occurrences = modification.occurrences
                    if changer.occurrenceFor is None:
                        occurrences = itertools.chain(occurrences, [changer])
                    for event in occurrences:
                        event._ignoreValueChanges = True
                        # not clear what should be done with differently
                        # stamped items when applying THISANDFUTURE. For now,
                        # low priority edge case, ignoring non-matching changes.
                        if event.itsKind.hasAttribute(attr):
                            setattr(event, attr, value)
                        if event is not self:
                            del event._ignoreValueChanges
                    modification._getFirstGeneratedOccurrence(True)
                    
            # move first's THIS modifications to self if first isn't master
            if modification == first and first != master and \
               modification.hasLocalAttributeValue('modifications'):
                for mod in modification.modifications:
                    propagateChange(mod, changer)
                            
        # determine what type of change to make
        if attr in TIMECHANGES: # time related, thus a destructive change
            self.cleanFuture()
            if self == master: # self is master, nothing to do
                pass
            elif self.modifies is 'thisandfuture':
                self._movePreviousRuleEnd()
            elif self.isGenerated:
                makeThisAndFutureMod()
                self._movePreviousRuleEnd()
            elif self.modificationFor is not None:# changing 'this' modification
                if self.recurrenceID == first.startTime:
                    self.modifies = 'thisandfuture'
                    if first == master: # replacing master
                        self.modificationFor = None
                    else:
                        self.modificationFor = master
                        self._movePreviousRuleEnd()
                    self.occurrenceFor = self
                    self.modificationRecurrenceID = self.startTime
                    first._ignoreValueChanges = True
                    first.delete()
                else:
                    makeThisAndFutureMod()
                    self._movePreviousRuleEnd()
        else: # not time related, propagate changes forward
            if self.modifies is 'this' and self.modificationFor is not None:
                #preserve self as a THIS modification
                if self.recurrenceID != first.startTime:
                    # create a new event, cloned from first, make it a
                    # thisandfuture modification with self overriding it
                    newfirst = first._cloneEvent()
                    newfirst._ignoreValueChanges = True
                    newfirst.rruleset = self.rruleset.copy(cloudAlias='copying')
                    newfirst.startTime = self.recurrenceID
                    newfirst.occurrenceFor = None #self overrides newfirst
                    newfirst.modificationFor = master
                    newfirst.modifies = 'thisandfuture'
                    newfirst._makeGeneralChange()
                    self.occurrenceFor = self.modificationFor = newfirst
                    # move THIS modifications after self to newfirst
                    if first.hasLocalAttributeValue('modifications'):
                        for mod in first.modifications:
                            if mod.modifies == 'this':
                                if mod.recurrenceID > newfirst.startTime:
                                    mod.occurrenceFor = newfirst
                                    mod.modificationFor = newfirst
                    self._movePreviousRuleEnd()
                    del newfirst._ignoreValueChanges

                for modification in master.modifications:
                    propagateChange(modification, self.occurrenceFor)
                    
            else:
                if self.isGenerated:
                    makeThisAndFutureMod()
                    self._movePreviousRuleEnd()
                    
                for modification in master.modifications:
                    propagateChange(modification)

        self._getFirstGeneratedOccurrence()

        del self._ignoreValueChanges

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
                    newfirst = backup._cloneEvent()
                    newfirst._ignoreValueChanges = True
                    newfirst.startTime = self.modificationRecurrenceID or \
                                         self.recurrenceID
                    if self.hasLocalAttributeValue('modifications'):
                        for mod in self.modifications:
                            mod.modificationFor = newfirst
                    if self.hasLocalAttributeValue('occurrences'):
                        for occ in self.occurrences:
                            occ.occurrenceFor = newfirst
                    newfirst.occurrenceFor = None #self overrides newfirst
                    newfirst.modificationFor = self.modificationFor
                    newfirst.modifies = 'thisandfuture'
                    # Unnecessary when we switch endTime->duration
                    newfirst.duration = backup.duration
                    self.occurrenceFor = self.modificationFor = newfirst
                    self._makeGeneralChange()
                    self.modifies = 'this'
                    self.recurrenceID = newfirst.startTime
                    del self.modificationRecurrenceID
                    del newfirst._ignoreValueChanges
                # if backup is None, allow the change to stand, applying just
                # to self.  This relies on _getFirstGeneratedOccurrence() always
                # being called.  Still, make sure changes to startTime change
                # modificationRecurrenceID
                else:
                    self.modificationRecurrenceID = self.startTime

            else:
                self.modificationFor = first
                self._makeGeneralChange()
                self.modifies = 'this'
                self._getFirstGeneratedOccurrence(True)
        if attr is not None:
            setattr(self, attr, value)


    def onValueChanged(self, name):
        # allow initialization code to avoid triggering onValueChanged
        if getattr(self, '_ignoreValueChanges', False) or self.rruleset is None:
            return
        # avoid infinite loops
        if name == "rruleset": 
            logger.debug("just set rruleset")
            gen = self._getFirstGeneratedOccurrence(True)
            if gen:
                logger.debug("got first generated occurrence, %s" % gen.serializeMods().getvalue())

            # make sure masters get modificationRecurrenceID set
            if self == self.getFirstInRule():
                self.modificationRecurrenceID = self.startTime
                self.recurrenceID = self.startTime
            # this kludge should be replaced with the new domain attribute aspect
##        elif name not in """modifications modificationFor occurrences
##                          occurrenceFor modifies isGenerated recurrenceID
##                          _ignoreValueChanges modificationRecurrenceID queries
##                          contentsOwner TPBSelectedItemOwner TPBDetailItemOwner
##                          itemCollectionInclusions
##                          """.split():
        # this won't work with stamping, temporary solution to allow testing
        if name in """displayName startTime endTime location body lastModified
                   """.split():
            logger.debug("about to changeThis in onValueChanged(name=%s) for %s" % (name, str(self)))
            logger.debug("value is: %s" % getattr(self, name))
            self.changeThis()

    def _deleteGeneratedOccurrences(self):
        first = self.getFirstInRule()
        for event in first.occurrences:
            if event.isGenerated:
                # don't let deletion result in spurious onValueChanged calls
                event._ignoreValueChanges = True
                event.delete()
                
    def cleanRule(self):
        """Delete generated occurrences in the current rule, create a backup."""
        first = self.getFirstInRule()
        self._deleteGeneratedOccurrences()
        if first.hasLocalAttributeValue('modifications'):
            for mod in first.modifications:
                if mod.modifies == 'this':
                    # this won't work for complicated rrulesets
                    if mod.recurrenceID > first.rruleset.rrules.first().calculatedUntil() \
                       and mod != first:
                        mod._ignoreValueChanges = True
                        mod.delete()
                    
        # create a backup
        first._getFirstGeneratedOccurrence(True)

    def removeFuture(self):
        """Delete self and all future occurrences and modifications."""
        pass

    def _deleteThisAndFutureModification(self):
        """Remove 'thisandfuture' modification and all its occurrences."""
        for event in self.occurrences:
            if event == self: #don't delete self quite yet
                continue
            event._ignoreValueChanges = True
            event.delete(recursive=True)

        self.rruleset._ignoreValueChanges = True
        self.rruleset.delete(recursive=True)
        self._ignoreValueChanges = True
        self.delete(recursive=True)

    def cleanFuture(self):
        """Delete all future occurrences and modifications."""

        def deleteLater(item):
            if item.startTime > self.startTime: 
                item._ignoreValueChanges = True
                item.delete()
                
        master = self.getMaster()
        for mod in master.modifications or []:
            if mod.modifies == 'thisandfuture':
                if mod.startTime > self.startTime:
                        mod._deleteThisAndFutureModification()
                else:
                    for event in mod.occurrences or []:
                        deleteLater(event)
        for event in master.occurrences:
            deleteLater(event)
                    
        self._getFirstGeneratedOccurrence(True)
        
    def removeRecurrence(self):
        master = self.getMaster()
        if master.rruleset is not None:
            del master.rruleset
        master.cleanFuture()
   
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

    def serializeMods(self, level=0, buf=None):
        if buf is None:
            buf = StringIO.StringIO()
        pad = "  " * level
        if level:
            buf.write(pad + "modification.  modifies: %s modificationFor: %s\n"\
                             % (self.modifies, self.modificationFor.startTime))
        buf.write(pad + "event is: %s %s\n" % (self.displayName, self.startTime))
        if self.modifies is 'thisandfuture' or self.modificationFor is None:
            try:
                buf.write(pad + "until: %s\n" % list(self.rruleset.rrules)[0].until)
            except:
                pass
        buf.write('\n')
        if self.hasLocalAttributeValue('modifications'):
            for mod in self.modifications:
                mod.serializeMods(level + 1, buf)
        return buf

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

class CalendarEvent(CalendarEventMixin, Note):
    """
    @note: CalendarEvent should maybe have a 'Timezone' attribute.
    @note: Do we want to have 'Duration' as a derived attribute on Calendar Event?
    @note: Do we want to have a Boolean 'AllDay' attribute, to indicate that an event is an all day event? Or should we instead have the 'startTime' and 'endTime' attributes be 'RelativeDateTime' instead of 'DateTime', so that they can store all day values like '14 June 2004' as well as specific time values like '4:05pm 14 June 2004'?
    """
    schema.kindInfo(displayName="Calendar Event")

    def __init__(self, name=None, parent=None, kind=None, view=None, **kw):
        kw.setdefault('participants',[])
        super (CalendarEvent, self).__init__(name, parent, kind, view, **kw)


class Calendar(ContentItem):
    """
    @note: Calendar should have an attribute that points to all the Calendar Events.
    @note: Calendar should maybe have a 'Timezone' attribute.
    """
    
    schema.kindInfo(displayName="Calendar", displayAttribute="displayName")


class Location(ContentItem):
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
##             queryString = u'for i in "//parcels/osaf/pim/calendar/Location" \
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

class RecurrencePattern(ContentItem):
    """
    @note: RecurrencePattern is still a placeholder, and might be general enough to live with PimSchema. RecurrencePattern should have an attribute that points to a CalendarEvent.
    """
    
    schema.kindInfo(displayName="Recurrence Pattern")

