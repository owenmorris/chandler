print """
####
#### WARNING
#### THIS FILE IS NOT BEING USED TO TEST PERFORMANCE 
#### THIS FILE IS STILL IN DEVELOPMENT.  USE THE FILES IN      
#### tools/QATestScripts/Performance                                  
####
"""
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
import os
import osaf.pim as pim

class LargeDataBackupRepository(ChandlerTestCase):
    
    def startTest(self):

        # initialization
        largeCollectionName = 'Generated3000'
        smallCollectionName = 'SmallCollection'
    
        # import
        QAUITestAppLib.UITestView(self.logger, u'%s.ics' % largeCollectionName)
        
        # Start in the small collection
        col = QAUITestAppLib.UITestItem("Collection", self.logger, timeInfo=False)
        col.SetDisplayName(smallCollectionName)
        self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, smallCollectionName)
        self.scripting.User.idle()
        
        # verification of import
        def VerifyEventCreation(title):
            self.logger.startAction('Verify event creation')
            global pim
            testEvent = self.app_ns.item_named(pim.EventStamp, title)
            if testEvent is not None:
                self.logger.endAction(True, "Testing event creation: '%s'" % title)
            else:
                self.logger.endAction(False, "Testing event creation: '%s' not created" % title)
        
        VerifyEventCreation("Go to the beach")
        VerifyEventCreation("Basketball game")
        VerifyEventCreation("Visit friend")
        VerifyEventCreation("Library")
        
        # Current tests measure the first time you switch or overlay.
        # If you want to measure the subsequent times, enable this section.
        if 0:
            self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, largeCollectionName, overlay=False)
            self.scripting.User.idle()
            self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, smallCollectionName, overlay=False)
            self.scripting.User.idle()
            self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, largeCollectionName, overlay=True)
            self.scripting.User.idle()
            self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, largeCollectionName, overlay=True)
            self.scripting.User.idle()
            
        # backup
        # - need to commit first so that the collection in the sidebar
        #   gets saved
        self.app_ns.itsView.commit()
        self.logger.startPerformanceAction("Backup repository")
        dbHome = self.app_ns.itsView.repository.backup()
        self.logger.endPerformanceAction()
        
        # verification of backup
        self.logger.startAction('Verify repository backup')
        if os.path.isdir(dbHome):
            self.logger.endAction(True, "Backup exists")
        else:
            self.logger.endAction(False, "Backup does not exist")
        
        


