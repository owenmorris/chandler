import osaf.framework.scripting.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATS_REPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()

#initialization
fileName = "TestNewEvent.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewEvent")
event = QAUITestAppLib.UITestItem(__view__, "Event", logger)

#action
event.logger.Start("setting calendar attributes")
event.SetAttr(displayName="bar", startDate="09/12/2004", startTime="6:00 PM", location="Office", status="FYI",body="test test")
event.logger.Stop()

#verification
event.Check_DetailView({"displayName":"bar","startDate":"9/12/04","endDate":"9/12/04","startTime":"6:00 PM","endTime":"7:00 PM","location":"Office","status":"FYI","body":"test test"})

#cleaning
logger.Close()
