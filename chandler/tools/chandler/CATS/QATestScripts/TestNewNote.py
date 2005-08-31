import osaf.framework.scripting.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewNote.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewNote")
note = QAUITestAppLib.UITestItem(app_ns().itsView, "Note", logger)

#action
note.logger.Start("Setting the note attributes")
note.SetAttr(displayName="A note to myself about filing taxes", body="FILE TAXES!")
note.logger.Stop()

#verification
note.Check_DetailView({"displayName":"A note to myself about filing taxes","body":"FILE TAXES!"})

#cleaning
logger.Close()
