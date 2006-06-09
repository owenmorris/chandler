import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import tools.QAUITestAppLib as QAUITestAppLib
import os, wx, sys
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim import ListCollection
from i18n.tests import uw

App_ns = app_ns()
appView = app_ns().itsView

# initialization
fileName = "TestImportOverwrite.log"
logger = QAUITestAppLib.QALogger(fileName, "TestImportOverwrite")

try:
    #create an event to export
    event = QAUITestAppLib.UITestItem("Event", logger)
    event_UUID = event.item.itsUUID
    #write some stuff in the event to make it unique
    event.SetAttr(displayName=uw("Original Event"), startDate="01/01/2001", startTime="12:00 AM", body=uw("This is the original event"))
    logger.ReportPass("Create Event to Export")

    #export the event
    path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
    filename = 'tempOverwriteTest.ics'
    fullpath = os.path.join(path, filename)
    if os.path.exists(fullpath):
        os.remove(fullpath)
    #Upcast path to unicode since Sharing requires a unicode path
    #for now. This will change in the next few days
    path = unicode(path, sys.getfilesystemencoding())
    share = Sharing.OneTimeFileSystemShare(path, 'tempOverwriteTest.ics', ICalendar.ICalendarFormat, itsView=appView)
    logger.ReportPass("Export Event")

    collection = ListCollection(itsView=appView)
    for tmpEvent in Calendar.CalendarEvent.iterItems(appView):
        collection.add(tmpEvent)
    share.contents = collection
    share.put()
    wx.GetApp().Yield()
    logger.ReportPass("Exporting event")

    #change the event after exporting
    event.SetAttr(displayName=uw("Changed Event"),  body=uw("This event has been changed"))
    logger.ReportPass("modifing event")

    #import the original event

    share = Sharing.OneTimeFileSystemShare(path, 'tempOverwriteTest.ics', ICalendar.ICalendarFormat, itsView=App_ns.itsView)
    share.get()
    wx.GetApp().Yield()
    logger.ReportPass("importing event")

    #check if changed attributes have reverted to original values
        #find imported event by UUID
    found = App_ns.view.findUUID(event_UUID)
    if found.body == uw('This is the original event') and \
                     found.displayName == uw('Original Event'):
        logger.ReportPass("Event overwriten")
    else:
        logger.ReportFailure('Event not overwriten')


finally: 
    #report results  
    logger.SetChecked(True)
    #logger.ReportPass()
    logger.Report()  
    # cleanup
    logger.Close()

