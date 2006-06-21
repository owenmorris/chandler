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

#initialization
fileName = "TestEnableTimezones.log"
logger = QAUITestAppLib.QALogger(fileName, "TestEnableTimezones")

def testEnabled(event, calendarBlock, logger):
    # Test that the detail view does display the timezone
    global floatingEvent
    floatingEvent.CheckDisplayedValues(EditTimeZone=(True, 'Floating'))

    # Test that the calendar view does display the timezone widget
    if calendarBlock.widget.tzChoice.IsShown():
        logger.ReportPass("Timezone widget found when timezones enabled")
    else:
        logger.ReportFailure("Timezone widget not found even though timezones are enabled")

def testDisabled(event, calendarBlock, logger):
    # Test that the detail view does not display the timezone
    event.CheckDisplayedValues(EditTimeZone=(False, 'Floating'))

    # Test that the calendar view does not displays the timezone widget
    if calendarBlock.widget.tzChoice.IsShown():
        logger.ReportFailure("Timezone widget shown incorrectly when timezones not enabled")
    else:
        logger.ReportPass("Timezone widget correctly not shown when timezones not enabled")

try:
    calendarBlock = getattr(app_ns(), "MainCalendarControl")

    # Before timezones are enabled, create an event
    floatingEvent = QAUITestAppLib.UITestItem("Event", logger)

    testDisabled(floatingEvent, calendarBlock, logger)
        
    # Enable timezones
    app_ns().root.EnableTimezones()

    testEnabled(floatingEvent, calendarBlock, logger)

    # Disable timezones again
    app_ns().root.EnableTimezones()

    testDisabled(floatingEvent, calendarBlock, logger)

    logger.SetChecked(True)
    logger.Report("TestEnableTimezones")

finally:
    #cleaning
    logger.Close()
