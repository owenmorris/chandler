#   Copyright (c) 2008 Open Source Applications Foundation
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
from datetime import *
import calendar
import dateutil.rrule as rrule
import util.testcase as testcase
import osaf.sharing as sharing
import osaf.pim as pim
import application.dialogs.CustomRecurrenceDialog as CustomRecurrenceDialog


class LayoutFormatRegexTest(unittest.TestCase):

    def failUnlessFormatMatches(self, inputStr, *expectedStrs):
    
        # Make sure we have C{list} objects in both case, for
        # == comparison.
        expected = list(s for s in expectedStrs)
        actual = list(s for s in CustomRecurrenceDialog.split_format(inputStr))
        
        self.failUnlessEqual(expected, actual)

    def testSimple(self):
        self.failUnlessFormatMatches('Woot', 'Woot')

    def testOne(self):
        self.failUnlessFormatMatches('This is great: %(woot)s', 'This is great: ', 'woot', '')

    def testOnly(self):
        self.failUnlessFormatMatches('%(my key)s', '', 'my key', '')

    def testDoublePercent(self):
        self.failUnlessFormatMatches('I have %%(done)s', 'I have %(done)s')

    def testMultiple(self):
        self.failUnlessFormatMatches('%(first)s day of %(Christmas)s%(pudding)s',
        '', 'first', ' day of ', 'Christmas', '', 'pudding', '')

class ParseRuleTestCase(unittest.TestCase):
    def failUnlessParseMatches(self, string, true_rep, canonical, passthru):
        rule = rrule.rrulestr(string)
        
        parsed = CustomRecurrenceDialog.parse_rrule(rule)

        self.failUnlessEqual(true_rep, parsed[0])
        self.failUnlessEqual(canonical, parsed[1])
        self.failUnlessEqual(passthru, parsed[2])

    # --- Unsupported frequencies (more frequent than daily)
    def testHourly(self):
        self.failUnlessParseMatches(
            "FREQ=HOURLY",
            False, {'freq':rrule.HOURLY, 'interval':1}, {}
        )

    def testMinutely(self):
        self.failUnlessParseMatches(
            "FREQ=MINUTELY;INTERVAL=30;BYSECOND=41,11",
            False, {'freq':rrule.MINUTELY, 'interval':30}, {'bysecond':(41,11)}
        )

    def testSecondly(self):
        self.failUnlessParseMatches(
            "FREQ=SECONDLY;INTERVAL=12",
            False, {'freq':rrule.SECONDLY, 'interval':12}, {}
        )

    # --- Unsupported: COUNT
    def testCount(self):
        self.failUnlessParseMatches(
            "FREQ=DAILY;COUNT=12",
            False, {'freq':rrule.DAILY, 'interval':1}, {}
        )

    # --- UNTIL should be passed through
    def testUntil(self):
        self.failUnlessParseMatches(
            "FREQ=DAILY;UNTIL=20100102",
            True,
            {'freq':rrule.DAILY, 'interval':1},
            {'until': datetime(2010, 1, 2, 0, 0)}
        )


    # --- DAILY
    def testDaily(self):
        self.failUnlessParseMatches(
            "FREQ=DAILY",
            True,
            {'freq':rrule.DAILY, 'interval':1},
            {}
        )

    # --- WEEKLY

    def testWeekly(self):
        self.failUnlessParseMatches(
            "FREQ=WEEKLY",
            True,
            {'freq':rrule.WEEKLY, 'interval':1},
            {}
        )

    def tsetByWeekday(self):
        self.failUnlessParseMatches(
            "FREQ=WEEKLY;BYDAY=MO,TH,SA",
            True,
            {'freq':rrule.WEEKLY, 'interval':1,
             'byweekday':(rrule.MO, rrule.TH, rrule.SA)},
            {}
        )

    # --- MONTHLY

    def testMonthlyByWeekday(self):
        self.failUnlessParseMatches(
            "FREQ=MONTHLY;BYDAY=4TH",
            True,
            {'freq':rrule.MONTHLY, 'interval':1,
             'byweekday':(rrule.TH(4),)},
            {}
        )

    def testMonthlyComplexByWeekday(self):
        self.failUnlessParseMatches(
            "FREQ=MONTHLY;BYDAY=WE,4TH,FR",
            True,
            {'freq':rrule.MONTHLY, 'interval':1,
             'byweekday':(rrule.TH(4), rrule.WE, rrule.FR)},
            {}
        )

    def testMonthlyByDay(self):
        self.failUnlessParseMatches(
            "FREQ=MONTHLY;BYMONTHDAY=1,14,22,-1",
            True,
            {'freq':rrule.MONTHLY, 'interval':1,
             'bymonthday':(-1, 1, 14, 22)},
            {}
        )

    def testUnsupportedByMonthDay(self):
        # Bymonthdays < -7 are unsupported
        self.failUnlessParseMatches(
            "FREQ=MONTHLY;BYMONTHDAY=4,-6",
            False,
            {'freq':rrule.MONTHLY, 'interval':1,
             'bymonthday':(-6, 4)},
            {}
        )
    

    def testAlternateByWeek(self):
        self.failUnlessParseMatches(
            "FREQ=MONTHLY;BYDAY=SA;BYSETPOS=3",
            True,
            {'freq':rrule.MONTHLY, 'interval':1,
            "byweekday":(rrule.SA(3),)},
            {}
        )

    def testPayrollRule(self):
        self.failUnlessParseMatches(
            "FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=-1",
            False,
            {'freq':rrule.MONTHLY, 'interval':1,
             'byweekday':(rrule.MO, rrule.TU, rrule.WE, rrule.TH, rrule.FR)},
             {}
         )

    def testNextToLast(self):
        self.failUnlessParseMatches(
            "FREQ=MONTHLY;BYDAY=-2FR",
            False, # we don't do "next to last" in the UI
            {'freq':rrule.MONTHLY, 'interval':1,
             'byweekday':(rrule.FR(-2),)},
            {}
        )

    def testFifthSunday(self):
        self.failUnlessParseMatches(
            "FREQ=MONTHLY;BYDAY=5SU",
            False, # we don't do "fifth" in the UI
            {'freq':rrule.MONTHLY, 'interval':1,
             'byweekday':(rrule.SU(5),)},
            {}
        )

    def testMultipleByWeek(self):
        self.failUnlessParseMatches(
            "FREQ=MONTHLY;BYDAY=-2FR,1SU",
            False, # we only do a single "on the nth Xday" rule in the UI
            {'freq':rrule.MONTHLY, 'interval':1,
             'byweekday':(rrule.FR(-2), rrule.SU(1))},
            {}
        )

    def testYearly(self):
        self.failUnlessParseMatches(
            "FREQ=YEARLY;INTERVAL=2",
            True,
            {'freq':rrule.YEARLY, 'interval':2},
            {}
        )

    def testByMonth(self):
        self.failUnlessParseMatches(
            "FREQ=YEARLY;BYMONTH=1,10,11",
            True,
            {'freq':rrule.YEARLY, 'interval':1,
             'bymonth':(1, 10, 11)},
            {}
        )

    def testByMonthDay(self):
        self.failUnlessParseMatches(
            "FREQ=YEARLY;BYMONTH=1,10,11;BYDAY=4SU",
            True,
            {'freq':rrule.YEARLY, 'interval':1,
             'bymonth':(1,10,11),
             'byweekday':(rrule.SU(4),)},
            {}
        )

    def testByWeekno(self):
        self.failUnlessParseMatches(
            "FREQ=MONTHLY;BYWEEKNO=3;BYDAY=WE,TH",
            False, # BYWEEKNO unsupported
            {'freq':rrule.MONTHLY, 'interval':1,
             'byweekno':(3,), 'byweekday':(rrule.WE, rrule.TH)},
            {}
        )

    def testByYearDay(self):
        self.failUnlessParseMatches(
            "FREQ=YEARLY;BYYEARDAY=1,-1",
            False, # BYYEARDAY unsupported
            {'freq':rrule.YEARLY, 'interval':1,
             'byyearday':(1, -1)},
            {}
        )

    # --- Cases that are unsupported because they're too complex

    def testYearlyByMonthAndDay(self):
        self.failUnlessParseMatches(
            "FREQ=YEARLY;BYMONTH=4,7;BYMONTHDAY=15,16",
            False,
            {'freq':rrule.YEARLY, 'interval':1,
             'bymonth':(4, 7), 'bymonthday':(15, 16)},
            {}
        )


    def testMonthlyByMonth(self):
        self.failUnlessParseMatches(
            "FREQ=MONTHLY;BYMONTH=1,3,5;BYMONTHDAY=11",
            False,
            {'freq':rrule.MONTHLY, 'interval':1,
             'bymonth':(4, 7), 'bymonth':(1,3,5), 'bymonthday':(11,)},
            {}
        )

    def testWeeklyByMonth(self):
        self.failUnlessParseMatches(
            "FREQ=WEEKLY;INTERVAL=4;BYMONTH=2",
            False,
            {'freq':rrule.WEEKLY, 'interval':4,
             'bymonth':(4, 7), 'bymonth':(2,)},
            {}
        )

    def testDailyByWeekno(self):
        self.failUnlessParseMatches(
            "FREQ=DAILY;INTERVAL=3;BYWEEKNO=2;BYHOUR=11,12",
            False,
            {'freq':rrule.DAILY, 'interval':3,
             'byweekno':(2,)},
            {'byhour':(11, 12)} # Test passthru of byhour
        )

    # --- passthru values
    
    def testPassThruWkst(self):
        newWkst = (calendar.firstweekday() + 2) % 7
        self.failUnlessParseMatches(
            "FREQ=WEEKLY;INTERVAL=2;BYDAY=SU,FR;WKST=%s" % (
                                            rrule.weekday(newWkst)),
            True,
            {'freq':rrule.WEEKLY, 'interval':2,
             'byweekday':(rrule.SU, rrule.FR)},
            {'wkst': newWkst} # Test passthru of wkst
        )

    def testPassThruByMinute(self):
        newWkst = (calendar.firstweekday() + 2) % 7
        self.failUnlessParseMatches(
            "FREQ=HOURLY;BYMINUTE=15,45",
            False,
            {'freq':rrule.HOURLY, 'interval':1},
            {'byminute': (15, 45)} # Test passthru of wkst
        )

    def testPassThruBySecond(self):
        newWkst = (calendar.firstweekday() + 2) % 7
        self.failUnlessParseMatches(
            "FREQ=HOURLY;BYMINUTE=15,45;BYSECOND=11,21,31,41",
            False,
            {'freq':rrule.HOURLY, 'interval':1},
            {'byminute': (15, 45),
             'bysecond': (11, 21, 31, 41)} # Test passthru of wkst
        )



class ExtractTestCase(testcase.SharedSandboxTestCase):
    def Import(self, view, filename):
        path = self.getTestResourcePath(filename)
        self.importedCollection = sharing.importFile(view, path)

    def makeParams(self, event):
        """"Utility, makes rrule params dict out of event."""
        rruleset = event.rruleset
        self.failUnless(rruleset is not None)
        self.failUnlessEqual(len(list(rruleset.rrules)), 1)
        thing = rruleset.rrules.first()
        rrule = thing.createDateUtilFromRule(event.startTime)
        
        return CustomRecurrenceDialog.parse_rrule(rrule)[1]
        
    def testCustomWeekly(self):
        self.Import(self.view, 'CustomRecurWeekly.ics')
        event = pim.EventStamp(sharing.findUID(
                                self.view,
                                '431391D1-5CEB-4326-9AE2-7D87B8494E63'))
        #### this one is fri/sat every other week
        params = self.makeParams(event)
        weekly = CustomRecurrenceDialog.extractIsWeekly(params)
        self.failUnlessEqual(True, weekly)
        days = CustomRecurrenceDialog.extractGuiWeekdays(params)
        self.failUnlessEqual([5, 6], days)  # assumes i18n first day is Sun
        self.failUnlessEqual(2, CustomRecurrenceDialog.extractInterval(params))
        
        #### every monday, weekly
        event = pim.EventStamp(sharing.findUID(
                                self.view,
                                'A2A6E03B-18D6-4364-9455-6155FD2B7F1A'))
        params = self.makeParams(event)
        weekly = CustomRecurrenceDialog.extractIsWeekly(params)
        self.failUnlessEqual(True, weekly)
        days = CustomRecurrenceDialog.extractGuiWeekdays(params)
        guiEventDay = CustomRecurrenceDialog._rr_weekday_to_gui(
                            event.startTime.weekday())
        self.failUnless([1] == days or guiEventDay == 1)
        self.failUnlessEqual(1, CustomRecurrenceDialog.extractInterval(params))

        #### every sun/tue/thu
        event = pim.EventStamp(sharing.findUID(
                                self.view,
                                '00516393-29AF-4DF6-A786-51C7DDBDCCF8'))
        params = self.makeParams(event)
        weekly = CustomRecurrenceDialog.extractIsWeekly(params)
        self.failUnlessEqual(True, weekly)
        days = CustomRecurrenceDialog.extractGuiWeekdays(params)
        self.failUnlessEqual([0, 2, 4], days)
        self.failUnlessEqual(1, CustomRecurrenceDialog.extractInterval(params))

    def testCustomMonthly(self):
        self.Import(self.view, 'CustomRecurMonthly.ics')
        event = pim.EventStamp(sharing.findUID(
                                self.view,
                                'AFAF34CC-827E-43EE-A7BB-004F7685E09E'))
        #### monthly, first wed
        params = self.makeParams(event)
        
        weekly = CustomRecurrenceDialog.extractIsWeekly(params)
        self.failUnlessEqual(False, weekly)
        monthly = CustomRecurrenceDialog.extractIsMonthly(params)
        self.failUnlessEqual(True, monthly)
        
        tuples = CustomRecurrenceDialog.extractGuiByWeekday(params)
        self.failUnlessEqual([(3, 1)], tuples)
        self.failUnlessEqual(1, CustomRecurrenceDialog.extractInterval(params))
        
        #### monthly, last thu
        event = pim.EventStamp(sharing.findUID(
                                self.view,
                                '1F9963CE-56D6-4C76-8C8A-444A9DF6A4C5'))
        params = self.makeParams(event)
        
        weekly = CustomRecurrenceDialog.extractIsWeekly(params)
        self.failUnlessEqual(False, weekly)
        monthly = CustomRecurrenceDialog.extractIsMonthly(params)
        self.failUnlessEqual(True, monthly)
        
        tuples = CustomRecurrenceDialog.extractGuiByWeekday(params)
        self.failUnlessEqual([(4, -1)], tuples)
        self.failUnlessEqual(1, CustomRecurrenceDialog.extractInterval(params))      
        
        

if __name__ == "__main__":
    unittest.main()
