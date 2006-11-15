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
import osaf.pim as pim
import osaf.framework.scripting as scripting
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class TestTriageSectioning(ChandlerTestCase):
    
    def startTest(self):

        # setup
        
        # create a collection and select it in the sidebar
        view = QAUITestAppLib.UITestView(self.logger)
        view.SwitchToAllView()
    
        col = QAUITestAppLib.UITestItem("Collection", self.logger)
        col.SetDisplayName("TestTriageSectioning")
        self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, "TestTriageSectioning")
    
        items = []
        for status in pim.TriageEnum.constants:
            item = QAUITestAppLib.UITestItem("Note", self.logger)
            if status != pim.TriageEnum.now: # it should default to 'now'!
                item.item.triageStatus = status
            items.append(item)
            
        # Let the display catch up to the items
        self.scripting.User.idle()
        
        # Get ready to bang on the dashboard
        dashboardBlock = self.app_ns.TableSummaryView
        dashboard = dashboardBlock.widget
        rowHeight = dashboard.GetDefaultRowSize()
        rowMiddle = rowHeight/2
        header_widget = dashboard.GetGridColLabelWindow()
    
        # sort by triage status
        self.scripting.User.emulate_click(header_widget, header_widget.GetSize()[0] - 15, 3)
        self.scripting.User.idle()
        
        # Check the data structures: see that we're sectioned properly
        # for a table with three items of different status:
        goodExpandedSectioning = [(0, 1, 1), (2, 1, 1), (4, 1, 1)]
        sectionRows = getattr(dashboard, 'sectionRows', None)
        self.logger.startAction('Check Sectioning')
        if not sectionRows:
            self.logger.endAction(False, "Dashboard not sectioned")
        else:
            self.logger.endAction(True)
        self.logger.startAction('Check section expansion')
        if sectionRows != goodExpandedSectioning:
            self.logger.endAction(False, "Dashboard not sectioned properly: %r != %r" 
                                  % (sectionRows, goodExpandedSectioning))
        else:
            self.logger.endAction(True)
        
        # Check that contraction and expansion work. For now, double-clicking 
        # expands and contracts the section rows; eventually, it'll be clicking on
        # the triangle.
        for row in (4, 2, 0):
            self.scripting.User.emulate_click(dashboard, 100, row*rowHeight + rowMiddle, double=True)
        self.scripting.User.idle()
        self.logger.startAction('Check contraction')
        if dashboard.sectionRows != [(0, 0, 1), (1, 0, 1), (2, 0, 1)]:
            self.logger.endAction(False, "Dashboard didn't contract properly: %r" % dashboard.sectionRows)
        else:
            self.logger.endAction(True)
        for row in (2, 1, 0):
            self.scripting.User.emulate_click(dashboard, 100, row*rowHeight + rowMiddle, double=True)
        self.scripting.User.idle()
        self.logger.startAction('Check expansion')
        if dashboard.sectionRows != goodExpandedSectioning:
            self.logger.endAction(False, "Dashboard didn't expand properly: %r != %r" 
                                  % (dashboard.sectionRows, goodExpandedSectioning))
        else:
            self.logger.endAction(True)
       


