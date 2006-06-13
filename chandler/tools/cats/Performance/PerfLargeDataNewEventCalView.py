import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class PerfLargeDataNewEventCalView(ChandlerTestCase):

    def startTest(self):

        # initialization
        
        # creation
        testView = QAUITestAppLib.UITestView(self.logger)#, u'Generated3000.ics')
    
        # action
        # double click in the calendar view => event creation or selection
        ev = testView.DoubleClickInCalView()
        
        # verification
        # check the detail view of the created event
        ev.Check_DetailView({"displayName":"New Event"})
        