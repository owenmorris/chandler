## FunctionalList1.py
## Author : Olivier Giroussens
## Description: This test suite runs the 4 basic testcases of generating event, mail, task and note items in chandler
 
import tools.QAUITestAppLib as QAUITestAppLib
import os, sys

functional_dir = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/Functional")

#initialization
fileName = "FunctionalTestSuite.log"
logger = QAUITestAppLib.QALogger(fileName,"FunctionalTestSuite")

def run_tests(tests):
    for filename in tests:
        try:
            execfile(os.path.join(functional_dir, filename))
        except:
            import traceback
            print "%s failed due to exception" % fileName
            type, value, stack = sys.exc_info()
            traceback.print_exception(type, value, stack, None, sys.stderr)
        
allTests = [
                "TestCreateAccounts.py",
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
                "TestSharing.py",
                "TestBlocks.py",
                ]

if sys.platform == 'win32': 
    platform = 'windows'
elif sys.platform == 'darwin': 
    platform = 'mac'
else:
    platform = 'other'
    
exclusions = {
    'other':(
        "TestCalView.py", #bug 5109 emulate typing starting with unhighlighted text appends rather than overwrites
    ),
    
    'mac':( 
            
    ),
    
    'windows':(
    ),
    
    'all':(        
        "TestAllDayEvent.py", #test not functioning bug#5110
        "TestDates.py", #Chandler not handling daylightsavings bug#5038
    )
}

tests_to_run = filter(lambda test : test not in exclusions['all'] and test not in exclusions[platform], allTests)

try:
    run_tests(tests_to_run)
finally:    
    #cleaning
    logger.Close()
