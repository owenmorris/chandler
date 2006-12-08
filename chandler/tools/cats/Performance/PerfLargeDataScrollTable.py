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
import wx

class PerfLargeDataScrollTable(ChandlerTestCase):
    
    def startTest(self):

        # Load a large calendar so we have events to scroll 
        # NOTE: Don't do this when we restore from backed up repository
        testView = QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
    
        # Switch views to the table after we load
        # Its currently important to do this after we load due
        # to a linux bug (4461)-- we want to make sure we have a scrollbar
        self.app_ns.root.ApplicationBarAll()
    
        self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, "Generated3000")
        
        # Process idle and paint cycles, make sure we're only
        # measuring scrolling performance, and not accidentally
        # measuring the consequences of a large import
        self.scripting.User.idle()
        
        # Fetch the table widget
        tableWidget = self.app_ns.summary.widget
        
        # Test Phase: Action (the action we are timing)
        
        self.logger.startPerformanceAction("Scroll table 25 scroll units")
        tableWidget.Scroll(0, 25)
        tableWidget.Update() # process only the paint events for this window
        self.logger.endPerformanceAction()
        
        # Test Phase: Verification
        
        self.logger.startAction('Verify table scrolled 25 units')
        (x, y) = tableWidget.GetViewStart()
        if (x == 0 and y == 25):
            self.logger.endAction(True)
        else:
            self.logger.endAction(False)
