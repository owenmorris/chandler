import osaf.framework.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestCalView.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestCalView")
testView = QAUITestAppLib.UITestView(logger)

#action
#switch to calendar view
testView.SwitchToCalView()
#double click in the calendar view => event creation or selection
ev = testView.DoubleClickInCalView()
#double click one more time => edit the title
testView.DoubleClickInCalView()
#type a new title and return
QAUITestAppLib.scripting.User.emulate_typing("foo")
QAUITestAppLib.scripting.User.emulate_return()

#check the detail view of the created event
ev.Check_DetailView({"displayName":"foo"})

#cleaning
logger.Close()
