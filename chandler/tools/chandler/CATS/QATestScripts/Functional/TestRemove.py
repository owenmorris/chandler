import util.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()
    
#initialization
fileName = "TestRemove.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestRemove")

#actions
col = QAUITestAppLib.UITestItem("Collection", logger)
col.Remove()
#verification
col.Check_CollectionExistance(expectedResult=False)


#cleaning
logger.Close()
