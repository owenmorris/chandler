import tools.QAUITestAppLib as QAUITestAppLib

#initialization
fileName = "PerfSwitchToAllView.log"
logger = QAUITestAppLib.QALogger(fileName, "Switching to All View for Performance")

try:
    # creation
    testView = QAUITestAppLib.UITestView(logger)
    
    # action
    # switch to all view
    testView.SwitchToAllView()

    # verification
    # for now, we just assume it worked

finally:
    # cleaning
    logger.Close()
