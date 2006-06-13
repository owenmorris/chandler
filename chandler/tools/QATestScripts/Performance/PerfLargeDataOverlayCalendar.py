import tools.QAUITestAppLib as QAUITestAppLib

from datetime import datetime

fileName = "PerfLargeDataOverlayCalendar.log"
logger = QAUITestAppLib.QALogger(fileName, "Overlay calendar")

App_ns = app_ns()

try:
    # Test Phase: Initialization

    # Start at the same date every time
    testdate = datetime(2005, 11, 27)
    App_ns.root.SelectedDateChanged(start=testdate)

    # Load a large calendar
    # NOTE: Don't do this when we restore from backed up repository
    testView = QAUITestAppLib.UITestView(logger, u'100Events.ics')
    User.idle()

    # Test Phase: Action

    logger.Start("Overlay calendar")
    clickSucceeded = User.emulate_sidebarClick(App_ns.sidebar, "100Events", overlay=True)
    User.idle()
    logger.Stop()

    # Test Phase: Verification

    logger.SetChecked(True)
    if clickSucceeded:
        logger.ReportPass("Overlay calendar")
    else:
        logger.ReportFailure("Overlay calendar")
    logger.Report("OverlayCalendar")
        
finally:
    logger.Close()
