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


import unittest, PyICU

from datetime     import datetime, timedelta
from TestTimeZone import TimeZoneTestCase
from i18n.tests   import uw
from application  import schema

import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.calendar.TimeZone import TimeZoneInfo

class TestEventIndexing(TimeZoneTestCase):

    def _createEvent(self, startTime):
        event = Calendar.CalendarEvent(None, itsView=self.rep.view)
        event.startTime = startTime
        event.endTime = event.startTime + timedelta(hours=1)
        event.anyTime = False
        event.summary = uw("Sample event")
        return event    
    
    def setUp(self):
        super(TestEventIndexing, self).setUp()

        self.tzInfoItem = TimeZoneInfo.get(self.rep.view)
        # eventsInRange will treat all timezones as equivalent unless timezone
        # display is turned on
        self.tzprefs = schema.ns('osaf.pim', self.rep.view).TimezonePrefs
        self.tzprefs.showUI = True
        
        self.pacific  = PyICU.ICUtzinfo.getInstance("US/Pacific")
        self.hawaii   = PyICU.ICUtzinfo.getInstance("US/Hawaii")
        self.eastern  = PyICU.ICUtzinfo.getInstance("US/Eastern")
        self.floating = PyICU.ICUtzinfo.floating
        
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
        daysEvents = list(Calendar.eventsInRange(self.rep.view, self.midnight,
                                                 self.midnight + timedelta(1))) 
        self.assertEqual(daysEvents[0], self.pacificEvent)
        self.assertEqual(daysEvents[1], self.floatingEvent)
        self.assertEqual(daysEvents[2], self.hawaiiEvent)
    
    def testReorderFloating(self):
        """Changes to floating time should cause events to be reindexed."""
        self.tzInfoItem.default = self.eastern
        daysEvents = list(Calendar.eventsInRange(self.rep.view, self.midnight,
                                                 self.midnight + timedelta(1)))
        #print [i.startTime for i in daysEvents]
        self.assertEqual(daysEvents[0], self.easternEvent)
        self.assertEqual(daysEvents[1], self.floatingEvent)
        self.assertEqual(daysEvents[2], self.pacificEvent)
        self.assertEqual(daysEvents[3], self.hawaiiEvent)
        

if __name__ == "__main__":
    unittest.main()


