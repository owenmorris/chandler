import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class PerfNewCalendar(ChandlerTestCase):

    def startTest(self):

        # action
        col = QAUITestAppLib.UITestItem("Collection", self.logger)
        
        # verfication
        col.Check_CollectionExistence("Untitled")
 
