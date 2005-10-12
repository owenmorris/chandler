import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import tools.QAUITestAppLib as QAUITestAppLib
import os, wx, sys
import osaf.pim as pim

App_ns = QAUITestAppLib.App_ns

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()

# initialization
fileName = "PerfImporting.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"Importing 3000 event calendar")


path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
print path

#Upcast path to unicode since Sharing requires a unicode path
#for now. This will change in the next few days
path = unicode(path, sys.getfilesystemencoding())

#share = Sharing.OneTimeFileSystemShare(path, 'Generated3000.ics', ICalendar.ICalendarFormat, view=App_ns.itsView)
share = Sharing.OneTimeFileSystemShare(path, u'Generated3000.ics', ICalendar.ICalendarFormat, view=App_ns.itsView)

logger.Start("Import Large Calendar")
try:
    collection = share.get()
except:
    logger.Stop()
    logger.ReportFailure("Importing calendar: exception raised")
else:
    App_ns.sidebarCollection.add(collection)
    wx.GetApp().Yield()
    ev = wx.IdleEvent()
    wx.GetApp().ProcessEvent(ev)
    logger.Stop()
    logger.ReportPass("Importing calendar")

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
logger.Close()
