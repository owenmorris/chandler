import util.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()
    
#initialization
fileName = "TestRemove.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestRemove")

#actions
note = QAUITestAppLib.UITestItem("Note", logger)
note.Remove()

#actions
col = QAUITestAppLib.UITestItem("Collection", logger)
col.Remove()

#cleaning
logger.Close()
