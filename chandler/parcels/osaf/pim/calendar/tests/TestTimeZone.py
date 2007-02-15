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


import unittest, PyICU

from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.persistence.RepositoryView import NullRepositoryView
from osaf.pim.calendar.TimeZone import *
from osaf.pim.calendar.Calendar import CalendarEvent
from datetime import datetime
from application import schema

class TimeZoneTestCase(RepositoryTestCase):
    def setUp(self):
        super(TimeZoneTestCase, self).setUp(True)
        PyICU.TimeZone.setDefault(PyICU.TimeZone.createTimeZone("America/Los_Angeles"))
        self.tzInfoItem = TimeZoneInfo.get(self.rep.view)

    def testGetTimeZone(self):
        self.failIfEqual(self.tzInfoItem.default, None)

    def testSetTimeZone(self):
        self.tzInfoItem.default = PyICU.ICUtzinfo.getInstance("America/Los_Angeles")
        self.failUnlessEqual(self.tzInfoItem.default.timezone.getID(), "America/Los_Angeles")

        self.tzInfoItem.default = PyICU.ICUtzinfo.getInstance("America/New_York")
        self.failUnlessEqual(self.tzInfoItem.default.timezone.getID(), "America/New_York")

class DefaultTimeZoneTestCase(TimeZoneTestCase):
    def testGetTimeZone(self):
        super(DefaultTimeZoneTestCase, self).testGetTimeZone()
        self.failUnlessEqual(PyICU.ICUtzinfo.floating, self.tzInfoItem.default)

    def testSetTimeZone(self):
        self.tzInfoItem.default = PyICU.ICUtzinfo.getInstance("America/New_York")
        self.failUnlessEqual(PyICU.ICUtzinfo.default, self.tzInfoItem.default)

class CanonicalTimeZoneTestCase(RepositoryTestCase):
    def setUp(self):
        super(CanonicalTimeZoneTestCase, self).setUp(True)
        PyICU.TimeZone.setDefault(PyICU.TimeZone.createTimeZone("America/Los_Angeles"))

    def testEquivalent(self):
        tz = PyICU.ICUtzinfo.getInstance("PST")
        canonicalTz = TimeZoneInfo.get(self.rep.view).canonicalTimeZone(tz)

        self.failUnlessEqual(canonicalTz.tzid, "America/Los_Angeles")

    def testNew(self):
        tz = PyICU.ICUtzinfo.getInstance("America/Caracas")
        info = TimeZoneInfo.get(self.rep.view)
        canonicalTz = info.canonicalTimeZone(tz)

        self.failUnless(canonicalTz is tz)
        self.failUnless(tz.tzid in info.wellKnownIDs)

    def testNone(self):
        info = TimeZoneInfo.get(self.rep.view)
        canonicalTz = info.canonicalTimeZone(None)

        self.failUnless(canonicalTz is PyICU.ICUtzinfo.floating)

class KnownTimeZonesTestCase(RepositoryTestCase):
    def setUp(self):
        super(KnownTimeZonesTestCase, self).setUp(True)
        self.info = TimeZoneInfo.get(self.rep.view)

    def testKnownTimeZones(self):
        numZones = 0
        for name, tz in self.info.iterTimeZones():
            self.failUnless(isinstance(name, unicode))
            self.failUnless(isinstance(tz, PyICU.ICUtzinfo))
            numZones += 1
        self.failIf(numZones <= 0)

class PersistenceTestCase(RepositoryTestCase):

    def setUp(self):
        super(PersistenceTestCase, self).setUp(True)

    def testGetTimeZone(self):
        # [Bug 5209] The timezone now defaults to floating
        defaultTzItem = TimeZoneInfo.get(self.rep.view)

        self.failUnlessEqual(defaultTzItem.default,
                             PyICU.ICUtzinfo.floating)

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
        defaultTzItem.default = PyICU.ICUtzinfo.getInstance("GMT")
        self.failUnlessEqual(defaultTzItem.default,
                PyICU.ICUtzinfo.getInstance("GMT"))
        # - Save the repo
        view.commit()

        # - Change the DefaultTimeZone default timezone
        PyICU.TimeZone.setDefault(PyICU.TimeZone.createTimeZone("America/Los_Angeles"))

        # - Reopen the repo
        self._reopenRepository()
        view = self.rep.view
        self.manager = None

        # - Now check the default timezone
        defaultTzItem = TimeZoneInfo.get(view)
        # ... see that it changed to what's in the repo
        self.failIfEqual(PyICU.ICUtzinfo.getInstance("America/Los_Angeles"),
                        defaultTzItem.default)
        # ... and make sure it is still the default!
        self.failUnlessEqual(defaultTzItem.default,
                             PyICU.ICUtzinfo.default)
        
    def testTimezoneConversion(self):
        """
        Floating events should be converted to non-floating when turning on
        show timezones.
        
        """
        pacific = PyICU.TimeZone.createTimeZone("America/Los_Angeles")
        PyICU.TimeZone.setDefault(pacific)
        tzprefs = schema.ns('osaf.pim', self.rep.view).TimezonePrefs
        tzprefs.showUI = False
        
        start = datetime(2007, 1, 17, 13, tzinfo=PyICU.ICUtzinfo.floating)
        event = CalendarEvent(None, itsView=self.rep.view)
        event.startTime = start
        
        tzprefs.showUI = True        

        self.failUnlessEqual(event.startTime.tzinfo.timezone.getID(),
                             "America/Los_Angeles")

class AbstractTimeZoneTestCase(unittest.TestCase):
    def setUp(self):
        super(AbstractTimeZoneTestCase, self).setUp()

        self.oldLocale = PyICU.Locale.getDefault()
        self.oldTzinfo = PyICU.ICUtzinfo.default

    def tearDown(self):
        if self.oldLocale is not None:
            PyICU.Locale.setDefault(self.oldLocale)
        if self.oldTzinfo is not None:
            PyICU.TimeZone.setDefault(self.oldTzinfo.timezone)

class DatetimeFormatTestCase(AbstractTimeZoneTestCase):

    def setUp(self):
        super(DatetimeFormatTestCase, self).setUp()
        PyICU.Locale.setDefault(PyICU.Locale.getUS())
        PyICU.TimeZone.setDefault(
            PyICU.ICUtzinfo.getInstance("America/Los_Angeles").timezone)

    def testNoTimeZone(self):

        dt = datetime(1999, 1, 2, 13, 46)
        self.failUnlessEqual(formatTime(dt), "1:46 PM")

        dt = datetime(2022, 9, 17, 2, 11)
        self.failUnlessEqual(formatTime(dt), "2:11 AM")

    def testFloating(self):

        dt = datetime(1999, 1, 2, 13, 46, tzinfo=PyICU.ICUtzinfo.floating)
        self.failUnlessEqual(formatTime(dt), "1:46 PM")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo=PyICU.ICUtzinfo.floating)
        self.failUnlessEqual(formatTime(dt), "2:11 AM")

    def testDefaultTimeZone(self):

        dt = datetime(1999, 1, 2, 13, 46, tzinfo=PyICU.ICUtzinfo.default)
        self.failUnlessEqual(formatTime(dt), "1:46 PM")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = PyICU.ICUtzinfo.default)
        self.failUnlessEqual(formatTime(dt), "2:11 AM")

    def testDifferentTimeZone(self):

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = PyICU.ICUtzinfo.getInstance("America/New_York"))
        self.failUnlessEqual(formatTime(dt), "2:11 AM EDT")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo=PyICU.ICUtzinfo.getInstance("Africa/Johannesburg"))
        self.failUnlessEqual(formatTime(dt), "2:11 AM GMT+02:00")

class DatetimeFrenchFormatTestCase(AbstractTimeZoneTestCase):
    def setUp(self):
        super(DatetimeFrenchFormatTestCase, self).setUp()
        PyICU.Locale.setDefault(PyICU.Locale.getFrance())
        PyICU.TimeZone.setDefault(
            PyICU.ICUtzinfo.getInstance("Europe/Paris").timezone)


    def testNoTimeZone(self):
        dt = datetime(1999, 1, 2, 13, 46)
        self.failUnlessEqual(formatTime(dt), "13:46")

        dt = datetime(2022, 9, 17, 2, 11)
        self.failUnlessEqual(formatTime(dt), u"02:11")

    def testDefaultTimeZone(self):
        dt = datetime(1999, 1, 2, 13, 46, tzinfo=PyICU.ICUtzinfo.default)
        self.failUnlessEqual(formatTime(dt), "13:46")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo=PyICU.ICUtzinfo.default)
        self.failUnlessEqual(formatTime(dt), u"02:11")

    def testDifferentTimeZone(self):
        dt = datetime(2022, 9, 17, 2, 11,
                tzinfo=PyICU.ICUtzinfo.getInstance("America/New_York"))
        self.failUnlessEqual(formatTime(dt), u'02:11 HAE (\u00c9UA)')

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = PyICU.ICUtzinfo.getInstance("Africa/Johannesburg"))
        self.failUnlessEqual(formatTime(dt), u"02:11 GMT+02:00")

class StripTimeZoneTestCase(AbstractTimeZoneTestCase):
    def setUp(self):
        super(StripTimeZoneTestCase, self).setUp()
        PyICU.TimeZone.setDefault(
            PyICU.ICUtzinfo.getInstance("America/Los_Angeles").timezone)

    def testStripNaiveDatetime(self):
        """ Test that stripTimeZone() works on a naive datetime"""
        dt = datetime(2003, 9, 17, 2, 11, tzinfo = None)

        self.failUnlessEqual(stripTimeZone(dt), dt)


    def testStripOtherDatetime(self):
        """ Test that stripTimeZone() works on a datetime in
        a timezone that's not the default"""
        dt = datetime(2012, 4, 28, 18, 4,
            tzinfo = PyICU.ICUtzinfo.getInstance("Asia/Beijing"))
        strippedDt = stripTimeZone(dt)

        self.failUnless(strippedDt.tzinfo is None)

        dtInDefault = dt.astimezone(PyICU.ICUtzinfo.default)

        self.failUnlessEqual(strippedDt.date(), dtInDefault.date())
        self.failUnlessEqual(strippedDt.time(), dtInDefault.time())

    def testStripDefaultDatetime(self):
        """ Test that stripTimeZone() works on a datetime in
        the default timezone """
        dt = datetime(2012, 4, 28, 18, 4, tzinfo = PyICU.ICUtzinfo.default)
        strippedDt = stripTimeZone(dt)

        self.failUnless(strippedDt.tzinfo is None)
        self.failUnlessEqual(strippedDt.date(), dt.date())
        self.failUnlessEqual(strippedDt.time(), dt.time())

class CoerceTimeZoneTestCase(AbstractTimeZoneTestCase):
    def setUp(self):
        super(CoerceTimeZoneTestCase, self).setUp()
        PyICU.TimeZone.setDefault(
            PyICU.ICUtzinfo.getInstance("America/Los_Angeles").timezone)

    def testCoerceNaiveToNaive(self):
        dt = datetime(2014, 10, 28, 2, 11, tzinfo = None)

        self.failUnlessEqual(coerceTimeZone(dt, None), dt)

    def testCoerceNaiveToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41, tzinfo = None)
        tzinfo = PyICU.ICUtzinfo.default
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(dt.date(), coercedDt.date())
        self.failUnlessEqual(dt.time(), coercedDt.time())

    def testCoerceNaiveToOther(self):
        dt = datetime(2012, 4, 28, 18, 4, tzinfo = None)
        tzinfo = PyICU.ICUtzinfo.getInstance("Asia/Tokyo")
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)

        compareDt = coercedDt.astimezone(PyICU.ICUtzinfo.default)
        self.failUnlessEqual(dt.date(), compareDt.date())
        self.failUnlessEqual(dt.time(), compareDt.time())

    def testCoerceDefaultToNaive(self):
        dt = datetime(2014, 10, 28, 2, 11,
            tzinfo=PyICU.ICUtzinfo.default)

        coercedDt = coerceTimeZone(dt, None)
        self.failUnlessEqual(dt.date(), coercedDt.date())
        self.failUnlessEqual(dt.time(), coercedDt.time())

    def testCoerceDefaultToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41,
            tzinfo=PyICU.ICUtzinfo.default)
        tzinfo = PyICU.ICUtzinfo.default
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceDefaultToOther(self):
        dt = datetime(2012, 4, 28, 18, 4,
            tzinfo=PyICU.ICUtzinfo.default)
        tzinfo = PyICU.ICUtzinfo.getInstance("Asia/Tokyo")
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        # Both are non-naive
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceOtherToNaive(self):
        dt = datetime(2014, 10, 28, 2, 11,
            tzinfo=PyICU.ICUtzinfo.getInstance("Africa/Johannesburg"))

        coercedDt = coerceTimeZone(dt, None)
        self.failUnless(coercedDt.tzinfo is None)

        compareDt = dt.astimezone(PyICU.ICUtzinfo.default)
        self.failUnlessEqual(compareDt.date(), coercedDt.date())
        self.failUnlessEqual(compareDt.time(), coercedDt.time())

    def testCoerceOtherToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41,
            tzinfo=PyICU.ICUtzinfo.getInstance("Africa/Johannesburg"))
        tzinfo = PyICU.ICUtzinfo.default
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceOtherToOwn(self):
        tzinfo = PyICU.ICUtzinfo.getInstance("Africa/Johannesburg")
        dt = datetime(2002, 1, 3, 19, 57, 41, tzinfo=tzinfo)
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceOtherToOtherOther(self):
        dt = datetime(2012, 4, 28, 18, 4,
            tzinfo=PyICU.ICUtzinfo.getInstance("Africa/Johannesburg"))
        tzinfo = PyICU.ICUtzinfo.getInstance("Asia/Tokyo")
        coercedDt = coerceTimeZone(dt, tzinfo)

        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        # Both are non-naive
        self.failUnlessEqual(coercedDt, dt)


def suite():
    """Unit test suite; run by testing 'parcels.osaf.sharing.tests.suite'"""
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
                'KnownTimeZonesTestCase']]
    )

if __name__ == "__main__":
    unittest.main()


