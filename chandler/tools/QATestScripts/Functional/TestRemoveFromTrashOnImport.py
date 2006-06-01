"""
Test that when an event that has been deleted is re-imported that it comes out of the trash 
and into the imported collection
"""
import tools.QAUITestAppLib as QAUITestAppLib
import os
from time import localtime, strftime
import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import osaf.framework.scripting as scripting

appView = app_ns().itsView
App_ns = app_ns()
today = strftime('%m/%d/%y',localtime())

#initialization
fileName = "TestRemoveFromTrashOnImport.log"
logger = QAUITestAppLib.QALogger(fileName, "TestRemoveFromTrashOnImport")
colName = "deleteThenImport"
eventName = "eventToTest"

try:
    #create a collection
    collection = QAUITestAppLib.UITestItem("Collection", logger)
    collection.SetDisplayName(colName)
    sb=App_ns.sidebar
    scripting.User.emulate_sidebarClick(sb,colName) 
    
    #create an event
    ev=QAUITestAppLib.UITestItem('Event', logger)
    ev.SetAttr(displayName=eventName, startDate=today, startTime="12:00 PM")
    
    #create a path to export to
    reportDir = os.getenv('CATSREPORTDIR')
    if not reportDir:
        reportDir = os.getcwd()
    fullpath = os.path.join(reportDir,colName)
    if os.path.exists(fullpath):
        os.remove(fullpath)
    reportDir = unicode(reportDir, 'utf8')

    #export
    share = Sharing.OneTimeFileSystemShare(reportDir, u'deleteThenImport.ics', ICalendar.ICalendarFormat, itsView=appView)
    share.contents = collection.item
    share.put()
    
    #delete collection
    scripting.User.emulate_sidebarClick(sb,colName) 
    collection.DeleteCollection()
    
    #import event back in
    share = Sharing.OneTimeFileSystemShare(reportDir, u'deleteThenImport.ics', ICalendar.ICalendarFormat, itsView=appView)
    collection = share.get()
    App_ns.sidebarCollection.add(collection)
    User.idle()    
        
    #verify
    ev.Check_ItemInCollection("Trash", expectedResult=False)
    ev.Check_ItemInCollection(colName, expectedResult=True)
        
finally:
    #cleaning
    logger.Close()
