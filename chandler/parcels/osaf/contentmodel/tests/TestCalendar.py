"""
Unit tests for calendar
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.tests.GenerateItems as GenerateItems

import mx.DateTime as DateTime

from repository.util.Path import Path


class CalendarTest(TestContentModel.ContentModelTestCase):
    """ Test Calendar Content Model """

    def testCalendar(self):
        """ Simple test for creating instances of calendar related kinds """

        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/calendar")

        def _verifyCalendarEvent(event):
            self.assertEqual(event.displayName, "simple headline")
            self.assertEqual(event.getItemDisplayName(), "simple headline")

            self.assertEqual(event.importance, 'fyi')
            self.assertEqual(event.getAttributeValue('importance'), 'fyi')

            self.assertEqual(event.transparency, "busy")
            self.assertEqual(event.getAttributeValue('transparency'), "busy")

        def _verifyCalendarItems(calendar, location, recurrence, reminder):
            self.assertEqual(calendar.displayName, "simple calendar")
            self.assertEqual(calendar.getAttributeValue('displayName'),
                              "simple calendar")

            self.assertEqual(location.displayName, "simple location")
            self.assertEqual(location.getAttributeValue('displayName'),
                              "simple location")

        # Check that the globals got created by the parcel
        calendarPath = Path('//parcels/osaf/contentmodel/calendar')
        
        self.assertEqual(Calendar.CalendarParcel.getCalendarEventKind(),
                         self.rep.find(Path(calendarPath, 'CalendarEvent')))
        self.assertEqual(Calendar.CalendarParcel.getCalendarKind(),
                         self.rep.find(Path(calendarPath, 'Calendar')))
        self.assertEqual(Calendar.CalendarParcel.getLocationKind(),
                         self.rep.find(Path(calendarPath, 'Location')))
        self.assertEqual(Calendar.CalendarParcel.getRecurrencePatternKind(),
                         self.rep.find(Path(calendarPath, 'RecurrencePattern')))
        self.assertEqual(Calendar.CalendarParcel.getReminderKind(),
                         self.rep.find(Path(calendarPath, 'Reminder')))

        # Construct a sample item
        calendarEventItem = Calendar.CalendarEvent("calendarEventItem")
        calendarItem = Calendar.Calendar("calendarItem")
        locationItem = Calendar.Location("locationItem")
        recurrenceItem = Calendar.RecurrencePattern("recurrenceItem")
        reminderItem = Calendar.Reminder("reminderItem")

        # CalendarEvent properties
        calendarEventItem.displayName = "simple headline"
        calendarEventItem.importance = "fyi"
        calendarEventItem.transparency = "busy"
        _verifyCalendarEvent(calendarEventItem)

        # Calendar properties
        calendarItem.displayName = "simple calendar"
        locationItem.displayName = "simple location"
        _verifyCalendarItems(calendarItem, locationItem,
                             recurrenceItem, reminderItem)

        # Re-examine items
        self._reopenRepository()

        contentItemParent = self.rep.findPath("//userdata/contentitems")

        calendarEventItem = contentItemParent.getItemChild("calendarEventItem")
        calendarItem = contentItemParent.getItemChild("calendarItem")
        locationItem = contentItemParent.getItemChild("locationItem")
        recurrenceItem = contentItemParent.getItemChild("recurrenceItem")
        reminderItem = contentItemParent.getItemChild("reminderItem")
        
        _verifyCalendarEvent(calendarEventItem)
        _verifyCalendarItems(calendarItem, locationItem,
                             recurrenceItem, reminderItem)

    def testTimeFields(self):
        """ Test time related fields and methods """
        
        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/calendar")

        # Test getDuration
        firstItem = Calendar.CalendarEvent()
        firstItem.startTime = DateTime.DateTime(2003, 2, 1, 10)
        firstItem.endTime = DateTime.DateTime(2003, 2, 1, 11, 30)
        self.assertEqual(firstItem.duration, DateTime.DateTimeDelta(0, 1.5))

        # Test setDuration
        secondItem = Calendar.CalendarEvent()
        secondItem.startTime = DateTime.DateTime(2003, 3, 5, 9)
        secondItem.duration = DateTime.DateTimeDelta(0, 1.5)
        self.assertEqual(secondItem.endTime,
                         DateTime.DateTime(2003, 3, 5, 10, 30))

        # Test changeStartTime
        firstItem.ChangeStart(DateTime.DateTime(2003, 3, 4, 12, 45))
        self.assertEqual(firstItem.duration, DateTime.DateTimeDelta(0, 1.5))
        self.assertEqual(firstItem.startTime,
                         DateTime.DateTime(2003, 3, 4, 12, 45))

    def testDeleteItem(self):
        """ Test calendar event deletion """
        
        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/calendar")

        item = Calendar.CalendarEvent()
        path = item.itsPath
        item.delete()
        del item
        itemShouldBeGone = self.rep.find(path)
        self.assertEqual(itemShouldBeGone, None)
        self.rep.commit()

    def testGeneratedEvents(self):

        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/calendar")

        GenerateItems.generateCalendarEventItems(100, 100)
        self.rep.commit()

if __name__ == "__main__":
    unittest.main()
