import tools.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()

# initialization
fileName = "PerfStampEvent.log"
logger = QAUITestAppLib.QALogger(fileName, "Perf Stamp as Event")

try:
    # creation
    note = QAUITestAppLib.UITestItem("Note", logger)

    # action
    note.StampAsCalendarEvent(True)
    
    # verification
    note.Check_DetailView({"stampEvent":True})

finally:
    # cleaning
    logger.Close()
