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

import osaf.sharing.Sharing as Sharing
import tools.QAUITestAppLib as QAUITestAppLib
import os, wx, sys
import osaf.pim as pim

App_ns = app_ns()

# initialization
fileName = "PerfImporting.log"
logger = QAUITestAppLib.QALogger(fileName, "Importing 3000 event calendar")

try:
    # creation
    logger.Start("Import")
    QAUITestAppLib.UITestView(logger, u'Generated3000.ics')
    logger.Stop()
    
    # no action - we just verify import

    # verification
    def VerifyEventCreation(title):
        global logger
        global App_ns
        global pim
        testEvent = App_ns.item_named(pim.EventStamp, title)
        if testEvent is not None:
            logger.ReportPass("Testing event creation: '%s'" % title)
        else:
            logger.ReportFailure("Testing event creation: '%s' not created" % title)
    
    VerifyEventCreation("Go to the beach")
    VerifyEventCreation("Basketball game")
    VerifyEventCreation("Visit friend")
    VerifyEventCreation("Library")
    
    logger.SetChecked(True)
    logger.Report("Import")

finally:
    # cleaning
    logger.Close()
