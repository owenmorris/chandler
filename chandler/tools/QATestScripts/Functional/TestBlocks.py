import tools.QAUITestAppLib as QAUITestAppLib

logger = QAUITestAppLib.QALogger("TestBlocks.log","TestBlocks")

# These tests help find problems with widget creation and destruction
# that occurs when the user interface is exercised. If a problem occurs
# you should see a traceback.
try:
    logger.Start('TestBlocks')
    logger.SetChecked(True)
    app_ns().root.ChooseCPIATestMainView()
    logger.ReportPass('CPIATestMainView')
    app_ns().root.ChooseChandlerMainView()
    logger.ReportPass('ChandlerMainView')
    app_ns().root.ReloadParcels()
    logger.ReportPass('ReloadParcels')
    logger.Stop()
finally:
    if len(logger.passedList) < 3:
        logger.ReportFailure('TestBlocks')
    logger.Report('TestBlocks')
    logger.Close()