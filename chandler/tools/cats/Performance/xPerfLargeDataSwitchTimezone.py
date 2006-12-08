print """
####
#### WARNING
#### THIS FILE IS NOT BEING USED TO TEST PERFORMANCE 
#### THIS FILE IS STILL IN DEVELOPMENT.  USE THE FILES IN      
#### tools/QATestScripts/Performance                                  
####
"""
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

import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class XXX(ChandlerTestCase):
    
    def startTest(self):

import tools.QAUITestAppLib as QAUITestAppLib

from datetime import datetime
from PyICU import ICUtzinfo

logger = QAUITestAppLib.QALogger("PerfLargeDataSwitchTimezone.log",
                                 "PerfLargeDataSwitchTimezone")

try:
    calendarBlock = getattr(self.app_ns(), "MainCalendarControl")

    # Enable timezones so that we can switch from the UI
    self.app_ns().root.EnableTimezones()
    
    # Start at the same date every time
    testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
    self.app_ns().root.SelectedDateChanged(start=testdate)

    # Load a large calendar
    testView = QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
    clickSucceeded = self.scripting.User.emulate_sidebarClick(self.app_ns().sidebar,
                                               "Generated3000",
                                               overlay=False)
    self.scripting.User.idle()

    # Switch the timezone (this is the action we are measuring)
    self.logger.startPerformanceAction("Switch timezone to US/Hawaii")
    QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, "US/Hawaii")
    self.scripting.User.idle()
    self.logger.endPerformanceAction()

    # Verification

    # @@@ KCP this test could be improved
    # Currently tests that the default tz is now US/Hawaii
    if ICUtzinfo.default == ICUtzinfo.getInstance("US/Hawaii"):
        self.logger.endAction(True, "Timezone switched")
    else:
        self.logger.endAction(False, "Timezone failed to switch")

    if clickSucceeded:
        self.logger.endAction(True, "Selected large data calendar")
    else:
        self.logger.endAction(False, "Failed to select large data calendar")
    
    self.logger.SetChecked(True)
    self.logger.Report("Switch timezone")

finally:
    self.logger.Close()

    
