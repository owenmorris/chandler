import tools.QAUITestAppLib as QAUITestAppLib

from datetime import datetime

fileName = "PerfLargeDataSwitchCalendar.log"
logger = QAUITestAppLib.QALogger(fileName, "Switch calendar")

App_ns = app_ns()

try:
    # Test Phase: Initialization

    # Start at the same date every time
    testdate = datetime(2005, 11, 27)
    App_ns.root.SelectedDateChanged(start=testdate)

    # Load a large calendar
    # NOTE: Don't do this when we restore from backed up repository
    testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')
    User.idle()

    # Test Phase: Action

    logger.Start("Switch calendar")
    clickSucceeded = User.emulate_sidebarClick(App_ns.sidebar, "Generated3000", overlay=False)
    User.idle()
    logger.Stop()

    # Test Phase: Verification

    logger.SetChecked(True)
    if clickSucceeded:
        logger.ReportPass("Switch calendar")
    else:
        logger.ReportFailure("Switch calendar")
    logger.Report("SwitchCalendar")
        
finally:
    logger.Close()
