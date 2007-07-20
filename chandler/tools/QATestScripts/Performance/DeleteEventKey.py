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

from application import schema
import tools.QAUITestAppLib as QAUITestAppLib
import wx

# This script tests deletion of a single, newly created event,
# by simulating the user hitting the delete key.

# Globals
App_ns = app_ns()
wxApp = wx.GetApp()


def removeEvent():
    # Could try to simulate the user hitting delete by the following:
    QAUITestAppLib.scripting.User.emulate_typing("\x08")
    User.idle()

# Test Phase: Initialization
logger = QAUITestAppLib.QALogger(
                            "DeleteEventKey.log"
                            "Delete a newly created event")

# If running with --catsProfile, we don't want to include
# all the setup code in the output profile.
logger.SuspendProfiling()
    

try:
    # Test in calendar view
    App_ns.appbar.press("ApplicationBarEventButton")
    wx.GetApp().Yield(True)
    QAUITestAppLib.UITestItem("Collection")

   # Create the event we're going to delete ...
    newEvent = QAUITestAppLib.UITestItem("Event", logger).item

    # ... and select it, so that the event's lozenge has
    # focus when we try to delete.
    #
    timedCanvas = App_ns.TimedEvents
    timedCanvas.widget.SetFocus()
    
    # Attempt to wait for the UI activity from changing the selection
    # to die down.
    User.idle()

    # Test Phase: Action
    # ResumeProfiling() will make the logger start profiling
    # in Start().
    logger.ResumeProfiling()
    
    logger.Start("Remove event")
    removeEvent()
    logger.Stop()
    
    # Test Phase: Verification
    logger.SetChecked(True)
    
    # Make sure the new event appears in the trash, and
    # no other collections.
    collections = list(newEvent.collections)
    if collections != [schema.ns("osaf.pim", newEvent.itsView).trashCollection]:
        logger.ReportFailure("Event was not removed: it's in %s" %
                             (collections,))
    else:
        logger.Report("On removing event via delete key")

finally:
    # cleanup
    logger.Close()
