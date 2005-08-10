import osaf.framework.scripting.QATestAppLib as QATestAppLib
import os

filePath = os.path.expandvars('$QAPROFILEDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()

#initialization
fileName = "FunctionalTestList1.log"
logger = QATestAppLib.Logger(os.path.join(filePath, fileName),"FunctionalTestList1")

#actions
execfile("/home/olivier/Desktop/TestNewEvent.py")
execfile("/home/olivier/Desktop/TestNewMail.py")
execfile("/home/olivier/Desktop/TestNewTask.py")
execfile("/home/olivier/Desktop/TestNewNote.py")

#cleaning
logger.Close()
