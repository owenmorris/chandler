## FunctionalList1.py
## Author : Olivier Giroussens
## Description: This test suite runs the 4 basic testcases of generating event, mail, task and note items in chandler
 

import osaf.framework.scripting.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATS_REPORTDIR')
cats_home = os.path.expandvars('$CATS_HOME')
if not os.path.exists(filePath):
    filePath = os.getcwd()


#initialization
fileName = "FunctionalTestList1.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"FunctionalTestList1")

#actions
execfile(os.path.join(cats_home,"QATestScripts/TestNewEvent.py"))
execfile(os.path.join(cats_home,"QATestScripts/TestNewMail.py"))
execfile(os.path.join(cats_home,"QATestScripts/TestNewTask.py"))
execfile(os.path.join(cats_home,"QATestScripts/TestNewNote.py"))

#cleaning
logger.Close()
