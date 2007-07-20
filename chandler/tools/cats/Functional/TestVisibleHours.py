#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

class TestVisibleHours(ChandlerTestCase):

    def startTest(self):
        # Creating a collection switches us to calendar view where we
        # do the actual test
        QAUITestAppLib.UITestItem("Collection", self.logger)
    
        # Find all the children of the Visible Hours menu
        eventsToTest = list(
            block.event for block in QAUITestAppLib.App_ns.VisibleHoursMenu.childBlocks
            if block.hasLocalAttributeValue('event') # ... exclude separators
            and block.event.visibleHours > 0 # ... and the "auto" item
        )
        
        
        for event in eventsToTest:
            name = event.blockName
            self.logger.startAction(name)
    
            # Post the visible hours event... doesn't seem to be
            # a straightforward way to do this
            QAUITestAppLib.App_ns.MainView.onVisibleHoursEvent(event)
            
            # Allow the UI to refresh
            QAUITestAppLib.scripting.User.idle()
            
            # Figure out how many hours the TimedEvents widget is
            # displaying
            widget = QAUITestAppLib.App_ns.TimedEvents.widget
            rect = widget.GetClientRect()
            if event.visibleHours == 24:
                import pdb; pdb.set_trace()
            relativeTime = widget.getRelativeTimeFromPosition(
                              None, wx.Point(0, rect.height))
            widgetHours = int(float(relativeTime.seconds)/3600.0 +
                               24.0 * relativeTime.days + 0.5)
            
            # ... and double-check it's working
            if widgetHours != event.visibleHours:
                self.logger.endAction(False, "Expected %s visible hours, got %s" %
                                     (event.visibleHours, widgetHours))
            else:
                self.logger.endAction(True, "Number of hours is correct")
    
