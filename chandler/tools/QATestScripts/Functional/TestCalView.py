import tools.QAUITestAppLib as QAUITestAppLib
import osaf.framework.scripting as scripting
from i18n.tests import uw
    
# initialization
fileName = "TestCalView.log"
logger = QAUITestAppLib.QALogger(fileName, "TestCalView")

try:
    # creation
    testView = QAUITestAppLib.UITestView(logger)
    # action
    # switch to calendar view
    testView.SwitchToCalView()
    # double click in the calendar view => event creation or selection
    ev = testView.DoubleClickInCalView()
    scripting.User.idle()
    # double click one more time => edit the title
    #testView.DoubleClickInCalView()
    # type a new title and return
    QAUITestAppLib.scripting.User.emulate_typing(uw("Writing tests"))
    QAUITestAppLib.scripting.User.emulate_return()
    
    # verification
    # check the detail view of the created event
    ev.Check_DetailView({"displayName": uw("Writing tests")})

finally:
    # cleaning
    logger.Close()
