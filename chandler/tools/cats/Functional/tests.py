#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

import sys

if sys.platform == 'win32': 
    platform = 'windows'
elif sys.platform == 'darwin': 
    platform = 'mac'
else:
    platform = 'other'

allTests = [
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
                ("TestCalView","TestCalView"),
                ("TestReminderProcessing","TestReminderProcessing"),  
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
                ("TestVisibleHours","TestVisibleHours"), 
                ("TestBlocks","TestBlocks"), 
                ]

exclusions = {#tests to exclude on specific platfoms only
    'other':[
            ("TestEditModeOnEnter","TestEditModeOnEnter"), #fails on Gutsy
    ],
    
    'mac':[
     
    ],
    
    'windows':[
        
    ],
    
    'all':[ #tests to exclude on all platforms       
        ("TestDates","TestDates"), #Chandler not handling daylightsavings bug#5038
        ("TestVisibleHours","TestVisibleHours"), # bug 8969
        ("TestNewTask", "TestNewTask"), # relies on removed menu item
        ]
}

tests_to_run = filter(lambda test : test not in exclusions['all'] and test not in exclusions[platform], allTests)
