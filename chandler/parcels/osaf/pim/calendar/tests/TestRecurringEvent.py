#   Copyright (c) 2005-2007 Open Source Applications Foundation
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
from datetime import datetime, timedelta, time, date
import dateutil.rrule
from util import testcase

from application import schema
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim import *
from osaf.pim.calendar.Recurrence import RecurrenceRule, RecurrenceRuleSet
from i18n.tests import uw

from application.dialogs.RecurrenceDialog import getProxy
from itertools import chain

from chandlerdb.item.ItemError import NoSuchAttributeError

class RecurringEventTest(testcase.SharedSandboxTestCase):
    """ Test CalendarEvent Recurrence """
    
    index = None

    def setUp(self):
        super(RecurringEventTest, self).setUp()
        
        view = self.sandbox.itsView
        
        self.start = datetime(2005, 7, 4, 13,
                              tzinfo=view.tzinfo.default) #1PM, July 4, 2005

        self.daily = {'end'    : datetime(2006, 9, 14, 19,
                                          tzinfo=view.tzinfo.default),
                       'start' : self.start,
                       'count' : 45}

        self.weekly = {'end'   : datetime(2005, 11, 14, 13,
                                          tzinfo=view.tzinfo.default),
                       'start' : self.start,
                       'count' : 20}

        self.monthly = {'end'   : datetime(2005, 11, 4, 13,
                                           tzinfo=view.tzinfo.default),
                       'start' : self.start,
                       'count' : 5}
        self.event = self._createEvent()
        
    def _createEvent(self):
        event = Calendar.CalendarEvent(None, itsParent=self.sandbox)
        event.startTime = self.start
        event.endTime = event.startTime + timedelta(hours=1)
        event.anyTime = False
        event.summary = uw("Sample event")
        return event

    def _createRuleSetItem(self, freq):
        ruleItem = RecurrenceRule(None, itsParent=self.sandbox)
        ruleItem.until = getattr(self, freq)['end']
        ruleItem.untilIsDate = False
        if freq == 'weekly':
            self.assertEqual(ruleItem.freq, 'weekly', 
                             "freq should default to weekly")
        else:
            ruleItem.freq = freq
        ruleSetItem = RecurrenceRuleSet(None, itsParent=self.sandbox)
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
                                      time(0, tzinfo=self.view.tzinfo.default)) + timedelta(1)
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
        event.rruleset = self._createRuleSetItem('weekly')
        def testBetween(expectedLength):        
            eventsBetween = list(event.getOccurrencesBetween(rangeStart, rangeEnd, True))
            self.assertEqual(len(eventsBetween), expectedLength)
            # @@@triageChange: this fails when triage automatically creates
            # modifications
            #eventsBetween = list(event.getOccurrencesBetween(rangeStart + oneWeek,
                                                             #rangeEnd + oneWeek))
            #self.assertEqual(len(eventsBetween), expectedLength)

        firstMod = event.getFirstOccurrence()
        def makeThisAndFutureChange(attr, value):
            # A helper, because EventStamp.changeThisAndFuture() takes a
            # "fully-qualified" attribute name
            attrName = getattr(EventStamp, attr).name
            # @@@triageChange: this doesn't do what we expect when even has been
            # modified
            #event.changeThisAndFuture(attrName, value)
            firstMod.changeThisAndFuture(attrName, value)
            
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

        secondStart = datetime(2005, 7, 11, 13,
                               tzinfo=self.view.tzinfo.default)
        second = self.event.getFirstOccurrence().getNextOccurrence()
        # @@@triageChange: this fails when triage automatically creates
        # modifications        
        #self.assert_(second.isGenerated)
        self.assertEqual(self.event.createDateUtilFromRule()[1], secondStart)
        self.assertEqual(second.startTime, secondStart)
        self.assertEqual(second.summary, self.event.summary)

        # make sure getNextOccurrence returns the same item when called twice
        self.assertEqual(second,
                         self.event.getFirstOccurrence().getNextOccurrence())

        third = second.getNextOccurrence()
        thirdStart = datetime(2005, 7, 18, 13,
                              tzinfo=self.view.tzinfo.default)
        self.assertEqual(third.startTime, thirdStart)

        fourthStart = datetime(2005, 7, 25, 13,
                               tzinfo=self.view.tzinfo.default)
        # @@@triageChange: can't _createOccurrence when the occurrence has
        # already been made by triage machinery.  Instead just get fourth.
        #fourth = self.event._createOccurrence(fourthStart)
        #self.assert_(fourth.isGenerated)
        #self.assertEqual(fourth, third.getNextOccurrence())
        fourth = third.getNextOccurrence()

        # create a modification to be automatically deleted
        fourth.summary = uw("changed title")
        
        simpleOccurrence = fourth.getNextOccurrence()

        second.cleanRule()

        self.event.rruleset.rrules.first().until = thirdStart
        
        # changing the rule doesn't delete off-rule modifications
        self.assert_(fourth.itsItem in self.event.occurrences)
        self.assert_(simpleOccurrence.itsItem not in self.event.occurrences)

        self.event.deleteOffRuleModifications()

        self.assert_(fourth.itsItem not in self.event.occurrences)


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
        # @@@triageChange: this fails when triage automatically creates
        # modifications
        #self.assertEqual(len(self.event.occurrences), 1)
        # We should really check this for other generated occurrences!
        self.failUnless(has_stamp(self.event.occurrences.first(), EventStamp))


    def testThisModification(self):
        self.event.summary = uw("Master Event") #no rruleset, so no modification
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.assertEqual(self.event.modifies, None)

        calmod = self.event.getFirstOccurrence().getNextOccurrence()
        # @@@triageChange: this fails when triage automatically creates
        # modifications
        #self.assertEqual(len(self.event.modifications), 0)

        calmod.changeThis('displayName', uw('Modified occurrence'))

        self.assertEqual(calmod.modificationFor, self.event.itsItem)
        self.assertEqual(calmod.getFirstInRule(), self.event)

        # @@@triageChange: this fails when triage automatically creates
        # modifications
        #self.assertEqual(list(self.event.modifications), [calmod.itsItem])

        evtaskmod = calmod.getNextOccurrence()

        # Add the task stamp to just THIS event
        TaskStamp(CHANGE_THIS(evtaskmod)).add()

        # changes to an event should, by default, create a THIS modification
        self.assertEqual(EventStamp(evtaskmod.modificationFor), self.event)
        self.assertEqual(evtaskmod.getFirstInRule(), self.event)

        for modOrMaster in [calmod, evtaskmod, self.event]:
            self.assertEqual(modOrMaster.getMaster(), self.event)

        self.failUnless(evtaskmod.itsItem in TaskStamp.getCollection(self.view))
        self.failIf(self.event.itsItem in TaskStamp.getCollection(self.view))
        
        TaskStamp(CHANGE_THIS(evtaskmod)).remove()
        self.failIf(evtaskmod.itsItem in TaskStamp.getCollection(self.view))
        self.failIf(self.event.itsItem in TaskStamp.getCollection(self.view))


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


    def testChangeAll(self):
        self.event.summary = uw("Master Event") #no rruleset, so no modification
        self.event.rruleset = self._createRuleSetItem('weekly')
        
        firstOccurrence = self.event.getFirstOccurrence()
        secondOccurrence = firstOccurrence.getNextOccurrence()
        
        originalStart = self.event.startTime
        secondStart = secondOccurrence.startTime.replace(hour=10, minute=5)
        
        # Try an ALL change to the second event ...
        secondOccurrence.changeAll(EventStamp.startTime.name, secondStart)
        
        # ... make sure that changed the master
        self.failUnlessEqual(self.event.startTime,
                             originalStart.replace(hour=10, minute=5))
        self.failUnlessEqual(secondOccurrence.startTime, secondStart)
        
        # Make THIS changes to the 2nd & 3rd events' displayNames
        thirdOccurrence = secondOccurrence.getNextOccurrence()
        thirdOccurrence.changeThis('displayName', uw("Not a master!"))
        secondOccurrence.changeThis('displayName', uw("Also not a master"))
        
        thirdOccurrence.changeAll('displayName', uw("Changed, baby"))
        self.failUnlessEqual(thirdOccurrence.itsItem.displayName,
                             uw("Changed, baby"))
        self.failUnlessEqual(self.event.itsItem.displayName,
                             uw("Changed, baby"))
        self.failUnlessEqual(secondOccurrence.itsItem.displayName,
                             uw("Also not a master"))

    def testRuleChange(self):
        self.event.rruleset = self._createRuleSetItem('weekly')
        # an automatically generated backup occurrence should exist
        # @@@triageChange: this fails when triage automatically creates
        # modifications        
        #self.assertEqual(len(self.event.occurrences), 1)
        # instead, just assert there's more than one occurrence
        self.assert_(len(self.event.occurrences) > 0)
        
        count = 3
        newRule = dateutil.rrule.rrule(dateutil.rrule.WEEKLY, count = count,
                                       interval = 3, dtstart = self.start)

        self.event.setRuleFromDateUtil(newRule)
        self.assertEqual(self.event.isCustomRule(), True)

        #XXX: i18n this is an application managed description that will change
        #     depending on the locale the test is run under
        value = datetime.combine(date(2005, 8, 15), time(0, tzinfo=self.sandbox.itsView.tzinfo.default))
        dateStr = shortDateTimeFormat.format(self.sandbox.itsView, value).split(' ')        
        self.assertEqual(self.event.getCustomDescription(), "Every 3 weeks until %s" % dateStr[0])

        # changing the rule for the master, modifies should stay None
        self.assertEqual(self.event.modifies, None)

        # all occurrences except the first should be deleted, then one should 
        # be generated
        # @@@triageChange: this fails when triage automatically creates
        # modifications
        #self.assertEqual(len(self.event.occurrences), 1)
        # instead, just assert there's more than one occurrence
        self.assert_(len(self.event.occurrences) > 0)
        self.assertEqual(len(list(self.event._generateRule())), count)

        threeWeeks = self.start + timedelta(days=21)
        occurs = list(self.event.getOccurrencesBetween(
                        threeWeeks +  timedelta(minutes=30),
                        datetime(2005, 8, 15, 14,
                                 tzinfo=self.view.tzinfo.default)))
        self.assertEqual(occurs[0].startTime, threeWeeks)
        self.assertEqual(occurs[1].startTime,
                         datetime(2005, 8, 15, 13,
                                  tzinfo=self.view.tzinfo.default))
        self.view.check()

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
        
        # Check that third is not a master ...
        self.failIfEqual(third, third.getMaster())
        third = third.getMaster()
        
        # And make sure self.event has exactly two occurrences
        self.failUnlessEqual(len(list(self.event._generateRule())), 2)
        
        # Now, move first's events ahead in time
        first = self.event.getRecurrenceID(self.event.startTime)
        first.changeThisAndFuture(EventStamp.startTime.name,
                                  self.event.startTime + timedelta(minutes=20))
        self.failUnlessEqual(len(list(self.event._generateRule())), 2)

    def testIcalUID(self):
        self.assertEqual(self.event.itsItem.icalUID, unicode(self.event.itsItem.itsUUID))
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.assertEqual(self.event.itsItem.icalUID, 
                         self.event.getFirstOccurrence().itsItem.icalUID)

    def testBug5483(self):
        """Check that an EXDATE of the first occurrence is correctly excluded."""
        self.start = self.event.startTime - timedelta(days=1)

        ruleItem = RecurrenceRule(None, itsParent=self.sandbox)
        ruleItem.freq = 'daily'
        ruleSetItem = RecurrenceRuleSet(None, itsParent=self.sandbox)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem

        self.event.rruleset.exdates = [self.event.startTime]

        oneWeek = self.start + timedelta(days=7, minutes=30)

        occurrences = self.event.getOccurrencesBetween(self.start, oneWeek)

        self.failIf(self.event.itsItem in occurrences)

    def testFirstOccurrence(self):
        """
        Test of getFirstOccurrence(), including the case where
        the master's startTime has been excluded.
        """
        self.event.rruleset = self._createRuleSetItem('weekly')
        
        firstOccurrence = self.event.getFirstOccurrence()
        self.failUnlessEqual(firstOccurrence,
                             self.event.getFirstOccurrence())
        self.failUnlessEqual(firstOccurrence.startTime, self.event.startTime)
        
        # Now exclude the first occurrence
        self.event.rruleset.exdates = [self.event.startTime]
        
        # Make sure that deleted the firstOccurrence object
        self._checkDeleted(firstOccurrence)
        
        # Make sure we don't generate multiple objects for the
        # first occurrence (bug 7072)
        firstOccurrence = self.event.getFirstOccurrence()
        self.failUnlessEqual(firstOccurrence,
                             self.event.getFirstOccurrence())
                             
        # Make sure we have the correct startTime
        self.failUnlessEqual(firstOccurrence.startTime,
                             self.event.startTime + timedelta(days=7))
        

        
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
        # @@@triageChange: this fails when triage automatically creates
        # modifications, because second.getNextOccurrence() is a modification
        #self.failUnlessEqual(second.getNextOccurrence().startTime,
                             #second.startTime + timedelta(days=1))
                             
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
        
        # @@@triageChange: this fails when triage automatically creates
        # modifications which aren't overridden by changeThisAndFuture
        #self.failUnlessEqual(second.getNextOccurrence().startTime,
                             #self.event.startTime + timedelta(days=14, hours=1))

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
        
    def testTimeModification(self):
        """
        Make sure we do the right thing with recurrenceIDs when
        making a THISANDFUTURE change to startTime
        """
        event = self.event
        event.startTime = datetime(2006, 1, 12, 9, 15,
                                   tzinfo=self.view.tzinfo.default)
        event.rruleset = self._createRuleSetItem('daily')
        
        first = event.getFirstOccurrence()
        third = first.getNextOccurrence().getNextOccurrence()
        # Make a THIS change of summary to first...
        first.changeThis(EventStamp.summary.name, uw("New First Summary"))
        
        # ... a THIS startTime change to third
        thirdStart = third.startTime + timedelta(hours=1)
        third.changeThis(EventStamp.startTime.name, thirdStart)
        self.failUnlessEqual(third.startTime, thirdStart)
        
        # ... and finally a THISANDFUTURE startTime change to first
        first.changeThisAndFuture(EventStamp.startTime.name,
                                  first.startTime + timedelta(hours=-1))
        
        # Make sure third's startTime is unchanged
        # c.f. https://bugzilla.osafoundation.org/show_bug.cgi?id=8222#c9
        self.failUnlessEqual(third.startTime, thirdStart)

        # Double-check its recurrenceID
        self.failUnlessEqual(
            third.recurrenceID,
            first.startTime + timedelta(days=2)
        )

        # ... and make sure we haven't manufactured an extra event by not
        # updating the recurrenceID of third                          
        after = datetime(2006, 1, 12, tzinfo=self.view.tzinfo.default)
        before = datetime(2006, 1, 19, tzinfo=self.view.tzinfo.default)
        self.failUnlessEqual(
            len(first.getMaster().getOccurrencesBetween(after, before)),
            7)


    def testChangeAllResetsMod(self):
        self.event.rruleset = self._createRuleSetItem('weekly')
        first = self.event.getFirstOccurrence()
        second = first.getNextOccurrence()
        
        # Make a THIS change to the 2nd event
        second.changeThis('displayName', u'A better name...')
        self.failUnlessEqual(second.summary, u'A better name...')
        self.failIfEqual(second.summary, second.getNextOccurrence().summary)
        
        # ... and now make an ALL change to the 2nd event
        second.changeAll('displayName', u'The best name!')
        # ... this should actually change the value for second ...
        self.failUnlessEqual(second.summary, u'The best name!')
        # ... and, for example, the next event in the series
        self.failUnlessEqual(second.summary, second.getNextOccurrence().summary)
        
        # Lastly, make a THIS change to the master's occurrence
        first.changeThis('displayName', u'A new name')
        # ... followed by an ALL change to the 2nd occurrence
        second.changeAll('displayName', u'An even bester name')
        # Make sure the master's occurrence is unchanged
        self.failUnlessEqual(first.summary, u'A new name')
        # ... but that the 2nd and 3rd occurrences have changed
        self.failUnlessEqual(second.summary, u'An even bester name')
        self.failUnlessEqual(second.summary, second.getNextOccurrence().summary)
        
    
    def testRemoveRecurrence(self):
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.event.removeRecurrence()
        self.failUnless(not self.event.occurrences)

        self.event.rruleset = self._createRuleSetItem('weekly')
        second = self.event.getFirstOccurrence().getNextOccurrence()
        second.removeRecurrence()
        self.failUnless(not self.event.occurrences)

        self.event.rruleset = self._createRuleSetItem('weekly')
        third = self.event.getFirstOccurrence().getNextOccurrence().getNextOccurrence()
        third.changeThisAndFuture(EventStamp.startTime.name, third.startTime + timedelta(hours=1))
        second = self.event.getFirstOccurrence().getNextOccurrence()

        rule = third.rruleset.rrules.first()

        third.removeRecurrence()
        self.failUnless(not third.occurrences)
        
        self._checkDeleted(rule)
        self._checkNotDeleted(second)

        # test a THIS modification to master, then removing recurrence
        self.event.rruleset = self._createRuleSetItem('weekly')
        eventModified = self.event.getRecurrenceID(self.event.startTime)
        eventModified.startTime += timedelta(hours=1)
        eventModified.removeRecurrence()
        self._checkDeleted(eventModified)
        self._checkNotDeleted(self.event)
        # bug 4084, rruleset isn't getting deleted from eventModified
        self.failIf(self.event.hasLocalAttributeValue('rruleset'))
        # bug 4681, removeRecurrence doesn't work for AllDay events
        self.event.allDay = True
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.event.removeRecurrence()


    def testProxy(self):
        self.failIf(self.event.itsItem.isProxy)

        proxy = getProxy('test', self.event.itsItem)
        stampedProxy = EventStamp(proxy)
        proxy.dialogUp = True # don't try to create a dialog in a test
        self.failUnless(proxy.isProxy)
        self.assertEqual(proxy, self.event.itsItem)
        self.assertEqual(proxy.changing, None)
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

        # @@@triageChange: this fails when triage automatically creates
        # modifications
        #self.assertEqual(second.modificationFor, None)
        
        self.assertNotEqual(second, second.getMaster())
        
        second = second.getMaster()

        self.assert_(list(self.event.rruleset.rrules)[0].until < second.startTime)
        self.assertEqual(second.summary, uw('Modified title'))
        self.assertEqual(list(second.rruleset.rrules)[0].freq, 'weekly')
        self.assertEqual(second.startTime, second.recurrenceID)
        # @@@triageChange: this fails when triage automatically makes second
        # a modification, instead turn second's master's into second
        second = second.getMaster()
        self.assertEqual(second.itsItem.icalUID,
                         unicode(second.itsItem.itsUUID))
        self.assertEqual(second.getLastUntil(), lastUntil)

        # make sure second is not one of its own occurrences
        self.failIf(second.itsItem in second.occurrences)
        # make sure a backup occurrence is created
        # @@@triageChange: this fails when triage automatically creates
        # modifications
        #self.assertEqual(len(list(second.occurrences)), 1)
        self.assert_(len(list(second.occurrences)) > 0)
        third = second.getFirstOccurrence().getNextOccurrence()
        # @@@triageChange: this fails when triage automatically creates
        # modifications
        #self.assertEqual(third.summary, uw('Modified title'))

        # create a changed fourth event to make sure its recurrenceID gets moved
        # when third's startTime is changed
        fourth = third.getNextOccurrence()
        fourth.changeThis('displayName', uw('fourth'))

        thirdStart = third.startTime
        thirdChangedStart = thirdStart + timedelta(hours=1)
        third.changeThisAndFuture(EventStamp.startTime.name, thirdChangedStart)
        
        self.assertNotEqual(third, third.getMaster())
        self.assertEqual(third.startTime, thirdChangedStart)
        self.assertEqual(third.startTime, third.getMaster().startTime)
        third = third.getMaster()

        # fourth's startTime and recurrenceID should have changed, since
        # fourth only modified displayName
        self.assertEqual(fourth.startTime - third.startTime, timedelta(weeks=1))
        # @@@triageChange: this fails when triage automatically creates
        # modifications
        #self.assertEqual(len(list(third.occurrences)), 2)
        #self.assertEqual(fourth.recurrenceID, fourth.startTime)
        self.assertEqual(third.rruleset, fourth.rruleset)
        self.assertEqual(third.itsItem.icalUID, fourth.itsItem.icalUID)
        self.assertNotEqual(second.itsItem.icalUID, third.itsItem.icalUID)

        # make sure second's rruleset was updated
        self.assert_(list(second.rruleset.rrules)[0].until < thirdChangedStart)

        # changing second's displayName again shouldn't create a new occurrence,
        # and third should be completely unchanged
        thirdLastUntil = third.getLastUntil()

        second.changeThisAndFuture('displayName', uw('Twice modified title'))
        # @@@triageChange: this fails when triage automatically creates
        # modifications
        #self.assertEqual(len(list(second.occurrences)), 1) # should use checkOccurrencesMatchEvent()
        #self.assertEqual(third.summary, uw('Modified title'))        
        self.assertEqual(third.startTime, thirdChangedStart)
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
        secondModified.changeThisAndFuture(EventStamp.duration.name, timedelta(hours=2))
        second = secondModified
        third = second.getFirstOccurrence().getNextOccurrence()
        # @@@triageChange: this fails when triage automatically creates
        # modifications 
        #self.assertEqual(newthird, third)
        #self.assertEqual(third.endTime, datetime(2005, 7, 18, 15,
                         #tzinfo=self.view.tzinfo.default))
       
        # secondModified's THIS change (to summary) should still be around
        self.assertEqual(second.summary, uw("THIS modified title"))
        # third should still have the unchanged title
        self.assertEqual(third.summary, uw("Twice modified title"))


        # check if modificationRecurrenceID works for changeThis mod
        second.startTime = datetime(2005, 7, 12, 13,
                                    tzinfo=self.view.tzinfo.default) #implicit THIS mod
        self.assertEqual(second.getNextOccurrence().startTime,
                         datetime(2005, 7, 18, 13,
                                  tzinfo=self.view.tzinfo.default))

        newLastModified = datetime(2005, 8, 11, 14,
                                   tzinfo=self.view.tzinfo.default)
        third.itsItem.lastModified = newLastModified
        fourth = third.getNextOccurrence()
        fourth.startTime += timedelta(hours=4)

        # propagating thisandfuture modification to this
        third.changeThisAndFuture('displayName', uw('Yet another title'))
        thirdModified = third
        third = EventStamp(third.occurrenceFor)
        # fourth is a THIS modification (of startTime), so its title should have changed
        self.assertEqual(fourth.summary, uw('Yet another title'))
        
        thirdModified.summary = uw('Changing title to be overridden')

        self.assertNotEqual(thirdModified.itsItem.icalUID,
                            second.itsItem.icalUID)
        self.assertEqual(thirdModified.itsItem.icalUID, third.itsItem.icalUID)
        self.assertEqual(third.itsItem.icalUID, fourth.itsItem.icalUID)
        self.assertEqual(third.rruleset, fourth.rruleset)

        self.assertEqual(third.summary, uw('Yet another title'))
        self.failIf(third.itsItem.hasLocalAttributeValue('lastModified'))
        self.assertEqual(thirdModified.itsItem.lastModified, newLastModified)

        self.assertEqual(EventStamp(fourth.modificationFor), third)

        # check propagation if first in rule is overridden with a THIS mod
        thirdModified.changeThisAndFuture('displayName', uw('Changed again'))
        self.failUnless(thirdModified.occurrenceFor is third.itsItem)
        self.assertEqual(thirdModified.summary, uw('Changed again'))
        self.assertEqual(third.summary, uw('Changed again'))

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

        self.assertEqual(self.event.startTime, self.start + timedelta(hours=3))

        # Test moving a later THIS modification when changing an earlier mod
        
        second = self.event.getFirstOccurrence().getNextOccurrence()
        second.summary = uw("second")
        third = second.getNextOccurrence()
        third.summary = uw("third")

        second.changeThisAndFuture('displayName', uw('changed title'))

        self.assertNotEqual(self.event.itsItem.icalUID, second.itsItem.icalUID)
        self.assertEqual(second.itsItem.icalUID, third.itsItem.icalUID)
        self.assertEqual(third.modificationFor, second.occurrenceFor)
        self.assertNotEqual(third.itsItem.displayName,
                            second.itsItem.displayName)
        
    @staticmethod
    def isDeleted(item):
        # Ignore any stamps when getting the isLive method
        return not getattr(item, 'itsItem', item).isLive()
    

    def _checkDeleted(self, *items):
        for item in items:
            self.failUnless(self.isDeleted(item),
                            "Item wasn't deleted: %r" % (item,))
                            
    def _checkNotDeleted(self, *items):
        for item in items:
            self.failIf(self.isDeleted(item),
                        "Item was deleted, but shouldn't have been: %r"
                        % (item,))



    def testDelete(self):
        # @@@triageChange: lots of changes made because there's never a normal
        # occurrence for the first occurrence, it's always a modification.

        event = self.event
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        firstMod = event.getFirstOccurrence()


        # check a simple recurring rule
        event.removeRecurrence()
        self.failUnless(not event.occurrences)
        self._checkDeleted(rruleset, firstMod)
        self._checkNotDeleted(event)

        # THIS modification
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        firstMod = event.getFirstOccurrence()
        event.getFirstOccurrence().getNextOccurrence().summary = 'changed'
        event.removeRecurrence()
        self.failUnless(not event.occurrences)
        self._checkDeleted(rruleset, firstMod)
        self._checkNotDeleted(event)
        
        # THIS modification to master
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.changeThis('displayName', 'changed')
        masterOccurrence = event.getRecurrenceID(event.startTime)
        event.removeRecurrence()

        # The removeRecurrence() call will delete master as well
        # as all occurrences except masterOccurrence. (Otherwise, we'd
        # lose any changes present in masterOccurrence).
        self._checkDeleted(rruleset, masterOccurrence)
        self._checkNotDeleted(event)
        self.failUnless(event.occurrenceFor is None)

        # THISANDFUTURE modification
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        firstMod = event.getFirstOccurrence()
        second = firstMod.getNextOccurrence()
        second.changeThisAndFuture('displayName', uw('changed'))
        event.removeRecurrence()
        self._checkDeleted(rruleset, firstMod)
        self._checkNotDeleted(event, second, second.rruleset)

        # simple deleteThis
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        firstMod = event.getFirstOccurrence()
        second = firstMod.getNextOccurrence()
        second.deleteThis()
        self._checkDeleted(second)
        self.assertEqual(rruleset.exdates, [self.start + timedelta(days=7)])
        event.removeRecurrence()

        # deleteThis on a master
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.deleteThis()
        self._checkNotDeleted(event)
        self.assertEqual(rruleset.exdates, [self.start])
        self.assertEqual(event.occurrenceFor, None)
        event.removeRecurrence()

        # deleteThis on a THIS modification
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second = event.getFirstOccurrence().getNextOccurrence()
        second.changeThis(EventStamp.startTime.name, self.start + timedelta(hours=1))
        second.deleteThis()
        self._checkDeleted(second)
        self._checkNotDeleted(rruleset, event)
        self.assertEqual(rruleset.exdates, [self.start + timedelta(days=7)])
        event.removeRecurrence()
        
        # simple deleteAll
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second = event.getFirstOccurrence().getNextOccurrence()
        second.deleteAll()
        self._checkDeleted(rruleset, event, second)

        # deleteAll on master
        event = self._createEvent()
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.deleteAll()
        self._checkDeleted(rruleset, event)

        # deleteAll on a modification to master
        event = self._createEvent()
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.changeThis('displayName', uw('modification to master'))
        newmaster = event
        event = event.getRecurrenceID(event.startTime)
        event.deleteAll()
        self._checkDeleted(rruleset, event, newmaster)

        # deleteThisAndFuture
        event = self._createEvent()
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second =  event.getFirstOccurrence().getNextOccurrence()
        third  = second.getNextOccurrence()
        third.changeThis('displayName', uw("Changed title"))
        third.deleteThisAndFuture()

        self._checkDeleted(third)
        self._checkNotDeleted(event, second)
        self.assertEqual(event.getLastUntil(), self.start + timedelta(days=7))
        
    def testDeleteItsItem(self):
        # delete of underlying Note item
        event = self._createEvent()
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        occurrences = event.getOccurrencesBetween(None, None)
        event.itsItem.delete()           
        self._checkDeleted(*chain([event], occurrences))
        
    def testDeleteRuleSet(self):
        event = self.event
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        rruleset.delete(recursive=True)

    def testDeleteRule(self):
        event = self.event
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        occurrence = event.getFirstOccurrence().getNextOccurrence()
        occurrence.changeThis(EventStamp.startTime.name,
                              occurrence.startTime + timedelta(days=1))
        rruleset.rrules.first().delete(recursive=True)
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
        ruleSetItem = RecurrenceRuleSet(None, itsParent=self.sandbox)
        
        tzinfo = self.view.tzinfo.getInstance("US/Eastern")
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
        self.failUnlessEqual(occurrenceDates, [self.start] + dates)

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
        
    def testAllDayFuture(self):
        # Make sure we can make a THISANDFUTURE change to all-day
        # without messing up the recurrenceIDs of the events in
        # the original series (c.f. Bug 10685)
        event = self.event
        event.rruleset = self._createRuleSetItem('weekly')
        
        first = event.getFirstOccurrence()
        third = first.getNextOccurrence().getNextOccurrence()
        
        self.failIf(event.allDay, "Mis-configured test")
        
        # Make a THISANDFUTURE change of allDay ...
        third.changeThisAndFuture(EventStamp.allDay.name, True)
        
        # Make sure it created a new master
        self.failIfEqual(third.getMaster(), first.getMaster())

        def reallyEqual(dt1, dt2):
            # Helper function, dt1 and dt2 can be datetimes or times ...
            # used to check that timezones haven't been changed accidentally
            # (eg. between default & floating).
            return dt1.tzinfo == dt2.tzinfo and dt1 == dt2
        
        # Since we made a new series starting @ the 3rd event,
        # getting occurrences for the original series over a
        # 31 day range should yield exactly 2 events.
        oldOccurrences = first.getOccurrencesBetween(
                             event.startTime - timedelta(days=1),
                             event.startTime + timedelta(days=30)
                         )
        self.failUnlessEqual(len(oldOccurrences), 2)

        # Make sure that the old occurrences haven't accidentally become
        # startTime modifications, and that their startTimes are still
        # correct.
        for occurrence in oldOccurrences:
            self.failUnless(
                reallyEqual(occurrence.recurrenceID, occurrence.startTime)
            )
            self.failUnless(
                reallyEqual(
                    occurrence.startTime.timetz(),
                    event.startTime.timetz(),
                )
            )

        # The new series is never ending, so there should be 5 events
        # in a 31-day range starting the day before its first occurrence's
        # startTime.
        newOccurrences = third.getOccurrencesBetween(
                             third.startTime - timedelta(days=1),
                             third.startTime + timedelta(days=30)
                         )
        self.failUnlessEqual(len(newOccurrences), 5)
        
        # Again, make sure that all the events aren't startTime
        # modifications. Also, since they now are allDay, their
        # effectiveStartTime should have a timetz() of midnight
        # (with floating tz).
        for occurrence in newOccurrences:
            self.failUnless(
                reallyEqual(occurrence.recurrenceID,
                            occurrence.effectiveStartTime)
            )
            self.failUnless(
                reallyEqual(occurrence.recurrenceID.timetz(),
                            time(0, tzinfo=self.view.tzinfo.floating))
            )
            self.failUnless(
                reallyEqual(occurrence.startTime.timetz(),
                            third.startTime.timetz())
            )
        

        # Now, make a THISANDFUTURE on the 2nd new event, resetting
        # allDay.
        newSecond = third.getNextOccurrence()
        newSecond.changeThisAndFuture(EventStamp.allDay.name, False)
        
        # ... This should result in a 1 event series
        thirdsOccurrences = third.getOccurrencesBetween(
                             third.startTime - timedelta(days=1),
                             third.startTime + timedelta(days=30)
                         )
        self.failUnlessEqual(len(thirdsOccurrences), 1)

        # Again, check that the occurrence has the "floating midnight"
        # effectiveStartTime/recurrenceID.
        for occurrence in thirdsOccurrences:
            self.failUnless(
                reallyEqual(occurrence.recurrenceID,
                            occurrence.effectiveStartTime)
            )
            self.failUnless(
                reallyEqual(occurrence.recurrenceID.timetz(),
                            time(0, tzinfo=self.view.tzinfo.floating))
            )
        
        # And repeat the checks for the latest recurring series
        # (i.e. one with non-allDay events)
        latestOccurrences = newSecond.getOccurrencesBetween(
                                newSecond.startTime - timedelta(days=1),
                                newSecond.startTime + timedelta(days=30)
                           )
        

        self.failUnlessEqual(len(latestOccurrences), 5)

        for occurrence in latestOccurrences:
            self.failUnless(
                reallyEqual(occurrence.recurrenceID,
                            occurrence.effectiveStartTime)
            )
            self.failUnless(
                reallyEqual(occurrence.recurrenceID.timetz(),
                            newSecond.startTime.timetz())
            )
        

    def testChangeTimeZone(self):
        event = self.event
        
        elLay = self.view.tzinfo.getInstance("America/Los_Angeles")
        enWhy = self.view.tzinfo.getInstance("America/New_York")
        
        # Create the event in Los Angeles time ...
        event.startTime = event.startTime.replace(tzinfo=elLay)
        # ... and make it recur
        event.rruleset = self._createRuleSetItem('daily')
        event.rruleset.rrules.first().until = event.startTime + timedelta(days=10)
        
        first = event.getFirstOccurrence()
        third = first.getNextOccurrence().getNextOccurrence()
        
        third.changeThisAndFuture(EventStamp.startTime.name,
                                  third.startTime.replace(tzinfo=enWhy))
                                  
        self.failUnlessEqual(third.getMaster().startTime.tzinfo, enWhy)
        self.failUnlessEqual(third.startTime.tzinfo, enWhy)
        self.failUnlessEqual(third.getNextOccurrence().recurrenceID.tzinfo,
                             enWhy)

    def testChangeAllTimeZone(self):
        event = self.event
        
        elLay = self.view.tzinfo.getInstance("America/Los_Angeles")
        enWhy = self.view.tzinfo.getInstance("America/New_York")
        
        # Create the event in Los Angeles time ...
        event.startTime = event.startTime.replace(tzinfo=elLay)
        # ... and make it recur
        event.rruleset = self._createRuleSetItem('daily')
        event.rruleset.rrules.first().until = event.startTime + timedelta(days=10)
        
        first = event.getFirstOccurrence()
        third = first.getNextOccurrence().getNextOccurrence()
        
        third.changeAll(EventStamp.startTime.name,
                        third.startTime.replace(tzinfo=enWhy))
                                  
        self.failUnlessEqual(self.event.startTime.tzinfo, enWhy)
        self.failUnlessEqual(third.startTime.tzinfo, enWhy)
        self.failUnlessEqual(third.getNextOccurrence().recurrenceID.tzinfo,
                             enWhy)

    def testNeverEndingEvents(self):
        ruleItem = RecurrenceRule(None, itsParent=self.sandbox)
        ruleItem.freq = 'daily'
        ruleSetItem = RecurrenceRuleSet(None, itsParent=self.sandbox)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem

        # make a THISANDFUTURE modification

        second = self.event.getFirstOccurrence().getNextOccurrence()
        second.changeThisAndFuture(EventStamp.startTime.name,
                                   self.start + timedelta(minutes=30))
        self.failIf(second.rruleset.rrules.first().hasLocalAttributeValue('until'))
        
    def testRecurrenceEnd(self):
        event = self.event
        event.startTime = datetime(2006, 11, 11, 13,
                                   tzinfo=self.view.tzinfo.default)
        event.rruleset = self._createRuleSetItem('daily')
        event.rruleset.rrules.first().until = event.startTime + timedelta(days=3)
        
        occurrences = event.getOccurrencesBetween(None, None)
        self.failUnlessEqual(4, len(occurrences))
        
        # Move the second occurrence out past the rrule's until
        secondOccurrence = occurrences[1]
        newStart = datetime.combine(event.startTime.date() + timedelta(days=10),
                                    time(10, tzinfo=self.view.tzinfo.default))
        secondOccurrence.changeThis(EventStamp.startTime.name, newStart)

        occurrences = event.getOccurrencesBetween(None, None)
        self.failUnless(secondOccurrence in occurrences)
        self.failUnlessEqual(4, len(occurrences))


    def testModificationsInCollections(self):
        event = self.event
        collection1 = ListCollection(itsParent=self.sandbox)
        collection2 = ListCollection(itsParent=self.sandbox)

        pim_ns = schema.ns('osaf.pim', self.view)
        all = pim_ns.allCollection
        mine = pim_ns.mine
        trash = pim_ns.trashCollection

        mine.sources.add(collection1)
        mine.sources.add(collection2)

        collection1.add(event.itsItem)
        self.assert_(event.itsItem in collection1)
        
        event.rruleset = self._createRuleSetItem('daily')
        mod = event.getFirstOccurrence()
        self.assert_(mod.itsItem in collection1)
        self.assert_(mod.itsItem in all)
        
        collection2.add(event.itsItem)
        self.assert_(mod.itsItem in collection2)
        
        collection1.remove(event.itsItem)
        self.failIf(mod.itsItem in collection1)
        
        trash.add(self.event.itsItem)
        self.failIf(all in mod.itsItem.appearsIn)
        self.failIf(collection2 in mod.itsItem.appearsIn)

        trash.remove(self.event.itsItem)
        self.assert_(all in mod.itsItem.appearsIn)
        # FIXME this is failing, removing the item from the trash isn't updating
        # appearsIn
        #self.assert_(collection2 in mod.itsItem.appearsIn)



    def testTriageStatus(self):
        """
        Make sure recurring events create Done, Now and Later modifications when
        appropriate, and remove Done modifications when there are extras.
        
        """
        event = self.event
        start = self.start
        # recurrence entirely in the past
        event.rruleset = self._createRuleSetItem('monthly')
        for modification in event.modifications:
            # the first modification will have the same triage status as the
            # original item, so don't test it
            if getattr(modification, EventStamp.recurrenceID.name) != start:
                self.failUnless(modification.triageStatus == TriageEnum.done)

        now = datetime.now(self.view.tzinfo.default)
        
        # make the event recur at least twice in the future
        event.rruleset.rrules.first().until = now + timedelta(days=65)
        
        def countStatus(evt):
            count = {TriageEnum.done  : 0, 
                     TriageEnum.now   : 0, 
                     TriageEnum.later : 0}
            
            for mod in evt.modifications:
                count[mod.triageStatus] += 1
                
            return (count[TriageEnum.later], count[TriageEnum.done],
                    count[TriageEnum.now])

        def assertOneDoneOneLater(evt):
            later, done, now = countStatus(evt)
            self.assertEqual(later, 1)
            self.assertEqual(done,  1)

                
        assertOneDoneOneLater(event)

        # make the later event now, which should create a new later mod
        for mod in event.modifications:
            if mod.triageStatus == TriageEnum.later:
                mod.setTriageStatus(TriageEnum.now)
                event.updateTriageStatus()
                break

        assertOneDoneOneLater(event)

        # make the done event now, creating a new done mod
        for mod in event.modifications:
            if mod.triageStatus == TriageEnum.done:
                doneEvent = mod
                mod.setTriageStatus(TriageEnum.now)
                event.updateTriageStatus()
                break

        assertOneDoneOneLater(event)
        
        # make the original done event done again, the previously created done
        # mod should stop being a modification
        doneEvent.setTriageStatus(TriageEnum.done)
        event.updateTriageStatus()

        assertOneDoneOneLater(event)

        # create an anyTime series starting two days ago, one modification
        # should be now
        event = Calendar.CalendarEvent(None, itsParent=self.sandbox)
        event.startTime = now - timedelta(days=2)
        event.anyTime = True

        rruleset = self._createRuleSetItem('daily')
        rruleset.rrules.first().until = now + timedelta(days=3)

        event.rruleset = rruleset
        
        # pre-triage purge, the first occurrence should be DONE (but in the
        # NOW section), there should be a NOW event for today, and then the 
        # normal DONE and LATER modifications
        self.assertEqual(countStatus(event), (1,2,1)) # later, done, now
        
        # purge the series
        for item in event.modifications:
            item.purgeSectionTriageStatus()
        event.updateTriageStatus()
        
        # The first occurrence should've been removed from the series
        self.assertEqual(countStatus(event), (1,1,1)) # later, done, now

        # create a future series
        event = Calendar.CalendarEvent(None, itsParent=self.sandbox)
        event.startTime = now + timedelta(days=2)

        rruleset = self._createRuleSetItem('daily')
        rruleset.rrules.first().until = now + timedelta(days=14)

        event.rruleset = rruleset
        
        self.assertEqual(countStatus(event), (1,0,0)) # later, done, now
        second = event.getFirstOccurrence().getNextOccurrence()
        second.changeThisAndFuture('displayName', "new displayName")
        
        newMaster = second.getMaster()
        self.assertEqual(newMaster.itsItem.displayName, "new displayName")
        self.assertEqual(countStatus(newMaster), (1,0,0)) # later, done, now
        

        
    def testUnmodify(self):
        """Unmodify should make most attributes be inherited."""
        
        event = self.event
        start = self.start
        # recurrence entirely in the past
        event.rruleset = self._createRuleSetItem('weekly')
        
        second = event.getFirstOccurrence().getNextOccurrence()
        second.changeThis('displayName', uw('Modified occurrence'))
        second.itsItem.setTriageStatus(TriageEnum.now)
        
        second.unmodify()
        self.assertEqual(second.itsItem._triageStatus, TriageEnum.done)
        self.failIf(second.itsItem.hasLocalAttributeValue('displayName'))
        self.failIf(second.itsItem.hasModifiedAttribute(Stamp.stampCollections.name))
        self.failIf(second.itsItem.collections)
        self.failIf(second.itsItem.hasLocalAttributeValue('appearsIn'))

    def testUnmodifyMail(self):
        """
        Unmodify should make most attributes be inherited,
        and remove item from stamp collections.
        """
        
        collection = SmartCollection(None, itsParent=self.sandbox)
        schema.ns("osaf.pim", self.view).mine.sources.add(collection)
        collection.add(self.event.itsItem)
        
        event = self.event
        start = self.start
        MailStamp(event).add()
        # recurrence entirely in the past
        event.rruleset = self._createRuleSetItem('weekly')
        
        second = event.getFirstOccurrence().getNextOccurrence()
        secondStart = second.startTime
        
        second.changeThis(EventStamp.startTime.name, secondStart + timedelta(hours=2))
        second.itsItem.setTriageStatus(TriageEnum.now)
        
        second.unmodify()
        self.assertEqual(second.itsItem._triageStatus, TriageEnum.done)
        self.failUnlessEqual(second.startTime, secondStart)
        self.failIf(second.itsItem.hasModifiedAttribute(Stamp.stampCollections.name))
        # check that our unmodified aren't in any stamp collections
        for stamp in EventStamp, MailStamp:
            self.failIf(second.itsItem in stamp.getCollection(self.view))
        
    def testEventCollection(self):
        events = EventStamp.getCollection(self.view)

        self.failUnless(self.event.itsItem in events)
        
        ruleItem = RecurrenceRule(None, itsParent=self.sandbox, freq='weekly')
        ruleSetItem = RecurrenceRuleSet(None, itsParent=self.sandbox)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem
        
        self.failUnless(self.event.itsItem in events)
        self.failUnless(self.event.modifications)
        
        for modItem in self.event.modifications:
            self.failUnless(modItem in events)
            
    def testGetEvents(self):
        
        # Put self.event in a collection
        collection = SmartCollection(None, itsParent=self.sandbox)
        Calendar.ensureIndexed(collection)
        collection.add(self.event.itsItem)
         
        self.failUnless(self.event.itsItem in collection)
        
        ruleItem = RecurrenceRule(None, itsParent=self.sandbox, freq='daily')
        ruleSetItem = RecurrenceRuleSet(None, itsParent=self.sandbox)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem
                
        self.failUnless(self.event.itsItem in collection)
        self.failUnless(self.event.modifications)
        
        zeroTime = time(0, tzinfo=self.view.tzinfo.default)
        start = datetime.combine(self.event.startTime.date(), zeroTime)
        end = datetime.combine(self.event.startTime.date() + timedelta(days=7),
                               zeroTime)
        recurringEvents = list(Calendar.recurringEventsInRange(
            self.view, start, end, filterColl=collection))
        self.failUnlessEqual(len(recurringEvents), 7)


    def testDateIndex(self):
        
        # Put self.event in a collection
        collection = SmartCollection(None, itsParent=self.sandbox)

        # Make an AttributeIndexDefinition for this collection. Index
        # ContentItem.displayDate (the way the dashboard does).
        indexDef = AttributeIndexDefinition(itsName='testDateIndex',
            itsParent=self.sandbox, useMaster=False,
            attributes=['displayDate'])
        indexDef.makeIndexOn(collection)
        
        collection.add(self.event.itsItem)

        self.failUnlessEqual(
            [self.event.itsItem.itsUUID],
            list(collection.iterkeys(indexDef.itsName))
        )
        now = datetime.now(self.view.tzinfo.default).replace(microsecond=0)
        self.event.startTime = now + timedelta(hours=1)

        # Add a note, with an absolute time reminder in two hours' time
        #  to the collection
        note = Note(None, itsParent=self.sandbox, displayName=u"Hello")
        reminderTime = datetime.now(self.view.tzinfo.default) + timedelta(hours=2)
        note.setUserReminderTime(reminderTime)
        collection.add(note)
        
        # Check sorting ... since Note has a reminder an hour after our
        # event's startTime, make sure it appears last in the index
        self.failUnlessEqual(
            [self.event.itsItem, note],
            list(collection.iterindexvalues(indexDef.itsName))
        )

        # Make event recur ...
        ruleItem = RecurrenceRule(None, itsParent=self.sandbox, freq='daily')
        ruleSetItem = RecurrenceRuleSet(None, itsParent=self.sandbox)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem
                
        self.failUnless(self.event.itsItem in collection)
        
        # Make sure some modifications got created
        self.failUnless(self.event.modifications)

        # ... and that they were all added in the collection
        for mod in self.event.modifications:
            self.failUnless(mod in collection)
        
        # Make sure the date index is still sorted
        indexDates = list(item.displayDate for item in
                      collection.iterindexvalues(indexDef.itsName))
        self.failUnlessEqual(indexDates, sorted(indexDates))

        # Move the event start times to after the note's reminder time
        self.event.changeThisAndFuture(EventStamp.startTime.name,
                                      self.event.startTime + timedelta(hours=3))
        # Make sure the dates are still sorted ...
        indexDates = list(item.displayDate for item in
                      collection.iterindexvalues(indexDef.itsName))
        self.failUnlessEqual(indexDates, sorted(indexDates))

        # The first date in the index should be the Note's reminderTime.
        self.failUnlessEqual(indexDates[0], reminderTime)

    def testDisplayNameIndex(self):
        # Put self.event in a collection
        collection = SmartCollection(None, itsParent=self.sandbox)

        # Make an AttributeIndexDefinition for this collection
        indexDef = AttributeIndexDefinition(
            itsName='testDisplayNameIndex',
            itsParent=self.sandbox, useMaster=False,
            attributes=['displayName'])
        indexDef.makeIndexOn(collection)
        

        self.event.summary = u'Whoa'
        collection.add(self.event.itsItem)

        self.failUnlessEqual(
            [self.event.itsItem],
            list(collection.iterindexvalues(indexDef.itsName))
        )

        # Add a note, with an absolute time reminder in two hours' time
        #  to the collection
        note = Note(None, itsParent=self.sandbox, displayName=u"Hello")
        reminderTime = datetime.now(self.view.tzinfo.default) + timedelta(hours=2)
        note.setUserReminderTime(reminderTime)
        collection.add(note)
        
        self.failUnlessEqual(
            [note, self.event.itsItem],
            list(collection.iterindexvalues(indexDef.itsName))
        )

        # Make the event recur ...
        ruleItem = RecurrenceRule(None, itsParent=self.sandbox, freq='daily')
        ruleSetItem = RecurrenceRuleSet(None, itsParent=self.sandbox)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem
        
        # Check that the index is still sorted ...
        indexDisplayNames = list(item.displayName for item in
                      collection.iterindexvalues(indexDef.itsName))
        self.failUnlessEqual(indexDisplayNames, sorted(indexDisplayNames))
        
        # Make a THISANDFUTURE change to the first item ...
        self.event.changeThisAndFuture('displayName', u'AAA')
        indexDisplayNames = list(item.displayName for item in
                      collection.iterindexvalues(indexDef.itsName))
        # ... and check that the index is still sorted
        self.failUnlessEqual(indexDisplayNames, sorted(indexDisplayNames))
        
    def testTooShortFrequency(self):
        """
        Check that an RRULE frequency of hourly or shorter returns an RDATE for
        the start of the series, and no more occurrences, bug 9035.
        """
        event = self.event
        start = event.startTime

        ruleItem = RecurrenceRule(None, itsParent=self.sandbox)
        ruleItem.freq = 'hourly'
        ruleSetItem = RecurrenceRuleSet(None, itsParent=self.sandbox)
        ruleSetItem.addRule(ruleItem)
        event.rruleset = ruleSetItem
        occurrences = list(event.getOccurrencesBetween(start, 
                                                       start + timedelta(1)))
        
        self.failUnlessEqual(len(occurrences), 1)
        self.failUnlessEqual(occurrences[0].startTime, start)

    def testMakeOrphan(self):
        """
        Make sure orphans have the appropriate attributes and stamps.
        
        """
        event = self.event
        start = event.startTime

        collection1 = ListCollection(itsParent=self.sandbox)

        event.itsItem.displayName = uw('Master displayName')
        event.itsItem.body = uw('Body of the master')
        event.itsItem.icalUID = 'masterUID'
        
        collection1.add(event.itsItem)
        TaskStamp(event).add()

        ruleItem = RecurrenceRule(None, itsParent=self.sandbox, freq='weekly')
        ruleSetItem = RecurrenceRuleSet(None, itsParent=self.sandbox)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem
        
        secondOccurrence = event.getFirstOccurrence().getNextOccurrence()
        secondOccurrence.changeThis('displayName', uw('Modified'))
        MailStamp(CHANGE_THIS(secondOccurrence)).add()
        TaskStamp(CHANGE_THIS(secondOccurrence)).remove()

        # create the orphan
        orphan = secondOccurrence.makeOrphan()

        # make sure it's not an Occurrence
        self.assert_(not isinstance(orphan, Calendar.Occurrence))

        # make sure it's in the right stamp collections, and had the right
        # stamps
        for stamp, stamped in (
            (EventStamp, True),
            (MailStamp, True),
            (TaskStamp, False)
        ):
            self.assertEqual(has_stamp(orphan, stamp), stamped)
            self.assertEqual(orphan in stamp.getCollection(orphan.itsView),
                             stamped)
        
        # the original item should be deleted
        self.assert_(secondOccurrence.itsItem.isDeleted)
        
        self.assertEqual(getattr(orphan, 'inheritFrom', None), None)
        self.assert_(not EventStamp(orphan).isGenerated)
        
        # collection membership should've been copied to the orphan
        self.assert_(orphan in collection1)
        
        self.assertEqual(orphan.displayName, uw('Modified'))
        self.assertEqual(orphan.body, uw('Body of the master'))
        self.failIfEqual(getattr(orphan, 'icalUID', None), 'masterUID')
        
        self.assert_(getattr(orphan, EventStamp.rruleset.name, None) is None)


    def testDisplayDate(self):
        now = datetime.now(self.view.tzinfo.default)
        twoDaysAgo = (datetime.now(self.view.tzinfo.default) -
                      timedelta(days=2)).date()
                      
        event = Calendar.CalendarEvent(None, 
            itsParent=self.sandbox,
            startTime=datetime.combine(
                          now.date() - timedelta(days=2),
                          time(13, 15, tzinfo=self.view.tzinfo.default)
                      ),
            anyTime=False,
        )
        self.failUnlessEqual(event.itsItem.displayDateSource, 'startTime')


        rule = RecurrenceRule(None, itsParent=self.sandbox, freq='weekly')
        event.rruleset = RecurrenceRuleSet(None, itsParent=self.sandbox,
                                           rrules=[rule])

        first = event.getFirstOccurrence()
        next = event.getNextOccurrence(after=now)
        # Make sure these are modifications
        self.failUnless(first.modificationFor is event.itsItem)
        self.failUnless(next.modificationFor is event.itsItem)
        
        # Now, give all events a relative reminder
        CHANGE_ALL(event).userReminderInterval = timedelta(minutes=-10)
        
        # next is in the future, so its displayDateSource is reminder
        self.failUnlessEqual(next.itsItem.displayDateSource, 'reminder')
        # ... with its displayDate being the reminder fire datetime
        self.failUnlessEqual(next.itsItem.displayDate,
                             next.startTime + timedelta(minutes=-10))
        # first is in the past, so its reminder is considered expired,
        # and its displayDate is based off of startTime
        self.failUnlessEqual(first.itsItem.displayDateSource, 'startTime')
        self.failUnlessEqual(first.itsItem.displayDate, first.startTime)

                             
        # Make an after reminder everywhere
        CHANGE_ALL(event).userReminderInterval = timedelta(minutes=30)
        # That makes startTime occur before fire datetime, hence displayDate
        # is equal to startTime
        self.failUnlessEqual(next.itsItem.displayDateSource, 'startTime')
        self.failUnlessEqual(next.itsItem.displayDate, next.startTime)
        self.failUnlessEqual(first.itsItem.displayDateSource, 'startTime')
        self.failUnlessEqual(first.itsItem.displayDate, first.startTime)
        
        # Now, make a THIS change to first's startTime, so that
        # its reminder time is in the future, startTime in the past.
        CHANGE_THIS(first).startTime = now - timedelta(minutes=15)
        self.failUnlessEqual(first.itsItem.displayDateSource, 'reminder')
        self.failUnlessEqual(first.itsItem.displayDate,
                             first.startTime + timedelta(minutes=30))

        # Check that, in the course of all this, we didn't accidentally
        # assign a displayDate to a "pure" occurrence.
        
        occurrence = next
        while occurrence and occurrence.modificationFor:
            occurrence = occurrence.getNextOccurrence()        

        
        self.failIf(occurrence.itsItem.hasLocalAttributeValue('displayDate'))
        self.failIf(occurrence.itsItem.hasLocalAttributeValue('displayDateSource'))


class NaiveTimeZoneRecurrenceTest(testcase.SingleRepositoryTestCase):
    """Test of recurring events that have startTimes that occur on different
       dates depending on whether timezone UI is enabled"""

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

        self.tzinfo = self.view.tzinfo.getInstance("US/Pacific")
    
        tzPrefs = schema.ns('osaf.pim', self.view).TimezonePrefs

        # Stash away the global values
        self._saveTzinfo = self.view.tzinfo.default
        self._saveTzEnabled = tzPrefs.showUI

        # ... and set up the values we want to run the test with
        self.view.tzinfo.setDefault(self.tzinfo)
        tzPrefs.showUI = self.enableTimeZones

        # 2006/04/09 05:00 Europe/London == 2006/04/08 US/Pacific
        start = datetime(2006, 4, 9, 5, 0,
                         tzinfo=self.view.tzinfo.getInstance("Europe/London"))

        # Make a weekly event with the above as the startTime, and
        # stash it in self.event
        self.event = Calendar.CalendarEvent(None, itsView=self.view)
        self.event.startTime = start
        self.event.duration = timedelta(hours=2)
        self.event.anyTime = False
        self.event.summary = uw("Sneaky recurring event")

        ruleItem = RecurrenceRule(None, itsView=self.view, freq='weekly')
        ruleSetItem = RecurrenceRuleSet(None, itsView=self.view)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem

    def tearDown(self):
        tzPrefs = schema.ns('osaf.pim', self.view).TimezonePrefs

        # Put everything back nicely....
        self.view.tzinfo.setDefault(self._saveTzinfo)
        tzPrefs.showUI = self._saveTzEnabled

        # ... and tip-toe out the room. Move along, nothing to see here.
        super(NaiveTimeZoneRecurrenceTest, self).tearDown()


    def testEdgeCases(self):

        oneWeek = timedelta(weeks=1)

        # OK, start on April 9, and get the occurrences in the next week.
        # (Since timezones are disabled here, we are supposed to be ignoring
        # them in comparisons, and expect self.event to appear here).
        rangeStart = datetime(2006, 4, 9, tzinfo=self.view.tzinfo.floating)

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

        rangeStart = datetime(2006, 4, 9, tzinfo=self.view.tzinfo.floating)
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
