"""
Unit tests for calendar
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os
from datetime import datetime, timedelta

import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.tests.GenerateItems as GenerateItems
import repository.item

from repository.util.Path import Path


class CalendarTest(TestContentModel.ContentModelTestCase):
    """ Test Calendar Content Model """


    def testCalendar(self):

        """ Simple test for creating instances of calendar related kinds """

        self.loadParcel("parcel:osaf.contentmodel.calendar")

        def _verifyCalendarEvent(event):
            self.assertEqual(event.displayName, "simple headline")
            self.assertEqual(event.getItemDisplayName(), "simple headline")

            self.assertEqual(event.importance, 'fyi')
            self.assertEqual(event.getAttributeValue('importance'), 'fyi')

            self.assertEqual(event.transparency, "confirmed")
            self.assertEqual(event.getAttributeValue('transparency'), "confirmed")
            
            self.assertEqual(event.allDay, False)
            self.assertEqual(event.getAttributeValue('allDay'), False)
            
            self.assertEqual(event.anyTime, True)
            self.assertEqual(event.getAttributeValue('anyTime'), True)

        def _verifyCalendarItems(calendar, location, recurrence):
            self.assertEqual(calendar.displayName, "simple calendar")
            self.assertEqual(calendar.getAttributeValue('displayName'),
                              "simple calendar")

            self.assertEqual(location.displayName, "simple location")
            self.assertEqual(location.getAttributeValue('displayName'),
                              "simple location")

        # Check that the globals got created by the parcel
        calendarPath = Path('//parcels/osaf/contentmodel/calendar')
        view = self.rep.view
        
        self.assertEqual(Calendar.CalendarEvent.getKind(view),
                         view.find(Path(calendarPath, 'CalendarEvent')))
        self.assertEqual(Calendar.Calendar.getKind(view),
                         view.find(Path(calendarPath, 'Calendar')))
        self.assertEqual(Calendar.Location.getKind(view),
                         view.find(Path(calendarPath, 'Location')))
        self.assertEqual(Calendar.RecurrencePattern.getKind(view),
                         view.find(Path(calendarPath, 'RecurrencePattern')))

        # Construct a sample item
        calendarEventItem = Calendar.CalendarEvent("calendarEventItem",
                                                   view=view)
        calendarItem = Calendar.Calendar("calendarItem", view=view)
        locationItem = Calendar.Location("locationItem", view=view)
        recurrenceItem = Calendar.RecurrencePattern("recurrenceItem", view=view)

        # CalendarEvent properties
        calendarEventItem.displayName = "simple headline"
        calendarEventItem.importance = "fyi"
        _verifyCalendarEvent(calendarEventItem)
        calendarEventItem.location = locationItem

        # Calendar properties
        calendarItem.displayName = "simple calendar"
        locationItem.displayName = "simple location"
        _verifyCalendarItems(calendarItem, locationItem,
                             recurrenceItem)

        # Check cloud membership - event + location

        items = calendarEventItem.getItemCloud('copying')
        self.assertEqual(len(items), 2)

        # Re-examine items
        self._reopenRepository()

        contentItemParent = self.rep.findPath("//userdata")

        calendarEventItem = contentItemParent.getItemChild("calendarEventItem")
        calendarItem = contentItemParent.getItemChild("calendarItem")
        locationItem = contentItemParent.getItemChild("locationItem")
        recurrenceItem = contentItemParent.getItemChild("recurrenceItem")

        _verifyCalendarEvent(calendarEventItem)
        _verifyCalendarItems(calendarItem, locationItem,
                             recurrenceItem)

    def testTimeFields(self):
        """ Test time related fields and methods """

        self.loadParcel("parcel:osaf.contentmodel.calendar")

        # Test getDuration
        view = self.rep.view
        firstItem = Calendar.CalendarEvent(view=view)
        firstItem.anyTime = False
        firstItem.startTime = datetime(2003, 2, 1, 10)
        firstItem.endTime = datetime(2003, 2, 1, 11, 30)
        self.assertEqual(firstItem.duration, timedelta(hours=1.5))

        # Test setDuration
        secondItem = Calendar.CalendarEvent(view=view)
        secondItem.anyTime = False
        secondItem.startTime = datetime(2003, 3, 5, 9)
        secondItem.duration = timedelta(hours=1.5)
        self.assertEqual(secondItem.endTime,
                         datetime(2003, 3, 5, 10, 30))

        # Test changeStartTime
        firstItem.ChangeStart(datetime(2003, 3, 4, 12, 45))
        self.assertEqual(firstItem.duration, timedelta(hours=1.5))
        self.assertEqual(firstItem.startTime, datetime(2003, 3, 4, 12, 45))

        # Test reminderTime
        firstItem.SetReminderDelta(timedelta(minutes=-30))
        self.assertEqual(firstItem.reminderTime, datetime(2003, 3, 4, 12, 15))
        firstItem.SetReminderDelta(None)
        self.failIf(firstItem.hasLocalAttributeValue('reminderTime'))

        # Test allDay
        firstItem.allDay = True
        self.assertEqual(firstItem.allDay, True)
        firstItem.allDay = False
        self.assertEqual(firstItem.allDay, False)

        # Test anyTime
        firstItem.anyTime = True
        self.assertEqual(firstItem.anyTime, True)
        firstItem.anyTime = False
        self.assertEqual(firstItem.anyTime, False)

    def testDeleteItem(self):

        """ Test calendar event deletion """

        self.loadParcel("parcel:osaf.contentmodel.calendar")

        view = self.rep.view
        item = Calendar.CalendarEvent(view=view)
        path = item.itsPath
        item.delete()
        del item
        itemShouldBeGone = view.find(path)
        self.assertEqual(itemShouldBeGone, None)
        view.commit()

    def testGeneratedEvents(self):

        self.loadParcel("parcel:osaf.contentmodel.calendar")

        view = self.rep.view
        GenerateItems.GenerateItems(view, 100, GenerateItems.GenerateCalendarEvent, days=100)
        view.commit()

if __name__ == "__main__":
    unittest.main()
