import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import osaf.framework.scripting.QATestAppLib as QATestAppLib
import os, wx

logger = QATestAppLib.Logger()
path = os.path.join(os.getenv('CHANDLERHOME') or '.', 'parcels', 'osaf','sharing','tests')
share = Sharing.OneTimeFileSystemShare(path, '3kevents.ics', ICalendar.ICalendarFormat, view=__view__)

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
logger.SetChecked(True)
logger.Report()
logger.Close()

