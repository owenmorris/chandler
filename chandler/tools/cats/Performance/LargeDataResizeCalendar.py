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
from PyICU import ICUtzinfo

class LargeDataResizeCalendar(ChandlerTestCase):
    
    def startTest(self):
    
        # Do the test in the large calendar
        self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, 'Generated3000', overlay=False)
        self.scripting.User.idle()
    
        # Start at the same date every time
        testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
        self.app_ns.root.SelectedDateChanged(start=testdate)
    
        frame = self.app_ns.root.widget.GetParent()
        (x, y) = frame.GetSize()
        x += 20
        y += 20
    
        # Test Phase: Action
    
        self.logger.startPerformanceAction("Resize app in calendar mode")
        frame.SetSize((x, y))
        scripting.User.idle()
        self.logger.endPerformanceAction()
    
        # Test Phase: Verification
    
        self.logger.startAction('Verify calendar resized')
        (bigx, bigy) = frame.GetSize()
        if (bigx == x and bigy == y):
            self.logger.endAction(True, "Resize app in calendar mode")
        else:
            self.logger.endAction(False, "Resize app in calendar mode")
            