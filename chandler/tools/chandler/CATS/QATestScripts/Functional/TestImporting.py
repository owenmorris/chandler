import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import util.QAUITestAppLib as QAUITestAppLib
import os, wx
import osaf.pim as pim

App_ns = QAUITestAppLib.App_ns

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()

# initialization
fileName = "TestImporting.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestImporting")


path = os.path.join(os.getenv('CHANDLERHOME'),"util/QATestScripts/DataFiles")
print path
share = Sharing.OneTimeFileSystemShare(path, 'importTest.ics', ICalendar.ICalendarFormat, view=App_ns.itsView)

logger.Start("Import Large Calendar")
try:
	collection = share.get()
except:
	logger.Stop()
	logger.ReportFailure("Importing calendar: exception raised")
else:
	App_ns.root.AddToSidebarWithoutCopying({'items' : [collection]})	
	wx.GetApp().Yield()
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
logger.Report()
logger.Close()

