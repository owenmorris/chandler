#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

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
    QAUITestAppLib.App_ns.itsView.check()
        
allTests = [
                "TestCreateAccounts.py",
                "TestAllDayEvent.py", 
                "TestNewCollection.py",
                "TestDates.py", 
                "TestNewEvent.py",
                "TestNewMail.py",
                "TestNewTask.py",
                "TestNewNote.py",
                "TestTableSelection.py",
                "TestStamping.py", 
                "TestSharing.py", 
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
                "TestCertstoreView.py",
                "TestEditModeOnEnter.py",
                "TestEventStacking.py",
                "TestRemoveFromTrashOnImport.py",
                "TestEnableTimezones.py",
                "TestSwitchTimezone.py",
                "TestSubscribe.py",
                "TestBlocks.py", 
                "TestCleanRepo.py", 
                ]

if sys.platform == 'win32': 
    platform = 'windows'
elif sys.platform == 'darwin': 
    platform = 'mac'
else:
    platform = 'other'
    
exclusions = {#tests to exclude on specific platfoms only
    'other':(
    ),
    
    'mac':( 
    "TestTableSelection.py",            # until tested on mac 
    ),
    
    'windows':(
    ),
    
    'all':( #tests to exclude on all platforms       
        "TestDates.py", #Chandler not handling daylightsavings bug#5038
        "TestEditModeOnEnter.py", #Chandler bug 5744
        "TestRemoveFromTrashOnImport.py", #not tested on all platforms yet
        "TestSwitchTimezone.py", #new test not yet working
        "TestSubscribe.py", # new test not yet working
        )
}

tests_to_run = filter(lambda test : test not in exclusions['all'] and test not in exclusions[platform], allTests)

try:
    run_tests(tests_to_run)
finally:    
    #cleaning
    logger.Close()
