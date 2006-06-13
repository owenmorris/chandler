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
                ("TestAdditionalViews","TestAdditionalViews"),
                ("TestCreateAccounts","TestCreateAccounts"),
                ("TestAllDayEvent","TestAllDayEvent"), 
                ("TestNewCollection","TestNewCollection"),
                ("TestDates","TestDates"),
                ("TestNewEvent","TestNewEvent"),
                ("TestNewMail","TestNewMail"),
                ("TestNewTask","TestNewTask"),
                ("TestNewNote","TestNewNote"),
                ("TestTableSelection","TestTableSelection"),
                ("TestStamping","TestStamping"), 
                ("TestSharing","TestSharing"), 
                ("TestMoveToTrash","TestMoveToTrash"), 
                ("TestDeleteCollection","TestDeleteCollection"),
                ("TestMulti","TestMulti"), 
                ("TestCalView","TestCalView"),
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
    ("TestTableSelection","TestTableSelection"),            #bug 5877 
    ],
    
    'mac':[
    #"TestTableSelection",            # until tested on mac 
    ],
    
    'windows':[
        
    ],
    
    'all':[ #tests to exclude on all platforms       
        ("TestDates","TestDates"), #Chandler not handling daylightsavings bug#5038
        ("TestEditModeOnEnter","TestEditModeOnEnter"), #Chandler bug 5744
        ("TestRemoveFromTrashOnImport","TestRemoveFromTrashOnImport"), #not tested on all platforms yet
        ("TestSwitchTimezone","TestSwitchTimezone"), #new test not yet working
        ("TestSharing","TestSharing"), # bug 5889
        ]
}

tests_to_run = filter(lambda test : test not in exclusions['all'] and test not in exclusions[platform], allTests)
teststring = ''.join(['%s:%s,' % (test, klass) for test, klass in tests_to_run])[:-1]

print teststring.replace(',',',\n')
run_tests(teststring)
