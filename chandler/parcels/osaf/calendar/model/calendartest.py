""" Unit test for calendar data parcel
"""

import unittest

from model.persistence.FileRepository import FileRepository

from OSAF.calendar.model.CalendarEvent import CalendarEvent
from OSAF.calendar.model.CalendarEvent import CalendarEventFactory

from mx import DateTime

class SimpleTest(unittest.TestCase):
    """Clean repository tests. Creates a fresh repository, does not save."""

    def setUp(self):
        self.rep = FileRepository('data')
        self.rep.loadPack('model/packs/schema.pack')
        self.rep.loadPack('parcels/OSAF/calendar/model/calendar.pack')
        self.factory = CalendarEventFactory(self.rep)
    
    def testFactoryBasics(self):
        """ Just testing simple behavior, should see no exceptions"""
        item = self.factory.NewItem()
        item.CalendarStartTime
        item.CalendarEndTime

    def testEventBasics(self):
        item = self.factory.NewItem()
        item.setAttribute("CalendarHeadline", "Test Event")
        self.assertEqual(item.CalendarHeadline, "Test Event")
        self.assertEqual(item.IsRemote(), False)

    def testGetDuration(self):
        item = self.factory.NewItem()
        item.CalendarStartTime = DateTime.DateTime(2003, 1, 1, 10)
        item.CalendarEndTime = DateTime.DateTime(2003, 1, 1, 11, 30)
        self.assertEqual(item.CalendarDuration, DateTime.DateTimeDelta(0, 1.5))

    def testSetDuration(self):
        item = self.factory.NewItem()
        item.CalendarStartTime = DateTime.DateTime(2003, 2, 2, 10)
        item.CalendarDuration = DateTime.DateTimeDelta(0, 1.5)
        self.assertEqual(item.CalendarEndTime, DateTime.DateTime(2003, 2, 2, 11, 30))

    def testChangeStartTime(self):
        item = self.factory.NewItem()
        item.CalendarStartTime = DateTime.DateTime(2003, 3, 3, 10)
        item.CalendarEndTime = DateTime.DateTime(2003, 3, 3, 11, 30)
        self.assertEqual(item.CalendarDuration, DateTime.DateTimeDelta(0, 1.5))
        item.ChangeStart(DateTime.DateTime(2003, 3, 4, 12, 45))
        self.assertEqual(item.CalendarDuration, DateTime.DateTimeDelta(0, 1.5))
        self.assertEqual(item.CalendarStartTime, DateTime.DateTime(2003, 3, 4, 12, 45))

    def tearDown(self):
        self.rep.save()

if __name__ == "__main__":
    unittest.main()

