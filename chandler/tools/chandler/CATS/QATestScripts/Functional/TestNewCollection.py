import osaf.framework.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewCollection.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewCollection")
col = QAUITestAppLib.UITestItem("Collection", logger)

#action
col.SetDisplayName("Meeting")

col.Check_Sidebar({"displayName":"Meeting"})

note = QAUITestAppLib.UITestItem("Note", logger)
note.SetCollection("Meeting")


#cleaning
logger.Close()
