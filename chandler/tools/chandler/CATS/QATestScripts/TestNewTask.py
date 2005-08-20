import osaf.framework.scripting.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATS_REPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewTask.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewTask")
task = QAUITestAppLib.UITestItem(__view__, "Task", logger)

#action
task.logger.Start("Setting Task attributes")
task.SetAttr(displayName="a Task", body="task body")
task.logger.Stop()

#verification
task.Check_DetailView({"displayName":"a Task","body":"task body"})

#cleaning
logger.Close()
