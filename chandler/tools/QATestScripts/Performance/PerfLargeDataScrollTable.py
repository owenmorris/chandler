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

# Test Phase: Initialization
App_ns = app_ns()

logger = QAUITestAppLib.QALogger("PerfLargeDataScrollTable.log",
                                 "Scrolling a table")

try:
    # Load a large calendar so we have events to scroll 
    # NOTE: Don't do this when we restore from backed up repository
    testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')

    # Switch views to the table after we load
    # Its currently important to do this after we load due
    # to a linux bug (4461)-- we want to make sure we have a scrollbar
    App_ns.root.ApplicationBarAll()

    User.emulate_sidebarClick(App_ns.sidebar, "Generated3000")
    
    # Process idle and paint cycles, make sure we're only
    # measuring scrolling performance, and not accidentally
    # measuring the consequences of a large import
    User.idle()
    
    # Fetch the table widget
    tableWidget = App_ns.summary.widget
    
    # Make sure the Done section is expanded, so we have enough to scroll
    tableWidget.ExpandSection(2)
    tableWidget.blockItem.synchronizeWidget()

    # For some reason we need another User.idle() for the PPC Mac mini to
    # completely paint the summary table. Without this the table will show
    # only a handful of entries and we scroll mostly grey, which makes us
    # report that we scrolled very fast. See bug 7457.
    User.idle()
    
    # Test Phase: Action (the action we are timing)
    
    logger.Start("Scroll table 25 scroll units")
    for units in xrange(1, 25):
        tableWidget.Scroll(0, units)
        wx.Yield() # Each Yield should result in a single paint to the table
    logger.Stop()
    
    # Test Phase: Verification
    
    logger.SetChecked(True)
    (x, y) = tableWidget.GetViewStart()
    if (x == 0 and y == units):
        logger.ReportPass("Scrolled table")
    else:
        logger.ReportFailure("Scrolled table, expected (0, %d), got (%d, %d)" % (units, x, y))
    logger.Report("Scroll table 25 scroll units")

finally:
    # cleanup
    logger.Close()
