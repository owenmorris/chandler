## FunctionalList1.py
## Author : Olivier Giroussens
## Description: This test suite runs the 4 basic testcases of generating event, mail, task and note items in chandler
 
import tools.QAUITestAppLib as QAUITestAppLib
import os, sys

functional_dir = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/Functional")

#initialization
fileName = "FunctionalTestSuite.log"
logger = QAUITestAppLib.QALogger(fileName,"FunctionalTestSuite")

def exclude(fullList, excludeList):
    for item in excludeList:
        if item in fullList:
            fullList.remove(item)
    return fullList

def run_tests(tests):
    for filename in tests:
        execfile(os.path.join(functional_dir, filename))
        
allTests = ["TestCreateAccounts.py",
                        "TestAllDayEvent.py", 
                        "TestNewCollection.py",
                        "TestDates.py", 
                        "TestNewEvent.py",
                        "TestNewMail.py",
                        "TestNewTask.py",
                        "TestNewNote.py",
                        "TestStamping.py", 
                        "TestMoveToTrash.py", 
                        "TestDeleteCollection.py",
                        "TestNewCollNoteStampMulti.py", 
                        "TestCalView.py",
                        "TestRecurrenceImporting.py", 
                        "TestRecurringEvent.py",  
                        "TestSwitchingViews.py",
                        "TestExporting.py",
                        "TestFlickr.py",
                        "TestImporting.py",
                        "TestImportOverwrite.py",
                        "TestSharing.py"]

exclude_on_linux = [                                          
                                        ]
exclude_on_mac = [ 
                                        ]
exclude_on_windows = [ 
                                        ]
exclude_on_all = [
                                        "TestMoveToTrash.py", #bug # 5150  
                                        "TestStamping.py", #Chandler bug#5097
                                        "TestNewCollNoteStampMulti.py", #Chandler bug #5097
                                        "TestAllDayEvent.py", #test not functioning bug#5110
                                        "TestDates.py", #Chandler not handling daylightsavings bug#5038
                                        "TestRecurrenceImporting.py", #Chandler bug #5116
                                    ]

tests_to_run = exclude(allTests, exclude_on_all)
if sys.platform == "linux2" : tests_to_run = exclude(tests_to_run, exclude_on_linux)
if sys.platform == "darwin" : tests_to_run = exclude(tests_to_run, exclude_on_mac)
if sys.platform == "win32" : tests_to_run = exclude(tests_to_run, exclude_on_windows)

try:
    run_tests(tests_to_run)
finally:    
    #cleaning
    logger.Close()
