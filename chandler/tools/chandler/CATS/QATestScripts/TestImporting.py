import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import osaf.framework.scripting.QAUITestAppLib as QAUITestAppLib
import os, wx


filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()

# initialization
fileName = "TestImporting.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestImporting")


path = os.path.join(os.path.expandvars('$CATSHOME'),"QATestScripts")
print path
share = Sharing.OneTimeFileSystemShare(path, '1kevents.ics', ICalendar.ICalendarFormat, view=__view__)

logger.Start("Import Large Calendar")
try:
	collection = share.get()
except:
	logger.Stop()
	logger.ReportFailure("Importing calendar: exception raised")
else:
	SidebarAdd(collection)
	wx.GetApp().Yield()
	logger.Stop()
	logger.ReportPass("Importing calendar")

def TestEventCreation(title):
    global logger
    testEvent = FindByName(pim.CalendarEvent, title)
    if testEvent is not None:
        logger.ReportPass("Testing event creation: '%s'" % title)
    else:
        logger.ReportFailure("Testing event creation: '%s' not created" % title)
TestEventCreation("Go to the beach")
TestEventCreation("Basketball game")
TestEventCreation("Visit friend")
TestEventCreation("Library")
TestEventCreation("Vacation")


logger.SetChecked(True)
logger.Report()
logger.Close()

