import osaf.framework.scripting.QATestAppLib as QATestAppLib
import os

filePath = os.path.expandvars('$QAPROFILEDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()

#initialization
fileName = "FunctionalTestList1.log"
logger = QATestAppLib.Logger(os.path.join(filePath, fileName),"FunctionalTestList1")

#actions
execfile("/home/olivier/qa/chandler/CATS/QATestScripts/TestNewEvent.py")
execfile("/home/olivier/qa/chandler/CATS/QATestScripts/TestNewMail.py")
execfile("/home/olivier/qa/chandler/CATS/QATestScripts/TestNewTask.py")
execfile("/home/olivier/qa/chandler/CATS/QATestScripts/TestNewNote.py")

#cleaning
logger.Close()
