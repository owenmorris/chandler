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

import tools.QAUITestAppLib as QAUITestAppLib
import wx
from application import schema
from osaf import pim

# Test Phase: Initialization
App_ns = app_ns()

logger = QAUITestAppLib.QALogger("PerfLargeDataTriage.log",
                                 "Dashboard triage")

try:
    testView = QAUITestAppLib.UITestView(logger)

    App_ns.root.ApplicationBarAll()
    User.emulate_sidebarClick(App_ns.sidebar, "Generated3000")
    User.idle()

    # Make sure the test is valid: we should start with no items 
    # with unpurged triage state.
    view = App_ns.itsView
    contentItems = schema.ns("osaf.pim", view).contentItems
    def countUnpurgedItems():
        return len([key for key in contentItems.iterkeys()
                    if view.findValue(key, '_sectionTriageStatus', None) is not None])
    unpurgedCount = countUnpurgedItems()
    if unpurgedCount != 0:
        raise AssertionError("Found %d unpurged items before the test" % unpurgedCount)

    # Expand the sections so we have plenty to click on.
    dashboardBlock = App_ns.DashboardSummaryView
    dashboardWidget = dashboardBlock.widget
    # all sections are expanded by default, nothing to expand
    #dashboardWidget.ExpandSection(1) # Later
    #dashboardWidget.ExpandSection(2) # Done
    #dashboardBlock.synchronizeWidget()
    #User.idle()

    # Where should we hit to click triage column cells?
    rowHeight = dashboardWidget.GetDefaultRowSize()
    rowMiddle = rowHeight/2
    triageColumn = dashboardWidget.GetNumberCols() - 1
    cellRect = dashboardWidget.CalculateCellRect((triageColumn, 0))
    triageColMiddle = cellRect.right - (cellRect.width / 2)    

    # Change triageStatus on some non-master items in the collection.
    toDo = 10
    done = 0
    for index, key in enumerate(dashboardBlock.contents.iterkeys()):
        item = dashboardBlock.itsView.find(key)
        if getattr(item, pim.EventStamp.modificationFor.name, None) is None:
            row = dashboardWidget.IndexToRow(index)
            User.emulate_click(dashboardWidget, triageColMiddle, (row*rowHeight) + rowMiddle)
            done += 1
            if done == toDo: 
                break
            
    unpurgedCount = countUnpurgedItems()
    if unpurgedCount != toDo:
        logger.ReportFailure("Set up failed: expected %d unpurged items, got %d"
                             % (toDo, unpurgedCount))
    User.idle()

    # Test Phase: Action (the action we are timing)
    # Click the triage column, then let the UI catch up.
    logger.Start("Triaging items")
    App_ns.appbar.press("TriageButton")
    User.idle()
    logger.Stop()

    # Test Phase: Verification  
    # Should have no unpurged items.
    logger.SetChecked(True)
    unpurgedCount = countUnpurgedItems()
    if unpurgedCount == 0:
        logger.ReportPass("Triaged")
    else:
        logger.ReportFailure("Triaging failed: found %d unpurged items"
                             % unpurgedCount)
    logger.Report("Triaging items")

finally:
    # cleanup
    logger.Close()
