import osaf.framework.scripting.QATestAppLib as QATestAppLib
import os

filePath = os.path.expandvars('$QAPROFILEDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewNote.log"
logger = QATestAppLib.Logger(os.path.join(filePath, fileName),"TestNewNote")
note = QATestAppLib.BaseByUI(__view__, "Note", logger)

#action
note.logger.Start("Setting the note attributes")
note.SetAttr(displayName="a Note", body="note body")
note.logger.Stop()

#verification
note.Check_DetailView({"displayName":"a Note","body":"note body"})
note.logger.Report()

#cleaning
logger.Close()
