import tools.QAUITestAppLib as QAUITestAppLib
import osaf.framework.scripting as scripting

from datetime import datetime

fileName = "PerfLargeDataResizeCalendar.log"
logger = QAUITestAppLib.QALogger(fileName, "Resize app in calendar mode")

App_ns = app_ns()

try:
    # Test Phase: Initialization

    # Start at the same date every time
    testdate = datetime(2005, 11, 27)
    App_ns.root.SelectedDateChanged(start=testdate)

    frame = App_ns.root.widget.GetParent()
    (x, y) = frame.GetSize()
    x += 20
    y += 20

    # Load a large calendar
    # NOTE: Don't do this when we restore from backed up repository
    testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')
    scripting.User.idle()

    # Test Phase: Action

    logger.Start("Resize app in calendar mode")
    frame.SetSize((x, y))
    scripting.User.idle()
    logger.Stop()

    # Test Phase: Verification

    logger.SetChecked(True)
    (bigx, bigy) = frame.GetSize()
    if (bigx == x and bigy == y):
        logger.ReportPass("Resize app in calendar mode")
    else:
        logger.ReportFailure("Resize app in calendar mode")
    logger.Report("Resize app in calendar mode")
        
finally:
    logger.Close()
