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
import osaf.pim.stamping as stamping
import osaf.pim.tests.TestDomainModel as TestDomainModel
import osaf.pim.generate as generate
import repository.item

from application import schema
from repository.util.Path import Path
from i18n.tests import uw


class CalendarTest(TestDomainModel.DomainModelTestCase):
    """ Test Calendar Domain Model """


    def testCalendar(self):

        """ Simple test for creating instances of calendar related kinds """

        self.loadParcel("osaf.pim.calendar")
        
        def getEventValue(event, attrName):
            try:
                attrName = getattr(type(event), attrName).name
            except AttributeError:
                pass
            return event.itsItem.getAttributeValue(attrName)

        def _verifyCalendarEvent(event):
            self.failUnless(stamping.has_stamp(event, Calendar.EventStamp))
            
            self.assertEqual(event.summary, uw("simple headline"))

            self.assertEqual(event.itsItem.importance, 'fyi')
            self.assertEqual(getEventValue(event, 'importance'), 'fyi')

            self.assertEqual(event.transparency, "confirmed")
            self.assertEqual(getEventValue(event, 'transparency'), "confirmed")

            self.assertEqual(event.allDay, False)
            self.assertEqual(getEventValue(event, 'allDay'), False)

            self.assertEqual(event.anyTime, True)
            self.assertEqual(getEventValue(event, 'anyTime'), True)

        def _verifyCalendarItems(location, recurrence):
            self.assertEqual(location.displayName, uw("simple location"))
            self.assertEqual(location.getAttributeValue('displayName'),
                              uw("simple location"))

        # Check that the globals got created by the parcel
        calendarPath = Path('//parcels/osaf/pim/calendar')
        view = self.rep.view

        self.assertEqual(schema.itemFor(Calendar.EventStamp, view),
                         view.find(Path(calendarPath, 'EventStamp')))
        self.assertEqual(Calendar.Location.getKind(view),
                         view.find(Path(calendarPath, 'Location')))
        self.assertEqual(Calendar.RecurrencePattern.getKind(view),
                         view.find(Path(calendarPath, 'RecurrencePattern')))

        # Construct a sample item
        calendarEventItem = Calendar.CalendarEvent("calendarEventItem",
                                                   itsView=view)
        locationItem = Calendar.Location("locationItem", itsView=view)
        recurrenceItem = Calendar.RecurrencePattern("recurrenceItem", itsView=view)

        # CalendarEvent properties
        calendarEventItem.summary = uw("simple headline")
        calendarEventItem.itsItem.importance = "fyi"
        _verifyCalendarEvent(calendarEventItem)
        calendarEventItem.location = locationItem

        # Calendar properties
        locationItem.displayName = uw("simple location")
        _verifyCalendarItems(locationItem, recurrenceItem)

        # Check cloud membership - event + location

        items = calendarEventItem.itsItem.getItemCloud('copying')
        self.assertEqual(len(items), 2)

        # Re-examine items
        self._reopenRepository()
        view = self.rep.view
        contentItemParent = view.findPath("//userdata")

        calendarEventItem = Calendar.EventStamp(
                    contentItemParent.getItemChild("calendarEventItem"))
        locationItem = contentItemParent.getItemChild("locationItem")
        recurrenceItem = contentItemParent.getItemChild("recurrenceItem")

        _verifyCalendarEvent(calendarEventItem)
        _verifyCalendarItems(locationItem, recurrenceItem)

    def testTimeFields(self):
        """ Test time related fields and methods """

        self.loadParcel("osaf.pim.calendar")

        # Test getting duration, setting endTime
        view = self.rep.view
        firstEvent = Calendar.CalendarEvent(itsView=view)
        firstEvent.anyTime = False
        firstEvent.startTime = datetime(2003, 2, 1, 10, tzinfo=ICUtzinfo.default)
        firstEvent.endTime = datetime(2003, 2, 1, 11, 30,
                                     tzinfo=ICUtzinfo.default)
        self.assertEqual(firstEvent.duration, timedelta(hours=1.5))

        # Test setting duration and getting endTime
        secondEvent = Calendar.CalendarEvent(itsView=view)
        secondEvent.anyTime = False
        secondEvent.startTime = datetime(2003, 3, 5, 9, tzinfo=ICUtzinfo.default)
        secondEvent.duration = timedelta(hours=1.5)
        self.assertEqual(secondEvent.endTime,
                         datetime(2003, 3, 5, 10, 30, tzinfo=ICUtzinfo.default))

        # Test changing startTime (shouldn't change duration)
        firstEvent.startTime = datetime(2003, 3, 4, 12, 45,
                                       tzinfo=ICUtzinfo.default)
        self.assertEqual(firstEvent.duration, timedelta(hours=1.5))
        self.assertEqual(firstEvent.startTime,
                         datetime(2003, 3, 4, 12, 45, tzinfo=ICUtzinfo.default))

        # Test allDay
        firstEvent.allDay = True
        self.assertEqual(firstEvent.allDay, True)
        firstEvent.allDay = False
        self.assertEqual(firstEvent.allDay, False)

        # Test anyTime
        firstEvent.anyTime = True
        self.assertEqual(firstEvent.anyTime, True)
        firstEvent.anyTime = False
        self.assertEqual(firstEvent.anyTime, False)

    def testDeleteItem(self):

        """ Test calendar event deletion """

        self.loadParcel("osaf.pim.calendar")

        view = self.rep.view
        event = Calendar.CalendarEvent(itsView=view)
        item = event.itsItem
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
