import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import osaf.framework.scripting as scripting
    
class TestCalView(ChandlerTestCase):
    
    def startTest(self):
    
        # creation
        testView = QAUITestAppLib.UITestView(self.logger)
        # action
        # switch to calendar view
        testView.SwitchToCalView()
        # double click in the calendar view => event creation or selection
        ev = testView.DoubleClickInCalView()
        scripting.User.idle()
        # double click one more time => edit the title
        #testView.DoubleClickInCalView()
        # type a new title and return
        QAUITestAppLib.scripting.User.emulate_typing("Writing tests")
        QAUITestAppLib.scripting.User.emulate_return()
        
        # verification
        # check the detail view of the created event
        ev.Check_DetailView({"displayName":"Writing tests"})

