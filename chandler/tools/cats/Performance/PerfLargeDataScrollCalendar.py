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

class PerfLargeDataScrollCalendar(ChandlerTestCase):

    def startTest(self):

        # Look at the same date every time -- do this before we import
        # to save time and grief
        
        testdate = datetime(2005, 12, 14, tzinfo=ICUtzinfo.default)
        self.app_ns.root.SelectedDateChanged(start=testdate)
        
        # Load a large calendar so we have events to scroll
        # NOTE: Don't do this when we restore from backed up repository
        testView = QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
    
        # Process idle and paint cycles, make sure we're only
        # measuring scrolling performance, and not accidentally
        # measuring the consequences of a large import
        self.scripting.User.idle()
    
        # Fetch the calendar widget
        calendarWidget = self.app_ns.TimedEvents.widget
        (xStart, yStart) = calendarWidget.GetViewStart()
    
        # Test Phase: Action (the action we are timing)
    
        self.logger.startAction("Scroll calendar one unit")
        calendarWidget.Scroll(0, yStart + 1)
        calendarWidget.Update() # process only the paint events for this window
        self.logger.endAction()
    
        # Test Phase: Verification
    
        self.logger.startAction(True, "Verify one unit scroll")
        (xEnd, yEnd) = calendarWidget.GetViewStart()
        if (yEnd == yStart + 1):
            self.logger.endAction(True, "On scrolling calendar one unit")
        else:
            self.logger.endAction(False, "On scrolling calendar one unit")
    
