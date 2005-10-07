import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import util.QAUITestAppLib as QAUITestAppLib
import os, wx
from osaf.pim import ListCollection
import osaf.pim.calendar.Calendar as Calendar

App_ns = QAUITestAppLib.App_ns


filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()

# initialization
fileName = u"TestExporting.log"
#Encode the unicode filename to the system character set encoding
fileName = fileName.encode(sys.getfilesystemencoding())
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),u"TestExporting")


path = os.path.join(os.getenv('CHANDLERHOME'),u"util/QATestScripts/DataFiles")
filename = u'exportTest.ics'
#Encode the unicode filename to the system character set encoding
fileName = fileName.encode(sys.getfilesystemencoding())
fullpath = os.path.join(path, filename)
if os.path.exists(fullpath):
    os.remove(fullpath)
share = Sharing.OneTimeFileSystemShare(unicode(path), u'exportTest.ics', ICalendar.ICalendarFormat, view=App_ns.itsView)



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
