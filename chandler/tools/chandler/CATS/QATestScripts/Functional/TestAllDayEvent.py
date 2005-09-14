import util.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()

#initialization
fileName = "TestAllDayEvent.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestAllDayEvent")
event = QAUITestAppLib.UITestItem("Event", logger)

#action
event.logger.Start("set the event to all-day")
event.SetAllDay(True)
event.logger.Stop()

#verification
event.Check_DetailView({"AllDay":True})
event.Check_Object({"AllDay":True})

#cleaning
logger.Close()
