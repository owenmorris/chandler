## FunctionalList1.py
## Author : Olivier Giroussens
## Description: This test suite runs the 4 basic testcases of generating event, mail, task and note items in chandler
 
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.TestOutput import TestOutput
import os, sys

functional_dir = os.path.join(os.getenv('CHANDLERHOME'),"tools/cats/Functional")

#initialization 

def run_tests(tests):
    
    logger = TestOutput(stdout=True, debug=4)
    logger.startSuite(name='ChandlerTestSuite')
    for paramSet in tests.split(','):
        try:
            filenameAndTest = paramSet.split(':')
            
            #dan added this as a convenience, I'm already tired of typing this stuff twice
            if len(filenameAndTest) < 2: filenameAndTest.append(filenameAndTest[0])
                
            teststring = 'from tools.cats.Functional.%s import %s' % (filenameAndTest[0], filenameAndTest[1])
            exec(compile(teststring, '%s/%s.py' % (functional_dir, filenameAndTest[0]), 'exec'))
            teststring = 'test = %s(name=\'%s\', logger=logger)' % (filenameAndTest[0], filenameAndTest[1])
            exec(compile(teststring, '%s/%s.py' % (functional_dir, filenameAndTest[0]), 'exec'))
            test.runTest()
        except:
            logger.traceback()

    logger.endSuite()
    import osaf.framework.scripting as scripting
    scripting.app_ns().root.Quit()
 
def run_perf_tests(tests):

    logger = TestOutput(stdout=True, debug=4)
    logger.startSuite(name='ChandlerTestSuite')
    for paramSet in tests.split(','):
        try:
            filenameAndTest = paramSet.split(':')
            
            #dan added this as a convenience, I'm already tired of typing this stuff twice
            if len(filenameAndTest) < 2: filenameAndTest.append(filenameAndTest[0])
            
            teststring = 'from tools.cats.Performance.%s import %s' % (filenameAndTest[0], filenameAndTest[1])
            exec(compile(teststring, '', 'exec'))
            teststring = 'test = %s(name=\'%s\', logger=logger)' % (filenameAndTest[1], filenameAndTest[1])
            exec(compile(teststring, '', 'exec'))
            test.runTest()
        except:
            logger.traceback()

    logger.endSuite()
    import osaf.framework.scripting as scripting
    scripting.app_ns().root.Quit()