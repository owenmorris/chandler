"""
Test that when an event that has been deleted is re-imported that it comes out of the trash 
and into the imported collection
"""
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import os, sys
from time import localtime, strftime
import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import osaf.framework.scripting as scripting

class TestRemoveFromTrashOnImport(ChandlerTestCase):
    
    def startTest(self):
    
        appView = self.app_ns.itsView
        today = strftime('%m/%d/%y',localtime())
        
        colName = "deleteThenImport"
        eventName = "eventToTest"

        #create a collection
        collection = QAUITestAppLib.UITestItem("Collection", self.logger)
        collection.SetDisplayName(colName)
        sb=self.app_ns.sidebar
        scripting.User.emulate_sidebarClick(sb,colName) 
        
        #create an event
        ev=QAUITestAppLib.UITestItem('Event', self.logger)
        ev.SetAttr(displayName=eventName, startDate=today, startTime="12:00 PM")
        
        #create a path to export to
        reportDir = os.getenv('CATSREPORTDIR')
        if not reportDir:
            reportDir = os.getcwd()
        fullpath = os.path.join(reportDir,colName)
        if os.path.exists(fullpath):
            os.remove(fullpath)
        reportDir = unicode(reportDir, sys.getfilesystemencoding())
        
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
        self.app_ns.sidebarCollection.add(collection)
        scripting.User.idle()    
            
        #verify
        ev.Check_ItemInCollection("Trash", expectedResult=False)
        ev.Check_ItemInCollection(colName, expectedResult=True)
            
