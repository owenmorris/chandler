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

fileName = "TestTableSelection.log"
logger = QAUITestAppLib.QALogger(fileName, "TestTableSelection")

App_ns = QAUITestAppLib.App_ns

ITEM_COUNT=12

try:
    # setup

    # create a collection and some test items
    col = QAUITestAppLib.UITestItem("Collection", logger)
    view = QAUITestAppLib.UITestView(logger)

    col.SetDisplayName("TestTableSelection")
    User.emulate_sidebarClick(App_ns.sidebar, "TestTableSelection")
    
    alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    items = []
    for i in xrange(ITEM_COUNT):
        mail = QAUITestAppLib.UITestItem("MailMessage", logger)
        # make sure the sorting is different for To vs. Subject
        mail.SetAttr(displayName="Mail Message %s" % (ITEM_COUNT-i),
                     toAddress = "%s@osafoundation.org" % alpha[i])
        items.append(mail.item)

    # action
    dashboardBlock = App_ns.TableSummaryView
    dashboard = dashboardBlock.widget

    User.emulate_click(dashboard, 20, 20)
    User.idle()

    rowsToSelect = [1, 3, 4, 9, 11]
    rowHeight = dashboard.GetDefaultRowSize()
    rowMiddle = rowHeight/2

    # select the first row
    User.emulate_click(dashboard, 100, rowsToSelect[0]*rowHeight + rowMiddle)

    # select 3 more rows, with control key down for multi selection
    for row in rowsToSelect[1:]:
        User.emulate_click(dashboard, 100,
                           rowHeight*row + rowMiddle,
                           control=True)

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
    # selected visually - this will fail if sections are enabled!
    # (because you'll need to recalculate what rows correspond to what
    # indexes)
    expectedRows = [(i,i) for i in rowsToSelect]
    topLeft = [i for i,j in dashboard.GetSelectionBlockTopLeft()]
    bottomRight = [i for i,j in dashboard.GetSelectionBlockBottomRight()]
    gridSelectedRows = zip(topLeft, bottomRight)

    view.Check_Equality(expectedRows, gridSelectedRows, "Table grid selection")

    #
    # now resort the table, and make sure we're still selecting the same item
    #
    header_widget = dashboard.GetGridColLabelWindow()

    # for some reason the first emulated click isn't doing anything
    User.emulate_click(header_widget, 100, 3)
    User.emulate_click(header_widget, 100, 3)
    User.idle()

    # First sort by first column
    newSelectedItems = list(dashboardBlock.contents.iterSelection())
    newSelectedItems.sort(key=lambda x: x.itsUUID)
    view.Check_Equality(expectedItems, newSelectedItems, "Selection by item after sorting #1")

    # Now sort by second column
    User.emulate_click(header_widget, 200, 3)
    newSelectedItems = list(dashboardBlock.contents.iterSelection())
    newSelectedItems.sort(key=lambda x: x.itsUUID)
    view.Check_Equality(expectedItems, newSelectedItems, "Selection by item after sorting #2")


    logger.Report("Table Selection")

finally:
    pass
    logger.Close()

