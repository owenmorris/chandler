""" Classes used for Calendar parcel kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.pim.calendar"

import application

from application import schema
from osaf.pim.contacts import Contact
from osaf.pim.items import Calculated, ContentItem
from osaf.pim.notes import Note
from osaf.pim.calendar import Recurrence

import wx

from osaf.pim.calendar.TimeZone import coerceTimeZone
from PyICU import ICUtzinfo
from datetime import datetime, time, timedelta
import itertools
import StringIO
import logging

from i18n import OSAFMessageFactory as _

logger = logging.getLogger(__name__)
DEBUG = logger.getEffectiveLevel() <= logging.DEBUG

#XXX [i18n] this file may require further localization of displayName attributes

class TimeTransparencyEnum(schema.Enumeration):
    """
    Time Transparency Enum

    The iCalendar values for Time Transparency are slightly different. We should consider making our values match the iCalendar ones, or be a superset of them.  Mitch suggested that a 'cancelled' value would be a useful extension.

    It'd be nice to not maintain the transparency choices separately from the enum values"""
    
    schema.kindInfo(
        displayName=u"Time Transparency"
    )
    values="confirmed", "tentative", "fyi"

class ModificationEnum(schema.Enumeration):
    schema.kindInfo(displayName=u"Modification")
    values="this", "thisandfuture"


def removeTypeError(f):
    def g(dt1, dt2):
        naive1 = (dt1.tzinfo is None)
        naive2 = (dt2.tzinfo is None)
        
        if naive1 != naive2:
            if naive1:
                dt2 = dt2.replace(tzinfo=None)
            else:
                dt1 = dt1.replace(tzinfo=None)
        return f(dt1, dt2)
    return g

__opFunctions = {
    'cmp': removeTypeError(lambda x, y: cmp(x, y)),
    'max': removeTypeError(lambda x, y: max(x, y)),
    'min': removeTypeError(lambda x, y: min(x, y)),
    '-':   removeTypeError(lambda x, y: x - y),
    '<':   removeTypeError(lambda x, y: x < y),
    '>':   removeTypeError(lambda x, y: x > y),
    '<=':  removeTypeError(lambda x, y: x <= y),
    '>=':  removeTypeError(lambda x, y: x >= y),
    '==':  removeTypeError(lambda x, y: x == y),
    '!=':  removeTypeError(lambda x, y: x != y)
}

def datetimeOp(dt1, operator, dt2):
    """
    This function is a workaround for some issues with
    comparisons of naive and non-naive C{datetimes}. Its usage
    is slightly goofy (but makes diffs easier to read):
    
    If you had in code::
    
        dt1 < dt2
        
    and you weren't sure whether dt1 and dt2 had timezones, you could
    convert this to::
    
       datetimeOp(dt1, '<', dt2)
       
    and not have to deal with the TypeError you'd get in the original code. 
   
    Similar conversions hold for other comparisons, '-', '>', '<=', '>=',
    '==', '!='. Also, there are functions with implied comparison; you can do::
   
       max(dt1, dt2) --> datetimeOp(dt1, 'max', dt2)
      
    and similarly for min, cmp.
    
    For more details (and why this is a kludge), see
    <http://wiki.osafoundation.org/bin/view/Journal/GrantBaillie20050809>
    """
    
    f = __opFunctions.get(operator, None)
    if f is None:
        raise ValueError, "Unrecognized operator '%s'" % (operator)
    return f(dt1, dt2)

def _sortEvents(eventlist, reverse=False):
    """Helper function for working with events."""
    def cmpEventStarts(event1, event2):
        return datetimeOp(event1.startTime, 'cmp', event2.startTime)
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
        displayName=u"Calendar Event Mixin Kind"
    )

    startTime = schema.One(
        schema.DateTime,
        displayName=_(u"Start-Time/Do-on"),
        doc="For items that represent *only* Tasks, this attribute serves as "
            "the 'Do-on' attribute. For items that represent only Calendar "
            "Events, this attribute serves as the 'Start-time' attribute. "
            "I think this unified attribute may match the way iCalendar "
            "models these attributes, but we should check to make sure. "
            "- Brian"
    )

    duration = schema.One(
        schema.TimeDelta, 
        displayName=u"Duration",
        doc="Duration.")

    recurrenceID = schema.One(
        schema.DateTime,
        displayName=u"Recurrence ID",
        defaultValue=None,
        doc="Date time this occurrence was originally scheduled. startTime and "
            "recurrenceID for everything but modifications"
    )

    allDay = schema.One(
        schema.Boolean,
        displayName=u"All-Day",
        initialValue=False
    )

    anyTime = schema.One(
        schema.Boolean,
        displayName=u"Any-Time",
        initialValue=True
    )

    transparency = schema.One(
        TimeTransparencyEnum,
        displayName=u"Time Transparency",
        initialValue="confirmed"
    )

    location = schema.One(
        "Location",
        displayName=_(u"location"),
        doc="We might want to think about having Location be just a 'String', "
            "rather than a reference to a 'Location' item."
     )

    reminderTime = schema.One(
        schema.DateTime,
        displayName=u"ReminderTime",
        doc="This may not be general enough"
    )

    rruleset = schema.One(
        Recurrence.RecurrenceRuleSet,
        displayName=u"Recurrence Rule Set",
        doc="Rule or rules for when future occurrences take place",
        inverse=Recurrence.RecurrenceRuleSet.events,
        defaultValue=None
    )

    organizer = schema.One(
        Contact,
        displayName=_(u"Meeting Organizer"),
        inverse=Contact.organizedEvents
    )

    participants = schema.Sequence(
        Contact,
        displayName=u"Participants",
        inverse=Contact.participatingEvents
    )

    icalUID = schema.One(
        schema.String,
        displayName=u"UID",
        doc="iCalendar uses arbitrary strings for UIDs, not UUIDs.  We can "
            "set UID to a string representation of UUID, but we need to be "
            "able to import iCalendar events with arbitrary UIDs."
    )

    icalUIDMap = schema.One(
        otherName = "items",
        doc = "For performance we maintain a ref collection mapping iCalendar "
              "UIDs to events, making lookup by UID quick."
    )

    modifies = schema.One(
        ModificationEnum,
        displayName=u"Modifies how",
        defaultValue=None,
        doc = "Describes whether a modification applies to future events, or "
              "just one event"
    )
    
    modifications = schema.Sequence(
        "CalendarEventMixin",
        displayName=u"Events modifying recurrence",
        defaultValue=None,
        inverse="modificationFor"
    )
    
    modificationFor = schema.One(
        "CalendarEventMixin",
        displayName=u"Modification for",
        defaultValue=None,
        inverse="modifications"
    )

    modificationRecurrenceID = schema.One(
        schema.DateTime,
        displayName=u"Start-Time backup",
        defaultValue=None,
        doc="If a modification's startTime is changed, none of its generated"
            "occurrences will backup startTime, so modifications must persist"
            "a backup for startTime"
    )

    occurrences = schema.Sequence(
        "CalendarEventMixin",
        displayName=u"Occurrences",
        defaultValue=None,
        inverse="occurrenceFor"
    )
    
    occurrenceFor = schema.One(
        "CalendarEventMixin",
        displayName=u"Occurrence for",
        defaultValue=None,
        inverse="occurrences"
    )

    isGenerated = schema.One(
        schema.Boolean,
        displayName=u"Generated",
        defaultValue=False
    )

    schema.addClouds(
        copying = schema.Cloud(organizer,location,rruleset,participants),
        sharing = schema.Cloud(
            startTime, duration, allDay, location, anyTime, modifies,
            reminderTime, transparency, isGenerated, recurrenceID, icalUID,
            byCloud = [organizer, participants, modifications, rruleset,
                occurrenceFor]
        )
    )

    # Redirections

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
        self.displayName = u"New Event"

    def _initMixin (self):
        """ 
          Init only the attributes specific to this mixin.
        Called when stamping adds these attributes, and from __init__ above.
        """
        # start at the nearest half hour, duration of an hour
        now = datetime.now(ICUtzinfo.getDefault())
        self.startTime = datetime.combine(now,
                                  time(hour=now.hour,
                                       minute=((now.minute/30) * 30),
                                       tzinfo=now.tzinfo))
        self.duration = timedelta(hours=1)

        # set the organizer to "me"
        self.organizer = self.getCurrentMeContact(self.itsView)

        # give a starting display name
        try:
            self.displayName = self.getAnyAbout ()
        except AttributeError:
            pass
        
        self.occurrenceFor = self

        if not hasattr(self, 'icalUID'):
            self.icalUID = str(self.itsUUID)
            
        
        # TBD - set participants to any existing "who"
        # participants are currently not implemented.

    def getEndTime(self):
        if (self.hasLocalAttributeValue("startTime") and 
            self.hasLocalAttributeValue("duration")):
            return self.startTime + self.duration
        else:
            return None
    
    def setEndTime(self, dateTime):
        if self.hasLocalAttributeValue("startTime"):
            duration = dateTime - self.startTime
            if duration < timedelta(0):
                raise ValueError, "End time must not be earlier than start time"
            self.duration = duration

    endTime = Calculated(
        schema.DateTime,
        displayName=u"End-Time",
        fget=getEndTime,
        fset=setEndTime,
        doc="End time, computed from startTime + duration."
    )

    def getEffectiveStartTime(self):
        """ 
        Get the effective start time of this event: ignore the time
        component of the startTime attribute if this is an allDay 
        or anyTime event.
        """
        # If startTime's time is invalid, ignore it.
        if self.anyTime or self.allDay:
            result = datetime.combine(self.startTime,
                time(0, tzinfo=self.startTime.tzinfo))
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
            result = datetime.combine(self.endTime, 
                        time(0, tzinfo=self.endTime.tzinfo))
        else:
            result = self.endTime
        return result
        
    def GetReminderDelta(self):
        """ Returns the difference between startTime and reminderTime, a timedelta """
        try:
            return datetimeOp(self.reminderTime, '-',
                            self.getEffectiveStartTime())
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
                               displayName=u"reminderDelta",
                               fget=GetReminderDelta, fset=SetReminderDelta,
                               doc="reminderDelta: the amount of time before " \
                                   "the event that we want a reminder")
    
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

    def getLastUntil(self):
        """Find the last modification's rruleset, return it's until value."""
        # for no-THISANDFUTURE, this is just return until
        try:
            return self.rruleset.rrules.first().until
        except:
            return None
                   
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
        return (before is None or datetimeOp(self.startTime, '<=', before)) and \
               (after is None or datetimeOp(self.endTime, '>=', after))

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
            # exclude collections so generated occurrences don't
            # appear in the collection
            if attr == 'collections':
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
        new.startTime = new.recurrenceID = recurrenceID
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
                    return datetimeOp(self.startTime, '<', mod.startTime) and \
                           (before is None or datetimeOp(mod.startTime, '<', before))
            else:
                def test(mod):
                    return mod.isBetween(after, before)
            for mod in first.modifications or []:
                if test(mod):
                    if nextEvent==None:
                        nextEvent = mod
                        # finally, well-ordering requires that we sort by
                        # recurrenceID if startTimes are equal
                    elif datetimeOp(mod.startTime, '<=', nextEvent.startTime):
                        if datetimeOp(mod.startTime, '==', nextEvent.startTime) and \
                           datetimeOp(mod.recurrenceID,'>=', nextEvent.recurrenceID):
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
                earliest = datetimeOp(self.recurrenceID, 'min', self.startTime)
                inc = False
            while True:
            
                fromRule = self.createDateUtilFromRule()
                # Here, we want to make sure that anything we pass
                # to fromRule has the same timezone as all the rules
                # and dates within fromRule.
                #
                # Otherwise, we could well end up with unsafe datetime
                # comparisons inside dateutil.
                try:
                    tzinfo = fromRule[0].tzinfo
                except IndexError:
                    tzinfo = self.startTime.tzinfo
                
                earliestWithTz = coerceTimeZone(earliest, tzinfo)
                    
                nextRecurrenceID = fromRule.after(earliestWithTz, inc)
                
                if nextRecurrenceID == None or \
                   (before != None and datetimeOp(nextRecurrenceID, '>', before)):
                    # no more generated occurrences, make sure no modifications
                    # match
                    return checkModifications(first, before)
                                
                # First, see if an occurrence for nextRecurrenceID exists.
                calculated = None
                for occurrence in first.occurrences:
                    if datetimeOp(occurrence.recurrenceID, '==',
                                    nextRecurrenceID):
                        calculated = occurrence
                        break
                    
                # If no occurrence already exists, create one
                if calculated is None:
                    calculated = self._createOccurrence(nextRecurrenceID)

                # now we have an event calculated from nextRecurrenceID.  It's
                # actual startTime may be too early, or there may be a
                # modification which is even earlier.
                
                if (after == None and \
                     datetimeOp(calculated.startTime, '<', self.startTime)) \
                  or (
                      after is not None
                      and not calculated.isBetween(after, before)):
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
                                    and datetimeOp(mod.startTime, '<=', before))
        _sortEvents(mods)
        # cut out mods which end before "after"
        index = -1
        for i, mod in enumerate(mods):
            if datetimeOp(mod.startTime, '>=', after):
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
                if datetimeOp(mod.recurrenceID, '==', recurrenceID):
                    return mod
            elif mod.modifies == 'thisandfuture':
                for occurrence in mod.occurrences or []:
                    if datetimeOp(occurrence.recurrenceID, '==', recurrenceID):
                        return occurrence

        # look through master's occurrences
        for occurrence in self.getMaster().occurrences:
            if datetimeOp(occurrence.recurrenceID, '==', recurrenceID):
                return occurrence

        # no existing matches, see if one can be generated:
        for occurrence in self.getOccurrencesBetween(recurrenceID,recurrenceID):
            if datetimeOp(occurrence.recurrenceID, '==', recurrenceID):
                return occurrence

        # no match
        return None

    def _movePreviousRuleEnd(self, master, recurrenceID):
        """Make sure the previous rule doesn't recreate or overlap with self."""
        newend = min(self.startTime, recurrenceID) - timedelta(minutes=1)
              
        #change the rule, onValueChanged will trigger cleanRule for master
        for rule in master.rruleset.getAttributeValue('rrules',default=[]):
            if not rule.hasLocalAttributeValue('until') or \
               datetimeOp(rule.calculatedUntil(), '>', newend):
                rule.until = newend
                rule.untilIsDate = False
            # TODO: enable support for RDATEs when making THISANDFUTURE changes
            #previousMod.rruleset.rdates = [rdate for rdate in \
            #       previousMod.rruleset.getAttributeValue('rdates', default=[])\
            #       if datetimeOp(rdate, '>', newend)]

    def _makeGeneralChange(self, master=None):
        """Do everything that should happen for any change call."""
        if master is None:
            master = self.getMaster()
        if master.hasLocalAttributeValue('collections'):
            # [Bug 3767] We want self to be in all master's
            # collections.
            for coll in master.collections:
                coll.add(self)
        self.isGenerated = False

    def changeNoModification(self, attr, value):
        """Set _ignoreValueChanges flag, set the attribute, then unset flag."""
        flagStart = getattr(self, '_ignoreValueChanges', None)
        self._ignoreValueChanges = True
        setattr(self, attr, value)
        if flagStart is None:
            del self._ignoreValueChanges

    def _propagateChange(self, modification, first, master):
        """Move later modifications to self."""
        #TODO: icalUID and rruleset changes
        if datetimeOp(modification.startTime, '>=',  self.startTime):
            # future 'this' modifications in master should move to self
            modification.modificationFor = self
            modification.occurrenceFor = self
                           
    def changeThisAndFuture(self, attr=None, value=None):
        """Modify this and all future events."""
        master = self.getMaster()
        first = master # Changed for no-THISANDFUTURE-style
        recurrenceID = self.recurrenceID
        isFirst = recurrenceID == master.startTime
        self._ignoreValueChanges = True
        
        if attr == 'startTime':
            startTimeDelta = datetimeOp(value, '-', self.startTime)
        
        setattr(self, attr, value)
        
        def makeThisAndFutureMod():
            self.modifies='this'
            # Changing occurrenceFor before changing rruleset is important, it
            # keeps the rruleset change from propagating inappropriately
            self.occurrenceFor = self
            if attr != 'rruleset':
                self.rruleset = self.rruleset.copy(cloudAlias='copying')
                # TODO: may need to remove early rdates
            # We have to pass in master because occurrenceFor has been changed
            self._makeGeneralChange(master)
            # Make this event a separate event from the original rule
            self.modificationFor = None
            self.recurrenceID = self.startTime
            self.icalUID = str(self.itsUUID)
                                        
        # determine what type of change to make
        if attr == 'rruleset': # rule change, thus a destructive change
            self.cleanFuture()
            if self == master: # self is master, nothing to do
                pass
            elif self.isGenerated:
                makeThisAndFutureMod()
                self._movePreviousRuleEnd(master, recurrenceID)
            elif self.modificationFor is not None:# changing 'this' modification
                if datetimeOp(self.recurrenceID, '==', first.startTime):
                    self.modifies = 'this'
                    self.modificationFor = None
                    self.occurrenceFor = self
                    self.modificationRecurrenceID = self.startTime
                    first._ignoreValueChanges = True
                    first.delete()
                else:
                    makeThisAndFutureMod()
                    self._movePreviousRuleEnd(master, recurrenceID)
        else: #propagate changes forward                       
            if self.modifies == 'this' and self.modificationFor is not None:
                #preserve self as a THIS modification
                if self.recurrenceID != first.startTime:
                    # create a new event, cloned from first, make it a
                    # thisandfuture modification with self overriding it
                    newfirst = first._cloneEvent()
                    newfirst._ignoreValueChanges = True
                    newfirst.rruleset = self.rruleset.copy(cloudAlias='copying')
                    # There are two events in play, self (which has been
                    # changed), and newfirst, a non-displayed item used to
                    # define generated events.  Make sure the current change
                    # is applied to both items, and that both items have the 
                    # same rruleset.
                    setattr(newfirst, attr, value)
                    self.rruleset = newfirst.rruleset
                    newfirst.startTime = self.recurrenceID
                    newfirst.occurrenceFor = None #self overrides newfirst
                    newfirst.modifies = 'this'
                    newfirst.icalUID = self.icalUID = str(newfirst.itsUUID)
                    newfirst._makeGeneralChange(master)
                    self.occurrenceFor = self.modificationFor = newfirst
                    # move THIS modifications after self to newfirst
                    if first.hasLocalAttributeValue('modifications'):
                        for mod in first.modifications:
                            if mod.modifies == 'this':
                                if datetimeOp(mod.recurrenceID, '>', newfirst.startTime):
                                    mod.occurrenceFor = newfirst
                                    mod.modificationFor = newfirst
                                    mod.icalUID = newfirst.icalUID
                                    mod.rruleset = newfirst.rruleset
                                    #rruleset needs to change, so does icalUID
                    del newfirst._ignoreValueChanges
                else:
                    # self was a THIS modification to the master, setattr needs
                    # to be called on master
                    master.changeNoModification(attr, value)

            else: # change applies to an event which isn't a modification
                if self.isGenerated:
                    makeThisAndFutureMod()
                else:
                    # Change applied to a master, make sure it gets its
                    # recurrenceID updated
                    self.recurrenceID = self.startTime
            master._deleteGeneratedOccurrences()
            
            if master.modifications:
                for modification in master.modifications:
                    self.occurrenceFor._propagateChange(modification, first, 
                                                                      master)
                    # change recurrenceIDs for modificationsif startTime change
                    if attr == 'startTime' and \
                       datetimeOp(modification.startTime, '>=', self.startTime):
                        modification.changeNoModification('recurrenceID', 
                            modification.recurrenceID + startTimeDelta)
            if not isFirst:
                self._movePreviousRuleEnd(master, recurrenceID)

        self._getFirstGeneratedOccurrence(True)

        del self._ignoreValueChanges

    def changeThis(self, attr=None, value=None):
        """Make this event a modification, don't modify future events.
        
        Without arguments, change self appropriately to make it a THIS 
        modification.
        
        One edge case does have an effect on other events.  Moving an event's
        startTime so it begins in a different rule will ........FIXME
        
        """
        if self.modifies == 'this' and self.modificationFor is not None:
            pass
        elif self.rruleset is not None:
            first = self.getFirstInRule()
            master = self.getMaster()
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
                    newfirst.modifies = 'this'
                    # Unnecessary when we switch endTime->duration
                    newfirst.duration = backup.duration
                    self.occurrenceFor = self.modificationFor = newfirst
                    newfirst._makeGeneralChange(master)
                    self.modifies = 'this'
                    self.recurrenceID = newfirst.startTime
                    if self.hasLocalAttributeValue('modificationRecurrenceID'):
                        del self.modificationRecurrenceID
                    del newfirst._ignoreValueChanges
                # if backup is None, allow the change to stand, applying just
                # to self.  This relies on _getFirstGeneratedOccurrence() always
                # being called.  Still, make sure changes to startTime change
                # modificationRecurrenceID, and recurrenceID if self is master.
                else:
                    self.modificationRecurrenceID = self.startTime
                    if master == self:
                        self.recurrenceID = self.startTime

            else:
                self.modificationFor = first
                self._makeGeneralChange()
                self.modifies = 'this'
                self._getFirstGeneratedOccurrence(True)
        if attr is not None:
            setattr(self, attr, value)


    changeNames = ('displayName', 'startTime', 'endTime', 'location', 'body',
                   'lastModified', 'allDay')

    def onValueChanged(self, name):
        # allow initialization code to avoid triggering onValueChanged
        rruleset = name == 'rruleset'
        changeName = not rruleset and name in CalendarEventMixin.changeNames

        if (not (rruleset or changeName) or
            self.rruleset is None or
            getattr(self, '_share_importing', False) or
            getattr(self, '_ignoreValueChanges', False)):
            return
        # avoid infinite loops
        if rruleset:
            logger.debug("just set rruleset")
            gen = self._getFirstGeneratedOccurrence(True)
            if DEBUG and gen:
                logger.debug("got first generated occurrence, %s", gen.serializeMods().getvalue())

            # make sure masters get modificationRecurrenceID set
            if self is self.getFirstInRule():
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
        elif changeName:
            if DEBUG:
                logger.debug("about to changeThis in onValueChanged(name=%s) for %s", name, str(self))
                logger.debug("value is: %s", getattr(self, name))
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
                    until = first.rruleset.rrules.first().calculatedUntil()
                    if until is not None \
                       and datetimeOp(mod.recurrenceID, '>', until) \
                       and mod !=  first:
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
            if datetimeOp(item.startTime, '>',  self.startTime): 
                item._ignoreValueChanges = True
                item.delete()
                
        master = self.getMaster()
        for mod in master.modifications or []:
            if mod.modifies == 'thisandfuture':
                if datetimeOp(mod.startTime, '>', self.startTime):
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
            masterHadModification = False
            for event in master.occurrences:
                if event.recurrenceID != master.startTime:
                    event.delete()
                elif event != master:
                    event.recurrenceID = event.startTime
                    event.modificationFor = None
                    event.occurrenceFor = event
                    masterHadModification = True

            if masterHadModification:
                master.delete()
        
                   
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
        """Pretty print the list of modifications as a debugging aid."""
        if buf is None:
            buf = StringIO.StringIO()
        pad = "  " * level
        try:
            if level:
                buf.write(pad + "modification.  modifies: %s modificationFor: %s\n"\
                                 % (self.modifies, self.modificationFor.startTime))
            buf.write(pad + "event is: %s %s\n" % (self.displayName.encode("utf8"),  self.startTime))
        except:
            pass
        if self.modifies == 'thisandfuture' or self.modificationFor is None:
            try:
                buf.write(pad + "until: %s\n" % getattr(self.rruleset.rrules.first(), 'until', None))
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


class CalendarEvent(CalendarEventMixin, Note):
    """
    @note: CalendarEvent should maybe have a 'Timezone' attribute.
    @note: Do we want to have 'Duration' as a derived attribute on Calendar Event?
    @note: Do we want to have a Boolean 'AllDay' attribute, to indicate that an event is an all day event? Or should we instead have the 'startTime' and 'endTime' attributes be 'RelativeDateTime' instead of 'DateTime', so that they can store all day values like '14 June 2004' as well as specific time values like '4:05pm 14 June 2004'?
    """
    schema.kindInfo(displayName=u"Calendar Event")

    def __init__(self, name=None, parent=None, kind=None, view=None, **kw):
        kw.setdefault('participants',[])
        super (CalendarEvent, self).__init__(name, parent, kind, view, **kw)


class Calendar(ContentItem):
    """
    @note: Calendar should have an attribute that points to all the Calendar Events.
    @note: Calendar should maybe have a 'Timezone' attribute.
    """
    
    schema.kindInfo(displayName=u"Calendar", displayAttribute="displayName")


class Location(ContentItem):
    """
       @note: Location may not be calendar specific.
    """
    
    schema.kindInfo(displayName=u"Location", displayAttribute="displayName")

    eventsAtLocation = schema.Sequence(
        CalendarEventMixin,
        displayName=u"Calendar Events",
        inverse=CalendarEventMixin.location
    )


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
        for item in Location.iterItems(view, exact=True):
            if item.displayName == locationName:
                return item

        # make a new Location
        newLocation = Location(view=view)
        newLocation.displayName = locationName
        return newLocation

    getLocation = classmethod (getLocation)

class RecurrencePattern(ContentItem):
    """
    @note: RecurrencePattern is still a placeholder, and might be general enough to live with PimSchema. RecurrencePattern should have an attribute that points to a CalendarEvent.
    """
    
    schema.kindInfo(displayName=u"Recurrence Pattern")

