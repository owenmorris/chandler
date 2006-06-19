import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import os, wx, sys
from osaf.pim import ListCollection
import osaf.pim.calendar.Calendar as Calendar

class TestExporting(ChandlerTestCase):

    def startTest(self):
        
        appView = self.app_ns.itsView
        path = os.path.join(os.getenv('CHANDLERHOME'),"tools/cats/DataFiles")
        filename = 'exportTest.ics'
        fullpath = os.path.join(path, filename)
        if os.path.exists(fullpath):
            os.remove(fullpath)
        
        #Upcast path to unicode since Sharing requires a unicode path
        path = unicode(path, sys.getfilesystemencoding())
        share = Sharing.OneTimeFileSystemShare(path, 'exportTest.ics', ICalendar.ICalendarFormat, itsView=appView)
     
        self.logger.startAction("Export Test Calendar")
        collection = ListCollection(itsView=appView)
        for event in Calendar.CalendarEvent.iterItems(appView):
            collection.add(event)
        share.contents = collection
        share.put()
        self.logger.endAction(True)
        


