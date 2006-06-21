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
import osaf.framework.scripting as scripting

from datetime import datetime
from PyICU import ICUtzinfo

fileName = "PerfLargeDataResizeCalendar.log"
logger = QAUITestAppLib.QALogger(fileName, "Resize app in calendar mode")

App_ns = app_ns()

try:
    # Test Phase: Initialization

    # Start at the same date every time
    testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
    App_ns.root.SelectedDateChanged(start=testdate)

    frame = App_ns.root.widget.GetParent()
    (x, y) = frame.GetSize()
    x += 20
    y += 20

    # Load a large calendar
    # NOTE: Don't do this when we restore from backed up repository
    testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')
    scripting.User.idle()

    # Test Phase: Action

    logger.Start("Resize app in calendar mode")
    frame.SetSize((x, y))
    scripting.User.idle()
    logger.Stop()

    # Test Phase: Verification

    logger.SetChecked(True)
    (bigx, bigy) = frame.GetSize()
    if (bigx == x and bigy == y):
        logger.ReportPass("Resize app in calendar mode")
    else:
        logger.ReportFailure("Resize app in calendar mode")
    logger.Report("Resize app in calendar mode")
        
finally:
    logger.Close()
