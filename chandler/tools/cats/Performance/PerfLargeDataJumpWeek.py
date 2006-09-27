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

class PerfLargeDataJumpWeek(ChandlerTestCase):

    def startTest(self):
    
        # Test Phase: Initialization
    
        # make user collection, since only user
        # collections can be displayed as a calendar
        col = QAUITestAppLib.UITestItem("Collection", self.logger)

        # Start at the same date every time
        testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
        self.app_ns.root.SelectedDateChanged(start=testdate)
    
        # Load a large calendar
        # NOTE: Don't do this when we restore from backed up repository
        testView = QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
        self.scripting.User.idle()
    
        # Test Phase: Action
    
        self.logger.startAction("Jump calendar by one week")
        testdate = datetime(2005, 12, 4, tzinfo=ICUtzinfo.default)
        self.app_ns.root.SelectedDateChanged(start=testdate)
        self.scripting.User.idle()
        self.logger.endAction()
    
        # Test Phase: Verification
    
        self.logger.startAction("Verifying one week jump")
        if self.app_ns.calendar.calendarControl.rangeStart == testdate:
            self.logger.endAction(True, "Jump calendar by one week")
        else:
            self.logger.endAction(False, "Jump calendar by one week")
            
