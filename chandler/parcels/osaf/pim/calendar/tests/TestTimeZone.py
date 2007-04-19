#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

from repository.tests.RepositoryTestCase import RepositoryTestCase
from util.testcase import SingleRepositoryTestCase
from repository.persistence.RepositoryView import NullRepositoryView
from osaf.pim.calendar.TimeZone import *
from osaf.pim.calendar.Calendar import CalendarEvent, EventStamp    
from osaf.pim.calendar.Recurrence import RecurrenceRuleSet, RecurrenceRule
from datetime import *
from application import schema
from PyICU import (TimeZone as ICUTimeZone, Locale as ICULocale, ICUtzinfo)

class TimeZoneTestCase(RepositoryTestCase):
    def setUp(self):
        super(TimeZoneTestCase, self).setUp(True)
        ICUTimeZone.setDefault(ICUTimeZone.createTimeZone("America/Los_Angeles"))
        self.tzInfoItem = TimeZoneInfo.get(self.rep.view)

    def testGetTimeZone(self):
        self.failIfEqual(self.tzInfoItem.default, None)

    def testSetTimeZone(self):
        self.tzInfoItem.default = ICUtzinfo.getInstance("America/Los_Angeles")
        self.failUnlessEqual(self.tzInfoItem.default.timezone.getID(), "America/Los_Angeles")

        self.tzInfoItem.default = ICUtzinfo.getInstance("America/New_York")
        self.failUnlessEqual(self.tzInfoItem.default.timezone.getID(), "America/New_York")

class DefaultTimeZoneTestCase(TimeZoneTestCase):
    def testGetTimeZone(self):
        super(DefaultTimeZoneTestCase, self).testGetTimeZone()
        self.failUnlessEqual(ICUtzinfo.floating, self.tzInfoItem.default)

    def testSetTimeZone(self):
        self.tzInfoItem.default = ICUtzinfo.getInstance("America/New_York")
        self.failUnlessEqual(ICUtzinfo.default, self.tzInfoItem.default)

class CanonicalTimeZoneTestCase(RepositoryTestCase):
    def setUp(self):
        super(CanonicalTimeZoneTestCase, self).setUp(True)
        ICUTimeZone.setDefault(ICUTimeZone.createTimeZone("America/Los_Angeles"))

    def testEquivalent(self):
        tz = ICUtzinfo.getInstance("PST")
        canonicalTz = TimeZoneInfo.get(self.rep.view).canonicalTimeZone(tz)

        self.failUnlessEqual(canonicalTz.tzid, "America/Los_Angeles")

    def testNew(self):
        tz = ICUtzinfo.getInstance("America/Caracas")
        info = TimeZoneInfo.get(self.rep.view)
        canonicalTz = info.canonicalTimeZone(tz)

        self.failUnless(canonicalTz is tz)
        self.failUnless(tz.tzid in info.wellKnownIDs)

    def testNone(self):
        info = TimeZoneInfo.get(self.rep.view)
        canonicalTz = info.canonicalTimeZone(None)

        self.failUnless(canonicalTz is ICUtzinfo.floating)

class KnownTimeZonesTestCase(RepositoryTestCase):
    def setUp(self):
        super(KnownTimeZonesTestCase, self).setUp(True)
        self.info = TimeZoneInfo.get(self.rep.view)

    def testKnownTimeZones(self):
        numZones = 0
        for name, tz in self.info.iterTimeZones():
            self.failUnless(isinstance(name, unicode))
            self.failUnless(isinstance(tz, ICUtzinfo))
            numZones += 1
        self.failIf(numZones <= 0)

class PersistenceTestCase(RepositoryTestCase):

    def setUp(self):
        super(PersistenceTestCase, self).setUp(True)

    def testGetTimeZone(self):
        # [Bug 5209] The timezone now defaults to floating
        defaultTzItem = TimeZoneInfo.get(self.rep.view)

        self.failUnlessEqual(defaultTzItem.default,
                             ICUtzinfo.floating)

    def testPerView(self):
        defaultTzItemOne = TimeZoneInfo.get(self.rep.view)
        defaultTzItemTwo = TimeZoneInfo.get(self.rep.createView('two'))

        self.failIf(defaultTzItemOne is defaultTzItemTwo)

    def testTimeZoneSaved(self):
        # Test case should:
        #
        # - Load the repo (Done in setUp())
        # - Get the repo's default DefaultTimeZone
        view = self.rep.view
        defaultTzItem = TimeZoneInfo.get(view)
        # - Change the default DefaultTimeZone
        defaultTzItem.default = ICUtzinfo.getInstance("GMT")
        self.failUnlessEqual(defaultTzItem.default,
                ICUtzinfo.getInstance("GMT"))
        # - Save the repo
        view.commit()

        # - Change the DefaultTimeZone default timezone
        ICUTimeZone.setDefault(ICUTimeZone.createTimeZone("America/Los_Angeles"))

        # - Reopen the repo
        self._reopenRepository()
        view = self.rep.view
        self.manager = None

        # - Now check the default timezone
        defaultTzItem = TimeZoneInfo.get(view)
        # ... see that it changed to what's in the repo
        self.failIfEqual(ICUtzinfo.getInstance("America/Los_Angeles"),
                        defaultTzItem.default)
        # ... and make sure it is still the default!
        self.failUnlessEqual(defaultTzItem.default,
                             ICUtzinfo.default)
        
    def testTimezoneConversion(self):
        """
        Floating events should be converted to non-floating when turning on
        show timezones.
        
        """
        pacific = ICUTimeZone.createTimeZone("America/Los_Angeles")
        ICUTimeZone.setDefault(pacific)
        tzprefs = schema.ns('osaf.pim', self.rep.view).TimezonePrefs
        tzprefs.showUI = False
        
        start = datetime(2007, 1, 17, 13, tzinfo=ICUtzinfo.floating)
        event = CalendarEvent(None, itsView=self.rep.view)
        event.startTime = start
        
        tzprefs.showUI = True        

        self.failUnlessEqual(event.startTime.tzinfo.timezone.getID(),
                             "America/Los_Angeles")

class AbstractTimeZoneTestCase(unittest.TestCase):
    def setUp(self):
        super(AbstractTimeZoneTestCase, self).setUp()

        self.oldLocale = ICULocale.getDefault()
        self.oldTzinfo = ICUtzinfo.default

    def tearDown(self):
        if self.oldLocale is not None:
            ICULocale.setDefault(self.oldLocale)
        if self.oldTzinfo is not None:
            ICUTimeZone.setDefault(self.oldTzinfo.timezone)

class DatetimeFormatTestCase(AbstractTimeZoneTestCase):

    def setUp(self):
        super(DatetimeFormatTestCase, self).setUp()
        ICULocale.setDefault(ICULocale.getUS())
        ICUTimeZone.setDefault(
            ICUtzinfo.getInstance("America/Los_Angeles").timezone)

    def testNoTimeZone(self):

        dt = datetime(1999, 1, 2, 13, 46)
        self.failUnlessEqual(formatTime(dt), "1:46 PM")

        dt = datetime(2022, 9, 17, 2, 11)
        self.failUnlessEqual(formatTime(dt), "2:11 AM")

    def testFloating(self):

        dt = datetime(1999, 1, 2, 13, 46, tzinfo=ICUtzinfo.floating)
        self.failUnlessEqual(formatTime(dt), "1:46 PM")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo=ICUtzinfo.floating)
        self.failUnlessEqual(formatTime(dt), "2:11 AM")

    def testDefaultTimeZone(self):

        dt = datetime(1999, 1, 2, 13, 46, tzinfo=ICUtzinfo.default)
        self.failUnlessEqual(formatTime(dt), "1:46 PM")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = ICUtzinfo.default)
        self.failUnlessEqual(formatTime(dt), "2:11 AM")

    def testDifferentTimeZone(self):

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = ICUtzinfo.getInstance("America/New_York"))
        self.failUnlessEqual(formatTime(dt), "2:11 AM EDT")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo=ICUtzinfo.getInstance("Africa/Johannesburg"))
        self.failUnlessEqual(formatTime(dt), "2:11 AM GMT+02:00")

class DatetimeFrenchFormatTestCase(AbstractTimeZoneTestCase):
    def setUp(self):
        super(DatetimeFrenchFormatTestCase, self).setUp()
        ICULocale.setDefault(ICULocale.getFrance())
        ICUTimeZone.setDefault(
            ICUtzinfo.getInstance("Europe/Paris").timezone)


    def testNoTimeZone(self):
        dt = datetime(1999, 1, 2, 13, 46)
        self.failUnlessEqual(formatTime(dt), "13:46")

        dt = datetime(2022, 9, 17, 2, 11)
        self.failUnlessEqual(formatTime(dt), u"02:11")

    def testDefaultTimeZone(self):
        dt = datetime(1999, 1, 2, 13, 46, tzinfo=ICUtzinfo.default)
        self.failUnlessEqual(formatTime(dt), "13:46")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo=ICUtzinfo.default)
        self.failUnlessEqual(formatTime(dt), u"02:11")

    def testDifferentTimeZone(self):
        dt = datetime(2022, 9, 17, 2, 11,
                tzinfo=ICUtzinfo.getInstance("America/New_York"))
        self.failUnlessEqual(formatTime(dt), u'02:11 HAE (\u00c9UA)')

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = ICUtzinfo.getInstance("Africa/Johannesburg"))
        self.failUnlessEqual(formatTime(dt), u"02:11 GMT+02:00")

class StripTimeZoneTestCase(AbstractTimeZoneTestCase):
    def setUp(self):
        super(StripTimeZoneTestCase, self).setUp()
        ICUTimeZone.setDefault(
            ICUtzinfo.getInstance("America/Los_Angeles").timezone)

    def testStripNaiveDatetime(self):
        """ Test that stripTimeZone() works on a naive datetime"""
        dt = datetime(2003, 9, 17, 2, 11, tzinfo = None)

        self.failUnlessEqual(stripTimeZone(dt), dt)


    def testStripOtherDatetime(self):
        """ Test that stripTimeZone() works on a datetime in
        a timezone that's not the default"""
        dt = datetime(2012, 4, 28, 18, 4,
            tzinfo = ICUtzinfo.getInstance("Asia/Beijing"))
        strippedDt = stripTimeZone(dt)

        self.failUnless(strippedDt.tzinfo is None)

        dtInDefault = dt.astimezone(ICUtzinfo.default)

        self.failUnlessEqual(strippedDt.date(), dtInDefault.date())
        self.failUnlessEqual(strippedDt.time(), dtInDefault.time())

    def testStripDefaultDatetime(self):
        """ Test that stripTimeZone() works on a datetime in
        the default timezone """
        dt = datetime(2012, 4, 28, 18, 4, tzinfo = ICUtzinfo.default)
        strippedDt = stripTimeZone(dt)

        self.failUnless(strippedDt.tzinfo is None)
        self.failUnlessEqual(strippedDt.date(), dt.date())
        self.failUnlessEqual(strippedDt.time(), dt.time())

class CoerceTimeZoneTestCase(AbstractTimeZoneTestCase):
    def setUp(self):
        super(CoerceTimeZoneTestCase, self).setUp()
        ICUTimeZone.setDefault(
            ICUtzinfo.getInstance("America/Los_Angeles").timezone)

    def testCoerceNaiveToNaive(self):
        dt = datetime(2014, 10, 28, 2, 11, tzinfo = None)

        self.failUnlessEqual(coerceTimeZone(dt, None), dt)

    def testCoerceNaiveToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41, tzinfo = None)
        tzinfo = ICUtzinfo.default
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(dt.date(), coercedDt.date())
        self.failUnlessEqual(dt.time(), coercedDt.time())

    def testCoerceNaiveToOther(self):
        dt = datetime(2012, 4, 28, 18, 4, tzinfo = None)
        tzinfo = ICUtzinfo.getInstance("Asia/Tokyo")
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)

        compareDt = coercedDt.astimezone(ICUtzinfo.default)
        self.failUnlessEqual(dt.date(), compareDt.date())
        self.failUnlessEqual(dt.time(), compareDt.time())

    def testCoerceDefaultToNaive(self):
        dt = datetime(2014, 10, 28, 2, 11,
            tzinfo=ICUtzinfo.default)

        coercedDt = coerceTimeZone(dt, None)
        self.failUnlessEqual(dt.date(), coercedDt.date())
        self.failUnlessEqual(dt.time(), coercedDt.time())

    def testCoerceDefaultToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41,
            tzinfo=ICUtzinfo.default)
        tzinfo = ICUtzinfo.default
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceDefaultToOther(self):
        dt = datetime(2012, 4, 28, 18, 4,
            tzinfo=ICUtzinfo.default)
        tzinfo = ICUtzinfo.getInstance("Asia/Tokyo")
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        # Both are non-naive
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceOtherToNaive(self):
        dt = datetime(2014, 10, 28, 2, 11,
            tzinfo=ICUtzinfo.getInstance("Africa/Johannesburg"))

        coercedDt = coerceTimeZone(dt, None)
        self.failUnless(coercedDt.tzinfo is None)

        compareDt = dt.astimezone(ICUtzinfo.default)
        self.failUnlessEqual(compareDt.date(), coercedDt.date())
        self.failUnlessEqual(compareDt.time(), coercedDt.time())

    def testCoerceOtherToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41,
            tzinfo=ICUtzinfo.getInstance("Africa/Johannesburg"))
        tzinfo = ICUtzinfo.default
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceOtherToOwn(self):
        tzinfo = ICUtzinfo.getInstance("Africa/Johannesburg")
        dt = datetime(2002, 1, 3, 19, 57, 41, tzinfo=tzinfo)
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceOtherToOtherOther(self):
        dt = datetime(2012, 4, 28, 18, 4,
            tzinfo=ICUtzinfo.getInstance("Africa/Johannesburg"))
        tzinfo = ICUtzinfo.getInstance("Asia/Tokyo")
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        # Both are non-naive
        self.failUnlessEqual(coercedDt, dt)



class FloatingEventTestCase(SingleRepositoryTestCase):

    def setUp(self):
        super(FloatingEventTestCase, self).setUp()
        self.tzprefs = schema.ns('osaf.pim', self.view).TimezonePrefs
        self.saveTzShowUI = self.tzprefs.showUI
        self.saveDefaultTz = ICUtzinfo.default
        
        self.tzprefs.default = ICUtzinfo.getInstance("America/Los_Angeles")
        
    def tearDown(self):
        self.tzprefs.showUI = self.saveTzShowUI
        ICUTimeZone.setDefault(self.saveDefaultTz.timezone)
        super(FloatingEventTestCase, self).tearDown()

    def testChange(self):
        from osaf import sharing
        from osaf.pim import ListCollection
        
        self.tzprefs.showUI = False
        
        gayParee = ICUtzinfo.getInstance("Europe/Paris")
        
        master = CalendarEvent(itsView=self.view, anyTime=False,
                    startTime=datetime(2007, 2, 7, 11, 30,
                                      tzinfo=ICUtzinfo.floating),
                    duration=timedelta(hours=1))

        master.rruleset = RecurrenceRuleSet(
            itsView=self.view, rrules=[
                RecurrenceRule(itsView=self.view,freq='daily')
            ]
        )

        ordinary = CalendarEvent(itsView=self.view, anyTime=False,
                    startTime=datetime(2007, 2, 7, 11, 30,
                                      tzinfo=ICUtzinfo.floating),
                    duration=timedelta(hours=1))
                    
        sharedFloating = CalendarEvent(itsView=self.view, anyTime=False,
                   startTime=datetime(2002, 12, 22, tzinfo=ICUtzinfo.floating))
        share = sharing.Share(itsView=self.view, hidden=False)
        item = sharing.SharedItem(sharedFloating)
        item.add()
        item.sharedIn = item.shares = [share]
        
        nonFloatingOccurrence = master.getNextOccurrence(
            after=datetime(2007, 5, 2, tzinfo=ICUtzinfo.floating))
            
        nonFloatingOccurrence.changeThis(
            EventStamp.startTime.name,
            nonFloatingOccurrence.startTime.replace(tzinfo=gayParee)
        )
        
        self.tzprefs.showUI = True
        
        tzItem = TimeZoneInfo.get(self.view)
        
        # Make sure that floating is no longer the default
        self.failIfEqual(ICUtzinfo.default, ICUtzinfo.floating)
        self.failIfEqual(tzItem.default, ICUtzinfo.floating)
        self.failUnlessEqual(tzItem.default, ICUtzinfo.default)
        
        # Make sure the ordinary and master events acquired the default tz
        self.failUnlessEqual(ordinary.startTime.tzinfo, ICUtzinfo.default)
        self.failUnlessEqual(master.startTime.tzinfo, ICUtzinfo.default)
        
        # Make sure the non-floating occurrence didn't have its tz changed
        self.failUnlessEqual(nonFloatingOccurrence.startTime.tzinfo, gayParee)
        
        # Check the master's occurrences ...
        for event in map(EventStamp, master.occurrences):
            # Everything but the modification we just made should have
            # the default timezone set for startTime ...
            if event != nonFloatingOccurrence:
                self.failUnlessEqual(event.startTime.tzinfo,
                                     ICUtzinfo.default)
                                     
            # ... but recurrenceIDs should always have the master's tzinfo
            self.failIfEqual(event.recurrenceID.tzinfo,
                             ICUtzinfo.default)

        # ... and the shared item's tzinfo should not have changed
        self.failUnlessEqual(sharedFloating.startTime.tzinfo,
                             ICUtzinfo.floating)

        self.tzprefs.showUI = False
        self.failUnlessEqual(tzItem.default, ICUtzinfo.floating)
        self.failIfEqual(ICUtzinfo.floating, ICUtzinfo.default)

def suite():
    """
    Unit test suite; run by testing
    
       'parcels.osaf.pim.calendar.tests.TestTimeZone.suite'
       
    """
    
    from util.test_finder import ScanningLoader
    from unittest import defaultTestLoader, TestSuite
    loader = ScanningLoader()
    return TestSuite(
        [loader.loadTestsFromName(__name__+'.'+test_name)
            for test_name in [
                'TimeZoneTestCase',
                'DefaultTimeZoneTestCase',
                'StripTimeZoneTestCase',
                'CoerceTimeZoneTestCase',
                'KnownTimeZonesTestCase',
                'FloatingEventTestCase']]
    )


if __name__ == "__main__":
    unittest.main()


