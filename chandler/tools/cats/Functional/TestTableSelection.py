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
import sys

class TestTableSelection(ChandlerTestCase):
    
    def startTest(self):
        
        ITEM_COUNT=12

        # create a collection and some test items
        col = QAUITestAppLib.UITestItem("Collection", self.logger)
        view = QAUITestAppLib.UITestView(self.logger)
    
        col.SetDisplayName("TestTableSelection")
        self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, "TestTableSelection")
        
        alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
        items = []
        for i in xrange(ITEM_COUNT):
            mail = QAUITestAppLib.UITestItem("MailMessage", self.logger)
            # make sure the sorting is different for To vs. Subject,
            # and that the sort by Subject will be the order we're adding them.
            mail.SetAttr(displayName="%s Mail Message" % alpha[i],
                         toAddress = "x%s@osafoundation.org" % (ITEM_COUNT-i))
            items.append(mail.item)
            
        # action
        self.logger.startAction("Test summary view")
        dashboardBlock = self.app_ns.TableSummaryView
        dashboard = dashboardBlock.widget
        header_widget = dashboard.GetGridColLabelWindow()

        # Select the About column
        aboutMiddle = sum(dashboard.GetColSize(i) for i in range(3)) + \
                      dashboard.GetColSize(3) / 2
        self.scripting.User.emulate_click(header_widget, aboutMiddle, 3)
        self.scripting.User.idle()
    
        rowsToSelect = [1, 3, 4, 9, 11]
        rowHeight = dashboard.GetDefaultRowSize()
        rowMiddle = rowHeight / 2

        # select the first row
        self.scripting.User.emulate_click(dashboard, 100, rowsToSelect[0]*rowHeight + rowMiddle)
                           
        # select 3 more rows, with control key down for multi selection
        # except for mac which wants the meta key held down
        if sys.platform == 'darwin':
            for row in rowsToSelect[1:]:
                self.scripting.User.emulate_click(dashboard, 100,
                                   rowHeight*row + rowMiddle,
                                   meta=True)
        else:
            for row in rowsToSelect[1:]:
                self.scripting.User.emulate_click(dashboard, 100,
                                   rowHeight*row + rowMiddle,
                                   control=True)
        self.logger.endAction(True)
            
        # verification
    
        # check selection indexes
        expectedIndexes = [(1,1), (3,4), (9,9), (11,11)]
        view.Check_Equality(expectedIndexes,
                           list(dashboardBlock.contents.getSelectionRanges()),
                           "Table Selection Ranges")
    
        # check selected items by collection indexes
        expectedItems = [items[row] for row in rowsToSelect]
        expectedItems.sort(key=lambda x: x.itsUUID)
        selectionByUUID = list(dashboardBlock.contents.iterSelection())
        selectionByUUID.sort(key=lambda x: x.itsUUID)
        view.Check_Equality(expectedItems,
                            selectionByUUID,
                            "Table Selection by Item")
    
        # check the grid widget itself to make sure the right rows are
        # selected visually.
        expectedRows = [(i, i) for i in rowsToSelect]
        topLeft = [i for i,j in dashboard.GetSelectionBlockTopLeft()]
        bottomRight = [i for i,j in dashboard.GetSelectionBlockBottomRight()]
        gridSelectedRows = zip(topLeft, bottomRight)
    
        view.Check_Equality(expectedRows, gridSelectedRows, "Table grid selection")
    
        #
        # reverse the table, and make sure we're still selecting the same items
        #
        self.scripting.User.emulate_click(header_widget, aboutMiddle, 3)
        self.scripting.User.idle()

        newSelectedItems = list(dashboardBlock.contents.iterSelection())
        newSelectedItems.sort(key=lambda x: x.itsUUID)
        view.Check_Equality(expectedItems, newSelectedItems, "Selection by item after reversing")
    
        # now sort by Who and check again
        whoMiddle = sum(map(lambda c: c.width, dashboardBlock.columns[0:2])) + \
                      (dashboardBlock.columns[2].width / 2)
        self.scripting.User.emulate_click(header_widget, whoMiddle, 3)
        newSelectedItems = list(dashboardBlock.contents.iterSelection())
        newSelectedItems.sort(key=lambda x: x.itsUUID)
        view.Check_Equality(expectedItems, newSelectedItems, "Selection by item after sorting by Who")
    
        # now sort by triage status (which uses sectioning) and check again
        triageStatusMiddle = sum(map(lambda c: c.width, dashboardBlock.columns)) - \
                             (dashboardBlock.columns[-1].width / 2)
        self.scripting.User.emulate_click(header_widget, triageStatusMiddle, 3)
        newSelectedItems = list(dashboardBlock.contents.iterSelection())
        newSelectedItems.sort(key=lambda x: x.itsUUID)
        view.Check_Equality(expectedItems, newSelectedItems, "Selection by item after sorting by Triage Status")
        
