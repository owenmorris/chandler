import osaf.framework.scripting.QATestAppLib as QATestAppLib
import os

filePath = os.path.expandvars('$QAPROFILEDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()

#initialization
fileName = "TestNewEvent.log"
logger = QATestAppLib.Logger(os.path.join(filePath, fileName),"TestNewEvent")
event = QATestAppLib.BaseByUI(__view__, "Event", logger)

#action
event.logger.Start("setting calendar attributes")
event.SetAttr(displayName="bar", startDate="09/12/2004", startTime="6:00 PM", location="Office", status="FYI",body="test test")
event.logger.Stop()

#verification
event.Check_DetailView({"displayName":"bar","startDate":"9/12/04","endDate":"9/12/04","startTime":"6:00 PM","endTime":"7:00 PM","location":"Office","status":"FYI","body":"test test"})
event.logger.Report()

#cleaning
logger.Close()
