import osaf.framework.scripting.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATS_REPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewNote.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewNote")
note = QAUITestAppLib.UITestItem(__view__, "Note", logger)

#action
note.logger.Start("Setting the note attributes")
note.SetAttr(displayName="a Note", body="note body")
note.logger.Stop()

#verification
note.Check_DetailView({"displayName":"a Note","body":"note body"})

#cleaning
logger.Close()
