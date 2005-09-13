import osaf.framework.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewNote.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewNote")
note = QAUITestAppLib.UITestItem("Note", logger)

#action
note.SetAttr(displayName="A note to myself about filing taxes", body="FILE TAXES!")

#verification
note.Check_DetailView({"displayName":"A note to myself about filing taxes","body":"FILE TAXES!"})

#cleaning
logger.Close()
