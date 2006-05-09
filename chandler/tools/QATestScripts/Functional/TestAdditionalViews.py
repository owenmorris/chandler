import tools.QAUITestAppLib as QAUITestAppLib

logger = QAUITestAppLib.QALogger("TestAdditionalViews.log","AdditionalViews")

# These tests help find problems with widget creation and destruction
# that occurs when the user interface is exercised. If a problem occurs
# you should see a traceback.
try:
    logger.Start('AdditionalViews')
    logger.SetChecked(True)
    app_ns().root.AddRepositoryView()
    logger.ReportPass('AddRepositoryView')
    app_ns().root.AddCPIAView()
    logger.ReportPass('AddCPIAView')
    logger.Stop()
finally:
    if len(logger.passedList) < 2:
        logger.ReportFailure('AdditionalViews')
    logger.Report('AdditionalViews')
    logger.Close()
