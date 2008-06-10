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


import unittest, PyICU

from datetime     import datetime, timedelta
from TestTimeZone import TimeZoneTestCase
from i18n.tests   import uw
from application  import schema

import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.calendar.TimeZone import TimeZoneInfo
from osaf.pim.calendar import EventStamp


class TestEventIndexing(TimeZoneTestCase):

    def _createEvent(self, startTime):
        event = Calendar.CalendarEvent(None, itsView=self.view)
        event.startTime = startTime
        event.endTime = event.startTime + timedelta(hours=1)
        event.anyTime = False
        event.summary = uw("Sample event")
        return event    
    
    def setUp(self):
        super(TestEventIndexing, self).setUp()
        view = self.view
        self.tzInfoItem = TimeZoneInfo.get(view)
        # eventsInRange will treat all timezones as equivalent unless timezone
        # display is turned on
        self.tzprefs = schema.ns('osaf.pim', view).TimezonePrefs
        self.tzprefs.showUI = True
        
        self.pacific  = view.tzinfo.getInstance("US/Pacific")
        self.hawaii   = view.tzinfo.getInstance("US/Hawaii")
        self.eastern  = view.tzinfo.getInstance("US/Eastern")
        self.floating = view.tzinfo.floating
        
        self.midnight = datetime(2006, 9, 1, 0, 0, tzinfo=self.floating)
        
        self.easternEvent = self._createEvent(self.midnight.replace(tzinfo=
            self.eastern))
        self.pacificEvent = self._createEvent(self.midnight.replace(tzinfo=
            self.pacific))
        self.hawaiiEvent  = self._createEvent(self.midnight.replace(tzinfo=
            self.hawaii))
        
        self.floatingEvent = self._createEvent(datetime(2006, 9, 1, 1, 0,
                                                        tzinfo = self.floating))
        
    def testEventIndex(self):
        """Make sure eventsInRange works."""
        daysEvents = list(Calendar.eventsInRange(self.view, self.midnight,
                                                 self.midnight + timedelta(1))) 
        self.assertEqual(daysEvents[0], self.pacificEvent)
        self.assertEqual(daysEvents[1], self.floatingEvent)
        self.assertEqual(daysEvents[2], self.hawaiiEvent)
    
    def testReorderFloating(self):
        """Changes to floating time should cause events to be reindexed."""
        self.tzInfoItem.default = self.eastern
        daysEvents = list(Calendar.eventsInRange(self.view, self.midnight,
                                                 self.midnight + timedelta(1)))
        #print [i.startTime for i in daysEvents]
        self.assertEqual(daysEvents[0], self.easternEvent)
        self.assertEqual(daysEvents[1], self.floatingEvent)
        self.assertEqual(daysEvents[2], self.pacificEvent)
        self.assertEqual(daysEvents[3], self.hawaiiEvent)

    def testMergeTZSameOffset(self):
        """
        Verify that when python lies to us about datetime/time values being
        the same - even though their tzinfo changed to a different tz of same
        offset - merging still picks up the change.
        If it doesn't, the floatingEvents collection's index is not maintained
        properly and check() fails with an index/collection mismatch error.
        """
        
        # return newValue or getattr(item, attribute) 
        # it makes no difference to this test
        def mergeFn(code, item, attribute, newValue):
            return newValue

        main = self.view
        main.commit()
        view = main.repository.createView('view')

        self.tzInfoItem.default = self.pacific

        self.floatingEvent.startTime -= timedelta(hours=1)
        self.assertTrue(main.check(), "main view didn't check out")
        main.commit()

        floatingEvent = EventStamp(view[self.floatingEvent.itsItem.itsUUID])
        floatingEvent.startTime = \
            (floatingEvent.startTime.replace(tzinfo=self.pacific) -
             timedelta(hours=1))
        view.commit(mergeFn)

        main.refresh()
        self.assertTrue(main.check(), "main view didn't check out")
        

if __name__ == "__main__":
    unittest.main()
