## FunctionalList1.py
## Author : Olivier Giroussens
## Description: This test suite runs the 4 basic testcases of generating event, mail, task and note items in chandler
 
import tools.QAUITestAppLib as QAUITestAppLib
import os

functional_dir = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/Functional")

#initialization
fileName = "FunctionalTestSuite.log"
logger = QAUITestAppLib.QALogger(fileName,"FunctionalTestSuite")

def run_tests(*tests):
    for filename in tests:
        execfile(os.path.join(functional_dir, filename))

run_tests("TestCreateAccounts.py",
          "TestNewCollection.py",
          "TestNewEvent.py",
          "TestNewMail.py",
          "TestNewTask.py",
          "TestNewNote.py",
          "TestStamping.py",
          "TestMoveToTrash.py",
          #"TestDeleteCollection.py",
          "TestNewCollNoteStampMulti.py",
          "TestCalView.py",
          "TestSwitchingViews.py",
          "TestExporting.py",
          "TestFlickr.py",
          "TestImporting.py",
          "TestSharing.py")


#cleaning
logger.Close()
