import util.QAUITestAppLib as QAUITestAppLib

import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewCollection.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewCollection")


#actions
col = QAUITestAppLib.UITestItem("Collection", logger)
col.SetDisplayName("Meeting")
#verification
col.Check_CollectionExistance()

#actions
note = QAUITestAppLib.UITestItem("Note", logger)
note.AddCollection("Meeting")
#verification
note.Check_ItemInCollection("Meeting")

#cleaning
logger.Close()
