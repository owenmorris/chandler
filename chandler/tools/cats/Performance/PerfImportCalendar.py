import osaf.sharing.Sharing as Sharing
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
import os, wx, sys
import osaf.pim as pim
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class PerfImportCalendar(ChandlerTestCase):

    def startTest(self):

        # creation
        self.logger.startAction("Import Generated3000.ics")
        QAUITestAppLib.UITestView(self.logger, u'Generated3000.ics')
        self.logger.endAction()
    
        # verification
        def VerifyEventCreation(title):
            self.logger.startAction("Testing event creation " + title )
            testEvent = self.app_ns.item_named(pim.CalendarEvent, title)
            if testEvent is not None:
                self.logger.endAction(True, "Testing event creation: '%s'" % title)
            else:
                self.logger.endAction(False, "Testing event creation: '%s' not created" % title)
        
        VerifyEventCreation("Go to the beach")
        VerifyEventCreation("Basketball game")
        VerifyEventCreation("Visit friend")
        VerifyEventCreation("Library")
        
        self.logger.addComment("Import Generated3000.ics test completed")

