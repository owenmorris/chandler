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

fileName = "PerfLargeDataSwitchCalendar.log"
logger = QAUITestAppLib.QALogger(fileName, "Switch calendar")

App_ns = app_ns()

try:
    # Test Phase: Initialization

    # Start at the same date every time
    testdate = datetime(2005, 11, 27)
    App_ns.root.SelectedDateChanged(start=testdate)

    # Load a large calendar
    # NOTE: Don't do this when we restore from backed up repository
    testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')
    User.idle()

    # Test Phase: Action

    logger.Start("Switch calendar")
    clickSucceeded = User.emulate_sidebarClick(App_ns.sidebar, "Generated3000", overlay=False)
    User.idle()
    logger.Stop()

    if clickSucceeded:
        clickSucceeded = User.emulate_sidebarClick(App_ns.sidebar, "SmallCollection", overlay=False)
        User.idle()

    if clickSucceeded:
        logger.Start("Switch calendar2")
        clickSucceeded = User.emulate_sidebarClick(App_ns.sidebar, "Generated3000", overlay=False)
        User.idle()
        logger.Stop()

    # Test Phase: Verification

    logger.SetChecked(True)
    if clickSucceeded:
        logger.ReportPass("Switch calendar")
    else:
        logger.ReportFailure("Switch calendar, click to switch failed")
    logger.Report("SwitchCalendar")
        
finally:
    logger.Close()
