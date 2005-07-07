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

    def _createRuleSetItem(self, freq):
        ruleItem = RecurrenceRule(None, view=self.rep.view)
        ruleItem.until = getattr(self, freq)['end']
        if freq == 'weekly':
            self.assertEqual(ruleItem.freq, 'weekly', 
                             "freq should default to weekly")
        else:
            ruleItem.freq = freq
        ruleSetItem = RecurrenceRuleSet(None, view=self.rep.view)
        ruleSetItem.addRule(ruleItem)
        return ruleSetItem

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
        event.modifications = [calmod, note]
        try:
            self.rep.check()
            self.failIf(True, "A note shouldn't be allowed as a modification")
        except NoSuchAttributeError:
            pass
        event.modifications = [calmod, evtaskmod]
        self.rep.check()
        for modOrMaster in [calmod, evtaskmod, event]:
            self.assertEqual(modOrMaster.getMaster(), event)

    def testSimpleRuleBehavoir(self):
        event = self._createEvent()
        event.startTime = self.start
        event.anyTime = False
        # event.occurrenceFor should default to event
        self.assertEqual(event.occurrenceFor, event)
        # getNextOccurrence for events without recurrence should be None
        self.assertEqual(event.getNextOccurrence(), None)
        
        event.rruleset = self._createRuleSetItem('weekly')
        #self.assertEqual(event.isCustomRule(), False)
        
        second = event.getNextOccurrence()
        secondStart = datetime(2005, 7, 11, 13)
        self.assertEqual(event.createDateUtilFromRule()[1], secondStart)
        self.assertEqual(second.startTime, secondStart)
        
        # make sure getNextOccurrence returns the same item when called twice
        self.assertEqual(second, event.getNextOccurrence())
        
        third = event.getNextOccurrence(fromTime=secondStart)
        thirdStart = datetime(2005, 7, 18, 13)
        self.assertEqual(third.startTime, thirdStart)
        
        second.cleanFuture()
        self.assertEqual(len(event.occurrences), 2)
        
        newRule = dateutil.rrule.rrule(dateutil.rrule.WEEKLY, count = 2,
                                       dtstart = self.start)
        
        # without currentlyModifying, what's the API for modifying future?
        # In this case, changing the rule, it can only mean thisandfuture.
        event.setRuleFromDateUtil(newRule)
        
        # setting the rule should delete occurrences
        self.assertEqual(len(event.occurrences), 1)
        

#tests to write:
"""

Test modification logic

Test modification model (max 2 levels deep...)

test cleanFuture for modifications

# getOccurrencesBetween(start, end) -> check for virtual events that end after start and start before end, create any that don't already exist, return an iterable of events ordered by startTime
# isCustomRule() -> return boolean depending on whether the rule must be represented as custom in the UI
# getCustomDescription() -> return a string describing the recurrence rule, like "TuTh every second week for 5 weeks", or "complex" if no description is available for the rule


test getNextOccurrence logic for finding modification or occurrence, make sure 
    new occurrences get attributes copied, have the proper kind

should we make sure GeneratedOccurrences can't be committed as modifications?
should icalUID be checked for equality in modification and master?

test recurrence behavior around DST (duration vs. endTime)

reminders - lots of work :)

tzical -> pyicu timezone

Test createDateUtilFromRule for more complicated modifications

# update spec: occurrences better explanation, getMaster override in GeneratedOccurrence, timezone stored entirely in startTime
# update spec: when creating an occurrence, references whose inverse has cardinality single lost
# update spec: changing a ruleset -> changes events automatically?
# update spec: add cleanFuture()

API and tests for proxying items # remove currentlyModifying from the spec

# deleteEvent() -> delete all modifications and occurrences for this event, delete self
# removeOne() -> remove this item, exclude its recurrenceID from the parent rule
# removeFuture() -> remove this item, delete future occurrences and modifications, modify master's rule to end before this occurrence

what behavior is appropriate when python del is called on an occurrence or modification?

"""