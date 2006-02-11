import tools.QAUITestAppLib as QAUITestAppLib

logger = QAUITestAppLib.QALogger("TestBlocks.log","TestBlocks")

# These tests help find problems with widget creation and destruction
# that occurs when the user interface is exercised. If a problem occurs
# you should see a traceback.
try:
    logger.Start('TestBlocks')
    logger.SetChecked(True)
    try:
        app_ns().root.ChooseCPIATestMainView()
        logger.ReportPass('CPIATestMainView')
    except:
        logger.ReportFailure('CPIATestMainView')
    try:
        app_ns().root.ChooseChandlerMainView()
        logger.ReportPass('ChandlerMainView')
    except:
        logger.ReportFailure('ChandlerMainView')
    try:
        app_ns().root.ReloadParcels()
        logger.ReportPass('ReloadParcels')
    except:
        logger.ReportFailure('ReloadParcels')
    logger.Stop()
finally:
    logger.Report('TestBlocks')
    logger.Close()