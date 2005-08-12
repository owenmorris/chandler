import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import osaf.framework.scripting.QATestAppLib as QATestAppLib
import os, wx

logger = QATestAppLib.Logger()
path = os.path.join(os.getenv('CHANDLERHOME') or '.', 'parcels', 'osaf','sharing','tests')
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

