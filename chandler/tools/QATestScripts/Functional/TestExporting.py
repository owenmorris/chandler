import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import tools.QAUITestAppLib as QAUITestAppLib
import os, wx, sys
from osaf.pim import ListCollection
import osaf.pim.calendar.Calendar as Calendar

appView = app_ns().itsView

# initialization
fileName = "TestExporting.log"
logger = QAUITestAppLib.QALogger(fileName, "TestExporting")

try:
    path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
    filename = 'exportTest.ics'
    fullpath = os.path.join(path, filename)
    if os.path.exists(fullpath):
        os.remove(fullpath)
    
    #Upcast path to unicode since Sharing requires a unicode path
    #for now. This will change in the next few days
    path = unicode(path, sys.getfilesystemencoding())
    share = Sharing.OneTimeFileSystemShare(path, 'exportTest.ics', ICalendar.ICalendarFormat, itsView=appView)
    
    logger.Start("Export Test Calendar")
    try:
        collection = ListCollection(itsView=appView)
        for event in Calendar.CalendarEvent.iterItems(appView):
            collection.add(event)
        share.contents = collection
        share.put()
    except:
        logger.Stop()
        logger.ReportException("Exporting calendar")
    else:
        User.idle()
        logger.Stop()
        logger.ReportPass("Exporting calendar")
    
    logger.SetChecked(True)
    logger.Report("Exporting calendar")

finally:
    # cleanup
    logger.Close()
