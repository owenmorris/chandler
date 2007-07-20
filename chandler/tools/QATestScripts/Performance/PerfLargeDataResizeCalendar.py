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

import wx
import tools.QAUITestAppLib as QAUITestAppLib
import osaf.framework.scripting as scripting

from datetime import datetime
from PyICU import ICUtzinfo

fileName = "PerfLargeDataResizeCalendar.log"
logger = QAUITestAppLib.QALogger(fileName, "Resize app in calendar mode")

App_ns = app_ns()

try:
    # Test Phase: Initialization
    
    # Do the test in the large calendar
    User.emulate_sidebarClick(App_ns.sidebar, 'Generated3000', overlay=False)

    # Start at the same date every time
    testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
    App_ns.root.SelectedDateChanged(start=testdate)
    User.idle()

    frame = wx.GetApp().mainFrame
    (x, y) = frame.GetSize()

    # Test Phase: Action

    logger.Start("Resize app in calendar mode")
    for d in xrange(10, 51, 10):
        frame.SetSize((x - d, y - d))
        wx.GetApp().Yield(True)
    User.idle() # Without this we'll quit during last resize
    logger.Stop()

    # Test Phase: Verification

    logger.SetChecked(True)
    (smallX, smallY) = frame.GetSize()
    if (smallX + d == x and smallY + d == y):
        logger.ReportPass("Resize app in calendar mode")
    else:
        logger.ReportFailure("Resize app in calendar mode, expected (%d, %d), got (%d, %d)" % (x - d, y - d, smallX, smallY))
    logger.Report("Resize app in calendar mode")
        
finally:
    logger.Close()
