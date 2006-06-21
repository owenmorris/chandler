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
import os, wx
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class DeleteEventKey(ChandlerTestCase):

    def startTest(self):

        # This script tests deletion of a single, newly created event,
        # by simulating the user hitting the delete key.
        
        # Globals
        App_ns = self.app_ns()
        wxApp = wx.GetApp()
        
        
        def removeEvent():
            # Could try to simulate the user hitting delete by the following:
            self.scripting.User.emulate_typing("\x08")
            User.idle()
        
        # Test Phase: Initialization
        
        # If running with --catsProfile, we don't want to include
        # all the setup code in the output profile.
        
        #assuming we won't need this in the new framework
        #self.logger.SuspendProfiling()
            
    
        # Create the event we're going to delete ...
        newEvent = QAUITestAppLib.UITestItem("Event", self.logger).item
    
        # ... and select it, so that the event's lozenge has
        # focus when we try to delete.
        #
        timedCanvas = App_ns.TimedEvents
        timedCanvas.widget.SetFocus()
        
        # Attempt to wait for the UI activity from changing the selection
        # to die down.
        User.idle()
    
        # Test Phase: Action
        # ResumeProfiling() will make the self.logger start profiling
        # in Start().
        
        self.logger.startAction("Remove event")
        removeEvent()
        self.logger.endAction()
        
        # Test Phase: Verification
        self.logger.startAction("Verify event in Trash")
        
        # Make sure the new event appears in the trash, and
        # no other collections.
        collections = list(newEvent.collections)
        if collections != [App_ns.trashCollection]:
            self.logger.endAction(False,"Event was not removed: it's in %s" %
                                 (collections,))
        else:
            self.logger.endAction(True, "On removing event via delete key")
        
