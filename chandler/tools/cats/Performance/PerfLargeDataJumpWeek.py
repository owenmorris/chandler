import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
from datetime import datetime
from PyICU import ICUtzinfo

class PerfLargeDataJumpWeek(ChandlerTestCase):

    def startTest(self):
    
        # Test Phase: Initialization
    
        # Start at the same date every time
        testdate = datetime(2005, 11, 27, tzinfo=ICUtzinfo.default)
        self.app_ns.root.SelectedDateChanged(start=testdate)
    
        # Load a large calendar
        # NOTE: Don't do this when we restore from backed up repository
        testView = QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
        self.scripting.User.idle()
    
        # Test Phase: Action
    
        self.logger.startAction("Jump calendar by one week")
        testdate = datetime(2005, 12, 4, tzinfo=ICUtzinfo.default)
        self.app_ns.root.SelectedDateChanged(start=testdate)
        self.scripting.User.idle()
        self.logger.endAction()
    
        # Test Phase: Verification
    
        self.logger.startAction("Verifying one week jump")
        if self.app_ns.calendar.calendarControl.rangeStart == testdate:
            self.logger.endAction(True, "Jump calendar by one week")
        else:
            self.logger.endAction(False, "Jump calendar by one week")
            
