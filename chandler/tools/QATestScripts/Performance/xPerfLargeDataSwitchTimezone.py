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

from datetime import datetime
from PyICU import ICUtzinfo

logger = QAUITestAppLib.QALogger("PerfLargeDataSwitchTimezone.log",
                                 "PerfLargeDataSwitchTimezone")

try:
    calendarBlock = getattr(app_ns(), "MainCalendarControl")

    # Enable timezones so that we can switch from the UI
    app_ns().root.EnableTimezones()
    
    # Start at the same date every time
    testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
    app_ns().root.SelectedDateChanged(start=testdate)

    # Load a large calendar
    testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')
    clickSucceeded = User.emulate_sidebarClick(app_ns().sidebar,
                                               "Generated3000",
                                               overlay=False)
    User.idle()

    # Switch the timezone (this is the action we are measuring)
    logger.Start("Switch timezone to US/Hawaii")
    QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, "US/Hawaii")
    User.idle()
    logger.Stop()

    # Verification

    # @@@ KCP this test could be improved
    # Currently tests that the default tz is now US/Hawaii
    if ICUtzinfo.default == ICUtzinfo.getInstance("US/Hawaii"):
        logger.ReportPass("Timezone switched")
    else:
        logger.ReportFailure("Timezone failed to switch")

    if clickSucceeded:
        logger.ReportPass("Selected large data calendar")
    else:
        logger.ReportFailure("Failed to select large data calendar")
    
    logger.SetChecked(True)
    logger.Report("Switch timezone")

finally:
    logger.Close()

    
