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
import osaf.contentmodel.tasks.Task as Task
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

    def testThisModification(self):
        event = self._createEvent()
        event.rruleset = self._createRuleSetItem('weekly')
        
        calmod = event.getNextOccurrence()
        calmod.changeThis('displayName', 'Modified occurrence')

        self.assertEqual(calmod.modificationFor, event)
        self.assertEqual(calmod.modifies, 'this')
        self.assertEqual(list(event.modifications), [calmod])

        evtaskmod = calmod.getNextOccurrence()
        evtaskmod.StampKind('add', Task.TaskMixin.getKind(self.rep.view))
        
        # changes to an event should, by default, create a THIS modification
        self.assertEqual(evtaskmod.modificationFor, event)
        self.assertEqual(evtaskmod.modifies, 'this')

        for modOrMaster in [calmod, evtaskmod, event]:
            self.assertEqual(modOrMaster.getMaster(), event)

    def testRuleChanges(self):
        event = self._createEvent()
        event.rruleset = self._createRuleSetItem('weekly')

        #create a generated occurrence so there's something to be deleted
        event.getNextOccurrence()        
        self.assertEqual(len(event.occurrences), 2)

        count = 3
        newRule = dateutil.rrule.rrule(dateutil.rrule.WEEKLY, count = count,
                                       interval = 2, dtstart = self.start)
        
        event.setRuleFromDateUtil(newRule)
        self.assertEqual(event.isCustomRule(), True)
        self.assertEqual(event.getCustomDescription(), "not yet implemented")

        # changing the rule must be a THISANDFUTURE modification, but because
        # we changed the master, modifies should stay None
        self.assertEqual(len(event.occurrences), 1)
        self.assertEqual(event.modifies, None)

        self.assertEqual(len(list(event._generateRule())), count)

        twoWeeks = self.start + timedelta(days=14)
        occurs = event.getOccurrencesBetween(twoWeeks + timedelta(minutes=30),
                                             datetime(2005, 8, 1, 13))
        self.assertEqual(list(occurs)[0].startTime, twoWeeks)
        self.assertEqual(list(occurs)[1].startTime, datetime(2005, 8, 1, 13))


    def testProxy(self):
        event = self._createEvent()
        self.failIf(event.isProxy())
        
        proxy = Calendar.getProxy(event)
        self.assert_(proxy.isProxy())
        self.assertEqual(proxy, event)
        self.assertEqual(proxy.currentlyModifying, None)

        proxy.rruleset = self._createRuleSetItem('weekly')
        self.assert_(event in proxy.rruleset.events)

        self.assertEqual(proxy.getNextOccurrence().occurrenceFor, event)
        self.assertEqual(len(list(proxy._generateRule())), self.weekly['count'])
        
        proxy.startTime = self.start + timedelta(days=1)
        
        # the change shouldn't propagate
        # holding off on this test
        #self.assertEqual(proxy.startTime, self.start)


#tests to write:
"""

changeThisAndFuture and changeThis

Test modification creation, updating future, etc.
Test modification model (max 2 levels deep...)

test modifying existing rules

test getOccurrencesBetween for events with no duration

test getNextOccurrence logic for finding modification or occurrence, make sure 
    new occurrences get attributes copied, have the proper kind

test cleanFuture for modifications



test stamping and unstamping behavior

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


Test modifying event with no proxy (update THIS unless it's a rule change)


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
# update spec: add changeThisAndFuture and changeThis
# update spec: changing an rrule always makes a THISANDFUTURE modification

"""