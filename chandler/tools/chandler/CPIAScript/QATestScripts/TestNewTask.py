import osaf.framework.scripting.QATestAppLib as QATestAppLib
import os
import string

login = os.getlogin()
plateform = os.uname()[0]
if not string.find(plateform,"Linux") == -1:
    filePath = "/home/%s" %login
elif not string.find(plateform,"Darwin") == -1:
    filePath = "/Users/%s" %login
elif not string.find(plateform,"Windows") == -1:
    filePath = "C:\temp"
else:
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewTask.log"
logger = QATestAppLib.TestLogger(os.path.join(filePath, fileName),"TestNewTask")
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
