import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "TestNewTask.log"
logger = QAUITestAppLib.QALogger(fileName, "TestNewTask")

try:
    # creation
    task = QAUITestAppLib.UITestItem("Task", logger)
    
    # action
    task.SetAttr(displayName="Task of sending birthday invites", body="Send birthday invitations")
    
    # verification
    task.Check_DetailView({"displayName":"Task of sending birthday invites","body":"Send birthday invitations"})

finally:
    # cleaning
    logger.Close()
