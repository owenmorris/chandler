import osaf.framework.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "PerfNewCalendar.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"Test New Calendar for performance")

#action
col = QAUITestAppLib.UITestItem("Collection", logger)

#action
col.Check_Sidebar({"displayName":"Untitled"})


#cleaning
logger.Close()
