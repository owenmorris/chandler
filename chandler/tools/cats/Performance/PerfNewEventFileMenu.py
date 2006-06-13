import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class PerfNewEventFileMenu(ChandlerTestCase):

    def startTest(self):

        #action
        event = QAUITestAppLib.UITestItem("Event", self.logger)
        
        #verification
        event.Check_DetailView({"displayName":"New Event"})
