## FunctionalList1.py
## Author : Olivier Giroussens
## Description: This test suite runs the 4 basic testcases of generating event, mail, task and note items in chandler
 
import tools.QAUITestAppLib as QAUITestAppLib
import os

functional_dir = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/Functional")

#initialization
fileName = "FunctionalTestSuite.log"
logger = QAUITestAppLib.QALogger(fileName,"FunctionalTestSuite")

#actions
execfile(os.path.join(functional_dir,"TestCreateAccounts.py"))
execfile(os.path.join(functional_dir,"TestNewCollection.py"))
execfile(os.path.join(functional_dir,"TestNewEvent.py"))
execfile(os.path.join(functional_dir,"TestNewMail.py"))
execfile(os.path.join(functional_dir,"TestNewTask.py"))
execfile(os.path.join(functional_dir,"TestNewNote.py"))
execfile(os.path.join(functional_dir,"TestStamping.py"))
execfile(os.path.join(functional_dir,"TestMoveToTrash.py"))
#execfile(os.path.join(functional_dir,"TestDeleteCollection.py"))
#execfile(os.path.join(functional_dir,"TestCalView.py"))
execfile(os.path.join(functional_dir,"TestSwitchingViews.py"))
execfile(os.path.join(functional_dir,"TestExporting.py"))
execfile(os.path.join(functional_dir,"TestFlickr.py"))
execfile(os.path.join(functional_dir,"TestImporting.py"))
execfile(os.path.join(functional_dir,"TestSharing.py"))

#cleaning
logger.Close()
