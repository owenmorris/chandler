#   Copyright (c) 2005-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""
Unit tests for recurring events
"""

import unittest, os
from datetime import datetime, timedelta, time
import dateutil.rrule

from application import schema
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.tasks import TaskStamp
from osaf.pim import EventStamp, has_stamp
from osaf.pim.calendar.Recurrence import RecurrenceRule, RecurrenceRuleSet
from PyICU import ICUtzinfo
from i18n.tests import uw

from application.dialogs.RecurrenceDialog import getProxy
from itertools import chain

import osaf.pim.tests.TestDomainModel as TestDomainModel
from chandlerdb.item.ItemError import NoSuchAttributeError

class RecurringEventTest(TestDomainModel.DomainModelTestCase):
    """ Test CalendarEvent Recurrence """

    def setUp(self):
        super(RecurringEventTest,self).setUp()
        self.start = datetime(2005, 7, 4, 13, tzinfo=ICUtzinfo.default) #1PM, July 4, 2005

        self.daily = {'end'    : datetime(2006, 9, 14, 19,
                                          tzinfo=ICUtzinfo.default),
                       'start' : self.start,
                       'count' : 45}

        self.weekly = {'end'   : datetime(2005, 11, 14, 13,
                                          tzinfo=ICUtzinfo.default),
                       'start' : self.start,
                       'count' : 20}

        self.monthly = {'end'   : datetime(2005, 11, 4, 13,
                                           tzinfo=ICUtzinfo.default),
                       'start' : self.start,
                       'count' : 5}
        self.event = self._createEvent()

    def _createEvent(self):
        event = Calendar.CalendarEvent(None, itsView=self.rep.view)
        event.startTime = self.start
        event.endTime = event.startTime + timedelta(hours=1)
        event.anyTime = False
        event.summary = uw("Sample event")
        return event

    def _createRuleSetItem(self, freq):
        ruleItem = RecurrenceRule(None, itsView=self.rep.view)
        ruleItem.until = getattr(self, freq)['end']
        ruleItem.untilIsDate = False
        if freq == 'weekly':
            self.assertEqual(ruleItem.freq, 'weekly', 
                             "freq should default to weekly")
        else:
            ruleItem.freq = freq
        ruleSetItem = RecurrenceRuleSet(None, itsView=self.rep.view)
        ruleSetItem.addRule(ruleItem)
        return ruleSetItem

 	

    def testOccurrenceMatchingMaster(self):
        """
        Make sure an occurrence with the same startTime as master is created
        when calling getNextOccurrence.

        """
        event = self.event
        event.anyTime = True
        event.rruleset = self._createRuleSetItem('daily')
        start = event.effectiveStartTime
        occurrence = event.getFirstOccurrence()
        self.assertEqual(occurrence.effectiveStartTime, start)

    def testEndMatchesStart(self):
        """
        Events whose endTime matches the start of a range shouldn't be
        included in that range.
        
        """
        event      = self.event
        rangeStart = datetime.combine(self.start.date(),
                             time(0, tzinfo=ICUtzinfo.default)) + timedelta(1)
        rangeEnd   = rangeStart + timedelta(1)
        oneWeek    = timedelta(7)

        event.endTime = rangeStart
        self.failIf(event.isBetween(rangeStart, rangeEnd))
        
        event.duration = timedelta(hours=1)
        event.anyTime  = True
        self.failIf(event.isBetween(rangeStart, rangeEnd))

        event.allDay = True
        self.failIf(event.isBetween(rangeStart, rangeEnd))
        
        # reset event
        event.anyTime = event.allDay = False
        event.endTime = rangeStart
        
        # now test recurrence
        self.event.rruleset = self._createRuleSetItem('weekly')
        def testBetween(expectedLength):        
            eventsBetween = list(event.getOccurrencesBetween(rangeStart, rangeEnd))
            self.assertEqual(len(eventsBetween), expectedLength)
    
            eventsBetween = list(event.getOccurrencesBetween(rangeStart + oneWeek,
                                                             rangeEnd + oneWeek))
            self.assertEqual(len(eventsBetween), expectedLength)

        def makeThisAndFutureChange(attr, value):
            # A helper, because EventStamp.changeThisAndFuture() takes a
            # "fully-qualified" attribute name
            attrName = getattr(EventStamp, attr).name
            event.changeThisAndFuture(attrName, value)
            
        testBetween(0)
        
        makeThisAndFutureChange('duration', timedelta(hours=1))
        makeThisAndFutureChange('anyTime', True)
        testBetween(0)
        
        makeThisAndFutureChange('anyTime', False)
        makeThisAndFutureChange('allDay', True)
        testBetween(0)
        
        # zero duration events
        makeThisAndFutureChange('duration', timedelta(0))
        makeThisAndFutureChange('startTime', rangeStart)
        testBetween(1)

        makeThisAndFutureChange('allDay', False)
        testBetween(1)
        

        event.removeRecurrence()
        self.failUnless(event.isBetween(rangeStart, rangeEnd))
        
        event.allDay = True
        self.failUnless(event.isBetween(rangeStart, rangeEnd))
        

    def testModificationEnum(self):
        self.assertEqual(self.event.modifies, None)
        self.event.modifies = "this"

    def testSimpleRuleBehavior(self):
        # self.event.occurrenceFor should default to None
        self.assertEqual(self.event.occurrenceFor, None)
        # getNextOccurrence for events without recurrence should be None
        self.assertEqual(self.event.getNextOccurrence(), None)
        self.failIf(self.event.isGenerated)

        self.event.rruleset = self._createRuleSetItem('weekly')
        self.assertEqual(self.event.isCustomRule(), False)

        secondStart = datetime(2005, 7, 11, 13, tzinfo=ICUtzinfo.default)
        second = self.event.getFirstOccurrence().getNextOccurrence()
        self.assert_(second.isGenerated)
        self.assertEqual(self.event.createDateUtilFromRule()[1], secondStart)
        self.assertEqual(second.startTime, secondStart)
        self.assertEqual(second.summary, self.event.summary)

        # make sure getNextOccurrence returns the same item when called twice
        self.assertEqual(second,
                         self.event.getFirstOccurrence().getNextOccurrence())

        third = second.getNextOccurrence()
        thirdStart = datetime(2005, 7, 18, 13, tzinfo=ICUtzinfo.default)
        self.assertEqual(third.startTime, thirdStart)

        fourthStart = datetime(2005, 7, 25, 13, tzinfo=ICUtzinfo.default)
        fourth = self.event._createOccurrence(fourthStart)
        self.assert_(fourth.isGenerated)
        self.assertEqual(fourth, third.getNextOccurrence())

        # create a modification to be automatically deleted
        fourth.summary = uw("changed title")

        second.cleanRule()
        self.assertEqual(len(self.event.occurrences), 2)

        self.event.rruleset.rrules.first().until = thirdStart

        #changing the rule should delete our modified fourth
        self.assertEqual(len(self.event.occurrences), 1)


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
        self.assertEqual(len(self.event.occurrences), 1)
        # We should really check this for other generated occurrences!
        self.failUnless(has_stamp(self.event.occurrences.first(), EventStamp))


    def testThisModification(self):
        self.event.summary = uw("Master Event") #no rruleset, so no modification
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.assertEqual(self.event.modifies, None)

        calmod = self.event.getFirstOccurrence().getNextOccurrence()
        self.assertEqual(self.event.modifications, None)

        calmod.changeThis('displayName', uw('Modified occurrence'))

        self.assertEqual(calmod.modificationFor, self.event.itsItem)
        self.assertEqual(calmod.getFirstInRule(), self.event)

        self.assertEqual(list(self.event.modifications), [calmod.itsItem])

        evtaskmod = calmod.getNextOccurrence()

        TaskStamp(evtaskmod).add()

        # changes to an event should, by default, create a THIS modification
        self.assertEqual(EventStamp(evtaskmod.modificationFor), self.event)
        self.assertEqual(evtaskmod.getFirstInRule(), self.event)

        for modOrMaster in [calmod, evtaskmod, self.event]:
            self.assertEqual(modOrMaster.getMaster(), self.event)

        # make a THIS modification ...
        occurrenceOfMaster = self.event.getRecurrenceID(self.event.startTime)
        occurrenceOfMaster.summary = uw("Modification to master")
        # that should leave self.event still a master
        self.assertEqual(None, self.event.occurrenceFor)
        # ... and leave its displayName unchanged
        self.assertNotEqual(self.event.summary,
                            uw("Modification to master"))

        # test getNextOccurrence ordering, bug 4083
        generated = evtaskmod.getNextOccurrence()
        self.assertEqual(self.event.getFirstOccurrence().getNextOccurrence(),
                         calmod)

        evtaskmod.startTime = calmod.startTime - timedelta(hours=1)
        self.assertEqual(self.event.getFirstOccurrence().getNextOccurrence(),
                         evtaskmod)
        self.assertEqual(calmod.getNextOccurrence(), generated)

        evtaskmod.startTime = generated.startTime + timedelta(hours=1)
        self.assertEqual(self.event.getFirstOccurrence().getNextOccurrence(),
                         calmod)
        self.assertEqual(calmod.getNextOccurrence(), generated)
        self.assertEqual(generated.getNextOccurrence(), evtaskmod)


    def testRuleChange(self):
        self.event.rruleset = self._createRuleSetItem('weekly')
        # an automatically generated backup occurrence should exist
        self.assertEqual(len(self.event.occurrences), 1)

        count = 3
        newRule = dateutil.rrule.rrule(dateutil.rrule.WEEKLY, count = count,
                                       interval = 3, dtstart = self.start)

        self.event.setRuleFromDateUtil(newRule)
        self.assertEqual(self.event.isCustomRule(), True)

        #XXX: i18n this is an application managed description that will change
        #     depending on the locale the test is run under
        self.assertEqual(self.event.getCustomDescription(), "every 3 weeks until 8/15/05")

        # changing the rule for the master, modifies should stay None
        self.assertEqual(self.event.modifies, None)

        # all occurrences except the first should be deleted, then one should 
        # be generated
        self.assertEqual(len(self.event.occurrences), 1)
        self.assertEqual(len(list(self.event._generateRule())), count)

        threeWeeks = self.start + timedelta(days=21)
        occurs = list(self.event.getOccurrencesBetween(
                        threeWeeks +  timedelta(minutes=30),
                        datetime(2005, 8, 15, 14, tzinfo=ICUtzinfo.default)))
        self.assertEqual(occurs[0].startTime, threeWeeks)
        self.assertEqual(occurs[1].startTime,
                         datetime(2005, 8, 15, 13, tzinfo=ICUtzinfo.default))
        self.rep.check()

    def testRuleSetChangeThisAndFuture(self):
        # Make a ruleset change the way the detail view does it
        newRuleset = self._createRuleSetItem('weekly')
        self.event.changeThisAndFuture(EventStamp.rruleset.name, newRuleset)
        occurrence = self.event.getRecurrenceID(self.event.startTime)
        self.failUnless(self.event.occurrences is not None)
        self.failUnless(self.event.occurrenceFor is None)
        self.failUnlessEqual(occurrence.occurrenceFor, self.event.itsItem)
        self.failUnlessEqual(occurrence.startTime, self.event.startTime)
        
        # Now, make a THISANDFUTURE change on the first occurrence
        occurrence.changeThisAndFuture(EventStamp.rruleset.name,
                                       self._createRuleSetItem('monthly'))
        
        # Make sure that the first occurrence is preserved                               
        self.failUnlessEqual(occurrence.occurrenceFor, self.event.itsItem)
        self.failUnlessEqual(occurrence.startTime, self.event.startTime)
        self.failUnless(occurrence.rruleset is self.event.rruleset)
        
    def testMoveMasterDates(self):
        # Make a new rruleset item
        self.event.rruleset = self._createRuleSetItem('daily')
        
        # Find its third occurrence
        first = self.event.getRecurrenceID(self.event.startTime)
        third = first.getNextOccurrence().getNextOccurrence()
        
        # Make that occur weekly
        third.changeThisAndFuture(EventStamp.rruleset.name,
                                  self._createRuleSetItem('weekly'))
        
        # Check that third is now a master
        self.failUnlessEqual(third.occurrenceFor, None)
        
        # And make sure self.event has exactly two occurrences
        self.failUnlessEqual(len(list(self.event._generateRule())), 2)
        
        # Now, move first's events ahead in time
        first = self.event.getRecurrenceID(self.event.startTime)
        first.changeThisAndFuture(EventStamp.startTime.name,
                                  self.event.startTime + timedelta(minutes=20))
        self.failUnlessEqual(len(list(self.event._generateRule())), 2)

    def testIcalUID(self):
        self.assertEqual(self.event.icalUID, unicode(self.event.itsItem.itsUUID))
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.assertEqual(self.event.icalUID, 
                         self.event.getFirstOccurrence().icalUID)

    def testBug5483(self):
        """Check that an EXDATE of the first occurrence is correctly excluded."""
        self.start = self.event.startTime - timedelta(days=1)

        ruleItem = RecurrenceRule(None, itsView=self.rep.view)
        ruleItem.freq = 'daily'
        ruleSetItem = RecurrenceRuleSet(None, itsView=self.rep.view)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem

        self.event.rruleset.exdates = [self.event.startTime]

        oneWeek = self.start + timedelta(days=7, minutes=30)

        occurrences = self.event.getOccurrencesBetween(self.start, oneWeek)

        self.failIf(self.event.itsItem in occurrences)
        
    def testChange_thisSummary_futureDate(self):
        self.event.rruleset = self._createRuleSetItem('daily')
        first = self.event.getFirstOccurrence()
        second = first.getNextOccurrence()
        
        second.changeThis(EventStamp.summary.name, u'I changed this')
        second.changeThisAndFuture(EventStamp.startTime.name,
                                   second.startTime + timedelta(hours=1))
                                   
        # Current behaviour is to make second a modification here
        self.failIfEqual(second, second.getMaster())
        # Make sure our summary really changed
        self.failIfEqual(second.summary, second.getMaster().summary)
                                   
        # Next occurrence after second should be in one day's time
        # (this is the first failure in bug 7042)
        self.failUnlessEqual(second.getNextOccurrence().startTime,
                             second.startTime + timedelta(days=1))
                             
        # ... and make sure the next occurrence has the correct summary
        self.failUnlessEqual(self.event.summary,
                             second.getNextOccurrence().summary)

    def testChange_thisDate_futureDate(self):
        self.event.rruleset = self._createRuleSetItem('weekly')
        first = self.event.getFirstOccurrence()
        second = first.getNextOccurrence()
        
        second.changeThis(EventStamp.startTime.name,
                          second.startTime + timedelta(minutes=-45))
        self.failUnlessEqual(second.getNextOccurrence().startTime,
                             self.event.startTime + timedelta(days=14))
                             
        second.changeThisAndFuture(EventStamp.startTime.name,
                                   second.startTime + timedelta(hours=1))
        self.failUnlessEqual(second.getNextOccurrence().startTime,
                             self.event.startTime + timedelta(days=14, hours=1))

    def testChange_thisSummary_futureStartTime_futureStartTime(self):
        self.event.rruleset = self._createRuleSetItem('daily')
        first = self.event.getFirstOccurrence()
        third = first.getNextOccurrence().getNextOccurrence()
        
        # Change the third occurrence's summary
        third.changeThis(EventStamp.summary.name, u'I changed this')
        # Now move it, and all future events, back 30 minutes
        third.changeThisAndFuture(EventStamp.startTime.name,
                                  third.startTime + timedelta(minutes=-30))
        # And now, forward by an hour. This triggered bug 7042
        third.changeThisAndFuture(EventStamp.startTime.name,
                                  third.startTime + timedelta(hours=1))
        

    def testRemoveRecurrence(self):
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.event.removeRecurrence()
        self.failUnless(self.event.occurrences is None)

        self.event.rruleset = self._createRuleSetItem('weekly')
        second = self.event.getFirstOccurrence().getNextOccurrence()
        second.removeRecurrence()
        self.assertEqual(self.event.occurrences, None)

        self.event.rruleset = self._createRuleSetItem('weekly')
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()
        third.changeThisAndFuture(EventStamp.startTime.name, third.startTime + timedelta(hours=1))
        second = self.event.getFirstOccurrence().getNextOccurrence()

        rule = third.rruleset.rrules.first()

        third.removeRecurrence()
        self.failUnless(third.occurrences is None)
        
        self._checkDeleted([rule], [second])

        # test a THIS modification to master, then removing recurrence
        self.event.rruleset = self._createRuleSetItem('weekly')
        eventModified = self.event.getRecurrenceID(self.event.startTime)
        eventModified.startTime += timedelta(hours=1)
        eventModified.removeRecurrence()
        self._checkDeleted([self.event], [eventModified])
        # bug 4084, rruleset isn't getting deleted from eventModified
        self.failIf(eventModified.hasLocalAttributeValue('rruleset'))
        # bug 4681, removeRecurrence doesn't work for AllDay events
        self.event = eventModified
        self.event.allDay = True
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.event.removeRecurrence()


    def testProxy(self):
        self.failIf(self.event.isProxy())

        proxy = getProxy('test', self.event.itsItem)
        stampedProxy = EventStamp(proxy)
        proxy.dialogUp = True # don't try to create a dialog in a test
        self.failUnless(proxy.isProxy())
        self.assertEqual(proxy, self.event.itsItem)
        self.assertEqual(proxy.currentlyModifying, None)
        self.failUnless(proxy is getProxy('test', proxy))

        stampedProxy.rruleset = self._createRuleSetItem('weekly')
        self.failUnless(self.event.itsItem in stampedProxy.rruleset.events)
        self.assertEqual(stampedProxy.getFirstOccurrence().occurrenceFor,
                         self.event.itsItem)
        self.assertEqual(len(list(stampedProxy._generateRule())),
                         self.weekly['count'])

        stampedProxy.startTime = self.start + timedelta(days=1)
        self.assertEqual(self.event.startTime, self.start)
        self.assertEqual(stampedProxy.startTime, self.start + timedelta(days=1))

    def testGetFirstOccurrence(self):
        self.event.rruleset = self._createRuleSetItem('weekly')
        first = self.event.getFirstOccurrence()
        second = first.getNextOccurrence()
        self.assertEqual(first.recurrenceID, self.start)
        
        first.changeThis(EventStamp.startTime.name,
                         self.start - timedelta(hours=1))
        
        self.assertEqual(first, self.event.getFirstOccurrence())
        
        second.changeThis(EventStamp.startTime.name,
                          self.start - timedelta(hours=2))
        
        # weird edge case: later occurrence moved earlier
        self.assertEqual(second, self.event.getFirstOccurrence())
        
        second.deleteThis()
        self.assertEqual(first, self.event.getFirstOccurrence())

        first.deleteThis()
        self.assertEqual(self.event.getFirstOccurrence().startTime,
                         self.start + timedelta(14))
        # make the recurrence end before it's begun
        self.event.rruleset.rrules.first().until = self.start
        self.assertEqual(None, self.event.getFirstOccurrence())

        
    def testThisAndFutureModification(self):
        #FIXME: test rruleset changes
        self.event.rruleset = self._createRuleSetItem('weekly')
        lastUntil = self.event.getLastUntil()
        second = self.event.getFirstOccurrence().getNextOccurrence()

        #one simple THISANDFUTURE modification
        second.changeThisAndFuture('displayName', uw('Modified title'))

        self.assertEqual(second.modificationFor, None)

        self.assert_(list(self.event.rruleset.rrules)[0].until < second.startTime)
        self.assertEqual(second.summary, uw('Modified title'))
        self.assertEqual(list(second.rruleset.rrules)[0].freq, 'weekly')
        self.assertEqual(second.startTime, second.recurrenceID)
        self.assertEqual(second.icalUID, unicode(second.itsItem.itsUUID))
        self.assertEqual(second.getLastUntil(), lastUntil)

        # make sure second is not one of its own occurrences
        self.failIf(second.itsItem in second.occurrences)
        # make sure a backup occurrence is created
        self.assertEqual(len(list(second.occurrences)), 1)
        third = second.getFirstOccurrence().getNextOccurrence()
        self.assertEqual(third.summary, uw('Modified title'))

        # create a changed fourth event to make sure its recurrenceID gets moved
        # when third's startTime is changed
        fourth = third.getNextOccurrence()
        fourth.changeThis('displayName', uw('fourth'))

        thirdStart = third.startTime
        thirdChangedStart = thirdStart + timedelta(hours=1)
        third.changeThisAndFuture(EventStamp.startTime.name, thirdChangedStart)

        # fourth's time shouldn't have changed, but its recurrenceID should have
        self.assertEqual(fourth.startTime - thirdStart, timedelta(weeks=1))
        self.assertEqual(len(list(third.occurrences)), 2)
        self.assertEqual(fourth.recurrenceID,
                         fourth.startTime + timedelta(hours=1))
        self.assertEqual(third.rruleset, fourth.rruleset)
        self.assertEqual(third.icalUID, fourth.icalUID)
        self.assertNotEqual(second.icalUID, third.icalUID)

        # make sure second's rruleset was updated
        self.assert_(list(second.rruleset.rrules)[0].until < thirdChangedStart)

        # changing second's displayName again shouldn't create a new occurrence,
        # and third should be completely unchanged
        thirdLastUntil = third.getLastUntil()

        second.changeThisAndFuture('displayName', uw('Twice modified title'))

        self.assertEqual(len(list(second.occurrences)), 1) # should use checkOccurrencesMatchEvent()
        self.assertEqual(third.startTime, thirdChangedStart)
        self.assertEqual(third.summary, uw('Modified title'))
        self.assertEqual(third.getLastUntil(), thirdLastUntil)

        # change second's rule 
        second.changeThisAndFuture(EventStamp.rruleset.name, 
                                   third.rruleset.copy(cloudAlias='copying'))
        newthird = second.getFirstOccurrence().getNextOccurrence()

        self.assertNotEqual(third, newthird)
        self.failIfEqual(newthird.startTime, thirdChangedStart)
        self.assertEqual(list(second.rruleset.rrules)[0].until, thirdLastUntil)

        # make a THIS change to a THISANDFUTURE modification 
        second.changeThis('displayName', uw("THIS modified title"))

        secondModified = second.getRecurrenceID(second.startTime)

        self.assertEqual(second.occurrenceFor, None)
        self.assertNotEqual(secondModified.summary, second.summary)
        self.assertEqual(second.getFirstOccurrence().getNextOccurrence(),
                         newthird)
        self.assertEqual(newthird.summary, uw('Twice modified title'))

        # make a THISANDFUTURE change to the THIS modification
        # FIXME: time changes need to preserve modifications for 0.6
        secondModified.changeThisAndFuture(EventStamp.duration.name, timedelta(hours=2))
        second = secondModified
        third = second.getFirstOccurrence().getNextOccurrence()
        self.assertNotEqual(newthird, third)
        self.assertEqual(third.endTime, datetime(2005, 7, 18, 15,
                         tzinfo=ICUtzinfo.default))
        # FIXME: these should work after time change preservation is implemented
        #self.assertEqual(second.displayName, u'Twice modified title')
        #self.assertEqual(third.displayName, u'Twice modified title')


        # check if modificationRecurrenceID works for changeThis mod
        second.startTime = datetime(2005, 7, 12, 13,
                                    tzinfo=ICUtzinfo.default) #implicit THIS mod
        self.assertEqual(second.getNextOccurrence().startTime,
                         datetime(2005, 7, 18, 13, tzinfo=ICUtzinfo.default))

        third.itsItem.lastModified = uw('Changed lastModified.')
        fourth = third.getNextOccurrence()
        fourth.startTime += timedelta(hours=4)

        # propagating thisandfuture modification to this
        third.changeThisAndFuture('displayName', uw('Yet another title'))
        thirdModified = third
        third = EventStamp(third.occurrenceFor)
        # Because fourth is a modification, its title should NOT have changed
        self.assertEqual(fourth.summary, uw('Twice modified title'))

        self.assertNotEqual(thirdModified.icalUID, second.icalUID)
        self.assertEqual(thirdModified.icalUID, third.icalUID)
        self.assertEqual(third.icalUID, fourth.icalUID)
        self.assertEqual(third.rruleset, fourth.rruleset)

        self.assertEqual(third.summary, uw('Yet another title'))
        self.failIf(third.itsItem.hasLocalAttributeValue('lastModified'))
        self.assertEqual(thirdModified.itsItem.lastModified, uw('Changed lastModified.'))

        self.assertEqual(EventStamp(fourth.modificationFor), third)

        # check propagation if first in rule is overridden with a THIS mod
        thirdModified.changeThisAndFuture('displayName', uw('Changed again'))
        self.failUnless(thirdModified.occurrenceFor is third.itsItem)
        self.assertEqual(thirdModified.summary, uw('Changed again'))
        self.assertEqual(third.summary, uw('Changed again'))

        # THIS mod to master with no occurrences because of later modifications 
        # doesn't create a mod
        self.event.startTime += timedelta(hours=6)
        self.assertEqual(self.event.occurrenceFor, None)
        self.assertEqual(self.event.startTime, self.event.recurrenceID)
        self.assertEqual(list(self.event._generateRule()), [])

        # change master event back to the original rule
        oldrule = self.event.rruleset
        self.event.changeThisAndFuture(EventStamp.rruleset.name,
                                      third.rruleset.copy(cloudAlias='copying'))

        self.assert_(oldrule.isDeleted)
        self.assertEqual(self.event.startTime, self.event.recurrenceID)

        # make sure changing master also changes master's recurrenceID
        # and master's lastUntil
        delta = timedelta(hours=3) + self.start - self.event.startTime
        lastUntil = self.event.getLastUntil()
        self.event.changeThisAndFuture(EventStamp.startTime.name, self.start + timedelta(hours=3))
        self.assertEqual(self.event.startTime, self.event.recurrenceID)
        self.assertEqual(self.event.getLastUntil(), delta + lastUntil)

        #make a THIS modification
        eventModified = self.event.getRecurrenceID(self.event.startTime)
        eventModified.startTime -= timedelta(hours=3)
        self.assertEqual(self.event.occurrenceFor, None)
        self.assertEqual(eventModified.startTime, self.start)

        self.assertEqual(self.event.startTime, self.start + timedelta(hours=3))

        # Test moving a later THIS modification when changing an earlier mod

        second = self.event.getFirstOccurrence().getNextOccurrence()
        second.summary = uw("second")
        third = second.getNextOccurrence()
        third.summary = uw("third")

        second.changeThisAndFuture('displayName', uw('changed title'))

        self.assertNotEqual(self.event.icalUID, second.icalUID)
        self.assertEqual(second.icalUID, third.icalUID)
        self.assertEqual(third.modificationFor, second.occurrenceFor)

    def _checkDeleted(self, items, notdeleted):
        for item in chain(items, notdeleted):
             # Ignore any stamps when getting the isDeleted method
            isDeleted = getattr(item, 'itsItem', item).isDeleted()
            if item in notdeleted:
                self.failIf(isDeleted,
                            "Item was deleted, but shouldn't have been: %s"
                            % repr(item))
            else:
                self.failUnless(isDeleted,
                             "Item wasn't deleted: %s" % repr(item))

    def testDelete(self):
        event = self.event
        rruleset = event.rruleset = self._createRuleSetItem('weekly')


        # check a simple recurring rule
        event.removeRecurrence()
        self.failUnless(event.occurrences is None)
        self._checkDeleted([rruleset], [event])

        # THIS modification
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.getFirstOccurrence().getNextOccurrence().summary = 'changed'
        event.removeRecurrence()
        self.failUnless(event.occurrences is None)
        self._checkDeleted([rruleset], [event])

        # THIS modification to master 
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.changeThis('displayName', 'changed')
        masterOccurrence = event.getRecurrenceID(event.startTime)
        event.removeRecurrence()

        # The removeRecurrence() call will delete master as well
        # as all occurrences except masterOccurrence. (Otherwise, we'd
        # lose any changes present in masterOccurrence).
        self._checkDeleted([rruleset, event], [masterOccurrence])
        event = masterOccurrence
        self.failUnless(event.occurrenceFor is None)

        # THISANDFUTURE modification
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second = event.getFirstOccurrence().getNextOccurrence()
        second.changeThisAndFuture('displayName', uw('changed'))
        event.removeRecurrence()
        self._checkDeleted([rruleset, event, second, second.rruleset],
                           [event, second, second.rruleset])

        # simple deleteThis
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second = event.getFirstOccurrence().getNextOccurrence()
        second.deleteThis()
        self._checkDeleted([second], [])
        self.assertEqual(rruleset.exdates, [self.start + timedelta(days=7)])
        event.removeRecurrence()

        # deleteThis on a master
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.deleteThis()
        self._checkDeleted([], [event])
        self.assertEqual(rruleset.exdates, [self.start])
        self.assertEqual(event.occurrenceFor, None)
        event.removeRecurrence()

        # deleteThis on a THIS modification
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second = event.getFirstOccurrence().getNextOccurrence()
        second.changeThis(EventStamp.startTime.name, self.start + timedelta(hours=1))
        second.deleteThis()
        self._checkDeleted([second], [])
        self.assertEqual(rruleset.exdates, [self.start + timedelta(days=7)])
        event.removeRecurrence()

        # simple deleteAll
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second = event.getFirstOccurrence().getNextOccurrence()
        second.deleteAll()
        self._checkDeleted([rruleset, event, second], [])

        # deleteAll on master
        event = self._createEvent()
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.deleteAll()
        self._checkDeleted([rruleset, event], [])

        # deleteAll on a modification to master
        event = self._createEvent()
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.changeThis('displayName', uw('modification to master'))
        newmaster = event
        event = event.getRecurrenceID(event.startTime)
        event.deleteAll()
        self._checkDeleted([rruleset, event, newmaster], [])

        # deleteThisAndFuture
        event = self._createEvent()
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second =  event.getFirstOccurrence().getNextOccurrence()
        third  = second.getNextOccurrence()
        third.changeThis('displayName', uw("Changed title"))
        third.deleteThisAndFuture()

        self._checkDeleted([event, second, third], [event])
        self.assertEqual(event.getLastUntil(), self.start + timedelta(days=7))
        
    def testDeleteItsItem(self):
        # delete of underlying Note item
        event = self._createEvent()
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        occurrences = event.getOccurrencesBetween(None, None)
        event.itsItem.delete()
        self._checkDeleted(chain([event], occurrences), [])

    def testDeleteRuleSet(self):
        event = self.event
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        rruleset.delete(recursive=True)


    def testRdatesAndExdates(self):
        event = self.event
        rruleset = event.rruleset = self._createRuleSetItem('weekly')

        # create an RDATE and an EXDATE
        rruleset.rdates = [self.start + timedelta(days=1)]
        extraDay = event.getFirstOccurrence().getNextOccurrence()
        extraDay.changeThis('displayName', uw('Extra day'))
        self.assertEqual(extraDay.startTime, self.start + timedelta(days=1))
        rruleset.exdates = [self.start + timedelta(days=7)]
        twoWeeks = extraDay.getNextOccurrence()
        self.assertEqual(twoWeeks.startTime, self.start + timedelta(days=14))

        extraDay.changeThisAndFuture(EventStamp.startTime.name,
                                     extraDay.startTime + timedelta(hours=1))
        self.assertEqual(rruleset.rdates,  [])
        self.assertEqual(rruleset.exdates, [])

        self.assertEqual(extraDay.rruleset.rdates,
                         [self.start + timedelta(days=1, hours=1)])
        self.assertEqual(extraDay.rruleset.exdates,
                         [self.start + timedelta(days=7, hours=1)])

    def testNoRRules(self):
        # A test for bug 6921: Oracle calendar sometimes creates
        # VEVENTs with just a bunch of RDATES, and no RRULE.
        event = self.event
        ruleSetItem = RecurrenceRuleSet(None, itsView=self.rep.view)
        
        tzinfo = ICUtzinfo.getInstance("US/Eastern")
        dates = [
            datetime(2006, 3, 11, 10, tzinfo=tzinfo),
            datetime(2006, 3, 15, 21, tzinfo=tzinfo),
            datetime(2006, 5, 4, 10, tzinfo=tzinfo),
        ]
        
        ruleSetItem.rrules = []
        ruleSetItem.rdates = dates
        event.rruleset = ruleSetItem
        
        occurrenceDates = list(occurrence.startTime for occurrence in
                               event.getOccurrencesBetween(None, None))
        self.failUnlessEqual(occurrenceDates, dates)

    def testAllDay(self):
        event = self.event
        event.allDay = True
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        self.assert_(event.allDay)
        self.assertEqual(self.start, event.startTime)
        second = event.getFirstOccurrence().getNextOccurrence()
        self.failUnless(second.allDay)
        second.changeThis(EventStamp.allDay.name, False)
        self.failIf(second.allDay)        

    def testNeverEndingEvents(self):
        ruleItem = RecurrenceRule(None, itsView=self.rep.view)
        ruleItem.freq = 'daily'
        ruleSetItem = RecurrenceRuleSet(None, itsView=self.rep.view)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem

        # make a THISANDFUTURE modification

        second = self.event.getFirstOccurrence().getNextOccurrence()
        second.changeThisAndFuture(EventStamp.startTime.name,
                                   self.start + timedelta(minutes=30))
        self.failIf(second.rruleset.rrules.first().hasLocalAttributeValue('until'))

class NaiveTimeZoneRecurrenceTest(TestDomainModel.DomainModelTestCase):
    """Test of recurring events that have startTimes that occur on different
       dates depending on whether timezone UI is enabled"""

    tzinfo = ICUtzinfo.getInstance("US/Pacific")
    enableTimeZones = False
    
    def checkOccurrencesMatchEvent(self, occurrences):
        """
        A little helper to check that occurrences contains
        exactly 1 event, and that event corresponds to self.event. 
        """
        self.failUnlessEqual(len(occurrences), 1)
        firstOccurrence = EventStamp(occurrences[0])
        self.failIfEqual(firstOccurrence, self.event)
        self.failUnlessEqual(firstOccurrence.occurrenceFor, self.event.itsItem)
        self.failUnlessEqual(firstOccurrence.startTime, self.event.startTime)
        self.failUnlessEqual(firstOccurrence.endTime, self.event.endTime)

    def setUp(self):
        # We want to set up the default timezone, and whether we're
        # in timezone-free mode, so that these tests are predictable.
        # In order to make subsequent tests predictable -- i.e., not
        # dependent on the order in which tests are run -- we
        # need to save this global state at test start, and
        # restore it once we're done (i.e. in tearDown()).
        super(NaiveTimeZoneRecurrenceTest, self).setUp()

        tzPrefs = schema.ns('osaf.app', self.rep.view).TimezonePrefs

        # Stash away the global values
        self._saveTzinfo = ICUtzinfo.default
        self._saveTzEnabled = tzPrefs.showUI

        # ... and set up the values we want to run the test with
        ICUtzinfo.default = self.tzinfo
        tzPrefs.showUI = self.enableTimeZones

        # 2006/04/09 05:00 Europe/London == 2006/04/08 US/Pacific
        start = datetime(2006, 4, 9, 5, 0,
                          tzinfo = ICUtzinfo.getInstance("Europe/London"))

        # Make a weekly event with the above as the startTime, and
        # stash it in self.event
        self.event = Calendar.CalendarEvent(None, itsView=self.rep.view)
        self.event.startTime = start
        self.event.duration = timedelta(hours=2)
        self.event.anyTime = False
        self.event.summary = uw("Sneaky recurring event")

        ruleItem = RecurrenceRule(None, itsView=self.rep.view, freq='weekly')
        ruleSetItem = RecurrenceRuleSet(None, itsView=self.rep.view)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem

    def tearDown(self):
        tzPrefs = schema.ns('osaf.app', self.rep.view).TimezonePrefs

        # Put everything back nicely....
        ICUtzinfo.default = self._saveTzinfo
        tzPrefs.showUI = self._saveTzEnabled

        # ... and tip-toe out the room. Move along, nothing to see here.
        super(NaiveTimeZoneRecurrenceTest, self).tearDown()


    def testEdgeCases(self):

        oneWeek = timedelta(weeks=1)

        # OK, start on April 9, and get the occurrences in the next week.
        # (Since timezones are disabled here, we are supposed to be ignoring
        # them in comparisons, and expect self.event to appear here).
        rangeStart = datetime(2006, 4, 9, tzinfo=ICUtzinfo.floating)

        occurrences = self.event.getOccurrencesBetween(rangeStart,
                                                       rangeStart + oneWeek)
        self.checkOccurrencesMatchEvent(occurrences)

        # Check that no events occur in the week preceding April 9 ...
        occurrences = self.event.getOccurrencesBetween(rangeStart - oneWeek,
                                                       rangeStart)
        self.failUnlessEqual(occurrences, [])

        # ... and lastly check that 1 event occurs in the week after April
        # 9, and that its startTime is exactly a week after the starting
        # event.
        occurrences = self.event.getOccurrencesBetween(rangeStart + oneWeek,
                                                       rangeStart + 2*oneWeek)
        self.failUnlessEqual(len(occurrences), 1)
        self.failUnlessEqual(occurrences[0].startTime,
                             self.event.startTime + oneWeek)


class TimeZoneEnabledRecurrenceTest(NaiveTimeZoneRecurrenceTest):
    """Just like NaiveTimeZoneRecurrenceTest, but tests with timezones
       enabled"""

    # OK, turn time zones on for this test
    enableTimeZones = True

    def testEdgeCases(self):

        rangeStart = datetime(2006, 4, 9, tzinfo=ICUtzinfo.floating)
        oneWeek = timedelta(weeks=1)

        # Here, we expect events to occur according to the usual
        # rules of datetime objects. So, in the week of April 9,
        # there will be an occurrence on the 15th (i.e. which occurs
        # at 5 a.m. on the 16th in Europe/London).
        occurrences = self.event.getOccurrencesBetween(rangeStart,
                                                       rangeStart + oneWeek)

        self.failUnlessEqual(len(occurrences), 1)
        self.failUnlessEqual(occurrences[0].startTime,
                             self.event.startTime + oneWeek)

        # self.event occurs in the week preceding April 9th (i.e.
        # on April 8th, US/Pacific).
        occurrences = self.event.getOccurrencesBetween(rangeStart - oneWeek,
                                                       rangeStart)
        self.checkOccurrencesMatchEvent(occurrences)

        # Lastly, make sure no events occur in the week preceding April 2nd.
        occurrences = self.event.getOccurrencesBetween(rangeStart - oneWeek,
                                                       rangeStart - 2*oneWeek)
        self.failUnlessEqual(occurrences, [])


#tests to write:
"""

test getOccurrencesBetween crossing THISANDFUTRE modification

test simultaneous events

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
# update spec: lots of other new methods :)

"""

if __name__ == "__main__":
    unittest.main()
