## FunctionalList1.py
## Author : Olivier Giroussens
## Description: This test suite runs the 4 basic testcases of generating event, mail, task and note items in chandler
 

import osaf.framework.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
cats_home = os.path.expandvars('$CATSHOME')
if not os.path.exists(filePath):
    filePath = os.getcwd()


#initialization
fileName = "FunctionalTestSuite.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"FunctionalTestSuite")

#actions
execfile(os.path.join(cats_home,"QATestScripts/Functional/TestCreateAccounts.py"))
execfile(os.path.join(cats_home,"QATestScripts/Functional/TestNewCollection.py"))
execfile(os.path.join(cats_home,"QATestScripts/Functional/TestNewEvent.py"))
execfile(os.path.join(cats_home,"QATestScripts/Functional/TestNewMail.py"))
execfile(os.path.join(cats_home,"QATestScripts/Functional/TestNewTask.py"))
execfile(os.path.join(cats_home,"QATestScripts/Functional/TestNewNote.py"))
execfile(os.path.join(cats_home,"QATestScripts/Functional/TestCalView.py"))
execfile(os.path.join(cats_home,"QATestScripts/Functional/TestSwitchingViews.py"))
execfile(os.path.join(cats_home,"QATestScripts/Functional/TestExporting.py"))
#cleaning
logger.Close()
