import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import osaf.framework.QAUITestAppLib as QAUITestAppLib
import os, wx
from osaf.pim import ListCollection
import osaf.pim.calendar.Calendar as Calendar

App_ns = QAUITestAppLib.App_ns


filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()

# initialization
fileName = "TestExporting.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestExporting")


path = os.path.join(os.path.expandvars('$CATSHOME'),"QATestScripts")
filename = 'exportTest.ics'
fullpath = os.path.join(path, filename)
if os.path.exists(fullpath):
    os.remove(fullpath)
share = Sharing.OneTimeFileSystemShare(path, 'exportTest.ics', ICalendar.ICalendarFormat, view=App_ns.itsView)



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
