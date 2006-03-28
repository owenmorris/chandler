import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "PerfLargeDataNewCalendar.log"
logger = QAUITestAppLib.QALogger(fileName, "Creating a new calendar after large data import") 

try:
    # creation
    QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')

    # action
    col = QAUITestAppLib.UITestItem("Collection", logger)
    
    # verification
    col.Check_Collectionexistence("Untitled")
    
finally:
    # cleaning
    logger.Close()
