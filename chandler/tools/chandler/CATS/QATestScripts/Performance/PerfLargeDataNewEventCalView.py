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
fileName = "PerfLargeDataNewEventCalView.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"Creating a new event in the Cal view after large data import")


path = os.path.join(os.getenv('CHANDLERHOME'),"util/QATestScripts/DataFiles")
print path
share = Sharing.OneTimeFileSystemShare(path, 'Generated3000.ics', ICalendar.ICalendarFormat, view=App_ns.itsView)
testView = QAUITestAppLib.UITestView(logger)

#logger.Start("Import a large calendar and create a new event")
try:
    collection = share.get()
except:
    logger.Stop()
    logger.ReportFailure("Importing calendar: exception raised")
else:
    App_ns.root.AddToSidebarWithoutCopying({'items' : [collection]})	
    wx.GetApp().Yield()
    ev = wx.IdleEvent()
    wx.GetApp().ProcessEvent(ev)
    #logger.Stop()
    logger.ReportPass("Importing calendar")

#def TestEventCreation(title):
#    global logger
#    global App_ns
#    global pim
#    testEvent = App_ns.item_named(pim.CalendarEvent, title)
#    if testEvent is not None:
#        logger.ReportPass("Testing event creation: '%s'" % title)
#    else:
#        logger.ReportFailure("Testing event creation: '%s' not created" % title)

#TestEventCreation("Go to the beach")
#TestEventCreation("Basketball game")
#TestEventCreation("Visit friend")
#TestEventCreation("Library")

#action
#double click in the calendar view => event creation or selection
ev = testView.DoubleClickInCalView()

#check the detail view of the created event
ev.Check_DetailView({"displayName":"New Event"})


#logger.SetChecked(True)
#logger.Report("Import")
logger.Close()
