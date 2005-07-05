"""
Unit tests for recurring events
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os
from datetime import datetime, timedelta
import dateutil.rrule

import osaf.contentmodel.calendar.Calendar as Calendar
from osaf.contentmodel.calendar.Recurrence import RecurrenceRule, \
                                                  RecurrenceRuleSet

from osaf.contentmodel import Notes
import osaf.contentmodel
import osaf.contentmodel.tests.TestContentModel as TestContentModel
from chandlerdb.item.ItemError import NoSuchAttributeError

class RecurringEventTest(TestContentModel.ContentModelTestCase):
    """ Test CalendarEvent Recurrence """

    def setUp(self):
        super(RecurringEventTest,self).setUp()
        self.start = datetime(2005, 7, 4, 13) #1PM, July 4, 2005

        self.weekly = {'end'   : datetime(2005, 11, 14, 13),
                       'start' : self.start,
                       'count' : 20}
        
        self.monthly = {'end'   : datetime(2005, 11, 4, 13),
                       'start' : self.start,
                       'count' : 5}

    def _createRule(self, freq):
        ruleItem = RecurrenceRule(None, view=self.rep.view)
        ruleItem.until = getattr(self, freq)['end']
        if freq == 'weekly':
            self.assertEqual(ruleItem.freq, 'weekly', 
                             "freq should default to weekly")
        else:
            ruleItem.freq = freq
        return ruleItem

    def _createEvent(self):
        return Calendar.CalendarEvent(None, view=self.rep.view)
    
    def testModificationEnum(self):
        event = self._createEvent()
        self.assertEqual(event.modifies, None)
        self.modifies = "this"
        
    def testModification(self):
        event = self._createEvent()
        calmod = self._createEvent()
        evtaskmod = osaf.contentmodel.EventTask(None, view=self.rep.view)
        note = Notes.Note(None, view=self.rep.view)
        self.assertEqual(event.modifications, None)
        event.modifications = [calmod]
        self.assertEqual(calmod.modificationFor, event)
        event.modifications = [calmod, evtaskmod]
        self.rep.check()
        event.modifications = [calmod, evtaskmod, note]
        try:
            self.rep.check()
            self.failIf(True, "A note shouldn't be allowed as a modification")
        except NoSuchAttributeError:
            pass

    def testRRuleSet(self):
        event = self._createEvent()
        # event.occurrenceFor should default to event
        self.assertEqual(event.occurrenceFor, event)
        # getNextOccurrence for events without recurrence should be None
        self.assertEqual(event.getNextOccurrence(), None)
        ruleSetItem = RecurrenceRuleSet(None, view=self.rep.view)
        ruleSetItem.setRuleFromDateUtil(self._createRule('weekly'))
        event.rruleset = ruleSetItem
        second = event.getNextOccurrence()
        self.assertEqual(second.startTime, datetime(2005, 7, 11, 13))
        self.assertEqual(second, event.getNextOccurrence())
        

#tests to write:
"""

Test modification logic

Test modification model (max 2 levels deep...)

getMaster

createDateUtilFromRule (needs getMaster)

# timezone - Timezone
# recurrenceID

# createDateUtilFromRule() -> convenience method, returning self.rruleset.createDateUtilFromRule(self.dtstart) or if self.rruleset is None, return None
# setRuleFromDateUtil(rule) -> create an appropriate RecurrenceRuleSet from a dateutil rrule or rruleset, set it to self.rruleset
# getMaster() -> convenience method, returning self if modificationFor is None, or self.modificationFor.getMaster()
# deleteEvent() -> delete all modifications and occurrences for this event, delete self
# removeOne() -> remove this item, exclude its recurrenceID from the parent rule
# removeFuture() -> remove this item, delete future occurrences and modifications, modify master's rule to end before this occurrence
# getOccurrencesBetween(start, end) -> check for virtual events that end after start and start before end, create any that don't already exist, return an iterable of events ordered by startTime
# isCustomRule() -> return boolean depending on whether the rule must be represented as custom in the UI
# getCustomDescription() -> return a string describing the recurrence rule, like "TuTh every second week for 5 weeks", or "complex" if no description is available for the rule
# getNextOccurrence(fromTime=None)

test getNextOccurrence logic for finding modification or occurrence, possibly
   creating new occurrences

should we makes sure GeneratedOccurrences can't be committed as modifications?
should icalUID be checked for equality in modification and master?

test recurrence behavior around DST (duration vs. endTime)

test changing a ruleset -> changing linked events

reminders - lots of work :)
change endTime implementation

# update spec: occurrences better explanation, getMaster override in GeneratedOccurrence

API and tests for proxying items # instead of currentlyModifying

"""