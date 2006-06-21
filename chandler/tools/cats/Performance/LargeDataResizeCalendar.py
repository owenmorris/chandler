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
from datetime import datetime
from PyICU import ICUtzinfo
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class LargeDataResizeCalendar(ChandlerTestCase):

    def startTest(self):
    
        # Test Phase: Initialization
    
        # Start at the same date every time
        testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
        self.app_ns.root.SelectedDateChanged(start=testdate)
    
        frame = self.app_ns.root.widget.GetParent()
        (x, y) = frame.GetSize()
        x += 20
        y += 20
    
        # Load a large calendar
        # NOTE: Don't do this when we restore from backed up repository
        testView = QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
        self.scripting.User.idle()
    
        # Test Phase: Action
    
        self.logger.startAction("Resize app in calendar mode")
        frame.SetSize((x, y))
        self.scripting.User.idle()
        self.logger.endAction()
    
        # Test Phase: Verification
    
        self.logger.startAction('Verify resize app in calendar mode')
        (bigx, bigy) = frame.GetSize()
        if (bigx == x and bigy == y):
            self.logger.endAction(True, "Resize app in calendar mode")
        else:
            self.logger.endAction(False, "Resize app in calendar mode")
        
