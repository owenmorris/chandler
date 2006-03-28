import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "PerfNewCalendar.log"
logger = QAUITestAppLib.QALogger(fileName, "Test New Calendar for performance")

try:
    # action
    col = QAUITestAppLib.UITestItem("Collection", logger)
    
    # verfication
    col.Check_Collectionexistence("Untitled")
    
finally:
    # cleaning
    logger.Close()
