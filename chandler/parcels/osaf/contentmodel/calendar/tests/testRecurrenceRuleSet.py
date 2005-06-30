"""
Unit tests for recurrence
"""

__revision__  = "$Revision: 5742 $"
__date__      = "$Date: 2005-06-23 09:21:54 -0700 (Thu, 23 Jun 2005) $"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os
from datetime import datetime, timedelta

import dateutil.rrule
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU, WEEKLY, MONTHLY
from osaf.contentmodel.calendar.Recurrence import \
     FrequencyEnum, RecurrenceRuleSet, RecurrenceRule
import osaf.contentmodel.tests.TestContentModel as TestContentModel

class RecurrenceRuleSetTest(TestContentModel.ContentModelTestCase):
    """ Test Recurrence Content Model """

    def setUp(self):
        super(RecurrenceRuleSetTest,self).setUp()
        self.start = datetime(2005, 7, 4, 13) #1PM, July 4, 2005

        self.weeklyEnd = datetime(2005, 11, 14, 13)
        self.weeklyCount = 20

        self.monthlyEnd = datetime(2005, 11, 4, 13)
        self.monthlyCount = 5
        
    def _testWeeklyRRule(self, rrule):
        """Create a simple rrule, make sure it behaves as we expect."""
        self.assertEqual(rrule[0], self.start)
        self.assertEqual(rrule[-1], self.weeklyEnd)
        self.assertEqual(len(list(rrule)), self.weeklyCount)

    def _testMonthlyRRule(self, rrule):
        """Create a simple rrule, make sure it behaves as we expect."""
        self.assertEqual(rrule[0], self.start)
        self.assertEqual(rrule[-1], self.monthlyEnd)
        self.assertEqual(len(list(rrule)), self.monthlyCount)

    def testBasicRRule(self):
        rrule = dateutil.rrule.rrule(WEEKLY, count=self.weeklyCount,
                                     dtstart=self.start)
        self._testWeeklyRRule(rrule)
        rrule = dateutil.rrule.rrule(MONTHLY, count=self.monthlyCount,
                                     dtstart=self.start)
        self._testMonthlyRRule(rrule)
        
    def testFrequencyEnum(self):
        freqItem = FrequencyEnum()
        self.assert_('yearly' in freqItem.values)
        self.failIf('bicentenially' in freqItem.values)

    def testRuleItem(self):
        """Test that the basic RuleSet definition exists."""
        ruleItem = RecurrenceRule("rRuleItem", view=self.rep.view)
        self.assertEqual(ruleItem.freq, 'weekly',
                         "freq should default to weekly")

        # rep.check() doesn't throw an exception.  Hmm...
#         try:
#             ruleItem.freq = 'badenum'
#             self.rep.check()
#             self.fail("Only FrequencyEnum should be allowed")
#         except ValueError:
#             pass

        ruleItem.freq = 'weekly'
        ruleItem.until = self.weeklyEnd
        rrule = ruleItem.createDateUtilFromRule(self.start)
        self._testWeeklyRRule(rrule)
        self.rep.check()
        # Every other week on Tuesday and Thursday, for 8 occurrences, note that
        # dtstart is a Monday and is NOT included, which is not RFC compliant.  VObject
        # works around this for now, someday dateutil will provide an RFC compliant mode,
        # hopefully.
        
        horridlyComplexRule = dateutil.rrule.rrule(WEEKLY, interval=2,
                                                   count=8, wkst=SU, byweekday=(TU,TH),
                                                   dtstart=self.start)
        lastDate = datetime(2005, 8, 18, 13)

        self.assertNotEqual(horridlyComplexRule[0], self.start)
        self.assertEqual(horridlyComplexRule[-1], lastDate)
        
        ruleItem.setRuleFromDateUtil(horridlyComplexRule)
        
        # make sure isCount was stored and until was set properly
        self.assert_(ruleItem.isCount)
        self.assertEqual(ruleItem.until, lastDate)

        # make sure setRuleFromDateUtil(rrule).createDateUtilFromRule(dtstart)
        # represents the same dates as rrule
        inversedRuleList = ruleItem.createDateUtilFromRule(self.start)

        self.assertEqual(list(inversedRuleList), list(horridlyComplexRule))



#tests to write:
"""
test RecurrenceRule

count sets until and isCount

test multiple RRULEs in one rruleset

createDateUtilFromRule(startTime) &rruleset

setRuleFromDateUtil(rruleset) & rrule

set -> createFrom are (almost) inverses
"""
