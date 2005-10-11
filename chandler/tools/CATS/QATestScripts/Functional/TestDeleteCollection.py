import util.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()
    
#initialization
fileName = "TestDeleteCollection.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestDeleteCollection")

#actions
col = QAUITestAppLib.UITestItem("Collection", logger)
col.DeleteCollection()
#verification
col.Check_CollectionExistance(expectedResult=False)


#cleaning
logger.Close()
