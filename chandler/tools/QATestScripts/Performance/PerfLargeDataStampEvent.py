import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "PerfLargeDataStampEvent.log"
logger = QAUITestAppLib.QALogger(fileName, "Stamping after large data import") 

try:
    # creation
    QAUITestAppLib.UITestView(logger, u'Generated3000.ics')

    # action
    note = QAUITestAppLib.UITestItem("Note", logger)
    note.StampAsCalendarEvent(True)
    
    # verification
    note.Check_DetailView({"stampEvent":True})
    
finally:
    # cleaning
    logger.Close()
