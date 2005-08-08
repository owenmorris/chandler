import repository.tests.RepositoryTestCase as RepositoryTestCase
import unittest
from osaf.pim.calendar.TimeZone import DefaultTimeZone
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
        defaultTzItem = DefaultTimeZone.get(view=self.rep.view)
        # - Change the default DefaultTimeZone
        defaultTzItem.tzinfo = PyICU.ICUtzinfo.getInstance("GMT")
        self.failUnlessEqual(defaultTzItem.tzinfo,
                PyICU.ICUtzinfo.getInstance("GMT"))
        # - Save the repo
        self.rep.commit()
        self.rep.closeView()
        
        # - Change the DefaultTimeZone default timezone
        PyICU.TimeZone.adoptDefault(PyICU.TimeZone.createTimeZone("US/Pacific"))
        
        # - Reopen the repo
        self.rep.openView()
        self.manager = None
        
        # - Now check the default timezone
        defaultTzItem = DefaultTimeZone.get(view=self.rep.view)
        # ... see that it changed to what's in the repo
        self.failIfEqual(PyICU.ICUtzinfo.getInstance("US/Pacific"),
                        defaultTzItem.tzinfo)
        # ... and make sure it is still the default!
        self.failUnlessEqual(defaultTzItem.tzinfo, PyICU.ICUtzinfo.getDefault())

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
                'KnownTimeZonesTestCase']]
    )

if __name__ == "__main__":
    unittest.main()


