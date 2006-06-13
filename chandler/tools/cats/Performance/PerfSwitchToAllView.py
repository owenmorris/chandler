import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class PerfSwitchToAllView(ChandlerTestCase):

    def startTest(self):

        # creation
        testView = QAUITestAppLib.UITestView(self.logger)
        
        # action
        # switch to all view
        testView.SwitchToAllView()
    
        # verification
        # for now, we just assume it worked

