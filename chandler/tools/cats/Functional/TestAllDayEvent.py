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

class TestAllDayEvent(ChandlerTestCase):

    def startTest(self):
        
        filename = "TestAllDayEvent.log"
        #print 'test3'
        #logger = QAUITestAppLib.QALogger(fileName,"TestAllDayEvent")
        #logger = TestLogger.TestOutput(logname=filename)
        #logger.startSuite('TestAllDayEvent')
        #logger.startTest('TestAllDayEvent')
        
        # creation
        event = QAUITestAppLib.UITestItem("Event", self.logger)
        
        # action
        event.SetAllDay(True)
        
        # verification
        event.Check_DetailView({"allDay":True})
        event.Check_Object({"allDay":True})
        
        #finally:
        #cleaning
