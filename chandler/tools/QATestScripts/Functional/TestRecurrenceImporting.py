import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import tools.QAUITestAppLib as QAUITestAppLib
import os
import osaf.pim as pim
from datetime import date
import osaf.framework.scripting as scripting

App_ns = app_ns()

# initialization
fileName = "TestRecurrenceImporting.log"
logger = QAUITestAppLib.QALogger(fileName, "TestRecurrenceImporting")

try:
    path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
    # Upcast path to unicode since Sharing requires a unicode path
    path = unicode(path, 'utf8')
    share = Sharing.OneTimeFileSystemShare(path, u'TestRecurrence.ics', ICalendar.ICalendarFormat, itsView=App_ns.itsView)
    
    logger.Start("Import calendar with recurring events")
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
    
    User.idle()
    VerifyEventCreation("Yearly Never End")
    VerifyEventCreation("Monthly Meeting")
    VerifyEventCreation("Multi-All Day")
    VerifyEventCreation("All-day never end")
    
    # bug 5593, set an end date for the "Weekly Never End" event
    sidebar = QAUITestAppLib.App_ns.sidebar
    scripting.User.emulate_sidebarClick(sidebar, 'TestRecurrence')    
    
    view = QAUITestAppLib.UITestView(logger)
    view.GoToDate('05/01/2006')
    
    event = QAUITestAppLib.GetOccurrence('Weekly Never End', date(2006, 5, 1))    
    QAUITestAppLib.UITestItem(event, logger).SetAttr(recurrenceEnd="05/01/2006")
    
    # event has been deleted by changing recurrence, get a new one
    event = QAUITestAppLib.GetOccurrence('Weekly Never End', date(2006, 5, 1))    
    testItem = QAUITestAppLib.UITestItem(event, logger)
    testItem.SelectItem(catchException=True)
    
    # Make sure this occurrence exists and was able to be selected
    testItem.Check_ItemSelected()
    
    logger.SetChecked(True)
    logger.Report()
finally:
    # cleanup
    logger.Close()
    
