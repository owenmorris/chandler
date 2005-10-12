import tools.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()
    
#initialization
fileName = "PerfSwitchToAllView.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"Switching to All View for Performance")
testView = QAUITestAppLib.UITestView(logger)

#action
#switch to all view
testView.SwitchToAllView()

#cleaning
logger.Close()
