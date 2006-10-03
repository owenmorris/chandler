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

"""runTests module for running cats tests

This is a module containing with methods defined for running tests
in the cats 0.2+ framework. Not used with cats < 0.2.
"""
__author__ =  'Mikeal Rogers <mikeal@osafoundation.org>'
__version__=  '0.2'

import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.TestOutput import TestOutput
import os, sys
from application import Globals

functional_dir = os.path.join(os.getenv('CHANDLERHOME'),"tools/cats/Functional")
testDebug = Globals.options.chandlerTestDebug
testMask = Globals.options.chandlerTestMask
logFileName = Globals.options.chandlerTestLogfile
filePath = Globals.options.profileDir
if filePath and logFileName:
    logFileName = os.path.join(filePath, logFileName)

     
def checkRepo(logger):
    """Check for coruption in the repository"""
    logger.addComment('Checking for repository corruption')
    QAUITestAppLib.App_ns.itsView.check()


def run_test(logger, paramSet):
    filenameAndTest = paramSet.split(':')
    
    #assume file name and and test name are the same if only one given
    if len(filenameAndTest) < 2: filenameAndTest.append(filenameAndTest[0])
        
    teststring = 'from tools.cats.Functional.%s import %s' % (filenameAndTest[0], filenameAndTest[1])
    exec(compile(teststring, '%s/%s.py' % (functional_dir, filenameAndTest[0]), 'exec'))
    teststring = 'test = %s(name=\'%s\', logger=logger)' % (filenameAndTest[0], filenameAndTest[1])
    exec(compile(teststring, '%s/%s.py' % (functional_dir, filenameAndTest[0]), 'exec'))
    test.runTest()
    if logger.debug == 2: checkRepo(logger)

def run_test_wrapped(logger, paramSet):
    try:
        run_test(logger, paramSet)
    except:
        logger.traceback()
    
def run_tests(tests, debug=testDebug, mask=testMask, logName=logFileName):
    """Method to execute cats tests, must be in Functional directory."""
    
    logger = TestOutput(stdout=True, debug=debug, mask=mask, logName=logName) 
    logger.startSuite(name='ChandlerFunctionalTestSuite')
    
    # We'll normally run individual tests with an exception wrapper; 
    # --catch=never will turn it off, so that a debugger can stop on 
    # uncaught exceptions.
    runner = Globals.options.catch != 'never' and run_test_wrapped or run_test
    for paramSet in tests.split(','):
        runner(logger, paramSet)

    if logger.debug < 2: checkRepo(logger)
    logger.endSuite()
    if logger.debug == 0:
        logger.easyReadSummary()
    else:
        logger.summary()
    logger.simpleSummary()
    logger.tinderOutput()
    import osaf.framework.scripting as scripting
    scripting.app_ns().root.Quit()
 
def run_perf_tests(tests, debug=testDebug, mask=testMask, logName=logFileName):
    """Method to execute cats tests, must be in Performance directory"""

    logger = TestOutput(stdout=True, debug=0, logName=logName)
    logger.startSuite(name='ChandlerTestSuite')
    for paramSet in tests.split(','):
        try:
            filenameAndTest = paramSet.split(':')
            
            #assume file name and and test name are the same if only one given
            if len(filenameAndTest) < 2: filenameAndTest.append(filenameAndTest[0])
            
            teststring = 'from tools.cats.Performance.%s import %s' % (filenameAndTest[0], filenameAndTest[1])
            exec(compile(teststring, '', 'exec'))
            teststring = 'test = %s(name=\'%s\', logger=logger)' % (filenameAndTest[1], filenameAndTest[1])
            exec(compile(teststring, '', 'exec'))
            test.runTest()
            if logger.debug == 2: checkRepo(logger)
        except:
            logger.traceback()
            
    logger.endSuite()
    if logger.debug == 0:
        logger.easyReadSummary()
    else:
        logger.summary()
    logger.simpleSummary()
    logger.tinderOutput()
    if logger.debug < 2: checkRepo(logger)
    logger.endSuite()
    import osaf.framework.scripting as scripting
    scripting.app_ns().root.Quit()
