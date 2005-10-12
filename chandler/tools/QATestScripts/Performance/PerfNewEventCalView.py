import tools.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()
    
#initialization
fileName = "PerfNewEventCalView.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"New Event by double clicking in the cal view for Performance")
testView = QAUITestAppLib.UITestView(logger)

#action
#double click in the calendar view => event creation or selection
ev = testView.DoubleClickInCalView()

#check the detail view of the created event
ev.Check_DetailView({"displayName":"New Event"})

#cleaning
logger.Close()
