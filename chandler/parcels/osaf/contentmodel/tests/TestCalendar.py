"""
Unit tests for calendar
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import OSAF.contentmodel.calendar.Calendar as Calendar
import OSAF.contentmodel.tests.TestContentModel as TestContentModel
import OSAF.contentmodel.tests.GenerateItems as GenerateItems

import mx.DateTime as DateTime

class CalendarTest(TestContentModel.ContentModelTestCase):
    """ Test Calendar Content Model """

    def testCalendar(self):
        """ Simple test for creating instances of calendar related kinds """

        self.loadParcel("OSAF/contentmodel/calendar")

        def _verifyCalendarEvent(event):
            self.assertEqual(event.headline, "simple headline")
            self.assertEqual(event.getAttributeValue('headline'),
                              "simple headline")
            self.assertEqual(event.getItemDisplayName(), "simple headline")

            self.assertEqual(event.priority, 3)
            self.assertEqual(event.getAttributeValue('priority'), 3)

            self.assertEqual(event.transparency, "busy")
            self.assertEqual(event.getAttributeValue('transparency'), "busy")

        def _verifyCalendarItems(calendar, location, recurrence, reminder):
            self.assertEqual(calendar.name, "simple calendar")
            self.assertEqual(calendar.getAttributeValue('name'),
                              "simple calendar")

            self.assertEqual(location.name, "simple location")
            self.assertEqual(location.getAttributeValue('name'),
                              "simple location")

        # Check that the globals got created by the parcel
        calendarPath = '//parcels/OSAF/contentmodel/calendar/%s'
        
        self.assertEqual(Calendar.CalendarParcel.getCalendarEventKind(),
                         self.rep.find(calendarPath % 'CalendarEvent'))
        self.assertEqual(Calendar.CalendarParcel.getCalendarKind(),
                         self.rep.find(calendarPath % 'Calendar'))
        self.assertEqual(Calendar.CalendarParcel.getLocationKind(),
                         self.rep.find(calendarPath % 'Location'))
        self.assertEqual(Calendar.CalendarParcel.getRecurrencePatternKind(),
                         self.rep.find(calendarPath % 'RecurrencePattern'))
        self.assertEqual(Calendar.CalendarParcel.getReminderKind(),
                         self.rep.find(calendarPath % 'Reminder'))

        # Construct a sample item
        calendarEventItem = Calendar.CalendarEvent("calendarEventItem")
        calendarItem = Calendar.Calendar("calendarItem")
        locationItem = Calendar.Location("locationItem")
        recurrenceItem = Calendar.RecurrencePattern("recurrenceItem")
        reminderItem = Calendar.Reminder("reminderItem")

        # CalendarEvent properties
        calendarEventItem.headline = "simple headline"
        calendarEventItem.priority = 3
        calendarEventItem.transparency = "busy"
        _verifyCalendarEvent(calendarEventItem)

        # Calendar properties
        calendarItem.name = "simple calendar"
        locationItem.name = "simple location"
        _verifyCalendarItems(calendarItem, locationItem,
                             recurrenceItem, reminderItem)

        # Re-examine items
        self._reopenRepository()

        contentItemParent = self.rep.find("//userdata/contentitems")

        calendarEventItem = contentItemParent.find("calendarEventItem")
        calendarItem = contentItemParent.find("calendarItem")
        locationItem = contentItemParent.find("locationItem")
        recurrenceItem = contentItemParent.find("recurrenceItem")
        reminderItem = contentItemParent.find("reminderItem")
        
        _verifyCalendarEvent(calendarEventItem)
        _verifyCalendarItems(calendarItem, locationItem,
                             recurrenceItem, reminderItem)

    def testTimeFields(self):
        """ Test time related fields and methods """
        
        self.loadParcel("OSAF/contentmodel/calendar")

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
        
        self.loadParcel("OSAF/contentmodel/calendar")

        item = Calendar.CalendarEvent()
        path = item.getItemPath()
        item.delete()
        del item
        itemShouldBeGone = self.rep.find(path)
        self.assertEqual(itemShouldBeGone, None)
        self.rep.commit()

    def testGeneratedEvents(self):

        self.loadParcel("OSAF/contentmodel/calendar")

        GenerateItems.GenerateCalendarEvents(100, 100)
        self.rep.commit()

if __name__ == "__main__":
    unittest.main()
