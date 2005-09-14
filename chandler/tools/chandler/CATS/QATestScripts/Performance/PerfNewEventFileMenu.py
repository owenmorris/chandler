import util.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
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
