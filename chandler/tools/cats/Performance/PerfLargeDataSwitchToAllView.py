import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class PerfLargeDataSwitchToAllView(ChandlerTestCase):

    def startTest(self):

        # creation
        testView = QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
    
        # action
        # switch to all view
        testView.SwitchToAllView()
  