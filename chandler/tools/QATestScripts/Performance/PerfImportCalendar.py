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
    logger.Start("Import")
    QAUITestAppLib.UITestView(logger, u'Generated3000.ics')
    logger.Stop()
    
    # no action - we just verify import

    # verification
    def VerifyEventCreation(title):
        global logger
        global App_ns
        global pim
        testEvent = App_ns.item_named(pim.CalendarEvent, title)
        if testEvent is not None:
            logger.ReportPass("Testing event creation: '%s'" % title)
        else:
            logger.ReportFailure("Testing event creation: '%s' not created" % title)
    
    VerifyEventCreation("Go to the beach")
    VerifyEventCreation("Basketball game")
    VerifyEventCreation("Visit friend")
    VerifyEventCreation("Library")
    
    logger.SetChecked(True)
    logger.Report("Import")

finally:
    # cleaning
    logger.Close()
