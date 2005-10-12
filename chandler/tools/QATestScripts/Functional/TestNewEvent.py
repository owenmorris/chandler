import tools.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()

#initialization
fileName = "TestNewEvent.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewEvent")
event = QAUITestAppLib.UITestItem("Event", logger)

#action
event.SetAttr(displayName="Birthday Party", startDate="09/12/2004", startTime="6:00 PM", location="Club101", status="FYI",body="This is a birthday party invitation",timeZone="US/Central", recurrence="Daily", recurrenceEnd="9/14/2005")

#verification
event.Check_DetailView({"displayName":"Birthday Party","startDate":"9/12/04","endDate":"9/12/04","startTime":"6:00 PM","endTime":"7:00 PM","location":"Club101","status":"FYI","body":"This is a birthday party invitation","timeZone":"US/Central","recurrence":"Daily", "recurrenceEnd":"9/14/05"})

#cleaning
logger.Close()
