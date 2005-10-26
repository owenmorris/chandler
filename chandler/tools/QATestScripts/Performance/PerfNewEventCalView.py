import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "PerfNewEventCalView.log"
logger = QAUITestAppLib.QALogger(fileName, "New Event by double clicking in the cal view for Performance")

try:
    # creation
    testView = QAUITestAppLib.UITestView(logger)

    # action
    # double click in the calendar view => event creation or selection
    ev = testView.DoubleClickInCalView()
    
    # verification
    # check the detail view of the created event
    ev.Check_DetailView({"displayName":"New Event"})

finally:
    # cleaning
    logger.Close()
