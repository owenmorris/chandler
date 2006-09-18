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
 
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.TestOutput import TestOutput
from tools.cats.framework.runTests import run_tests
import os, sys

functional_dir = os.path.join(os.getenv('CHANDLERHOME'),"tools/cats/Functional")

#initialization

allTests = [
                ("TestCreateAccounts","TestCreateAccounts"),
                ("TestAllDayEvent","TestAllDayEvent"), 
                ("TestNewCollection","TestNewCollection"),
                ("TestDates","TestDates"),
                ("TestNewEvent","TestNewEvent"),
                ("TestNewMail","TestNewMail"),
                ("TestNewTask","TestNewTask"),
                ("TestNewNote","TestNewNote"),
                ("TestTriageSectioning","TestTriageSectioning"),
                ("TestTableSelection","TestTableSelection"),
                ("TestStamping","TestStamping"), 
                ("TestSharing","TestSharing"), 
                ("TestMoveToTrash","TestMoveToTrash"), 
                ("TestDeleteCollection","TestDeleteCollection"),
                ("TestMulti","TestMulti"), 
                # disabling TestCalView because of sporadic failures on Linux,
                # bug 6733.  The problems are probably related to bug 6737,
                # odd keystroke handling in the calendar, so hopefully fixing
                # bug 6737 will also fix bug 6733 and this can be re-enabled.
                #("TestCalView","TestCalView"),
                ("TestRecurrenceImporting","TestRecurrenceImporting"), 
                ("TestRecurringEvent","TestRecurringEvent"),  
                ("TestSwitchingViews","TestSwitchingViews"),
                ("TestExporting","TestExporting"),
                ("TestFlickr","TestFlickr"),
                ("TestImporting","TestImporting"),
                ("TestImportOverwrite","TestImportOverwrite"),
                ("TestCertstoreView","TestCertstoreView"),
                ("TestEditModeOnEnter","TestEditModeOnEnter"),
                ("TestEventStacking","TestEventStacking"),
                ("TestRemoveFromTrashOnImport","TestRemoveFromTrashOnImport"),
                ("TestEnableTimezones","TestEnableTimezones"),
                ("TestSwitchTimezone","TestSwitchTimezone"),
                ("TestSubscribe", "TestSubscribe"),
                ("TestBlocks","TestBlocks"), 
                ]

if sys.platform == 'win32': 
    platform = 'windows'
elif sys.platform == 'darwin': 
    platform = 'mac'
else:
    platform = 'other'
    
exclusions = {#tests to exclude on specific platfoms only
    'other':[
    ],
    
    'mac':[
     
    ],
    
    'windows':[
        
    ],
    
    'all':[ #tests to exclude on all platforms       
        ("TestDates","TestDates"), #Chandler not handling daylightsavings bug#5038
        ("TestEditModeOnEnter","TestEditModeOnEnter"), #Chandler bug 5744
        ("TestSubscribe", "TestSubscribe"),# new test not yet working
        ]
}

tests_to_run = filter(lambda test : test not in exclusions['all'] and test not in exclusions[platform], allTests)
teststring = ''.join(['%s:%s,' % (test, klass) for test, klass in tests_to_run])[:-1]

run_tests(teststring)
