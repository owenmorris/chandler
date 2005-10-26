import tools.QAUITestAppLib as QAUITestAppLib

#initialization
fileName = "PerfNewEventFileMenu.log"
logger = QAUITestAppLib.QALogger(fileName, "New Event from File Menu for Performance")

try:
    #action
    event = QAUITestAppLib.UITestItem("Event", logger)
    
    #verification
    event.Check_DetailView({"displayName":"New Event"})
    
finally:
    #cleaning
    logger.Close()
