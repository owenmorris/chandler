import tools.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewTask.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewTask")
task = QAUITestAppLib.UITestItem("Task", logger)

#action
task.SetAttr(displayName="Task of sending birthday invites", body="Send birthday invitations")

#verification
task.Check_DetailView({"displayName":"Task of sending birthday invites","body":"Send birthday invitations"})

#cleaning
logger.Close()
