import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
import os
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class PerfStampEvent(ChandlerTestCase):

    def startTest(self):
    
        filePath = os.getenv('CATSREPORTDIR')
        if not filePath:
            filePath = os.getcwd()
 
        # creation
        note = QAUITestAppLib.UITestItem("Note", self.logger)
    
        # action
        note.StampAsCalendarEvent(True)
        
        # verification
        note.Check_DetailView({"stampEvent":True})

