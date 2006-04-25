import tools.QAUITestAppLib as QAUITestAppLib

import wx

# Test Phase: Initialization
App_ns = app_ns()

logger = QAUITestAppLib.QALogger("PerfLargeDataScrollTable.log",
                                 "Scrolling a table")

try:
    # Load a large calendar so we have events to scroll 
    # NOTE: Don't do this when we restore from backed up repository
    testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')

    # Switch views to the table after we load
    # Its currently important to do this after we load due
    # to a linux bug (4461)-- we want to make sure we have a scrollbar
    App_ns.root.ApplicationBarAll()

    User.emulate_sidebarClick(App_ns.sidebar, "Generated3000")
    
    # Process idle and paint cycles, make sure we're only
    # measuring scrolling performance, and not accidentally
    # measuring the consequences of a large import
    User.idle()
    
    # Fetch the table widget
    tableWidget = App_ns.summary.widget
    
    # Test Phase: Action (the action we are timing)
    
    logger.Start("Scroll table 25 scroll units")
    tableWidget.Scroll(0, 25)
    tableWidget.Update() # process only the paint events for this window
    logger.Stop()
    
    # Test Phase: Verification
    
    logger.SetChecked(True)
    (x, y) = tableWidget.GetViewStart()
    if (x == 0 and y == 25):
        logger.ReportPass("Scrolled table")
    else:
        logger.ReportFailure("Scrolled table")
    logger.Report("Scroll table 25 scroll units")

finally:
    # cleanup
    logger.Close()
