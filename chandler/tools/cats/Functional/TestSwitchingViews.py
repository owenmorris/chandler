import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class TestSwitchingViews(ChandlerTestCase):

    def startTest(self):
    
        # creation
        testView = QAUITestAppLib.UITestView(self.logger)
        
        # action
        # switch to all view
        testView.SwitchToAllView()
        # switch to tasks view
        testView.SwitchToTaskView()
        # switch to email view
        testView.SwitchToMailView()
        # switch to calendar view
        testView.SwitchToCalView()
    
