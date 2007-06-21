#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
from PyICU import Locale as ICULocale, ICUtzinfo, FloatingTZ


class TimeZoneTestCase(SingleRepositoryTestCase):
    def setUp(self):
        super(TimeZoneTestCase, self).setUp()
        view = self.view
        view.tzinfo.setDefault(view.tzinfo.getInstance("America/Los_Angeles"))
        self.tzInfoItem = TimeZoneInfo.get(self.view)

    def testGetTimeZone(self):
        self.failIfEqual(self.tzInfoItem.default, None)

    def testSetTimeZone(self):
        self.tzInfoItem.default = self.view.tzinfo.getInstance("America/Los_Angeles")
        self.failUnlessEqual(self.tzInfoItem.default.timezone.getID(), "America/Los_Angeles")

        self.tzInfoItem.default = self.view.tzinfo.getInstance("America/New_York")
        self.failUnlessEqual(self.tzInfoItem.default.timezone.getID(), "America/New_York")

class DefaultTimeZoneTestCase(TimeZoneTestCase):
    def testGetTimeZone(self):
        super(DefaultTimeZoneTestCase, self).testGetTimeZone()
        self.failUnlessEqual(self.view.tzinfo.floating, self.tzInfoItem.default)

    def testSetTimeZone(self):
        self.tzInfoItem.default = self.view.tzinfo.getInstance("America/New_York")
        self.failUnlessEqual(self.view.tzinfo.default, self.tzInfoItem.default)

class CanonicalTimeZoneTestCase(SingleRepositoryTestCase):
    def setUp(self):
        super(CanonicalTimeZoneTestCase, self).setUp()
        view = self.view
        view.tzinfo.setDefault(view.tzinfo.getInstance("America/Los_Angeles"))

    def testEquivalent(self):
        tz = self.view.tzinfo.getInstance("PST")
        canonicalTz = TimeZoneInfo.get(self.view).canonicalTimeZone(tz)

        self.failUnlessEqual(canonicalTz.tzid, "America/Los_Angeles")

    def testNew(self):
        tz = self.view.tzinfo.getInstance("America/Caracas")
        info = TimeZoneInfo.get(self.view)
        canonicalTz = info.canonicalTimeZone(tz)

        self.failUnless(canonicalTz is tz)
        self.failUnless(tz.tzid in info.wellKnownIDs)

    def testNone(self):
        info = TimeZoneInfo.get(self.view)
        canonicalTz = info.canonicalTimeZone(None)

        self.failUnless(canonicalTz is self.view.tzinfo.floating)

class KnownTimeZonesTestCase(SingleRepositoryTestCase):
    def setUp(self):
        super(KnownTimeZonesTestCase, self).setUp()
        self.info = TimeZoneInfo.get(self.view)

    def testKnownTimeZones(self):
        numZones = 0
        for name, tz in self.info.iterTimeZones():
            self.failUnless(isinstance(name, unicode))
            self.failUnless(isinstance(tz, (ICUtzinfo, FloatingTZ)))
            numZones += 1
        self.failIf(numZones <= 0)

class PersistenceTestCase(SingleRepositoryTestCase):

    def setUp(self):
        super(PersistenceTestCase, self).setUp()

    def testGetTimeZone(self):
        # [Bug 5209] The timezone now defaults to floating
        defaultTzItem = TimeZoneInfo.get(self.view)

        self.failUnlessEqual(defaultTzItem.default,
                             self.view.tzinfo.floating)

    def testPerView(self):
        defaultTzItemOne = TimeZoneInfo.get(self.view)
        defaultTzItemTwo = TimeZoneInfo.get(self.view.repository.createView('two'))

        self.failIf(defaultTzItemOne is defaultTzItemTwo)

    def testTimeZoneSaved(self):
        # Test case should:
        #
        # - Load the repo (Done in setUp())
        # - Get the repo's default DefaultTimeZone
        view = self.view
        defaultTzItem = TimeZoneInfo.get(view)
        # - Change the default DefaultTimeZone
        defaultTzItem.default = self.view.tzinfo.getInstance("GMT")
        self.failUnlessEqual(defaultTzItem.default,
                             self.view.tzinfo.getInstance("GMT"))
        # - Save the repo
        view.commit()

        # - Change the DefaultTimeZone default timezone
        view.tzinfo.setDefault(view.tzinfo.getInstance("America/Los_Angeles"))

        # - Reopen the repo
        self.reopenRepository()  # commits changes, including tzinfo.default
        view = self.view
        self.manager = None

        # - Now check the default timezone
        defaultTzItem = TimeZoneInfo.get(view)
        # ... see that it changed to what's in the repo
        self.failUnlessEqual(self.view.tzinfo.getInstance("America/Los_Angeles"),
                             defaultTzItem.default)
        # ... and make sure it is still the default!
        self.failUnlessEqual(defaultTzItem.default,
                             self.view.tzinfo.default)
        
    def testTimezoneConversion(self):
        """
        Floating events should be converted to non-floating when turning on
        show timezones.
        
        """
        view = self.view
        view.tzinfo.setDefault(view.tzinfo.getInstance("America/Los_Angeles"))
        tzprefs = schema.ns('osaf.pim', self.view).TimezonePrefs
        tzprefs.showUI = False
        
        start = datetime(2007, 1, 17, 13, tzinfo=view.tzinfo.floating)
        event = CalendarEvent(None, itsView=view)
        event.startTime = start
        
        tzprefs.showUI = True        

        self.failUnlessEqual(event.startTime.tzinfo.timezone.getID(),
                             "America/Los_Angeles")

class AbstractTimeZoneTestCase(RepositoryTestCase):
    def setUp(self):
        super(AbstractTimeZoneTestCase, self).setUp()

        self.oldLocale = ICULocale.getDefault()
        self.oldTzinfo = self.view.tzinfo.default

    def tearDown(self):
        if self.oldLocale is not None:
            ICULocale.setDefault(self.oldLocale)
        if self.oldTzinfo is not None:
            self.view.tzinfo.setDefault(self.oldTzinfo)

class DatetimeFormatTestCase(AbstractTimeZoneTestCase):

    def setUp(self):
        super(DatetimeFormatTestCase, self).setUp()
        view = self.view
        ICULocale.setDefault(ICULocale.getUS())
        view.tzinfo.setDefault(view.tzinfo.getInstance("America/Los_Angeles"))

    def testNoTimeZone(self):

        dt = datetime(1999, 1, 2, 13, 46)
        self.failUnlessEqual(formatTime(self.view, dt), "1:46 PM")

        dt = datetime(2022, 9, 17, 2, 11)
        self.failUnlessEqual(formatTime(self.view, dt), "2:11 AM")

    def testFloating(self):

        dt = datetime(1999, 1, 2, 13, 46, tzinfo=self.view.tzinfo.floating)
        self.failUnlessEqual(formatTime(self.view, dt), "1:46 PM")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo=self.view.tzinfo.floating)
        self.failUnlessEqual(formatTime(self.view, dt), "2:11 AM")

    def testDefaultTimeZone(self):

        dt = datetime(1999, 1, 2, 13, 46, tzinfo=self.view.tzinfo.default)
        self.failUnlessEqual(formatTime(self.view, dt), "1:46 PM")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = self.view.tzinfo.default)
        self.failUnlessEqual(formatTime(self.view, dt), "2:11 AM")

    def testDifferentTimeZone(self):

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = self.view.tzinfo.getInstance("America/New_York"))
        self.failUnlessEqual(formatTime(self.view, dt), "2:11 AM EDT")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo=self.view.tzinfo.getInstance("Africa/Johannesburg"))
        self.failUnlessEqual(formatTime(self.view, dt), "2:11 AM GMT+02:00")

class DatetimeFrenchFormatTestCase(AbstractTimeZoneTestCase):

    def setUp(self):
        super(DatetimeFrenchFormatTestCase, self).setUp()
        view = self.view
        ICULocale.setDefault(ICULocale.getFrance())
        view.tzinfo.setDefault(view.tzinfo.getInstance("Europe/Paris"))

    def testNoTimeZone(self):
        dt = datetime(1999, 1, 2, 13, 46)
        self.failUnlessEqual(formatTime(self.view, dt), "13:46")

        dt = datetime(2022, 9, 17, 2, 11)
        self.failUnlessEqual(formatTime(self.view, dt), u"02:11")

    def testDefaultTimeZone(self):
        dt = datetime(1999, 1, 2, 13, 46, tzinfo=self.view.tzinfo.default)
        self.failUnlessEqual(formatTime(self.view, dt), "13:46")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo=self.view.tzinfo.default)
        self.failUnlessEqual(formatTime(self.view, dt), u"02:11")

    def testDifferentTimeZone(self):
        dt = datetime(2022, 9, 17, 2, 11,
                tzinfo=self.view.tzinfo.getInstance("America/New_York"))
        self.failUnlessEqual(formatTime(self.view, dt), u'02:11 HAE (\u00c9UA)')

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = self.view.tzinfo.getInstance("Africa/Johannesburg"))
        self.failUnlessEqual(formatTime(self.view, dt), u"02:11 GMT+02:00")

class StripTimeZoneTestCase(AbstractTimeZoneTestCase):
    def setUp(self):
        super(StripTimeZoneTestCase, self).setUp()
        self.view.tzinfo.setDefault(
            self.view.tzinfo.getInstance("America/Los_Angeles"))

    def testStripNaiveDatetime(self):
        """ Test that stripTimeZone() works on a naive datetime"""
        dt = datetime(2003, 9, 17, 2, 11, tzinfo = None)

        self.failUnlessEqual(stripTimeZone(self.view, dt), dt)


    def testStripOtherDatetime(self):
        """ Test that stripTimeZone() works on a datetime in
        a timezone that's not the default"""
        dt = datetime(2012, 4, 28, 18, 4,
            tzinfo = self.view.tzinfo.getInstance("Asia/Beijing"))
        strippedDt = stripTimeZone(self.view, dt)

        self.failUnless(strippedDt.tzinfo is None)

        dtInDefault = dt.astimezone(self.view.tzinfo.default)

        self.failUnlessEqual(strippedDt.date(), dtInDefault.date())
        self.failUnlessEqual(strippedDt.time(), dtInDefault.time())

    def testStripDefaultDatetime(self):
        """ Test that stripTimeZone() works on a datetime in
        the default timezone """
        dt = datetime(2012, 4, 28, 18, 4, tzinfo = self.view.tzinfo.default)
        strippedDt = stripTimeZone(self.view, dt)

        self.failUnless(strippedDt.tzinfo is None)
        self.failUnlessEqual(strippedDt.date(), dt.date())
        self.failUnlessEqual(strippedDt.time(), dt.time())

class CoerceTimeZoneTestCase(AbstractTimeZoneTestCase):
    def setUp(self):
        super(CoerceTimeZoneTestCase, self).setUp()
        view = self.view
        view.tzinfo.setDefault(view.tzinfo.getInstance("America/Los_Angeles"))

    def testCoerceNaiveToNaive(self):
        dt = datetime(2014, 10, 28, 2, 11, tzinfo = None)

        self.failUnlessEqual(coerceTimeZone(self.view, dt, None), dt)

    def testCoerceNaiveToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41, tzinfo = None)
        tzinfo = self.view.tzinfo.default
        coercedDt = coerceTimeZone(self.view, dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(dt.date(), coercedDt.date())
        self.failUnlessEqual(dt.time(), coercedDt.time())

    def testCoerceNaiveToOther(self):
        dt = datetime(2012, 4, 28, 18, 4, tzinfo = None)
        tzinfo = self.view.tzinfo.getInstance("Asia/Tokyo")
        coercedDt = coerceTimeZone(self.view, dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)

        compareDt = coercedDt.astimezone(self.view.tzinfo.default)
        self.failUnlessEqual(dt.date(), compareDt.date())
        self.failUnlessEqual(dt.time(), compareDt.time())

    def testCoerceDefaultToNaive(self):
        dt = datetime(2014, 10, 28, 2, 11,
            tzinfo=self.view.tzinfo.default)

        coercedDt = coerceTimeZone(self.view, dt, None)
        self.failUnlessEqual(dt.date(), coercedDt.date())
        self.failUnlessEqual(dt.time(), coercedDt.time())

    def testCoerceDefaultToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41,
            tzinfo=self.view.tzinfo.default)
        tzinfo = self.view.tzinfo.default
        coercedDt = coerceTimeZone(self.view, dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceDefaultToOther(self):
        dt = datetime(2012, 4, 28, 18, 4,
            tzinfo=self.view.tzinfo.default)
        tzinfo = self.view.tzinfo.getInstance("Asia/Tokyo")
        coercedDt = coerceTimeZone(self.view, dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        # Both are non-naive
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceOtherToNaive(self):
        dt = datetime(2014, 10, 28, 2, 11,
            tzinfo=self.view.tzinfo.getInstance("Africa/Johannesburg"))

        coercedDt = coerceTimeZone(self.view, dt, None)
        self.failUnless(coercedDt.tzinfo is None)

        compareDt = dt.astimezone(self.view.tzinfo.default)
        self.failUnlessEqual(compareDt.date(), coercedDt.date())
        self.failUnlessEqual(compareDt.time(), coercedDt.time())

    def testCoerceOtherToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41,
            tzinfo=self.view.tzinfo.getInstance("Africa/Johannesburg"))
        tzinfo = self.view.tzinfo.default
        coercedDt = coerceTimeZone(self.view, dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceOtherToOwn(self):
        tzinfo = self.view.tzinfo.getInstance("Africa/Johannesburg")
        dt = datetime(2002, 1, 3, 19, 57, 41, tzinfo=tzinfo)
        coercedDt = coerceTimeZone(self.view, dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceOtherToOtherOther(self):
        dt = datetime(2012, 4, 28, 18, 4,
            tzinfo=self.view.tzinfo.getInstance("Africa/Johannesburg"))
        tzinfo = self.view.tzinfo.getInstance("Asia/Tokyo")
        coercedDt = coerceTimeZone(self.view, dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        # Both are non-naive
        self.failUnlessEqual(coercedDt, dt)



class FloatingEventTestCase(SingleRepositoryTestCase):

    def setUp(self):
        super(FloatingEventTestCase, self).setUp()
        self.tzprefs = schema.ns('osaf.pim', self.view).TimezonePrefs
        self.saveTzShowUI = self.tzprefs.showUI
        self.saveDefaultTz = self.view.tzinfo.default
        
        self.tzprefs.default = self.view.tzinfo.getInstance("America/Los_Angeles")
        
    def tearDown(self):
        self.tzprefs.showUI = self.saveTzShowUI
        self.view.tzinfo.setDefault(self.saveDefaultTz)
        super(FloatingEventTestCase, self).tearDown()

    def testChange(self):
        from osaf import sharing
        from osaf.pim import ListCollection
        
        self.tzprefs.showUI = False
        
        gayParee = self.view.tzinfo.getInstance("Europe/Paris")
        
        master = CalendarEvent(itsView=self.view, anyTime=False,
                    startTime=datetime(2007, 2, 7, 11, 30,
                                      tzinfo=self.view.tzinfo.floating),
                    duration=timedelta(hours=1))

        master.rruleset = RecurrenceRuleSet(
            itsView=self.view, rrules=[
                RecurrenceRule(itsView=self.view,freq='daily')
            ]
        )

        ordinary = CalendarEvent(itsView=self.view, anyTime=False,
                    startTime=datetime(2007, 2, 7, 11, 30,
                                      tzinfo=self.view.tzinfo.floating),
                    duration=timedelta(hours=1))
                    
        sharedFloating = CalendarEvent(itsView=self.view, anyTime=False,
                   startTime=datetime(2002, 12, 22, tzinfo=self.view.tzinfo.floating))
        share = sharing.Share(itsView=self.view, hidden=False)
        item = sharing.SharedItem(sharedFloating)
        item.add()
        item.sharedIn = item.shares = [share]
        
        nonFloatingOccurrence = master.getNextOccurrence(
            after=datetime(2007, 5, 2, tzinfo=self.view.tzinfo.floating))

        
        nonFloatingOccurrence.changeThis(
            EventStamp.startTime.name,
            nonFloatingOccurrence.startTime.replace(tzinfo=gayParee)
        )

        titleMod = nonFloatingOccurrence.getNextOccurrence()
        titleMod.itsItem.summary = "yabba dabba doo"
                
        self.tzprefs.showUI = True
        
        tzItem = TimeZoneInfo.get(self.view)
        
        # Make sure that floating is no longer the default
        self.failIfEqual(self.view.tzinfo.default, self.view.tzinfo.floating)
        self.failIfEqual(tzItem.default, self.view.tzinfo.floating)
        self.failUnlessEqual(tzItem.default, self.view.tzinfo.default)
        
        # Make sure the ordinary and master events acquired the default tz
        self.failUnlessEqual(ordinary.startTime.tzinfo, self.view.tzinfo.default)
        self.failUnlessEqual(master.startTime.tzinfo, self.view.tzinfo.default)
        
        # Make sure the non-floating occurrence didn't have its tz changed
        self.failUnlessEqual(nonFloatingOccurrence.startTime.tzinfo, gayParee)
        
        # Check the master's occurrences ...
        for event in map(EventStamp, master.occurrences):
            # Everything but the modification we just made should have
            # the default timezone set for startTime ...
            if event != nonFloatingOccurrence:
                self.failUnlessEqual(event.startTime.tzinfo, self.view.tzinfo.default)
                                     
            # and recurrenceIDs should always have the master's tzinfo
            self.failUnlessEqual(event.recurrenceID.tzinfo, self.view.tzinfo.default)

        # ... and the shared item's tzinfo should not have changed
        self.failUnlessEqual(sharedFloating.startTime.tzinfo,
                             self.view.tzinfo.floating)

        self.tzprefs.showUI = False
        self.failUnlessEqual(tzItem.default, self.view.tzinfo.floating)
        self.failIfEqual(self.view.tzinfo.floating, self.view.tzinfo.default)

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


