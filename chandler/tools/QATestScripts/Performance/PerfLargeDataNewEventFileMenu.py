import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "PerfLargeDataNewEventFileMenu.log"
logger = QAUITestAppLib.QALogger(fileName, "Creating new event from the File Menu after large data import") 

try:
    # creation
    QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')

    # action
    event = QAUITestAppLib.UITestItem("Event", logger)
    
    # verification
    event.Check_DetailView({"displayName":"New Event"})
    
finally:
    # cleaning
    logger.Close()
