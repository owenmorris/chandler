import tools.QAUITestAppLib as QAUITestAppLib

import wx
from datetime import datetime

# Test Phase: Initialization
App_ns = app_ns()

logger = QAUITestAppLib.QALogger("PerfLargeDataScrollCalendar.log",
                                 "Scroll calendar one unit")

try:
    # Look at the same date every time -- do this before we import
    # to save time and grief
    
    testdate = datetime(2005, 12, 14)
    App_ns.root.SelectedDateChanged(start=testdate)
    
    # Load a large calendar so we have events to scroll
    # NOTE: Don't do this when we restore from backed up repository
    testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')

    # Process idle and paint cycles, make sure we're only
    # measuring scrolling performance, and not accidentally
    # measuring the consequences of a large import
    User.idle()

    # Fetch the calendar widget
    calendarWidget = App_ns.TimedEvents.widget
    (xStart, yStart) = calendarWidget.GetViewStart()

    # Test Phase: Action (the action we are timing)

    logger.Start("Scroll calendar one unit")
    calendarWidget.Scroll(0, yStart + 1)
    calendarWidget.Update() # process only the paint events for this window
    logger.Stop()

    # Test Phase: Verification

    logger.SetChecked(True)
    (xEnd, yEnd) = calendarWidget.GetViewStart()
    if (yEnd == yStart + 1):
        logger.ReportPass("On scrolling calendar one unit")
    else:
        logger.ReportFailure("On scrolling calendar one unit")
    logger.Report("Scroll calendar one unit")

finally:
    # cleanup
    logger.Close()
