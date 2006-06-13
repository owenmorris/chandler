import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class PerfLargeDataNewCalendar(ChandlerTestCase):

    def startTest(self):

        # initialization
    
        # creation
        QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
    
        # action
        col = QAUITestAppLib.UITestItem("Collection", self.logger)
        
        # verification
        col.Check_CollectionExistence("Untitled")
        

