import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class PerfLargeDataNewEventFileMenu(ChandlerTestCase):

    def startTest(self):

        # creation
        QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
    
        # action
        event = QAUITestAppLib.UITestItem("Event", self.logger)
        
        # verification
        event.Check_DetailView({"displayName":"New Event"})
    
