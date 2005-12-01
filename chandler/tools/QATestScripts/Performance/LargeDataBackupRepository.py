import osaf.sharing.Sharing as Sharing
import tools.QAUITestAppLib as QAUITestAppLib
import os, wx, sys
import osaf.pim as pim

App_ns = app_ns()

# initialization
fileName = "LargeDataBackupRepository.log"
logger = QAUITestAppLib.QALogger(fileName, "Backing up 3000 event repository")

try:
    # import
    QAUITestAppLib.UITestView(logger, u'Generated3000.ics')
    
    # verification of import
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
    
    # backup
    logger.Start("Backup repository")
    dbHome = App_ns.itsView.repository.backup()
    logger.Stop()
    
    # verification of backup
    if os.path.isdir(dbHome):
        logger.ReportPass("Backup exists")
    else:
        logger.ReportFailure("Backup does not exist")
    
    logger.SetChecked(True)
    logger.Report("Backup")

finally:
    # cleaning
    logger.Close()
