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
fileName = "TestNewEvent.log"
logger = QATestAppLib.TestLogger(os.path.join(filePath, fileName),"TestNewEvent")
event = QATestAppLib.BaseByUI(__view__, "Event", logger)

#action
event.logger.Start("setting calendar attributes")
event.SetAttr(displayName="bar", startDate="09/12/2004", startTime="2:00 PM", location="Office", status="FYI", alarm="30",body="test test",stampTask=True)
event.logger.Stop()

#verification
event.Check_DetailView({"displayName":"bar","startDate":"9/12/04","endDate":"9/12/04","startTime":"2:00 PM","endTime":"3:00 PM","location":"Office","status":"FYI","alarm":"30 minutes","body":"test test","stampTask":True})
event.logger.Report()

#cleaning
logger.Close()
