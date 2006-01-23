import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import tools.QAUITestAppLib as QAUITestAppLib
import os, sys
import osaf.pim as pim

App_ns = app_ns()

# initialization
fileName = "TestRecurrenceImporting.log"
logger = QAUITestAppLib.QALogger(fileName, "TestRecurrenceImporting")

try:
    path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
    # Upcast path to unicode since Sharing requires a unicode path
    path = unicode(path, sys.getfilesystemencoding())
    share = Sharing.OneTimeFileSystemShare(path, u'TestRecurrence.ics', ICalendar.ICalendarFormat, itsView=App_ns.itsView)
    
    logger.Start("Import calendar with recurring events")
    try:
        collection = share.get()
    except:
        logger.Stop()
        logger.ReportFailure("Importing calendar: exception raised")
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
    
    User.idle()
    VerifyEventCreation("Yearly Never End")
    VerifyEventCreation("Monthly Meeting")
    VerifyEventCreation("Multi-All Day")
    VerifyEventCreation("All-day never end")
    
    logger.SetChecked(True)
    logger.Report()
finally:
    # cleanup
    logger.Close()
    
