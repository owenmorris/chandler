import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import tools.QAUITestAppLib as QAUITestAppLib
import os, sys
import osaf.pim as pim

App_ns = app_ns()

# initialization
fileName = "TestImporting.log"
logger = QAUITestAppLib.QALogger(fileName, "TestImporting")

try:
    path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
    # Upcast path to unicode since Sharing requires a unicode path
    path = unicode(path, sys.getfilesystemencoding())
    share = Sharing.OneTimeFileSystemShare(path, u'importTest.ics', ICalendar.ICalendarFormat, itsView=App_ns.itsView)

    logger.Start("Import Large Calendar")
    try:
        collection = share.get()
    except:
        logger.Stop()
        logger.ReportException("Importing calendar")
    else:
        App_ns.sidebarCollection.add(collection)
        User.idle()
        logger.Stop()
        logger.ReportPass("Importing calendar")

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
    logger.Report()
finally:
    # cleanup
    logger.Close()
    
