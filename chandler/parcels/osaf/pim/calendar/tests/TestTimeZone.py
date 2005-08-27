import repository.tests.RepositoryTestCase as RepositoryTestCase
import unittest
from osaf.pim.calendar.TimeZone import *
import PyICU
from datetime import datetime

class TimeZoneTestCase(unittest.TestCase):
    def setUp(self):
        self.defaultTzItem = DefaultTimeZone.get()

    def testGetTimeZone(self):
        self.failIfEqual(self.defaultTzItem.tzinfo, None)
        
    def testSetTimeZone(self):
        self.defaultTzItem.tzinfo = PyICU.ICUtzinfo.getInstance("US/Pacific")
        self.failUnlessEqual(self.defaultTzItem.tzinfo.timezone.getID(), "US/Pacific")

        self.defaultTzItem.tzinfo = PyICU.ICUtzinfo.getInstance("US/Eastern")
        self.failUnlessEqual(self.defaultTzItem.tzinfo.timezone.getID(), "US/Eastern")
        
class DefaultTimeZoneTestCase(TimeZoneTestCase):
    def setUp(self):
        self.defaultTzItem = DefaultTimeZone.get()
        
    def testGetTimeZone(self):
        super(DefaultTimeZoneTestCase, self).testGetTimeZone()
        self.failUnlessEqual(PyICU.ICUtzinfo.getDefault(), self.defaultTzItem.tzinfo)

    def testSetTimeZone(self):
        self.defaultTzItem.tzinfo = PyICU.ICUtzinfo.getInstance("US/Eastern")
        self.failUnlessEqual(PyICU.ICUtzinfo.getDefault(), self.defaultTzItem.tzinfo)

class KnownTimeZonesTestCase(unittest.TestCase):
    def setUp(self):
        self.knownTimeZones = DefaultTimeZone.knownTimeZones
        
    def testKnownTimeZones(self):
        self.failUnless(isinstance(self.knownTimeZones, list))
        self.failIf(len(self.knownTimeZones) <= 0)
        
        for tzinfo in self.knownTimeZones:
            self.failUnless(isinstance(tzinfo, PyICU.ICUtzinfo))

class PersistenceTestCase(RepositoryTestCase.RepositoryTestCase):
    def setUp(self):
        self.ramdb = True
        super(PersistenceTestCase, self).setUp()

    def testGetTimeZone(self):
        defaultTzItem = DefaultTimeZone.get(view=self.rep.view)
        
        self.failUnlessEqual(defaultTzItem.tzinfo, PyICU.ICUtzinfo.getDefault())

    def testPerView(self):
        defaultTzItemOne = DefaultTimeZone.get(view=self.rep.view)
        defaultTzItemTwo = DefaultTimeZone.get()
        
        self.failIf(defaultTzItemOne is defaultTzItemTwo)

    def testTimeZoneSaved(self):
        # Test case should:
        #
        # - Load the repo (Done in setUp())
        # - Get the repo's default DefaultTimeZone
        view = self.rep.view
        defaultTzItem = DefaultTimeZone.get(view=view)
        # - Change the default DefaultTimeZone
        defaultTzItem.tzinfo = PyICU.ICUtzinfo.getInstance("GMT")
        self.failUnlessEqual(defaultTzItem.tzinfo,
                PyICU.ICUtzinfo.getInstance("GMT"))
        # - Save the repo
        view.commit()

        # - Change the DefaultTimeZone default timezone
        PyICU.TimeZone.adoptDefault(PyICU.TimeZone.createTimeZone("US/Pacific"))
        
        # - Reopen the repo
        self._reopenRepository()
        view = self.rep.view
        self.manager = None
        
        # - Now check the default timezone
        defaultTzItem = DefaultTimeZone.get(view=view)
        # ... see that it changed to what's in the repo
        self.failIfEqual(PyICU.ICUtzinfo.getInstance("US/Pacific"),
                        defaultTzItem.tzinfo)
        # ... and make sure it is still the default!
        self.failUnlessEqual(defaultTzItem.tzinfo, PyICU.ICUtzinfo.getDefault())

class AbstractTimeZoneTestCase(unittest.TestCase):
    def setUp(self):
        super(AbstractTimeZoneTestCase, self).setUp()
        
        self.oldLocale = PyICU.Locale.getDefault()
        self.oldTzinfo = PyICU.ICUtzinfo.getDefault()
        
    def tearDown(self):
        if self.oldLocale is not None:
            PyICU.Locale.setDefault(self.oldLocale)
        if self.oldTzinfo is not None:
            PyICU.TimeZone.adoptDefault(self.oldTzinfo.timezone)

class DatetimeFormatTestCase(AbstractTimeZoneTestCase):

    def setUp(self):
        super(DatetimeFormatTestCase, self).setUp()
        PyICU.Locale.setDefault(PyICU.Locale.getUS())
        PyICU.TimeZone.adoptDefault(
            PyICU.ICUtzinfo.getInstance("US/Pacific").timezone)

    def testNoTimeZone(self):

        dt = datetime(1999, 1, 2, 13, 46)
        self.failUnlessEqual(formatTime(dt), "1:46 PM")

        dt = datetime(2022, 9, 17, 2, 11)
        self.failUnlessEqual(formatTime(dt), "2:11 AM")

    def testDefaultTimeZone(self):

        dt = datetime(1999, 1, 2, 13, 46, tzinfo=PyICU.ICUtzinfo.getDefault())
        self.failUnlessEqual(formatTime(dt), "1:46 PM")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = PyICU.ICUtzinfo.getDefault())
        self.failUnlessEqual(formatTime(dt), "2:11 AM")

    def testDifferentTimeZone(self):

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = PyICU.ICUtzinfo.getInstance("US/Eastern"))
        self.failUnlessEqual(formatTime(dt), "2:11 AM EDT")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo=PyICU.ICUtzinfo.getInstance("Africa/Johannesburg"))
        self.failUnlessEqual(formatTime(dt), "2:11 AM GMT+02:00")

class DatetimeFrenchFormatTestCase(AbstractTimeZoneTestCase):
    def setUp(self):
        super(DatetimeFrenchFormatTestCase, self).setUp()
        PyICU.Locale.setDefault(PyICU.Locale.getFrance())
        PyICU.TimeZone.adoptDefault(
            PyICU.ICUtzinfo.getInstance("Europe/Paris").timezone)
    

    def testNoTimeZone(self):
        dt = datetime(1999, 1, 2, 13, 46)
        self.failUnlessEqual(formatTime(dt), "13:46")

        dt = datetime(2022, 9, 17, 2, 11)
        self.failUnlessEqual(formatTime(dt), u"02:11")

    def testDefaultTimeZone(self):
        dt = datetime(1999, 1, 2, 13, 46, tzinfo=PyICU.ICUtzinfo.getDefault())
        self.failUnlessEqual(formatTime(dt), "13:46")

        dt = datetime(2022, 9, 17, 2, 11, tzinfo=PyICU.ICUtzinfo.getDefault())
        self.failUnlessEqual(formatTime(dt), u"02:11")

    def testDifferentTimeZone(self):
        dt = datetime(2022, 9, 17, 2, 11,
                tzinfo=PyICU.ICUtzinfo.getInstance("US/Eastern"))
        self.failUnlessEqual(formatTime(dt), u'02:11 HAE (\u00c9UA)')

        dt = datetime(2022, 9, 17, 2, 11, tzinfo = PyICU.ICUtzinfo.getInstance("Africa/Johannesburg"))
        self.failUnlessEqual(formatTime(dt), u"02:11 GMT+02:00")

class StripTimeZoneTestCase(AbstractTimeZoneTestCase):
    def setUp(self):
        super(StripTimeZoneTestCase, self).setUp()
        PyICU.TimeZone.adoptDefault(
            PyICU.ICUtzinfo.getInstance("US/Pacific").timezone)
            
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
        
        dtInDefault = dt.astimezone(PyICU.ICUtzinfo.getDefault())
        
        self.failUnlessEqual(strippedDt.date(), dtInDefault.date())
        self.failUnlessEqual(strippedDt.time(), dtInDefault.time())

    def testStripDefaultDatetime(self):
        """ Test that stripTimeZone() works on a datetime in
        the default timezone """
        dt = datetime(2012, 4, 28, 18, 4, tzinfo = PyICU.ICUtzinfo.getDefault())
        strippedDt = stripTimeZone(dt)
        
        self.failUnless(strippedDt.tzinfo is None)
        self.failUnlessEqual(strippedDt.date(), dt.date())
        self.failUnlessEqual(strippedDt.time(), dt.time())

class CoerceTimeZoneTestCase(AbstractTimeZoneTestCase):
    def setUp(self):
        super(CoerceTimeZoneTestCase, self).setUp()
        PyICU.TimeZone.adoptDefault(
            PyICU.ICUtzinfo.getInstance("US/Pacific").timezone)

    def testCoerceNaiveToNaive(self):
        dt = datetime(2014, 10, 28, 2, 11, tzinfo = None)
        
        self.failUnlessEqual(coerceTimeZone(dt, None), dt)

    def testCoerceNaiveToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41, tzinfo = None)
        tzinfo = PyICU.ICUtzinfo.getDefault()
        coercedDt = coerceTimeZone(dt, tzinfo)
        
        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(dt.date(), coercedDt.date())
        self.failUnlessEqual(dt.time(), coercedDt.time())

    def testCoerceNaiveToOther(self):
        dt = datetime(2012, 4, 28, 18, 4, tzinfo = None)
        tzinfo = PyICU.ICUtzinfo.getInstance("Asia/Tokyo")
        coercedDt = coerceTimeZone(dt, tzinfo)
        
        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        
        compareDt = coercedDt.astimezone(PyICU.ICUtzinfo.getDefault())
        self.failUnlessEqual(dt.date(), compareDt.date())
        self.failUnlessEqual(dt.time(), compareDt.time())

    def testCoerceDefaultToNaive(self):
        dt = datetime(2014, 10, 28, 2, 11,
            tzinfo=PyICU.ICUtzinfo.getDefault())
        
        coercedDt = coerceTimeZone(dt, None)
        self.failUnlessEqual(dt.date(), coercedDt.date())
        self.failUnlessEqual(dt.time(), coercedDt.time())

    def testCoerceDefaultToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41,
            tzinfo=PyICU.ICUtzinfo.getDefault())
        tzinfo = PyICU.ICUtzinfo.getDefault()
        coercedDt = coerceTimeZone(dt, tzinfo)
        
        self.failUnlessEqual(coercedDt.tzinfo, tzinfo)
        self.failUnlessEqual(coercedDt, dt)

    def testCoerceDefaultToOther(self):
        dt = datetime(2012, 4, 28, 18, 4,
            tzinfo=PyICU.ICUtzinfo.getDefault())
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
        
        compareDt = dt.astimezone(PyICU.ICUtzinfo.getDefault())
        self.failUnlessEqual(compareDt.date(), coercedDt.date())
        self.failUnlessEqual(compareDt.time(), coercedDt.time())

    def testCoerceOtherToDefault(self):
        dt = datetime(2002, 1, 3, 19, 57, 41,
            tzinfo=PyICU.ICUtzinfo.getInstance("Africa/Johannesburg"))
        tzinfo = PyICU.ICUtzinfo.getDefault()
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
    from run_tests import ScanningLoader
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


