import osaf.framework.scripting.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATS_REPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestCalView.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestCalView")
testView = QAUITestAppLib.UITestView(__view__, logger)

#action
#switch to calendar view
testView.SwitchToCalView()
#double click in the calendar view => event creation or selection
ev = testView.DoubleClickInCalView()
#double click one more time => edit the title
testView.DoubleClickInCalView()
#type a new title and return
Type("foo")
KeyboardReturn()

#check the detail view of the created event
ev.Check_DetailView({"displayName":"foo"})

#cleaning
logger.Close()
