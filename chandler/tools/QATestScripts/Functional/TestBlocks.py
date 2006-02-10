import tools.QAUITestAppLib as QAUITestAppLib

logger = QAUITestAppLib.QALogger("TestBlocks.log","TestBlocks")

# These tests help find problems with widget creation and destruction
# that occurs when the user interface is exercised. If a problem occurs
# you should see a traceback.
try:
    app_ns().root.ChooseCPIATestMainView()
    app_ns().root.ChooseChandlerMainView()
    app_ns().root.ReloadParcels()

finally:
    logger.Close()