import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import util.QAUITestAppLib as QAUITestAppLib
import os, wx, sys
from osaf.pim import ListCollection
import osaf.pim.calendar.Calendar as Calendar

App_ns = QAUITestAppLib.App_ns


filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()

# initialization
fileName = "TestExporting.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestExporting")


path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
filename = 'exportTest.ics'
fullpath = os.path.join(path, filename)
if os.path.exists(fullpath):
    os.remove(fullpath)

#Upcast path to unicode since Sharing requires a unicode path
#for now. This will change in the next few days
path = unicode(path, sys.getfilesystemencoding())
share = Sharing.OneTimeFileSystemShare(path, u'exportTest.ics', ICalendar.ICalendarFormat, view=App_ns.itsView)





logger.Start("Export Test Calendar")
try:
    collection = ListCollection(view=App_ns.itsView)
    for event in Calendar.CalendarEvent.iterItems(App_ns.itsView):
        collection.add(event)
    share.contents = collection
    share.put()
except:
    logger.Stop()
    logger.ReportFailure("Exporting calendar: exception raised")
else:
    wx.GetApp().Yield()
    logger.Stop()
    logger.ReportPass("Exporting calendar")

logger.SetChecked(True)
logger.Report("Exporting calendar")
logger.Close()
