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
        event = Calendar.CalendarEvent(None, view=self.rep.view)
        event.startTime = self.start
        event.endTime = event.startTime + timedelta(hours=1)
        event.anyTime = False
        event.displayName = "Sample event"
        return event
    
    def testModificationEnum(self):
        event = self._createEvent()
        self.assertEqual(event.modifies, None)
        self.modifies = "this"
        
    def testModification(self):
        event = self._createEvent()
        calmod = self._createEvent()
        evtaskmod = osaf.contentmodel.EventTask(None, view=self.rep.view)

        self.assertEqual(event.modifications, None)
        event.modifications = [calmod]
        self.assertEqual(calmod.modificationFor, event)

        event.modifications = [calmod, evtaskmod]
        self.rep.check()
        for modOrMaster in [calmod, evtaskmod, event]:
            self.assertEqual(modOrMaster.getMaster(), event)

    def testSimpleRuleBehavior(self):
        event = self._createEvent()

        # event.occurrenceFor should default to event
        self.assertEqual(event.occurrenceFor, event)
        # getNextOccurrence for events without recurrence should be None
        self.assertEqual(event.getNextOccurrence(), None)
        self.failIf(event.isGenerated)
        
        event.rruleset = self._createRuleSetItem('weekly')
        self.assertEqual(event.isCustomRule(), False)
        
        secondStart = datetime(2005, 7, 11, 13)
        second = event._createOccurrence(secondStart)
        self.assert_(second.isGenerated)
        self.assertEqual(event.createDateUtilFromRule()[1], secondStart)
        self.assertEqual(second.startTime, secondStart)
        self.assertEqual(second.displayName, event.displayName)
        
        # make sure getNextOccurrence returns the same item when called twice
        self.assertEqual(second, event.getNextOccurrence())
        
        third = event.getNextOccurrence(after=secondStart)
        thirdStart = datetime(2005, 7, 18, 13)
        self.assertEqual(third.startTime, thirdStart)
        
        second.cleanFuture()
        self.assertEqual(len(event.occurrences), 2)
        
        count = 3
        newRule = dateutil.rrule.rrule(dateutil.rrule.WEEKLY, count = count,
                                       interval = 2, dtstart = self.start)
        
        # without currentlyModifying, what's the API for modifying future?
        # In this case, changing the rule, it can only mean thisandfuture.
        event.setRuleFromDateUtil(newRule)
        self.assertEqual(event.isCustomRule(), True)
        self.assertEqual(event.getCustomDescription(), "not yet implemented")
        
        # changing the rule should delete generated occurrences
        self.assertEqual(len(event.occurrences), 1)

        # generateRule should create count events
        self.assertEqual(len(list(event._generateRule())), count)

        
        occurs = event.getOccurrencesBetween(thirdStart - timedelta(minutes=30),
                                             datetime(2005, 8, 1, 13))
        
        # getOccurrencesBetween must take duration into account
        self.assertEqual(list(occurs)[0].startTime, thirdStart)
        
        # getOccurrencesBetween should be inclusive of start/end times
        self.assertEqual(list(occurs)[1].startTime, datetime(2005, 8, 1, 13))

#tests to write:
"""

API and tests for proxying items 

Life Cycle Analysis of proxy
    createProxy when first rendering a view
        currentlyModifying = None
    proxy intercepts setattr
        if currentlyModifying is None
            save attrname and value in the proxy
            dialog box has been requested
            queue dialog box
                when dialog box is clicked
                    
registry of proxies
foo.registerProxy(CalendarEventMixin, CalendarEventMixinProxy)
proxy = foo.getProxiedItem(item)

test cleanFuture for modifications

Test modification creation, updating future, etc.

Test modification model (max 2 levels deep...)

test getOccurrencesBetween for events with no duration

test getNextOccurrence logic for finding modification or occurrence, make sure 
    new occurrences get attributes copied, have the proper kind

test automatic icalUID setting

test recurrence behavior around DST (duration vs. endTime)

Test createDateUtilFromRule for a THIS modification

# deleteEvent() -> delete all modifications and occurrences for this event, delete self
# removeOne() -> remove this item, exclude its recurrenceID from the parent rule
# removeFuture() -> remove this item, delete future occurrences and modifications, modify master's rule to end before this occurrence

# expand getCustomDescription() "TuTh every second week for 5 weeks", or "complex" if no description is available for the rule

should isCustom continue to return False after removeOne() is called?  If so, then exdates should be ignored.

what default behavior is appropriate when delete() is called on an occurrence or modification?

reminders - lots of work :)

tzical -> pyicu timezone

# update spec: occurrences better explanation, getMaster override in GeneratedOccurrence, timezone stored entirely in startTime
# update spec: when creating an occurrence, references whose inverse has cardinality single lost
# update spec: changing a ruleset -> changes events automatically?
# update spec: add cleanFuture()
# update spec: THIS modifications can't cross into different rules

"""