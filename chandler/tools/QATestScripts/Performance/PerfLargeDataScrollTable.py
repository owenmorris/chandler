import tools.QAUITestAppLib as QAUITestAppLib

import wx

# Utilities
def processNextIdle():
    wx.GetApp().Yield()
    ev = wx.IdleEvent()
    wx.GetApp().ProcessEvent(ev)
    wx.GetApp().Yield()

# Test Phase: Initialization
App_ns = app_ns()

logger = QAUITestAppLib.QALogger("PerfLargeDataScrollTable.log",
                                 "Scrolling a table")

try:
    # Switch views to the table before we load
    App_ns.root.ApplicationBarAll()
    wx.GetApp().Yield()
    
    # Load a large calendar so we have events to scroll 
    testView = QAUITestAppLib.UITestView(logger, u'Generated3000.ics')
    
    # Process idle and paint cycles, make sure we're only
    # measuring scrolling performance, and not accidentally
    # measuring the consequences of a large import
    processNextIdle()
    
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
