import util.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()
    
#initialization
fileName = "TestSwitchingViews.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestSwitchingViews")
testView = QAUITestAppLib.UITestView(logger)

#action
#switch to all view
testView.SwitchToAllView()
#switch to tasks view
testView.SwitchToTaskView()
#switch to email view
testView.SwitchToMailView()
#switch to calendar view
testView.SwitchToCalView()

#cleaning
logger.Close()
