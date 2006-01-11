import tools.QAUITestAppLib as QAUITestAppLib

from datetime import datetime

fileName = "PerfLargeDataJumpWeek.log"
logger = QAUITestAppLib.QALogger(fileName, "Jump from one week to another")

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

    logger.Start("Jump calendar by one week")
    testdate = datetime(2005, 12, 4)
    App_ns.root.SelectedDateChanged(start=testdate)
    User.idle()
    logger.Stop()

    # Test Phase: Verification

    logger.SetChecked(True)
    if App_ns.calendar.calendarControl.rangeStart == testdate:
        logger.ReportPass("Jump calendar by one week")
    else:
        logger.ReportFailure("Jump calendar by one week")
    logger.Report("Jump calendar by one week")
        
finally:
    logger.Close()
