import tools.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()

#initialization
fileName = "PerfStampEvent.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"Perf Stamp as Event")

#action
note = QAUITestAppLib.UITestItem("Note", logger)
note.StampAsCalendarEvent(True)

#verification
note.Check_DetailView({"stampEvent":True})

#cleaning
logger.Close()
