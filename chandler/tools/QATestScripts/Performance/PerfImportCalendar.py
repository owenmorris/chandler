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

# This performance test does actually a couple of things:
#   - acts as performance test #5 Import 3k event calendar
#   - creates a repository backup for PerfLargeData* tests

from __future__ import with_statement

import tools.QAUITestAppLib as QAUITestAppLib
import os
import osaf.pim as pim
from application import schema

App_ns = app_ns()

# initialization
fileName = "PerfImporting.log"
logger = QAUITestAppLib.QALogger(fileName, "Importing 3000 event calendar")

largeCollectionName = 'Generated3000'
smallCollectionName = 'SmallCollection'

try:
    # import
    logger.Start("Import")
    QAUITestAppLib.UITestView(logger, u'%s.ics' % largeCollectionName)
    logger.Stop()
    
    # Start in the small collection
    col = QAUITestAppLib.UITestItem("Collection")
    col.SetDisplayName(smallCollectionName)
    User.emulate_sidebarClick(App_ns.sidebar, smallCollectionName)
    # Create a dummy new event so that we have detail view showing
    QAUITestAppLib.UITestItem("Event")
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
        
    # Make sure none of our content items have pending triage
    # (This will make things more consistent in tests we do against this repo)
    view = App_ns.itsView
    with view.observersDeferred():
        with view.reindexingDeferred():
            contentItems = schema.ns("osaf.pim", view).contentItems
            keys = [k for k in contentItems.iterkeys() if view.findValue(k, '_sectionTriageStatus', None) is not None]
            if view.findValue(keys[0], '_sectionTriageStatus', None) != pim.TriageEnum.now:
                logger.ReportFailure('First row was expected to have triage status NOW')
            for key in keys[1:]: # Leave one so we'll always have 3 sections in summary view
                item = view[key]
                del item._sectionTriageStatus
                del item._sectionTriageStatusChanged

    # backup
    # - need to commit first so that the collection in the sidebar
    #   gets saved
    view.commit()
    dbHome = view.repository.backup()
    
    # verification of backup
    if os.path.isdir(dbHome):
        logger.ReportPass("Backup exists")
    else:
        logger.ReportFailure("Backup does not exist")
    
    logger.SetChecked(True)
    logger.Report("Import")

finally:
    # cleaning
    logger.Close()
