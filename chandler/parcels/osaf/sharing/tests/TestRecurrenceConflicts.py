#   Copyright (c) 2007 Open Source Applications Foundation
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

import unittest
from util.testcase import NRVTestCase
from osaf import pim, sharing
from osaf.sharing.model import EventRecord
from osaf.sharing.translator import formatDateTime
from osaf.sharing import findRecurrenceConflicts
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.calendar.Recurrence import RecurrenceRule, RecurrenceRuleSet
from chandlerdb.item.Item import Item
import datetime

one_week = datetime.timedelta(7)
one_day  = datetime.timedelta(1)

class RecurrenceConflictTestCase(NRVTestCase):

    def setUp(self):

        if not hasattr(RecurrenceConflictTestCase, 'view'):
            super(RecurrenceConflictTestCase,self).setUp()
            RecurrenceConflictTestCase.view = self.view
            del self.view
            
        view = RecurrenceConflictTestCase.view
        self.sandbox = Item("sandbox", view, None)

        self.pacific = self.view.tzinfo.getInstance("America/Los_Angeles")
        self.floating = self.view.tzinfo.floating
        self.utc = self.view.tzinfo.UTC
        
        self.start = datetime.datetime(2007,4,10,9, tzinfo = self.floating)
        
        self.master = Calendar.CalendarEvent(None, itsParent=self.sandbox)
        self.uuid = self.master.itsItem.itsUUID.str16()
        self.master.startTime = self.start
        self.master.anyTime = self.master.allDay = False
        
        # create a baseline dictionary with keywords for creating an EventRecord
        names = (i.name for i in EventRecord.__fields__ if i.name != 'uuid')
        # default values to NoChange
        self.kwds = dict.fromkeys(names, sharing.NoChange)

    def tearDown(self):
        self.master.deleteAll()
        self.sandbox.delete(recursive=True)
        self.sandbox = None

    def _makeRecurrenceRuleSet(self, until=None, freq='daily'):
        ruleItem = RecurrenceRule(None, itsParent=self.sandbox)
        ruleItem.freq = freq
        if until is not None:
            ruleItem.until = until
        ruleSetItem = RecurrenceRuleSet(None, itsParent=self.sandbox)
        ruleSetItem.addRule(ruleItem)
        return ruleSetItem

    def _getAliases(self, uuid, dtlist, allDay=False):
        view = self.view
        aliases = []
        for dt in dtlist:
            if allDay or dt.tzinfo == self.floating:
                real_dt = formatDateTime(self.view, dt, allDay, False)
            else:
                real_dt = formatDateTime(self.view, dt.astimezone(self.utc),
                                         False, False)
            aliases.append(uuid + ":" + real_dt)
        return aliases

    def _getConflicts(self, diff, aliases):
        return findRecurrenceConflicts(self.view, self.uuid, diff, aliases)

    def testUntilChange(self):
        """
        Inbound changes to Until should work.
        """
        # set up master to recur
        self.master.rruleset = self._makeRecurrenceRuleSet(freq='weekly')
        
        # create a diff
        self.kwds['rrule'] = 'FREQ=WEEKLY;UNTIL=20070425T170000Z'
        record = sharing.model.EventRecord(self.uuid, **self.kwds)
        diff = sharing.Diff(set([record]), set())
        
        # get a sample set of aliases to test
        aliases = self._getAliases(self.uuid,
                                   [self.start + n*one_week for n in range(5)])
        
        # the first three come before April 25
        self.assertEqual(self._getConflicts(diff, aliases), aliases[3:])

    def testNoRecurrenceChange(self):
        """
        If recurrence fields weren't changed, empty list should be returned.
        """

        emptyDiff = sharing.Diff(set(), set())
        aliases = self._getAliases(self.uuid,
                                   [self.start + n*one_week for n in range(5)])

        # No conflicts when master isn't recurring
        self.assertEqual(self._getConflicts(emptyDiff, aliases), [])
        
        # create a diff with an EventRecord, but no recurrence changes
        self.kwds['dtstart'] = ';VALUE=DATE-TIME:20070301T090000'
        record = sharing.model.EventRecord(self.uuid, **self.kwds)
        diff = sharing.Diff(set([record]), set())

        # No conflicts
        self.assertEqual(self._getConflicts(diff, aliases), [])

        # try again when master is recurring
        self.master.rruleset = self._makeRecurrenceRuleSet(freq='weekly')
        
        conflicts = findRecurrenceConflicts(self.view, self.uuid, emptyDiff,
                                            aliases)
        # No conflicts with an empty diff
        self.assertEqual(self._getConflicts(emptyDiff, aliases), [])
        # A start time change should give conflicts
        self.assertNotEqual(self._getConflicts(diff, aliases), [])

    def testRemoveRecurrence(self):
        """All modifications should be returned if recurrence was removed."""
        self.master.rruleset = self._makeRecurrenceRuleSet(freq='weekly')
        aliases = self._getAliases(self.uuid,
                                   [self.start + n*one_week for n in range(5)])

        # create a diff with all recurrence fields empty
        recurrence_fields = ('exdate', 'rdate', 'rrule', 'exrule')
        self.kwds.update(dict.fromkeys(recurrence_fields))
        record = sharing.model.EventRecord(self.uuid, **self.kwds)
        diff = sharing.Diff(set([record]), set())

        self.assertEqual(self._getConflicts(diff, aliases), aliases)

    def testUnstamping(self):
        """If EventRecord is removed, it will be in exclusions."""
        self.master.rruleset = self._makeRecurrenceRuleSet(freq='weekly')
        aliases = self._getAliases(self.uuid,
                                   [self.start + n*one_week for n in range(5)])

        # create a diff with an EventRecord in exclusions.  The EventRecord
        # can't be empty or it'll be seen as NoChange, so make a small change
        self.kwds['exdate'] = None
        record = sharing.model.EventRecord(self.uuid, **self.kwds)
        diff = sharing.Diff(set(), set([record]))

        self.assertEqual(self._getConflicts(diff, aliases), aliases)

    def testExdate(self):
        """If an EXDATE is added, it should conflict."""
        self.master.rruleset = self._makeRecurrenceRuleSet(freq='weekly')
        aliases = self._getAliases(self.uuid,
                                   [self.start + n*one_week for n in range(5)])

        # create a diff with an EventRecord in exclusions.  The EventRecord
        # can't be empty or it'll be seen as NoChange, so make a small change
        self.kwds['exdate'] = ';VALUE=DATE-TIME:20070417T090000'
        record = sharing.model.EventRecord(self.uuid, **self.kwds)
        diff = sharing.Diff(set([record]), set())

        self.assertEqual(self._getConflicts(diff, aliases), aliases[1:2])

        # choose an exdate that doesn't conflict with anything (changed time)
        self.kwds['exdate'] = ';VALUE=DATE-TIME:20070417T000000'
        record = sharing.model.EventRecord(self.uuid, **self.kwds)
        diff = sharing.Diff(set([record]), set())

        self.assertEqual(self._getConflicts(diff, aliases), [])

    def testFrequencyChange(self):
        """
        Currently, Chandler leaves off-rule modifications after recurrence rule
        changes (there's no pending deletion).  For now, remote rule changes
        that leave the event recurring *do* conflict with local off-rule
        modifications for sharing.
        
        """
        # set up master to recur
        self.master.rruleset = self._makeRecurrenceRuleSet(freq='daily')
        
        # create a diff changing frequency to weekly
        self.kwds['rrule'] = 'FREQ=WEEKLY'
        record = sharing.model.EventRecord(self.uuid, **self.kwds)
        diff = sharing.Diff(set([record]), set())
        
        # get a sample set of aliases to test that don't overlap with seven day
        # intervals
        aliases = self._getAliases(self.uuid,
                              [self.start + n*one_day for n in range(0, 30, 5)])
        
        self.assertEqual(self._getConflicts(diff, aliases), aliases[1:])

    def testRemoveRrruleLeaveRdate(self):
        """
        Removing an RRULE shouldn't cause everything to conflict if there are
        still RDATEs.
        
        """
        self.master.rruleset = self._makeRecurrenceRuleSet(freq='weekly')
        self.master.rruleset.rdates = [self.start + n*one_day for n in range(1,3)]

        # create a diff removing the RRULE
        self.kwds['rrule'] = None
        record = sharing.model.EventRecord(self.uuid, **self.kwds)
        diff = sharing.Diff(set([record]), set())

        # get a sample set of aliases to test that don't overlap with seven day
        # intervals
        aliases = self._getAliases(self.uuid,
                                   [self.start + n*one_day for n in range(5)])
        
        self.assertEqual(self._getConflicts(diff, aliases), aliases[3:])

    def testAllDay(self):
        self.master.allDay = True

        self.master.rruleset = self._makeRecurrenceRuleSet(freq='weekly')
        self.kwds['rrule'] = 'FREQ=WEEKLY;UNTIL=20070424'
        record = sharing.model.EventRecord(self.uuid, **self.kwds)
        diff = sharing.Diff(set([record]), set())

        aliases = self._getAliases(self.uuid,
                                   [self.master.effectiveStartTime + n*one_week
                                    for n in range(5)])
        
        self.assertEqual(self._getConflicts(diff, aliases), aliases[3:])

    def testTimezonedEvent(self):
        self.master.startTime = self.start.replace(tzinfo=self.pacific)

        self.master.rruleset = self._makeRecurrenceRuleSet(freq='weekly')
        self.kwds['rrule'] = 'FREQ=WEEKLY;UNTIL=20070424T160000Z'
        self.kwds['exdate'] = ';VALUE=DATE-TIME;TZID=America/Los_Angeles:20070417T090000'
        record = sharing.model.EventRecord(self.uuid, **self.kwds)
        diff = sharing.Diff(set([record]), set())

        aliases = self._getAliases(self.uuid,
                                   [self.master.startTime + n*one_week
                                    for n in range(5)])
        
        self.assertEqual(self._getConflicts(diff, aliases),
                         aliases[1:2] + aliases[3:])


if __name__ == "__main__":
    unittest.main()
