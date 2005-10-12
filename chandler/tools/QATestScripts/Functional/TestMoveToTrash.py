import tools.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()
    
#initialization
fileName = "TestMoveToTrash.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestMoveToTrash")

#actions
note = QAUITestAppLib.UITestItem("Note", logger)
note.SetAttr(displayName="A note to move to Trash", body="TO MOVE TO TRASH")
note.MoveToTrash()
#verification
note.Check_ItemInCollection("Trash")
note.Check_ItemInCollection("All", expectedResult=False)

#cleaning
logger.Close()
