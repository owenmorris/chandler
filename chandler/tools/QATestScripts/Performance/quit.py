# The fastest way to cleanly quit Chandler
import os
import tools.QAUITestAppLib as QAUITestAppLib
filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()
fileName = "quit.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName), "quit")
logger.Start("quit")
logger.SetChecked(True)
logger.Report("quit")
logger.Close()

