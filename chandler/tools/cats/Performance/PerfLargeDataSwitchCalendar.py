import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
from datetime import datetime

class PerfLargeDataSwitchCalendar(ChandlerTestCase):

    def startTest(self):
    
        # Test Phase: Initialization
    
        # Start at the same date every time
        testdate = datetime(2005, 11, 27)
        self.app_ns.root.SelectedDateChanged(start=testdate)
    
        # Load a large calendar
        # NOTE: Don't do this when we restore from backed up repository
        testView = QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
        self.scripting.User.idle()
    
        # Test Phase: Action
    
        self.logger.startAction("Switch calendar")
        clickSucceeded = self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, "Generated3000",  overlay=False)
        self.scripting.User.idle()
        self.logger.endAction()
    
        # Test Phase: Verification
        self.logger.startAction("Verify calendar switch")
        if clickSucceeded:
            self.logger.endAction(True, "Switch calendar")
        else:
            self.logger.endAction(False, "Switch calendar")
            
