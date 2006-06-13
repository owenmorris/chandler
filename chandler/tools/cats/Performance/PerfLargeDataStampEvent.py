import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class PerfLargeDataStampEvent(ChandlerTestCase):

    def startTest(self):

        
        # creation
        QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
    
        # action
        note = QAUITestAppLib.UITestItem("Note", self.logger)
        note.StampAsCalendarEvent(True)
        
        # verification
        note.Check_DetailView({"stampEvent":True})
        