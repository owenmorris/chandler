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

import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

from osaf.pim.calendar.TimeZone import TimeZoneInfo

class TestSwitchTimezone(ChandlerTestCase):

    def startTest(self):
        
        # make user collection, since only user
        # collections can be displayed as a calendar
        col = QAUITestAppLib.UITestItem("Collection", self.logger)
        
        calendarBlock = getattr(self.app_ns, "MainCalendarControl")
    
        # Find the "canonical timezone" to use in test comparisons
        view = self.app_ns.itsView
        info = TimeZoneInfo.get(view)
        originalTz = info.canonicalTimeZone(view.tzinfo.default).tzid
        switchTz = "Pacific/Honolulu"
    
        # Enable timezones so that we can switch from the UI
        self.app_ns.root.EnableTimezones()
    
        # Create a new event, which should inherit the default tz 
        timezoneEvent = QAUITestAppLib.UITestItem("Event", self.logger)
    
        # Test that the new event has indeed inherited the default tz
        timezoneEvent.CheckDisplayedValues(EditTimeZone=(True, originalTz))
    
        # Change the timezone to Pacific/Honolulu
        QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, switchTz)
    
        # Test that the event timezone hasn't changed
        timezoneEvent.CheckDisplayedValues(EditTimeZone=(True, originalTz))
    
        # Test that the default timezone has switched
        self.logger.startAction("Verify timezone switched")
        if view.tzinfo.setDefault(view.tzinfo.getInstance(switchTz)):
            self.logger.endAction(True, "Timezone switched")
        else:
            self.logger.endAction(False, "Timezone failed to switch")
    
        # @@@ More interesting tests could be added here
    
        # Switch back to original timezone
        QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, originalTz)
        

