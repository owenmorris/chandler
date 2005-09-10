import osaf.framework.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()

#initialization
fileName = "PerfNewEventFileMenu.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"New Event from File Menu for Performance")

#action
event = QAUITestAppLib.UITestItem("Event", logger)

#verification
event.Check_DetailView({"displayName":"New Event"})


#cleaning
logger.Close()
