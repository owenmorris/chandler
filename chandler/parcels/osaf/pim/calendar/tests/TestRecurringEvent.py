"""
Unit tests for recurring events
"""

__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os
from datetime import datetime, timedelta
import dateutil.rrule

from application import schema
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.tasks import TaskMixin
from osaf.pim.calendar.Recurrence import RecurrenceRule, RecurrenceRuleSet
from PyICU import ICUtzinfo
from i18n.tests import uw

from application.dialogs.RecurrenceDialog import getProxy
from itertools import chain

import osaf.pim
import osaf.pim.tests.TestDomainModel as TestDomainModel
from chandlerdb.item.ItemError import NoSuchAttributeError

class RecurringEventTest(TestDomainModel.DomainModelTestCase):
    """ Test CalendarEvent Recurrence """

    def setUp(self):
        super(RecurringEventTest,self).setUp()
        self.start = datetime(2005, 7, 4, 13, tzinfo=ICUtzinfo.default) #1PM, July 4, 2005

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
        event.displayName = uw("Sample event")
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

        secondStart = datetime(2005, 7, 11, 13, tzinfo=ICUtzinfo.default)
        second = self.event.getNextOccurrence()
        self.assert_(second.isGenerated)
        self.assertEqual(self.event.createDateUtilFromRule()[1], secondStart)
        self.assertEqual(second.startTime, secondStart)
        self.assertEqual(second.displayName, self.event.displayName)

        # make sure getNextOccurrence returns the same item when called twice
        self.assertEqual(second, self.event.getNextOccurrence())

        third = second.getNextOccurrence()
        thirdStart = datetime(2005, 7, 18, 13, tzinfo=ICUtzinfo.default)
        self.assertEqual(third.startTime, thirdStart)

        fourthStart = datetime(2005, 7, 25, 13, tzinfo=ICUtzinfo.default)
        fourth = self.event._createOccurrence(fourthStart)
        self.assert_(fourth.isGenerated)
        self.assertEqual(fourth, third.getNextOccurrence())

        # create a modification to be automatically deleted
        fourth.displayName = uw("changed title")

        second.cleanRule()
        self.assertEqual(len(self.event.occurrences), 3)

        self.event.rruleset.rrules.first().until = thirdStart

        #changing the rule should delete our modified fourth
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
        self.event.displayName = uw("Master Event") #no rruleset, so no modification
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.assertEqual(self.event.modifies, None)

        calmod = self.event.getNextOccurrence()
        self.assertEqual(self.event.modifications, None)

        calmod.changeThis('displayName', uw('Modified occurrence'))

        self.assertEqual(calmod.modificationFor, self.event)
        self.assertEqual(calmod.getFirstInRule(), self.event)

        self.assertEqual(list(self.event.modifications), [calmod])

        evtaskmod = calmod.getNextOccurrence()

        evtaskmod.StampKind('add', TaskMixin.getKind(self.rep.view))

        # changes to an event should, by default, create a THIS modification
        self.assertEqual(evtaskmod.modificationFor, self.event)
        self.assertEqual(evtaskmod.getFirstInRule(), self.event)

        for modOrMaster in [calmod, evtaskmod, self.event]:
            self.assertEqual(modOrMaster.getMaster(), self.event)

        self.event.displayName = uw("Modification to master")
        self.assertNotEqual(None, self.event.occurrenceFor)
        self.assertNotEqual(self.event, self.event.occurrenceFor)

        # test getNextOccurrence ordering, bug 4083
        generated = evtaskmod.getNextOccurrence()
        self.assertEqual(self.event.getNextOccurrence(), calmod)

        evtaskmod.startTime = calmod.startTime - timedelta(hours=1)
        self.assertEqual(self.event.getNextOccurrence(), evtaskmod)
        self.assertEqual(calmod.getNextOccurrence(), generated)

        evtaskmod.startTime = generated.startTime + timedelta(hours=1)
        self.assertEqual(self.event.getNextOccurrence(), calmod)
        self.assertEqual(calmod.getNextOccurrence(), generated)
        self.assertEqual(generated.getNextOccurrence(), evtaskmod)


    def testRuleChange(self):
        self.event.rruleset = self._createRuleSetItem('weekly')
        # self and an automatically generated backup occurrence should exist
        self.assertEqual(len(self.event.occurrences), 2)

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
        self.assertEqual(len(self.event.occurrences), 2)
        self.assertEqual(len(list(self.event._generateRule())), count)

        threeWeeks = self.start + timedelta(days=21)
        occurs = self.event.getOccurrencesBetween(threeWeeks + 
                                timedelta(minutes=30),
                                datetime(2005, 8, 15, 14,
                                         tzinfo=ICUtzinfo.default))
        self.assertEqual(list(occurs)[0].startTime, threeWeeks)
        self.assertEqual(list(occurs)[1].startTime,
                         datetime(2005, 8, 15, 13, tzinfo=ICUtzinfo.default))
        self.rep.check()

    def testIcalUID(self):
        self.assertEqual(self.event.icalUID, unicode(self.event.itsUUID))
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.assertEqual(self.event.icalUID, 
                         self.event.getNextOccurrence().icalUID)

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

        self.failIf(self.event in occurrences)

    def testRemoveRecurrence(self):
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.event.removeRecurrence()
        self.assertEqual(len(self.event.occurrences), 1)

        self.event.rruleset = self._createRuleSetItem('weekly')
        second = self.event.getNextOccurrence()
        second.removeRecurrence()
        self.assertEqual(len(self.event.occurrences), 1)

        self.event.rruleset = self._createRuleSetItem('weekly')
        third = self.event.getNextOccurrence().getNextOccurrence()
        third.changeThisAndFuture('startTime', third.startTime + timedelta(hours=1))
        second = self.event.getNextOccurrence()

        rule = third.rruleset.rrules.first()

        third.removeRecurrence()
        self.assertEqual(len(third.occurrences), 1)
        self.failIf(second.isDeleted())
        self.assert_(rule.isDeleted())

        # test a THIS modification to master, then removing recurrence
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.event.startTime += timedelta(hours=1)
        eventModified = self.event
        self.event = self.event.occurrenceFor
        eventModified.removeRecurrence()
        self.assert_(self.event.isDeleted())
        self.failIf(eventModified.isDeleted())
        # bug 4084, rruleset isn't getting deleted from eventModified
        self.failIf(eventModified.hasLocalAttributeValue('rruleset'))
        # bug 4681, removeRecurrence doesn't work for AllDay events
        self.event = eventModified
        self.event.allDay = True
        self.event.rruleset = self._createRuleSetItem('weekly')
        self.event.removeRecurrence()


    def testProxy(self):
        self.failIf(self.event.isProxy())

        proxy = getProxy('test', self.event)
        proxy.dialogUp = True # don't try to create a dialog in a test
        self.assert_(proxy.isProxy())
        self.assertEqual(proxy, self.event)
        self.assertEqual(proxy.currentlyModifying, None)
        self.assert_(proxy is getProxy('test', proxy))

        proxy.rruleset = self._createRuleSetItem('weekly')
        self.assert_(self.event in proxy.rruleset.events)
        self.assertEqual(proxy.getNextOccurrence().occurrenceFor, self.event)
        self.assertEqual(len(list(proxy._generateRule())), self.weekly['count'])

        proxy.startTime = self.start + timedelta(days=1)
        self.assertEqual(self.event.startTime, self.start)
        self.assertEqual(proxy.startTime, self.start + timedelta(days=1))


    def testThisAndFutureModification(self):
        #FIXME: test rruleset changes
        self.event.rruleset = self._createRuleSetItem('weekly')
        lastUntil = self.event.rruleset.rrules.first().until
        second = self.event.getNextOccurrence()

        #one simple THISANDFUTURE modification
        second.changeThisAndFuture('displayName', uw('Modified title'))

        self.assertEqual(second.modificationFor, None)

        self.assert_(list(self.event.rruleset.rrules)[0].until < second.startTime)
        self.assertEqual(second.displayName, uw('Modified title'))
        self.assertEqual(list(second.rruleset.rrules)[0].freq, 'weekly')
        self.assertEqual(second.startTime, second.recurrenceID)
        self.assertEqual(second.icalUID, unicode(second.itsUUID))
        self.assertEqual(second.getLastUntil(), lastUntil)

        # make sure a backup occurrence is created
        self.assertEqual(len(list(second.occurrences)), 2)
        third = second.getNextOccurrence()
        self.assertEqual(third.displayName, uw('Modified title'))

        # create a changed fourth event to make sure its recurrenceID gets moved
        # when third's startTime is changed
        fourth = third.getNextOccurrence()
        fourth.changeThis('displayName', uw('fourth'))

        thirdStart = third.startTime
        thirdChangedStart = thirdStart + timedelta(hours=1)
        third.changeThisAndFuture('startTime', thirdChangedStart)

        # fourth's time shouldn't have changed, but its recurrenceID should have
        self.assertEqual(fourth.startTime - thirdStart, timedelta(weeks=1))
        self.assertEqual(len(list(third.occurrences)), 3)
        self.assertEqual(fourth.recurrenceID,
                         fourth.startTime + timedelta(hours=1))
        self.assertEqual(third.rruleset, fourth.rruleset)
        self.assertEqual(third.icalUID, fourth.icalUID)
        self.assertNotEqual(second.icalUID, third.icalUID)

        # make sure second's rruleset was updated
        self.assert_(list(second.rruleset.rrules)[0].until < thirdChangedStart)

        # changing second's displayName again shouldn't create a new occurrence,
        # and third should be completely unchanged
        second.changeThisAndFuture('displayName', uw('Twice modified title'))

        self.assertEqual(len(list(second.occurrences)), 1)
        self.assertEqual(third.startTime, thirdChangedStart)
        self.assertEqual(third.displayName, uw('Modified title'))
        self.assertEqual(third.getLastUntil(), lastUntil)

        # change second's rule 
        second.changeThisAndFuture('rruleset', 
                                   third.rruleset.copy(cloudAlias='copying'))
        newthird = second.getNextOccurrence()

        self.assertNotEqual(third, newthird)
        self.failIf(newthird.startTime == thirdChangedStart)
        self.assertEqual(list(second.rruleset.rrules)[0].until, lastUntil)

        # make a THIS change to a THISANDFUTURE modification 
        second.changeThis('displayName', uw("THIS modified title"))

        secondModified = second
        second = second.occurrenceFor

        self.assertEqual(second.occurrenceFor, None)
        self.assertNotEqual(secondModified.displayName, second.displayName)
        self.assertEqual(second.getNextOccurrence(), newthird)
        self.assertEqual(newthird.displayName, uw('Twice modified title'))

        # make a THISANDFUTURE change to the THIS modification
        # FIXME: time changes need to preserve modifications for 0.6
        secondModified.changeThisAndFuture('duration', timedelta(hours=2))
        second = secondModified
        third = second.getNextOccurrence()
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

        third.lastModified = uw('Changed lastModified.')
        fourth = third.getNextOccurrence()
        fourth.startTime += timedelta(hours=4)

        # propagating thisandfuture modification to this
        third.changeThisAndFuture('displayName', uw('Yet another title'))
        thirdModified = third
        third = third.occurrenceFor
        # Because fourth is a modification, its title should NOT have changed
        self.assertEqual(fourth.displayName, uw('Twice modified title'))

        self.assertNotEqual(thirdModified.icalUID, second.icalUID)
        self.assertEqual(thirdModified.icalUID, third.icalUID)
        self.assertEqual(third.icalUID, fourth.icalUID)
        self.assertEqual(third.rruleset, fourth.rruleset)

        self.assertEqual(third.displayName, uw('Yet another title'))
        self.failIf(third.hasLocalAttributeValue('lastModified'))
        self.assertEqual(thirdModified.lastModified, uw('Changed lastModified.'))

        self.assertEqual(fourth.modificationFor, third)

        #check propagation if first in rule is overridden with a THIS mod
        thirdModified.changeThisAndFuture('displayName', uw('Changed again'))

        self.assertEqual(third.displayName, uw('Changed again'))
        self.assertEqual(thirdModified.displayName, uw('Changed again'))

        # THIS mod to master with no occurrences because of later modifications 
        # doesn't create a mod
        self.event.startTime += timedelta(hours=6)
        self.assertEqual(self.event.occurrenceFor, self.event)
        self.assertEqual(self.event.modificationRecurrenceID,
                         self.event.startTime)
        self.assertEqual(self.event.startTime, self.event.recurrenceID)

        # change master event back to the original rule
        oldrule = self.event.rruleset
        self.event.changeThisAndFuture('rruleset',
                                      third.rruleset.copy(cloudAlias='copying'))

        self.assert_(oldrule.isDeleted)
        self.assertEqual(self.event.startTime, self.event.recurrenceID)

        # make sure changing master also changes master's recurrenceID
        self.event.changeThisAndFuture('startTime', self.start + timedelta(hours=3))
        self.assertEqual(self.event.startTime, self.event.recurrenceID)
        self.assertEqual(self.event.getLastUntil(), lastUntil)

        #make a THIS modification
        self.event.startTime -= timedelta(hours=3)
        eventModified = self.event
        self.event = self.event.occurrenceFor
        self.assertEqual(self.event.occurrenceFor, None)
        self.assertEqual(eventModified.startTime, self.start)

        self.assertEqual(self.event.startTime, self.start + timedelta(hours=6))

        # Test moving a later THIS modification when changing an earlier mod

        second = self.event.getNextOccurrence()
        second.displayName = uw("second")
        third = second.getNextOccurrence()
        third.displayName = uw("third")

        second.changeThisAndFuture('displayName', uw('changed title'))

        self.assertNotEqual(self.event.icalUID, second.icalUID)
        self.assertEqual(second.icalUID, third.icalUID)
        self.assertEqual(third.modificationFor, second.occurrenceFor)

    def _checkDeleted(self, items, notdeleted):
        for item in chain(items, notdeleted):
            if item in notdeleted:
                self.failIf(item.isDeleted(),
                            "Item was deleted, but shouldn't have been: %s"
                            % repr(item))
            else:
                self.assert_(item.isDeleted(),
                             "Item wasn't deleted: %s" % repr(item))

    def testDelete(self):
        event = self.event
        rruleset = event.rruleset = self._createRuleSetItem('weekly')


        # check a simple recurring rule
        event.removeRecurrence()
        self._checkDeleted(chain(event.occurrences, [rruleset]), [event])

        # THIS modification
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.getNextOccurrence().displayName = 'changed'
        event.removeRecurrence()
        self._checkDeleted(chain(event.occurrences, [rruleset]), [event])

        # THIS modification to master 
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.displayName = 'changed'
        event.removeRecurrence()
        master = event.occurrenceFor
        self._checkDeleted(chain([master], master.occurrences, [rruleset]),
                                 [event])

        # THISANDFUTURE modification
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second = event.getNextOccurrence()
        second.changeThisAndFuture('displayName', uw('changed'))
        event.removeRecurrence()
        self._checkDeleted([rruleset, event, second, second.rruleset],
                           [event, second, second.rruleset])

        # simple deleteThis
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second = event.getNextOccurrence()
        second.deleteThis()
        self.assert_(second.isDeleted())
        self.assertEqual(rruleset.exdates, [self.start + timedelta(days=7)])
        event.removeRecurrence()

        # deleteThis on a master
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        event.deleteThis()
        self.failIf(event.isDeleted())
        self.assertEqual(rruleset.exdates, [self.start])
        self.assertEqual(event.occurrenceFor, None)
        event.removeRecurrence()

        # deleteThis on a THIS modification
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second = event.getNextOccurrence()
        second.changeThis('startTime', self.start + timedelta(hours=1))
        second.deleteThis()
        self.assert_(second.isDeleted())
        self.assertEqual(rruleset.exdates, [self.start + timedelta(days=7)])
        event.removeRecurrence()

        # simple deleteAll
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second = event.getNextOccurrence()
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
        newmaster = event.occurrenceFor
        event.deleteAll()
        self._checkDeleted([rruleset, event, newmaster], [])

        # deleteThisAndFuture
        event = self._createEvent()
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        second =  event.getNextOccurrence()
        third  = second.getNextOccurrence()
        third.changeThis('displayName', uw("Changed title"))
        third.deleteThisAndFuture()

        self._checkDeleted([event, second, third], [event])
        self.assertEqual(event.getLastUntil(), self.start + timedelta(days=7))



    def testRdatesAndExdates(self):
        event = self.event
        rruleset = event.rruleset = self._createRuleSetItem('weekly')

        # create an RDATE and an EXDATE
        rruleset.rdates = [self.start + timedelta(days=1)]
        extraDay = event.getNextOccurrence()
        extraDay.changeThis('displayName', uw('Extra day'))
        self.assertEqual(extraDay.startTime, self.start + timedelta(days=1))
        rruleset.exdates = [self.start + timedelta(days=7)]
        twoWeeks = extraDay.getNextOccurrence()
        self.assertEqual(twoWeeks.startTime, self.start + timedelta(days=14))

        extraDay.changeThisAndFuture('startTime',
                                     extraDay.startTime + timedelta(hours=1))
        self.assertEqual(rruleset.rdates,  [])
        self.assertEqual(rruleset.exdates, [])

        self.assertEqual(extraDay.rruleset.rdates,
                         [self.start + timedelta(days=1, hours=1)])
        self.assertEqual(extraDay.rruleset.exdates,
                         [self.start + timedelta(days=7, hours=1)])

    def testAllDay(self):
        event = self.event
        event.allDay = True
        rruleset = event.rruleset = self._createRuleSetItem('weekly')
        self.assert_(event.allDay)
        self.assertEqual(self.start, event.startTime)
        second = event.getNextOccurrence()
        self.assert_(second.allDay)
        second.changeThis('allDay', False)
        self.assert_(not second.allDay)        

    def testNeverEndingEvents(self):
        ruleItem = RecurrenceRule(None, itsView=self.rep.view)
        ruleItem.freq = 'daily'
        ruleSetItem = RecurrenceRuleSet(None, itsView=self.rep.view)
        ruleSetItem.addRule(ruleItem)
        self.event.rruleset = ruleSetItem

        # make a THISANDFUTURE modification

        second = self.event.getNextOccurrence()
        second.changeThisAndFuture('startTime',
                                   self.start + timedelta(minutes=30))
        self.failIf(second.rruleset.rrules.first().hasLocalAttributeValue('until'))

class NaiveTimeZoneRecurrenceTest(TestDomainModel.DomainModelTestCase):
    """Test of recurring events that have startTimes that occur on different
       dates depending on whether timezone UI is enabled"""

    tzinfo = ICUtzinfo.getInstance("US/Pacific")
    enableTimeZones = False

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
        self.event.displayName = uw("Sneaky recurring event")

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
        self.failUnlessEqual(occurrences, [self.event])

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
        self.failUnlessEqual(occurrences, [self.event])

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
