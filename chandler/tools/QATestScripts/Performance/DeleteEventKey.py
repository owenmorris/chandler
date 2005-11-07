import tools.QAUITestAppLib as QAUITestAppLib
import os, wx

# This script tests deletion of a single, newly created event,
# by simulating the user hitting the delete key.

# Globals
App_ns = QAUITestAppLib.App_ns
wxApp = wx.GetApp()


# Utility...(This should go in QAUITestLib.py)
def processNextIdle():
    wxApp.Yield()
    ev = wx.IdleEvent()
    wxApp.ProcessEvent(ev)
    wxApp.Yield()



def removeEvent():
    # Could try to simulate the user hitting delete by the following:
    QAUITestAppLib.scripting.User.emulate_typing("\x08")
    processNextIdle()

# Test Phase: Initialization
logger = QAUITestAppLib.QALogger(
                            "DeleteEventKey.log"
                            "Delete a newly created event")

# If running with --catsProfile, we don't want to include
# all the setup code in the output profile.
logger.SuspendProfiling()
    

try:
    # Create the event we're going to delete ...
    newEvent = QAUITestAppLib.UITestItem("Event", logger).item

    # ... and select it, so that the event's lozenge has
    # focus when we try to delete.
    #
    timedCanvas = App_ns.TimedEvents
    timedCanvas.widget.SetFocus()
    
    # Attempt to wait for the UI activity from changing the selection
    # to die down.
    processNextIdle()

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
    if collections != [App_ns.TrashCollection]:
        logger.ReportFailure("Event was not removed: it's in %s" %
                             (collections,))
    else:
        logger.Report("On removing event via delete key")

finally:
    # cleanup
    logger.Close()
