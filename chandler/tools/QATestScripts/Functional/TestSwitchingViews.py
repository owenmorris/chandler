import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "TestSwitchingViews.log"
logger = QAUITestAppLib.QALogger(fileName, "TestSwitchingViews")

try:
    # creation
    testView = QAUITestAppLib.UITestView(logger)
    
    # action
    # switch to all view
    testView.SwitchToAllView()
    # switch to tasks view
    testView.SwitchToTaskView()
    # switch to email view
    testView.SwitchToMailView()
    # switch to calendar view
    testView.SwitchToCalView()
    
finally:
    # cleaning
    logger.Close()
