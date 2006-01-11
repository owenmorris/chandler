import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "PerfLargeDataNewEventCalView.log"
logger = QAUITestAppLib.QALogger(fileName, "Creating a new event in the Cal view after large data import")

try:
    # creation
    testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')

    # action
    # double click in the calendar view => event creation or selection
    ev = testView.DoubleClickInCalView()
    
    # verification
    # check the detail view of the created event
    ev.Check_DetailView({"displayName":"New Event"})
    
finally:
    # cleaning
    logger.Close()
