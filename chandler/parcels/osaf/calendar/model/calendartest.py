""" Unit test for calendar data parcel
"""

import unittest

from model.persistence.FileRepository import FileRepository

from OSAF.calendar.model.CalendarEvent import CalendarEvent
from OSAF.calendar.model.CalendarEvent import CalendarEventFactory

from mx import DateTime

class SimpleTest(unittest.TestCase):
    """Simple calendar data parcel tests"""

    def setUp(self):
        """Creates a new repository and a factory. Loads the schema and calendar"""
        self.rep = FileRepository('test')
        self.rep.create()
        self.rep.loadPack('model/packs/schema.pack')
        self.rep.loadPack('parcels/OSAF/calendar/model/calendar.pack')
        self.factory = CalendarEventFactory(self.rep)
    
    def testFactoryBasics(self):
        """Test that the basic factory method worked"""
        item = self.factory.NewItem()
        item.CalendarStartTime
        item.CalendarEndTime
        foundItem = self.rep.find(item.getItemPath())
        self.assert_(foundItem)
        self.assertEqual(foundItem.getUUID(), item.getUUID())

    def testEventBasics(self):
        """Test basic features of CalendarEvent class"""
        item = self.factory.NewItem()
        item.setAttributeValue("CalendarHeadline", "Test Event")
        self.assertEqual(item.CalendarHeadline, "Test Event")
        self.assertEqual(item.IsRemote(), False)

    def testGetDuration(self):
        """Test the duration property, GET"""
        item = self.factory.NewItem()
        item.CalendarStartTime = DateTime.DateTime(2003, 1, 1, 10)
        item.CalendarEndTime = DateTime.DateTime(2003, 1, 1, 11, 30)
        self.assertEqual(item.CalendarDuration, DateTime.DateTimeDelta(0, 1.5))

    def testSetDuration(self):
        """Test the duration property, SET"""
        item = self.factory.NewItem()
        item.CalendarStartTime = DateTime.DateTime(2003, 2, 2, 10)
        item.CalendarDuration = DateTime.DateTimeDelta(0, 1.5)
        self.assertEqual(item.CalendarEndTime, DateTime.DateTime(2003, 2, 2, 11, 30))

    def testChangeStartTime(self):
        """Test ChangeStartTime"""
        item = self.factory.NewItem()
        item.CalendarStartTime = DateTime.DateTime(2003, 3, 3, 10)
        item.CalendarEndTime = DateTime.DateTime(2003, 3, 3, 11, 30)
        self.assertEqual(item.CalendarDuration, DateTime.DateTimeDelta(0, 1.5))
        item.ChangeStart(DateTime.DateTime(2003, 3, 4, 12, 45))
        self.assertEqual(item.CalendarDuration, DateTime.DateTimeDelta(0, 1.5))
        self.assertEqual(item.CalendarStartTime, DateTime.DateTime(2003, 3, 4, 12, 45))

    def tearDown(self):
        # Note: to use for diagnosis if a test fails
        self.rep.close(purge=True)

if __name__ == "__main__":
    unittest.main()

