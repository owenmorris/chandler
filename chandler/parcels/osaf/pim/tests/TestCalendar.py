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

"""
Unit tests for calendar
"""

import unittest, os
from datetime import datetime, timedelta
from PyICU import ICUtzinfo

import osaf.pim.calendar.Calendar as Calendar
import osaf.pim.tests.TestDomainModel as TestDomainModel
import osaf.pim.generate as generate
import repository.item

from repository.util.Path import Path
from i18n.tests import uw


class CalendarTest(TestDomainModel.DomainModelTestCase):
    """ Test Calendar Domain Model """


    def testCalendar(self):

        """ Simple test for creating instances of calendar related kinds """

        self.loadParcel("osaf.pim.calendar")

        def _verifyCalendarEvent(event):
            self.assertEqual(event.displayName, uw("simple headline"))
            self.assertEqual(event.getItemDisplayName(), uw("simple headline"))

            self.assertEqual(event.importance, 'fyi')
            self.assertEqual(event.getAttributeValue('importance'), 'fyi')

            self.assertEqual(event.transparency, "confirmed")
            self.assertEqual(event.getAttributeValue('transparency'), "confirmed")

            self.assertEqual(event.allDay, False)
            self.assertEqual(event.getAttributeValue('allDay'), False)

            self.assertEqual(event.anyTime, True)
            self.assertEqual(event.getAttributeValue('anyTime'), True)

        def _verifyCalendarItems(calendar, location, recurrence):
            self.assertEqual(calendar.displayName, uw("simple calendar"))
            self.assertEqual(calendar.getAttributeValue('displayName'),
                              uw("simple calendar"))

            self.assertEqual(location.displayName, uw("simple location"))
            self.assertEqual(location.getAttributeValue('displayName'),
                              uw("simple location"))

        # Check that the globals got created by the parcel
        calendarPath = Path('//parcels/osaf/pim/calendar')
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
                                                   itsView=view)
        calendarItem = Calendar.Calendar("calendarItem", itsView=view)
        locationItem = Calendar.Location("locationItem", itsView=view)
        recurrenceItem = Calendar.RecurrencePattern("recurrenceItem", itsView=view)

        # CalendarEvent properties
        calendarEventItem.displayName = uw("simple headline")
        calendarEventItem.importance = "fyi"
        _verifyCalendarEvent(calendarEventItem)
        calendarEventItem.location = locationItem

        # Calendar properties
        calendarItem.displayName = uw("simple calendar")
        locationItem.displayName = uw("simple location")
        _verifyCalendarItems(calendarItem, locationItem,
                             recurrenceItem)

        # Check cloud membership - event + location

        items = calendarEventItem.getItemCloud('copying')
        self.assertEqual(len(items), 2)

        # Re-examine items
        self._reopenRepository()
        view = self.rep.view
        contentItemParent = view.findPath("//userdata")

        calendarEventItem = contentItemParent.getItemChild("calendarEventItem")
        calendarItem = contentItemParent.getItemChild("calendarItem")
        locationItem = contentItemParent.getItemChild("locationItem")
        recurrenceItem = contentItemParent.getItemChild("recurrenceItem")

        _verifyCalendarEvent(calendarEventItem)
        _verifyCalendarItems(calendarItem, locationItem,
                             recurrenceItem)

    def testTimeFields(self):
        """ Test time related fields and methods """

        self.loadParcel("osaf.pim.calendar")

        # Test getting duration, setting endTime
        view = self.rep.view
        firstItem = Calendar.CalendarEvent(itsView=view)
        firstItem.anyTime = False
        firstItem.startTime = datetime(2003, 2, 1, 10, tzinfo=ICUtzinfo.default)
        firstItem.endTime = datetime(2003, 2, 1, 11, 30,
                                     tzinfo=ICUtzinfo.default)
        self.assertEqual(firstItem.duration, timedelta(hours=1.5))

        # Test setting duration and getting endTime
        secondItem = Calendar.CalendarEvent(itsView=view)
        secondItem.anyTime = False
        secondItem.startTime = datetime(2003, 3, 5, 9, tzinfo=ICUtzinfo.default)
        secondItem.duration = timedelta(hours=1.5)
        self.assertEqual(secondItem.endTime,
                         datetime(2003, 3, 5, 10, 30, tzinfo=ICUtzinfo.default))

        # Test changing startTime (shouldn't change duration)
        firstItem.startTime = datetime(2003, 3, 4, 12, 45,
                                       tzinfo=ICUtzinfo.default)
        self.assertEqual(firstItem.duration, timedelta(hours=1.5))
        self.assertEqual(firstItem.startTime,
                         datetime(2003, 3, 4, 12, 45, tzinfo=ICUtzinfo.default))

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

        self.loadParcel("osaf.pim.calendar")

        view = self.rep.view
        item = Calendar.CalendarEvent(itsView=view)
        path = item.itsPath
        item.delete()
        del item
        itemShouldBeGone = view.find(path)
        self.assertEqual(itemShouldBeGone, None)
        view.commit()

    def testGeneratedEvents(self):

        self.loadParcel("osaf.pim.calendar")

        view = self.rep.view
        generate.GenerateItems(view, 100, generate.GenerateCalendarEvent, days=100)
        view.commit()

if __name__ == "__main__":
    unittest.main()
