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

from tools import QAUITestAppLib
import osaf.pim as pim

fileName = "TestTriageSectioning.log"
logger = QAUITestAppLib.QALogger(fileName, "TestTriageSectioning")

App_ns = QAUITestAppLib.App_ns

try:
    # setup
    
    # create a collection and select it in the sidebar
    view = QAUITestAppLib.UITestView(logger)
    view.SwitchToAllView()

    col = QAUITestAppLib.UITestItem("Collection", logger)
    col.SetDisplayName("TestTriageSectioning")
    User.emulate_sidebarClick(App_ns.sidebar, "TestTriageSectioning")

    items = []
    for status in pim.TriageEnum.values:
        item = QAUITestAppLib.UITestItem("Note", logger)
        if status != 'now': # it should default to 'now'!
            item.item.triageStatus = status
        items.append(item)
        
    # action
    
    # Get ready to bang on the dashboard
    dashboardBlock = App_ns.TableSummaryView
    dashboard = dashboardBlock.widget
    rowHeight = dashboard.GetDefaultRowSize()
    rowMiddle = rowHeight/2
    header_widget = dashboard.GetGridColLabelWindow()

    # sort by triage status
    User.emulate_click(header_widget, header_widget.GetSize()[0] - 15, 3)
    User.idle()
    
    # Check the data structures: see that we're sectioned properly
    # for a table with three items of different status:
    goodExpandedSectioning = [(0, 1, 1), (2, 1, 1), (4, 1, 1)]
    sectionRows = getattr(dashboard, 'sectionRows', None)
    if not sectionRows:
        logger.ReportFailure("Dashboard not sectioned")
    if sectionRows != goodExpandedSectioning:
        logger.ReportFailure("Dashboard not sectioned properly")
    
    # Check that contraction and expansion work. For now, double-clicking 
    # expands and contracts the section rows; eventually, it'll be clicking on
    # the triangle.
    for row in (4, 2, 0):
        User.emulate_click(dashboard, 100, row*rowHeight + rowMiddle, double=True)
    User.idle()
    if dashboard.sectionRows != [(0, 0, 1), (1, 0, 1), (2, 0, 1)]:
        logger.ReportFailure("Dashboard didn't contract properly")
    for row in (2, 1, 0):
        User.emulate_click(dashboard, 100, row*rowHeight + rowMiddle, double=True)
    User.idle()
    if dashboard.sectionRows != goodExpandedSectioning:
        logger.ReportFailure("Dashboard didn't expand properly")
    
    logger.Report("TriageSectioning")

finally:
    pass
    logger.Close()
