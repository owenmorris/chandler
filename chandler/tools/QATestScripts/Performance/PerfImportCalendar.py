import osaf.sharing.Sharing as Sharing
import tools.QAUITestAppLib as QAUITestAppLib
import os, wx, sys
import osaf.pim as pim

App_ns = app_ns()

# initialization
fileName = "PerfImporting.log"
logger = QAUITestAppLib.QALogger(fileName, "Importing 3000 event calendar")

try:
    # creation
    QAUITestAppLib.UITestView(logger, u'Generated3000.ics')
    
    # no action - we just verify imporation

    # verification
    def TestEventCreation(title):
        global logger
        global App_ns
        global pim
        testEvent = App_ns.item_named(pim.CalendarEvent, title)
        if testEvent is not None:
            logger.ReportPass("Testing event creation: '%s'" % title)
        else:
            logger.ReportFailure("Testing event creation: '%s' not created" % title)
    
    TestEventCreation("Go to the beach")
    TestEventCreation("Basketball game")
    TestEventCreation("Visit friend")
    TestEventCreation("Library")
    
    logger.SetChecked(True)
    logger.Report("Import")

finally:
    # cleaning
    logger.Close()
