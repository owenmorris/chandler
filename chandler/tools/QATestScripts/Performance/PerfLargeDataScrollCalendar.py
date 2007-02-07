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

import wx
from datetime import datetime
from PyICU import ICUtzinfo

# Test Phase: Initialization
App_ns = app_ns()

logger = QAUITestAppLib.QALogger("PerfLargeDataScrollCalendar.log",
                                 "Scroll calendar one unit")

try:
    # Look at the same date every time -- do this before we import
    # to save time and grief
    
    # Do the test in the large calendar
    User.emulate_sidebarClick(App_ns.sidebar, 'Generated3000', overlay=False)
    User.idle()

    testdate = datetime(2005, 12, 14, tzinfo=ICUtzinfo.default)
    App_ns.root.SelectedDateChanged(start=testdate)
    
    # Load a large calendar so we have events to scroll
    # NOTE: Don't do this when we restore from backed up repository
    testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')

    # Process idle and paint cycles, make sure we're only
    # measuring scrolling performance, and not accidentally
    # measuring the consequences of a large import
    User.idle()

    # Fetch the calendar widget
    calendarWidget = App_ns.TimedEvents.widget
    (xStart, yStart) = calendarWidget.GetViewStart()

    # Test Phase: Action (the action we are timing)

    logger.Start("Scroll calendar one unit")
    calendarWidget.Scroll(0, yStart + 1)
    calendarWidget.Update() # process only the paint events for this window
    logger.Stop()

    # Test Phase: Verification

    logger.SetChecked(True)
    (xEnd, yEnd) = calendarWidget.GetViewStart()
    if (yEnd == yStart + 1):
        logger.ReportPass("On scrolling calendar one unit")
    else:
        logger.ReportFailure("On scrolling calendar one unit")
    logger.Report("Scroll calendar one unit")

finally:
    # cleanup
    logger.Close()
