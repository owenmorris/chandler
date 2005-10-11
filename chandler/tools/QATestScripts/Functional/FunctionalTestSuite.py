## FunctionalList1.py
## Author : Olivier Giroussens
## Description: This test suite runs the 4 basic testcases of generating event, mail, task and note items in chandler
 
import util.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
functional_dir = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/Functional")
if not filePath:
    filePath = os.getcwd()


#initialization
fileName = "FunctionalTestSuite.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"FunctionalTestSuite")

#actions
execfile(os.path.join(functional_dir,"TestCreateAccounts.py"))
execfile(os.path.join(functional_dir,"TestNewCollection.py"))
execfile(os.path.join(functional_dir,"TestNewEvent.py"))
execfile(os.path.join(functional_dir,"TestNewMail.py"))
execfile(os.path.join(functional_dir,"TestNewTask.py"))
execfile(os.path.join(functional_dir,"TestNewNote.py"))
execfile(os.path.join(functional_dir,"TestStamping.py"))
execfile(os.path.join(functional_dir,"TestMoveToTrash.py"))
execfile(os.path.join(functional_dir,"TestDeleteCollection.py"))
execfile(os.path.join(functional_dir,"TestCalView.py"))
execfile(os.path.join(functional_dir,"TestSwitchingViews.py"))
execfile(os.path.join(functional_dir,"TestExporting.py"))

#cleaning
logger.Close()
