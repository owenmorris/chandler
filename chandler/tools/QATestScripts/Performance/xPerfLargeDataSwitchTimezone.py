import tools.QAUITestAppLib as QAUITestAppLib

from datetime import datetime
from PyICU import ICUtzinfo

fileName = "PerfLargeDataSwitchTimezone.log"
logger = QAUITestAppLib.QALogger(fileName, "Switch timezone")

try:
    app_ns = app_ns()
    calendarBlock = getattr(app_ns, "MainCalendarControl")

    # Enable timezones so that we can switch from the UI
    app_ns.root.EnableTimezones()
    
    # Start at the same date every time
    testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
    app_ns.root.SelectedDateChanged(start=testdate)

    # Load a large calendar
    testView = QAUITestAppLib.UITestView(logger, "office.ics")#, u'Generated3000.ics')
    app_ns.sidebar.select(testView.collection)
    User.idle()

    # Switch the timezone (this is the action we are measuring)
    logger.Start("Switch timezone to US/Hawaii")
    QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, "US/Hawaii")
    User.idle()
    logger.Stop()

    # Verification

    # @@@ KCP this test could be improved
    # Currently tests that the default tz is now US/Hawaii
    if ICUtzinfo.default == ICUtzinfo.getInstance("US/Hawaii"):
        logger.ReportPass("Timezone switched")
    else:
        logger.ReportFailure("Timezone failed to switch")
    
    logger.SetChecked(True)
    logger.Report("Switch timezone")

finally:
    logger.Close()
    
import tools.QAUITestAppLib as QAUITestAppLib

from datetime import datetime
from PyICU import ICUtzinfo

fileName = "PerfLargeDataSwitchTimezone.log"
logger = QAUITestAppLib.QALogger(fileName, "Switch timezone")

try:
    app_ns = app_ns()
    calendarBlock = getattr(app_ns, "MainCalendarControl")

    # Enable timezones so that we can switch from the UI
    app_ns.root.EnableTimezones()
    
    # Start at the same date every time
    testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
    app_ns.root.SelectedDateChanged(start=testdate)

    # Load a large calendar
    testView = QAUITestAppLib.UITestView(logger, "office.ics")#, u'Generated3000.ics')
    app_ns.sidebar.select(testView.collection)
    User.idle()

    # Switch the timezone (this is the action we are measuring)
    logger.Start("Switch timezone to US/Hawaii")
    QAUITestAppLib.SetChoice(calendarBlock.widget.tzChoice, "US/Hawaii")
    User.idle()
    logger.Stop()

    # Verification

    # @@@ KCP this test could be improved
    # Currently tests that the default tz is now US/Hawaii
    if ICUtzinfo.default == ICUtzinfo.getInstance("US/Hawaii"):
        logger.ReportPass("Timezone switched")
    else:
        logger.ReportFailure("Timezone failed to switch")
    
    logger.SetChecked(True)
    logger.Report("Switch timezone")

finally:
    logger.Close()
    
