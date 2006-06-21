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

import tools.QAUITestAppLib as QAUITestAppLib

from PyICU import ICUtzinfo

fileName = "TestSwitchTimezone.log"
logger = QAUITestAppLib.QALogger(fileName, "Switch timezone")

originalTz = ICUtzinfo.default.tzid
switchTz = "US/Hawaii"

try:
    app_ns = app_ns()
    calendarBlock = getattr(app_ns, "MainCalendarControl")

    # Enable timezones so that we can switch from the UI
    app_ns.root.EnableTimezones()

    # Create a new event, which should inherit the default tz 
    timezoneEvent = QAUITestAppLib.UITestItem("Event", logger)

    # Test that the new event has indeed inherited the default tz
    timezoneEvent.CheckDisplayedValues(EditTimeZone=(True, originalTz))

    # Change the timezone to US/Hawaii
    QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, switchTz)

    # Test that the event timezone hasn't changed
    timezoneEvent.CheckDisplayedValues(EditTimeZone=(True, originalTz))

    # Test that the default timezone has switched
    if ICUtzinfo.default == ICUtzinfo.getInstance(switchTz):
        logger.ReportPass("Timezone switched")
    else:
        logger.ReportFailure("Timezone failed to switch")

    # @@@ More interesting tests could be added here

    # Switch back to original timezone
    QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, originalTz)
    
    logger.SetChecked(True)
    logger.Report("Switched timezones")

finally:
    logger.Close()
