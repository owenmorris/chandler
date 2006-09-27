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
from datetime import datetime

class PerfLargeDataOverlayCalendar(ChandlerTestCase):

    def startTest(self):
    
        # Test Phase: Initialization
    
        # Start at the same date every time
        testdate = datetime(2005, 11, 27)
        self.app_ns.root.SelectedDateChanged(start=testdate)
    
        # Load a large calendar
        # NOTE: Don't do this when we restore from backed up repository
        testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')
        self.scripting.User.idle()
    
        # Test Phase: Action
    
        self.logger.startAction("Overlay calendar")
        clickSucceeded = User.emulate_sidebarClick(App_ns.sidebar, "Generated3000", overlay=True)
        self.scripting.User.idle()
        self.logger.endAction()
    
        # Test Phase: Verification
        self.logger.startAction("Verify calendar overlay")
        if clickSucceeded:
            self.logger.endAction(True, "Overlay calendar")
        else:
            self.logger.endAction(False, "Overlay calendar")
            
