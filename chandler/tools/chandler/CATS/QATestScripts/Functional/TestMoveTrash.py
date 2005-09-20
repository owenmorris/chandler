import util.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()
    
#initialization
fileName = "TestMoveTrash.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestMoveTrash")

#actions
note = QAUITestAppLib.UITestItem("Note", logger)
note.SetAttr(displayName="A note to move to Trash", body="TO MOVE TO TRASH")
note.MoveToTrash()
#verification
note.Check_Collection("Trash")

#actions
col = QAUITestAppLib.UITestItem("Collection", logger)
col.MoveToTrash()
#verification
col.Check_Collection("Trash")

#cleaning
logger.Close()
