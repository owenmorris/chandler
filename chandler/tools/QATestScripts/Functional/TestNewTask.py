import tools.QAUITestAppLib as QAUITestAppLib
from i18n.tests import uw

# initialization
fileName = "TestNewTask.log"
logger = QAUITestAppLib.QALogger(fileName, "TestNewTask")

try:
    # creation
    task = QAUITestAppLib.UITestItem("Task", logger)
    
    # action
    task.SetAttr(displayName=uw("Task of sending birthday invites"), body=uw("Send birthday invitations"))
    
    # verification
    task.Check_DetailView({"displayName":uw("Task of sending birthday invites"),"body":uw("Send birthday invitations")})

finally:
    # cleaning
    logger.Close()
