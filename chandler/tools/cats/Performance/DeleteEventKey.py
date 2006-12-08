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
from application import schema
import os, wx

class DeleteEventKey(ChandlerTestCase):
    
    def startTest(self):


        # This script tests deletion of a single, newly created event,
        # by simulating the self.scripting.User hitting the delete key.
        
        # Globals
        wxApp = wx.GetApp()
        
        
        def removeEvent():
            # Could try to simulate the self.scripting.User hitting delete by the following:
            self.scripting.User.emulate_typing("\x08")
            self.scripting.User.idle()
        
        ### do we need to do this???
        # If running with --catsProfile, we don't want to include
        # all the setup code in the output profile.
        #self.logger.SuspendProfiling()
            
        
        # Creating a collection switches us to calendar view where we
        # do the actual test
        QAUITestAppLib.UITestItem("Collection",self.logger, timeInfo=False)
    
       # Create the event we're going to delete ...
        newEvent = QAUITestAppLib.UITestItem("Event", self.logger).item
    
        # ... and select it, so that the event's lozenge has
        # focus when we try to delete.
        #
        timedCanvas = self.app_ns.TimedEvents
        timedCanvas.widget.SetFocus()
        
        # Attempt to wait for the UI activity from changing the selection
        # to die down.
        self.scripting.User.idle()
    
        # Test Phase: Action
        # ResumeProfiling() will make the self.logger start profiling
        # in Start().
        #self.logger.ResumeProfiling()
        
        self.logger.startPerformanceActionPerformanceAction("Remove event")
        removeEvent()
        self.logger.endPerformanceActionPerformanceAction()
        
        
        # Make sure the new event appears in the trash, and
        # no other collections.
        self.logger.startPerformanceActionAction('Verify event appears in trash and no other collections')
        collections = list(newEvent.collections)
        if collections != [schema.ns("osaf.pim", newEvent.itsView).trashCollection]:
            self.logger.endPerformanceActionAction(False, "Event was not removed: it's in %s" %
                                 (collections,))
        else:
            self.logger.endPerformanceActionAction(True, "On removing event via delete key")
       