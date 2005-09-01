import osaf.framework.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestSwitchingViews.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestSwitchingViews")
testView = QAUITestAppLib.UITestView(logger)

#action
#switch to calendar view
testView.SwitchToCalView()
#switch to all view
testView.SwitchToAllView()
#switch to tasks view
testView.SwitchToTaskView()
#switch to email view
testView.SwitchToMailView()

#cleaning
logger.Close()
