import osaf.framework.scripting.QATestAppLib as QATestAppLib
import os
import string

login = os.getlogin()
plateform = os.uname()[0]
if not string.find(plateform,"Linux") == -1:
    filePath = "/home/%s" %login
elif not string.find(plateform,"Darwin") == -1:
    filePath = "/Users/%s" %login
elif not string.find(plateform,"Windows") == -1:
    filePath = "C:\temp"
else:
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewNote.log"
logger = QATestAppLib.TestLogger(os.path.join(filePath, fileName),"TestNewNote")
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
