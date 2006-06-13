import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import wx

class PerfLargeDataScrollTable(ChandlerTestCase):

    def startTest(self):
    
        # Load a large calendar so we have events to scroll 
        # NOTE: Don't do this when we restore from backed up repository
        testView = QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
    
        # Switch views to the table after we load
        # Its currently important to do this after we load due
        # to a linux bug (4461)-- we want to make sure we have a scrollbar
        self.app_ns.root.ApplicationBarAll()
    
        self.scripting.User.emulate_sidebarClick(self.app_ns.sidebar, "Generated3000")
        
        # Process idle and paint cycles, make sure we're only
        # measuring scrolling performance, and not accidentally
        # measuring the consequences of a large import
        self.scripting.User.idle()
        
        # Fetch the table widget
        tableWidget = self.app_ns.summary.widget
        
        # Test Phase: Action (the action we are timing)
        
        self.logger.startAction("Scroll table 25 scroll units")
        tableWidget.Scroll(0, 25)
        tableWidget.Update() # process only the paint events for this window
        self.logger.endAction()
        
        # Test Phase: Verification
        
        self.logger.startAction("Verify table scroll")
        (x, y) = tableWidget.GetViewStart()
        if (x == 0 and y == 25):
            self.logger.endAction(True, "Scrolled table")
        else:
            self.logger.endAction(False, "Scrolled table")
    
        
