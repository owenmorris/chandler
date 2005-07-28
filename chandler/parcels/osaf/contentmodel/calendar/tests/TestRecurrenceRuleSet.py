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
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU, WEEKLY
from osaf.contentmodel.calendar.Recurrence import \
     FrequencyEnum, RecurrenceRuleSet, RecurrenceRule, toDateUtil
import osaf.contentmodel.tests.TestContentModel as TestContentModel

class RecurrenceRuleTest(TestContentModel.ContentModelTestCase):
    """ Test Recurrence Content Model """

    def setUp(self):
        super(RecurrenceRuleTest,self).setUp()
        self.start = datetime(2005, 7, 4, 13) #1PM, July 4, 2005

        self.weekly = {'end'   : datetime(2005, 11, 14, 13),
                       'start' : self.start,
                       'count' : 20}
        
        self.monthly = {'end'   : datetime(2005, 11, 4, 13),
                       'start' : self.start,
                       'count' : 5}
        
    def _testRRule(self, freq, rrule):
        """Create a simple rrule, make sure it behaves as we expect."""
        self.assertEqual(rrule[0], getattr(self, freq)['start'])
        self.assertEqual(rrule[-1], getattr(self, freq)['end'])
        self.assertEqual(rrule.count(), getattr(self, freq)['count'])
    
    def _testCombined(self, rruleset):
        #not count1 + count2, because the two rules share self.start
        self.assertEqual(rruleset.count(), self.weekly['count'] +
                                           self.monthly['count'] - 1)
        self.assertEqual(rruleset[-1], self.weekly['end'])

    def _createBasicItem(self, freq):
        ruleItem = RecurrenceRule(None, view=self.rep.view)
        ruleItem.until = getattr(self, freq)['end']
        if freq == 'weekly':
            self.assertEqual(ruleItem.freq, 'weekly', 
                             "freq should default to weekly")
        else:
            ruleItem.freq = freq
        return ruleItem
    
    def _createBasicDateUtil(self, freq):
        return dateutil.rrule.rrule(toDateUtil(freq),
                                    count   = getattr(self, freq)['count'],
                                    dtstart = getattr(self, freq)['start'])

    def testDateUtilRRules(self):
        for freq in 'weekly', 'monthly':
            self._testRRule(freq, self._createBasicDateUtil(freq))
        
    def testFrequencyEnum(self):
        freqItem = FrequencyEnum()
        self.assert_('yearly' in freqItem.values)
        self.failIf('bicentenially' in freqItem.values)
    
    def testRuleItem(self):
        """Test that transformations of RecurrenceRules work."""
        ruleItem = self._createBasicItem('weekly')
        rrule = ruleItem.createDateUtilFromRule(self.weekly['start'])
        self._testRRule('weekly', rrule)
        self.rep.check()
        
        # Every other week in which Tuesday or Thursday falls on the 5th or 8th
        # of the month, for 4 occurrences.  Yes, this is absurd :)
        complexRule = dateutil.rrule.rrule(WEEKLY, interval=2, count=4, wkst=SU,
                                           byweekday=(TU,TH), bymonthday=[5,8],
                                           dtstart=self.start)
        lastDate = datetime(2006, 1, 5, 13)

        # Note that dtstart is a Monday and is NOT included, which is not RFC
        # compliant.  VObject works around this for now, someday dateutil will
        # provide an RFC compliant mode, hopefully.
        self.assertNotEqual(complexRule[0], self.start)
        self.assertEqual(complexRule[-1], lastDate)
        
        ruleItem.setRuleFromDateUtil(complexRule)
        
        # make sure isCount was stored and until was set properly
        self.assert_(ruleItem.isCount)
        self.assertEqual(ruleItem.until, lastDate)
        
        # make sure byhour, byminute, and bysecond aren't set
        for ignored in ("byhour", "byminute", "bysecond"):
            self.assertEqual(getattr(ruleItem, ignored), None)

        # make sure setRuleFromDateUtil(rrule).createDateUtilFromRule(dtstart)
        # represents the same dates as rrule
        identityTransformedRule = ruleItem.createDateUtilFromRule(self.start)
        
        # make sure the transform sets count, not until, since isCount==True
        self.assertEqual(identityTransformedRule._until, None)
        self.assertEqual(identityTransformedRule._count, 4)

        # compare datetimes for original rule and identityTransformedRule
        self.assertEqual(list(identityTransformedRule),
                         list(complexRule))
                         
    def testInfiniteRuleItem(self):
        """Test that infinite RecurrenceRules work."""
        ruleItem = RecurrenceRule(None, view=self.rep.view)
        #default frequency is weekly
        rule = ruleItem.createDateUtilFromRule(self.start)
        self.assertEqual(rule[149], datetime(2008, 5, 12, 13))
        
    def testTwoRuleSet(self):
        """Test two RecurrenceRules composed into a RuleSet."""
        ruleSetItem = RecurrenceRuleSet(None, view=self.rep.view)
        ruleItem = self._createBasicItem('weekly')
        ruleSetItem.addRule(ruleItem)
        ruleSet = ruleSetItem.createDateUtilFromRule(self.start)
        
        #rrulesets support the rrule interface
        self._testRRule('weekly', ruleSet)
        
        ruleItem = self._createBasicItem('monthly')
        ruleSetItem.addRule(ruleItem)
        self._testCombined(ruleSetItem.createDateUtilFromRule(self.start))
        
    def testRuleSetFromDateUtil(self):
        ruleSet = dateutil.rrule.rruleset()
        for freq in 'weekly', 'monthly':
            ruleSet.rrule(self._createBasicDateUtil(freq))
        ruleSetItem = RecurrenceRuleSet(None, view=self.rep.view)
        ruleSetItem.setRuleFromDateUtil(ruleSet)
        self._testCombined(ruleSetItem.createDateUtilFromRule(self.start))
        
        # test setting a rule instead of a ruleset
        ruleSetItem.setRuleFromDateUtil(self._createBasicDateUtil('weekly'))
        self._testRRule('weekly',ruleSetItem.createDateUtilFromRule(self.start))
        
        # test raising an exception when setting a non-rrule or rruleset
        self.assertRaises(TypeError, ruleSetItem.setRuleFromDateUtil, 0)

    def testRDate(self):
        ruleSet = dateutil.rrule.rruleset()
        for freq in 'weekly', 'monthly':
            ruleSet.rrule(self._createBasicDateUtil(freq))
        ruleSet.rdate(self.start + timedelta(days=1))
        ruleSet.rdate(self.start + timedelta(days=2))
        ruleSetItem = RecurrenceRuleSet(None, view=self.rep.view)
        ruleSetItem.setRuleFromDateUtil(ruleSet)
        
        self.assertEqual(ruleSetItem.rdates[0], self.start + timedelta(days=1))
        
        identityTransformed = ruleSetItem.createDateUtilFromRule(self.start)
        self.assertEqual(identityTransformed[2], self.start + timedelta(days=2))
        self.assertEqual(identityTransformed.count(), self.weekly['count'] +
                                                      self.monthly['count'] - 1
                                                      + 2)

    def testExDate(self):
        ruleSet = dateutil.rrule.rruleset()
        for freq in 'weekly', 'monthly':
            ruleSet.rrule(self._createBasicDateUtil(freq))
        ruleSet.exdate(self.start)
        ruleSetItem = RecurrenceRuleSet(None, view=self.rep.view)
        ruleSetItem.setRuleFromDateUtil(ruleSet)
        identityTransformed = ruleSetItem.createDateUtilFromRule(self.start)
        self.assertNotEqual(self.start, identityTransformed[0])
        
    def testExRule(self):
        ruleSet = dateutil.rrule.rruleset()
        for freq in 'weekly', 'monthly':
            ruleSet.rrule(self._createBasicDateUtil(freq))
        exrule = dateutil.rrule.rrule(WEEKLY, count=10, dtstart=self.start)
        ruleSet.exrule(exrule)
        
        ruleSetItem = RecurrenceRuleSet(None, view=self.rep.view)
        ruleSetItem.setRuleFromDateUtil(ruleSet)
        identityTransformed = ruleSetItem.createDateUtilFromRule(self.start)
        # The monthly rule dates aren't in the exclusion rule
        self.assertEqual(identityTransformed[0],self.start + timedelta(days=31))
        self.assertEqual(identityTransformed.count(), self.weekly['count'] +
                                                      self.monthly['count'] - 1
                                                      - 10)
    
    def testNoAutoDateUtil(self):
        """dateutil sometimes sets bymonthday, byweekday, and bymonth based on
           dtstart, we want to avoid persisting this spurious data.
        """
        ruleItem = RecurrenceRule(None, view=self.rep.view)
        weeklyRule = dateutil.rrule.rrule(dateutil.rrule.WEEKLY)
        ruleItem.setRuleFromDateUtil(weeklyRule)
        self.failIf(ruleItem.hasLocalAttributeValue('byweekday'))

        monthlyRule = dateutil.rrule.rrule(dateutil.rrule.MONTHLY)
        ruleItem.setRuleFromDateUtil(monthlyRule)
        self.failIf(ruleItem.hasLocalAttributeValue('bymonthday'))
        
        yearlyRule = dateutil.rrule.rrule(dateutil.rrule.YEARLY)
        ruleItem.setRuleFromDateUtil(yearlyRule)
        self.failIf(ruleItem.hasLocalAttributeValue('bymonthday'))
        self.failIf(ruleItem.hasLocalAttributeValue('bymonth'))


#tests to write:
"""

Check behavior when bad enums are set

"""