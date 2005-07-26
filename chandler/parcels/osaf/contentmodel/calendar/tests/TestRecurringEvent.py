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
        self.event = Calendar.CalendarEvent(None, view=self.rep.view)
        self.event.startTime = self.start
        self.event.endTime = self.event.startTime + timedelta(hours=1)
        self.event.anyTime = False
        self.event.displayName = "Sample event"

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
    
    def testModificationEnum(self):
        self.assertEqual(self.event.modifies, None)
        self.modifies = "this"
        
    def testSimpleRuleBehavior(self):
        # self.event.occurrenceFor should default to self.event
        self.assertEqual(self.event.occurrenceFor, self.event)
        # getNextOccurrence for events without recurrence should be None
        self.assertEqual(self.event.getNextOccurrence(), None)
        self.failIf(self.event.isGenerated)
        
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.assertEqual(self.event.isCustomRule(), False)
        
        secondStart = datetime(2005, 7, 11, 13)
        second = self.event.getNextOccurrence()
        self.assert_(second.isGenerated)
        self.assertEqual(self.event.createDateUtilFromRule()[1], secondStart)
        self.assertEqual(second.startTime, secondStart)
        self.assertEqual(second.displayName, self.event.displayName)
        
        # make sure getNextOccurrence returns the same item when called twice
        self.assertEqual(second, self.event.getNextOccurrence())
        
        third = self.event.getNextOccurrence(startsafter=secondStart)
        thirdStart = datetime(2005, 7, 18, 13)
        self.assertEqual(third.startTime, thirdStart)
        
        fourthStart = datetime(2005, 7, 25, 13)
        fourth = self.event._createOccurrence(fourthStart)
        self.assert_(fourth.isGenerated)
        self.assertEqual(fourth, third.getNextOccurrence())
        
        second.cleanRule()
        self.assertEqual(len(self.event.occurrences), 2)
        

    def testFirstGeneratedOccurrence(self):
        """At least one generated occurrence must be created when rules are set.
        
        Because non-UI changes to recurring events should create THIS
        modifications to a master via onValueChanged, such modifications need to 
        be created after the master's value has already changed.  To make sure
        this data is available to the modification generating code, a 
        generated occurrence (which is identical in every way to the master
        except date and certain references) must be created each time a
        modification is made or a rule changes, so that, in effect, a backup
        of the master's data always exists.
        
        Note that it's possible for all of a rule's occurrences to be
        modifications, so occasionally no backup will exist
        
        """
        self.event.rruleset = self._createRuleSetItem('weekly')
        
        # setting the rule should trigger _getFirstGeneratedOccurrence
        self.assertEqual(len(self.event.occurrences), 2)
        

    def testThisModification(self):
        self.event.displayName = "Master Event" #no rruleset, so no modification
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.assertEqual(self.event.modifies, None)
        
        calmod = self.event.getNextOccurrence()
        self.assertEqual(self.event.modifications, None)
        
        calmod.changeThis('displayName', 'Modified occurrence')

        self.assertEqual(calmod.modificationFor, self.event)
        self.assertEqual(calmod.modifies, 'this')
        self.assertEqual(calmod.getFirstInRule(), self.event)
            
        self.assertEqual(list(self.event.modifications), [calmod])

        evtaskmod = calmod.getNextOccurrence()
        
        evtaskmod.StampKind('add', Task.TaskMixin.getKind(self.rep.view))
        
        # changes to an event should, by default, create a THIS modification
        self.assertEqual(evtaskmod.modificationFor, self.event)
        self.assertEqual(evtaskmod.modifies, 'this')
        self.assertEqual(evtaskmod.getFirstInRule(), self.event)

        for modOrMaster in [calmod, evtaskmod, self.event]:
            self.assertEqual(modOrMaster.getMaster(), self.event)
            
        self.event.displayName = "Modification to master"
        self.assertEqual(self.event.modifies, 'this')
        self.assertNotEqual(None, self.event.occurrenceFor)
        self.assertNotEqual(self.event, self.event.occurrenceFor)

    def testRuleChange(self):
        self.event.rruleset = self._createRuleSetItem('weekly')
        # automatically generated backup occurrence    
        self.assertEqual(len(self.event.occurrences), 2)

        count = 3
        newRule = dateutil.rrule.rrule(dateutil.rrule.WEEKLY, count = count,
                                       interval = 2, dtstart = self.start)
        
        self.event.setRuleFromDateUtil(newRule)
        self.assertEqual(self.event.isCustomRule(), True)
        self.assertEqual(self.event.getCustomDescription(), "not yet implemented")

        # changing the rule for the master, modifies should stay None
        self.assertEqual(self.event.modifies, None)

        # all occurrences except the first should be deleted, then one should 
        # be generated
        self.assertEqual(len(self.event.occurrences), 2)
        self.assertEqual(len(list(self.event._generateRule())), count)

        twoWeeks = self.start + timedelta(days=14)
        occurs = self.event.getOccurrencesBetween(twoWeeks + 
                                timedelta(minutes=30), datetime(2005, 8, 1, 13))
        self.assertEqual(list(occurs)[0].startTime, twoWeeks)
        self.assertEqual(list(occurs)[1].startTime, datetime(2005, 8, 1, 13))
        self.rep.check()

    def testProxy(self):
        self.failIf(self.event.isProxy())
        
        proxy = Calendar.getProxy(self.event)
        self.assert_(proxy.isProxy())
        self.assertEqual(proxy, self.event)
        self.assertEqual(proxy.currentlyModifying, None)

        proxy.rruleset = self._createRuleSetItem('weekly')
        self.assert_(self.event in proxy.rruleset.events)
        self.assertEqual(proxy.getNextOccurrence().occurrenceFor, self.event)
        self.assertEqual(len(list(proxy._generateRule())), self.weekly['count'])
        
        proxy.startTime = self.start + timedelta(days=1)
        
        # the change shouldn't propagate
        # holding off on this test
        #self.assertEqual(proxy.startTime, self.start)

    def testThisAndFutureModification(self):
        self.event.rruleset = self._createRuleSetItem('weekly')
        second = self.event.getNextOccurrence()
        
        #one simple THISANDFUTURE modification
        second.changeThisAndFuture('displayName', 'Modified title')
        self.assertEqual(second.modifies, 'thisandfuture')
        self.assertEqual(second.modificationFor, self.event)
        self.assert_(list(self.event.rruleset.rrules)[0].until < second.startTime)
        self.assertEqual(second.displayName, 'Modified title')
        self.assertEqual(list(second.rruleset.rrules)[0].freq, 'weekly')
        self.assertEqual(second.startTime, second.modificationRecurrenceID)
        self.assertEqual(len(list(self.event.modifications)), 1)
        
        # make sure a backup occurrence is created
        self.assertEqual(len(list(second.occurrences)), 2)
        third = second.getNextOccurrence()
        self.assertEqual(third.displayName, 'Modified title')
        
        # another simple THISANDFUTURE modification
        thirdChangedStart = third.startTime + timedelta(hours=1)
        third.changeThisAndFuture('startTime', thirdChangedStart)
        fourth = third.getNextOccurrence()
        self.assertEqual(fourth.startTime-thirdChangedStart, timedelta(weeks=1))
        self.assertEqual(len(list(second.occurrences)), 1)
        self.assertEqual(self.event, third.modificationFor)
        self.assertEqual(len(list(self.event.modifications)), 2)
        
        # make sure second's rruleset was updated
        self.assert_(list(second.rruleset.rrules)[0].until < thirdChangedStart)
        
        # changing second's displayName again shouldn't delete third
        second.changeThisAndFuture('displayName', 'Twice modified title')
        self.assertEqual(third.startTime, thirdChangedStart)
        self.assertEqual(third.displayName, 'Twice modified title')
        self.assertEqual(len(list(self.event.modifications)), 2)
        
        # change second's rule, deleting third
        second.changeThisAndFuture('rruleset', 
                                   third.rruleset.copy(cloudAlias='copying'))
        newthird = second.getNextOccurrence()
        
        self.assertNotEqual(third, newthird)
        self.failIf(newthird.startTime == thirdChangedStart)
        self.assertEqual(list(second.rruleset.rrules)[0].until, 
                              self.weekly['end'])
        self.assertEqual(len(list(self.event.modifications)), 1)
        
        # make a THIS change to a THISANDFUTURE modification 
        second.changeThis('displayName', "THIS modified title")
        
        secondModified = second
        second = second.occurrenceFor

        self.assertEqual(second.occurrenceFor, None)
        self.assertEqual(second.modificationFor, self.event)
        self.assertNotEqual(secondModified.displayName, second.displayName)
        self.assertEqual(second.getNextOccurrence(), newthird)
        self.assertEqual(newthird.displayName, 'Twice modified title')
        self.assertEqual(len(list(self.event.modifications)), 1)
                
        # make a destructive THISANDFUTURE change to the THIS modification
        secondModified.changeThisAndFuture('duration', timedelta(hours=2))
        second = secondModified
        third = second.getNextOccurrence()
        self.assertEqual(len(list(self.event.modifications)), 1)
        self.assertEqual(second.modificationFor, self.event)
        self.assertEqual(second.modifications, None)
        self.assertEqual(third.endTime, datetime(2005, 7, 18, 15))
        self.assertEqual(second.modifies, 'thisandfuture')
        

        # check if modificationRecurrenceID works for changeThis mod
        second.startTime = datetime(2005, 7, 12, 13) #implicit THIS mod
        self.assertEqual(second.modifies, 'this')
        self.assertEqual(second.getNextOccurrence().startTime,
                         datetime(2005, 7, 18, 13))
                         
        third.lastModified = 'Changed lastModified.'
        fourth = third.getNextOccurrence()
        fourth.startTime += timedelta(hours=4)

        # propagating thisandfuture modification to this
        third.changeThisAndFuture('displayName', 'Yet another title')
        thirdModified = third
        third = third.occurrenceFor
        
        self.assertEqual(third.displayName, 'Yet another title')
        self.failIf(third.hasLocalAttributeValue('lastModified'))
        self.assertEqual(third.modificationFor, self.event)
        self.assertEqual(third.modifies, 'thisandfuture')
        self.assertEqual(thirdModified.modifies, 'this')
        self.assertEqual(thirdModified.lastModified, 'Changed lastModified.')

        self.assertEqual(fourth.modificationFor, third)
        
        #check propagation if first in rule is overridden with a THIS mod
        thirdModified.changeThisAndFuture('displayName', 'Changed again')
        self.assertEqual(third.displayName, 'Changed again')
        self.assertEqual(thirdModified.displayName, 'Changed again')
        self.assertEqual(fourth.displayName, 'Changed again')

        # THIS mod to master with no occurrences because of later modifications 
        # doesn't create a mod
        self.event.startTime += timedelta(hours=6)
        self.assertEqual(self.event.occurrenceFor, self.event)
        self.assertEqual(self.event.modificationRecurrenceID,
                         self.event.startTime)

        # change master event back
        oldrule = self.event.rruleset
        self.event.changeThisAndFuture('rruleset', 
                                      third.rruleset.copy(cloudAlias='copying'))

        self.assert_(oldrule.isDeleted)
        self.assert_(second.isDeleted and third.isDeleted and fourth.isDeleted)
              
        #make a THIS modification
        self.event.startTime -= timedelta(hours=6)
        eventModified = self.event
        self.event = self.event.occurrenceFor
        self.assertEqual(self.event.occurrenceFor, None)
        self.assertEqual(eventModified.startTime, self.start)
        
        self.assertEqual(self.event.startTime, self.start + timedelta(hours=6))



#tests to write:
"""

test getNextOccurrence with wacky duration stuff, date ordering issues

test anyTime, allDay, and no duration  events

test getOccurrencesBetween for events with no duration

test getNextOccurrence logic for finding modification or occurrence, make sure 
    new occurrences get attributes copied, have the proper kind

test stamping and unstamping behavior, changing stamped item THISANDFUTURE

test indefinite recurrence


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


test automatic icalUID setting

test recurrence behavior around DST (duration vs. endTime)

Test THIS modification moving outside the existing rule's date range

# deleteEvent() -> delete all modifications and occurrences for this event, delete self
# removeOne() -> remove this item, exclude its recurrenceID from the parent rule
# removeFuture() -> remove this item, delete future occurrences and modifications, modify master's rule to end before this occurrence

# expand getCustomDescription() "TuTh every second week for 5 weeks", or "complex" if no description is available for the rule

should isCustom continue to return False after removeOne() is called?  If so, then exdates should be ignored.

what default behavior is appropriate when delete() is called on an occurrence or modification?

reminders - lots of work :)

For UI testing, write a test menu item to create a recurring item.

tzical -> pyicu timezone

pyicu timezone -> rrule

# update spec: occurrences better explanation, getMaster override in GeneratedOccurrence, timezone stored entirely in startTime
# update spec: when creating an occurrence, references whose inverse has cardinality single lost
# update spec: changing a ruleset -> changes events automatically
# update spec: add cleanRule()
# update spec: THIS modifications can't cross into different rules
# update spec: add changeThisAndFuture and changeThis
# update spec: changing an rrule always makes a THISANDFUTURE modification
# update spec: changeThis on something where modifies=THISANDFUTURE isn't quite right in the spec
# update spec: changing the rule behavior
# update spec: thisandfuture mod to stamped attribute is ignored for items not sharing that stamp?

"""