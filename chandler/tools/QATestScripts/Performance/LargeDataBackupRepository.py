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
import os
import osaf.pim as pim

App_ns = app_ns()

# initialization
fileName = "LargeDataBackupRepository.log"
logger = QAUITestAppLib.QALogger(fileName, "Backing up 3000 event repository")

largeCollectionName = 'Generated3000'
smallCollectionName = 'SmallCollection'

try:
    # import
    QAUITestAppLib.UITestView(logger, u'%s.ics' % largeCollectionName)
    
    # Start in the small collection
    col = QAUITestAppLib.UITestItem("Collection")
    col.SetDisplayName(smallCollectionName)
    User.emulate_sidebarClick(App_ns.sidebar, smallCollectionName)
    User.idle()
    
    # verification of import
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
    
    # Current tests measure the first time you switch or overlay.
    # If you want to measure the subsequent times, enable this section.
    if 0:
        User.emulate_sidebarClick(App_ns.sidebar, largeCollectionName, overlay=False)
        User.idle()
        User.emulate_sidebarClick(App_ns.sidebar, smallCollectionName, overlay=False)
        User.idle()
        User.emulate_sidebarClick(App_ns.sidebar, largeCollectionName, overlay=True)
        User.idle()
        User.emulate_sidebarClick(App_ns.sidebar, largeCollectionName, overlay=True)
        User.idle()
        
    # backup
    # - need to commit first so that the collection in the sidebar
    #   gets saved
    App_ns.itsView.commit()
    logger.Start("Backup repository")
    dbHome = App_ns.itsView.repository.backup()
    logger.Stop()
    
    # verification of backup
    if os.path.isdir(dbHome):
        logger.ReportPass("Backup exists")
    else:
        logger.ReportFailure("Backup does not exist")
    
    logger.SetChecked(True)
    logger.Report("Backup")

finally:
    # cleaning
    logger.Close()
