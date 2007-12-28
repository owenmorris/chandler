#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
from datetime import datetime, timedelta, time

import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.calendar.TimeZone import TimeZoneInfo
import osaf.pim.stamping as stamping
import util.testcase as testcase

from application import schema
from chandlerdb.util.Path import Path
from i18n.tests import uw


class CalendarTest(testcase.SharedSandboxTestCase):
    """ Test Calendar Domain Model """

    def testCalendar(self):
        """ Simple test for creating instances of calendar related kinds """

        def getEventValue(event, attrName):
            try:
                attrName = getattr(type(event), attrName).name
            except AttributeError:
                pass
            return getattr(event.itsItem, attrName)

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

        # Check that the globals got created by the parcel
        calendarPath = Path('//parcels/osaf/pim/calendar')
        view = self.sandbox.itsView

        self.assertEqual(schema.itemFor(Calendar.EventStamp, view),
                         view.find(Path(calendarPath, 'EventStamp')))
        self.assertEqual(Calendar.Location.getKind(view),
                         view.find(Path(calendarPath, 'Location')))
        self.assertEqual(Calendar.RecurrencePattern.getKind(view),
                         view.find(Path(calendarPath, 'RecurrencePattern')))

        # Construct a sample item
        calendarEventItem = Calendar.CalendarEvent("calendarEventItem",
                                                   itsParent=self.sandbox)
        locationItem = Calendar.Location("locationItem", itsParent=self.sandbox)
        recurrenceItem = Calendar.RecurrencePattern("recurrenceItem",
                                                    itsParent=self.sandbox)

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
        self.reopenRepository()
        view = self.sandbox.itsView

        calendarEventItem = Calendar.EventStamp(
                    self.sandbox.getItemChild("calendarEventItem"))
        locationItem = self.sandbox.getItemChild("locationItem")
        recurrenceItem = self.sandbox.getItemChild("recurrenceItem")

        _verifyCalendarEvent(calendarEventItem)
        _verifyCalendarItems(locationItem, recurrenceItem)
        
    def testCalendarEvent(self):
        from i18n import ChandlerMessageFactory
        
        event = Calendar.CalendarEvent(
            itsParent=self.sandbox,
        )
        
        # Call InitOutgoingAttributes() on the created event, the
        # hook for item/stamp creation in the Chandler UI.
        item = event.itsItem
        event.InitOutgoingAttributes()
        
        newEventTitle = ChandlerMessageFactory(u"New Event")
        
        self.failUnless(stamping.has_stamp(event, Calendar.EventStamp))
        self.failUnlessEqual(item.displayName, newEventTitle)
        
        newNote = type(item)(itsParent=self.sandbox)
        newNote.InitOutgoingAttributes() # Should be _(u"Untitled")
        
        # Make sure the new event title gets reset on unstamp
        event.remove()
        
        self.failUnlessEqual(
            item.displayName,
            newNote.displayName
        )

    def testDefaultSettings(self):
        defaultTz = TimeZoneInfo.get(self.sandbox.itsView).default
        ROUND = 30
        
        # A new event, by default, has its startTime set to the current time
        # rounded to a 30-minute boundary
        start = datetime.now(defaultTz)
        event = Calendar.CalendarEvent(itsParent=self.sandbox, anyTime=False,
                                       allDay=False)
        end = datetime.now(defaultTz)

        # Check that it falls within 30 minutes of now
        self.failUnless(start - timedelta(minutes=ROUND) <= event.startTime and
                        event.startTime <= end + timedelta(minutes=ROUND))
        
        # Check that the correct rounding occurred
        self.failUnlessEqual(event.startTime.second, 0)
        self.failUnlessEqual(event.startTime.microsecond, 0)
        self.failUnlessEqual(event.startTime.minute % ROUND, 0)
        
        # Make sure it's in the right timezone
        self.failUnlessEqual(event.startTime.tzinfo, defaultTz)
        
        # Lastly, check the dates if possible
        if start.date() == end.date():
            self.failUnlessEqual(start.date(), event.startTime.date())
        
        self.failUnlessEqual(event.effectiveStartTime, event.startTime)
        self.failUnlessEqual(event.effectiveEndTime, event.endTime)

    def testTimeFields(self):
        """ Test time related fields and methods """

        # Test getting duration, setting endTime
        defaultTz = self.sandbox.itsView.tzinfo.default
        firstEvent = Calendar.CalendarEvent(itsParent=self.sandbox)
        firstEvent.anyTime = False
        firstEvent.startTime = datetime(2003, 2, 1, 10, tzinfo=defaultTz)
        firstEvent.endTime = datetime(2003, 2, 1, 11, 30, tzinfo=defaultTz)
        self.assertEqual(firstEvent.duration, timedelta(hours=1.5))

        # Test setting duration and getting endTime
        secondEvent = Calendar.CalendarEvent(itsParent=self.sandbox)
        secondEvent.anyTime = False
        secondEvent.startTime = datetime(2003, 3, 5, 9, tzinfo=defaultTz)
        secondEvent.duration = timedelta(hours=1.5)
        self.assertEqual(secondEvent.endTime,
                         datetime(2003, 3, 5, 10, 30, tzinfo=defaultTz))

        # Test changing startTime (shouldn't change duration)
        firstEvent.startTime = datetime(2003, 3, 4, 12, 45, tzinfo=defaultTz)
        self.assertEqual(firstEvent.duration, timedelta(hours=1.5))
        self.assertEqual(firstEvent.startTime,
                         datetime(2003, 3, 4, 12, 45, tzinfo=defaultTz))

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

        view = self.sandbox.itsView
        event = Calendar.CalendarEvent(itsParent=self.sandbox)
        item = event.itsItem
        path = item.itsPath
        item.delete()
        del item
        self.sandbox.itsView.commit()

        itemShouldBeGone = view.find(path)
        self.assertEqual(itemShouldBeGone, None)

class EffectiveTimeTestCase(testcase.SharedSandboxTestCase):
        
    @property
    def floatingMidnight(self):
        return time(0, tzinfo=self.sandbox.itsView.tzinfo.floating)

    def testAtTime(self):
        event = Calendar.CalendarEvent(itsParent=self.sandbox, anyTime=False,
                                       allDay=False, duration=timedelta(0))
        self.failUnlessEqual(event.effectiveStartTime, event.startTime)
        self.failUnlessEqual(event.endTime, event.startTime)
        self.failUnlessEqual(event.effectiveEndTime, event.startTime)
                             
    def testTimed(self):
        event = Calendar.CalendarEvent(
            itsParent=self.sandbox,
            anyTime=False,
            allDay=False,
            startTime=datetime(2006, 11, 4, 13, 25,
                               tzinfo=self.sandbox.itsView.tzinfo.default),
            duration=timedelta(hours=1)
        )
        self.failUnlessEqual(event.effectiveStartTime, event.startTime)
        self.failUnlessEqual(event.endTime - timedelta(hours=1),
                             event.startTime)
        self.failUnlessEqual(event.effectiveEndTime, event.endTime)

    def testAnyTime(self):
        event = Calendar.CalendarEvent(itsParent=self.sandbox, anyTime=False)
        self.failUnlessEqual(event.effectiveStartTime, event.startTime)
        
        event.anyTime = True
        self.failUnlessEqual(event.effectiveStartTime.timetz(),
                             self.floatingMidnight)
        self.failUnlessEqual(event.effectiveStartTime.date(),
                             event.startTime.date())
        self.failUnlessEqual(event.effectiveEndTime,
                             event.effectiveStartTime + timedelta(days=1))


    def testAllDay(self):
        event = Calendar.CalendarEvent(itsParent=self.sandbox,
                                       anyTime=False, allDay=True)
        self.failUnlessEqual(event.effectiveStartTime.timetz(),
                             self.floatingMidnight)
        self.failUnlessEqual(event.effectiveStartTime.date(),
                             event.startTime.date())
        self.failUnlessEqual(event.effectiveEndTime,
                             event.effectiveStartTime + timedelta(days=1))
        
        event.anyTime = True
        self.failUnlessEqual(event.effectiveStartTime.timetz(),
                             self.floatingMidnight)
        self.failUnlessEqual(event.effectiveStartTime.date(),
                             event.startTime.date())
        self.failUnlessEqual(event.effectiveEndTime,
                             event.effectiveStartTime + timedelta(days=1))

        event.anyTime = event.allDay = False
        self.failUnlessEqual(event.startTime, event.effectiveStartTime)
        self.failUnlessEqual(event.effectiveStartTime.date(),
                             event.startTime.date())
        self.failUnlessEqual(event.effectiveEndTime,
                             event.effectiveStartTime + event.duration)
                             
    def testDayBoundary(self):
        tzinfo = self.sandbox.itsView.tzinfo
        
        event = Calendar.CalendarEvent(
                    itsParent=self.sandbox,
                    allDay=True,
                    anyTime=False,
                    startTime=datetime(2007, 10, 16, 23, 30,
                                       tzinfo=tzinfo.default),
                    duration=timedelta(hours=1),
                )
        self.failUnlessEqual(event.effectiveStartTime,
                             datetime(2007, 10, 16, tzinfo=tzinfo.floating))
        self.failUnlessEqual(event.effectiveEndTime,
                             datetime(2007, 10, 17, tzinfo=tzinfo.floating))
                             
    def testMultidayEdgeCase(self):
        tzinfo = self.sandbox.itsView.tzinfo
        
        event = Calendar.CalendarEvent(
                    itsParent=self.sandbox,
                    allDay=True,
                    anyTime=False,
                    startTime=datetime(2007, 7, 20,
                                       tzinfo=tzinfo.floating),
                    duration=timedelta(days=0),
                )
        self.failUnlessEqual(event.effectiveStartTime,
                             datetime(2007, 7, 20, tzinfo=tzinfo.floating))
        self.failUnlessEqual(event.effectiveEndTime,
                             datetime(2007, 7, 21, tzinfo=tzinfo.floating))

        event.duration = timedelta(days=1)
        # Really, the following should be 2007/07/21. However, for a while
        # Chandler has treated an all-day event with duration of exactly
        # one day as lasting two days. Jeffrey pointed out that there is
        # import/export code we would need to change in addition to the
        # domain model here. [grant 2007/10/17]
        self.failUnlessEqual(event.effectiveEndTime,
                             datetime(2007, 7, 22, tzinfo=tzinfo.floating))

        event.duration = timedelta(days=2, hours=3)
        self.failUnlessEqual(event.effectiveEndTime,
                             datetime(2007, 7, 23, tzinfo=tzinfo.floating))

class AdjustTimesTestCase(testcase.SharedSandboxTestCase):

    def setUp(self):
        super(AdjustTimesTestCase, self).setUp()
        view = self.sandbox.itsView

        self.start = datetime(2006, 4, 21,
                              tzinfo=view.tzinfo.getInstance("Europe/Paris"))
        self.end = self.start + timedelta(days=1)

        self.dt1 = datetime(2006, 4, 21, 3,
                            tzinfo=view.tzinfo.getInstance("Asia/Vladivostok"))

        self.dt2 = datetime(2006, 4, 20, 22,
                            tzinfo=view.tzinfo.getInstance("Pacific/Pitcairn"))
                       

    def testWithTimeZones(self):
        showTZUI = True
        adjustStart, adjustEnd = Calendar.adjustSearchTimes(
                                                self.start, self.end, showTZUI)
                                                            
        self.failUnlessEqual(adjustStart, self.start,
                             "If showTZUI is True, shouldn't adjust start")
        self.failUnlessEqual(adjustEnd, self.end,
                             "If showTZUI is True, shouldn't adjust end")
        
        expected = [self.dt1, adjustStart, self.dt2, adjustEnd]
        sortedTimes = sorted(expected)
        self.failUnlessEqual(sortedTimes, expected,
                            "Misordered datetimes: got %s; expected %s" % (
                                expected, sortedTimes))
                                
    def testWithoutTimeZones(self):
        showTZUI = False
        adjustStart, adjustEnd = Calendar.adjustSearchTimes(
                                                self.start, self.end, showTZUI)

        self.failIfEqual(adjustStart, self.start,
                             "If showTZUI is False, should adjust start")
        self.failIfEqual(adjustEnd, self.end,
                             "If showTZUI is False, should adjust end")

        expected = [adjustStart, self.dt2, self.start, self.dt1, self.end,
                    adjustEnd]
        sortedTimes = sorted(expected,
                             key = lambda dt: dt.replace(tzinfo=None))
        self.failUnlessEqual(sortedTimes, expected,
                            "Misordered datetimes: got %s; expected %s" % (
                                expected, sortedTimes))
                                
    def testNone(self):
        showTZUI = False

        adjustStart, adjustEnd = Calendar.adjustSearchTimes(
                                                self.start, None, showTZUI)
        self.failUnless(adjustEnd is None)
        self.failIf(adjustStart is None)
        self.failIfEqual(adjustStart, self.start,
                             "If showTZUI is False, should adjust start")

        adjustStart, adjustEnd = Calendar.adjustSearchTimes(
                                                None, self.end, showTZUI)
        self.failUnless(adjustStart is None)
        self.failIf(adjustEnd is None)
        self.failIfEqual(adjustEnd, self.end,
                             "If showTZUI is False, should adjust end")
     

if __name__ == "__main__":
    unittest.main()
