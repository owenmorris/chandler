import osaf.framework.scripting.QATestAppLib as QATestAppLib
import os

filePath = os.path.expandvars('$QAPROFILEDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewTask.log"
logger = QATestAppLib.Logger(os.path.join(filePath, fileName),"TestNewTask")
task = QATestAppLib.BaseByUI(__view__, "Task", logger)

#action
task.logger.Start("Setting Task attributes")
task.SetAttr(displayName="a Task", body="task body")
task.logger.Stop()

#verification
task.Check_DetailView({"displayName":"a Task","body":"task body"})
task.logger.Report()

#cleaning
logger.Close()
