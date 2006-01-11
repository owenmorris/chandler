import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "PerfLargeDataiSwitchToAllView.log"
logger = QAUITestAppLib.QALogger(fileName, "Switching view after importing large data") 

try:
    # creation
    testView = QAUITestAppLib.UITestView(logger)#, u'Generated3000.ics')

    # action
    # switch to all view
    testView.SwitchToAllView()

finally:
    # cleaning
    logger.Close()
