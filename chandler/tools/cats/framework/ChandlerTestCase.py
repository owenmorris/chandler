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

"""ChandlerTestCase class for testing chandler

This is a module containing one class, ChandlerTestCase, which is
used for writing test class for Chandler.
"""
__author__ =  'Mikeal Rogers <mikeal@osafoundation.org>'
__version__=  '0.2'

import osaf.pim as pim
from datetime import date
import osaf.framework.scripting as scripting

class ChandlerTestCase:
    """ChandlerTestCase class for testing chandler"""
    
    def __init__(self, name, logger, recurrence=1, appendVar='', printAppend='', appendDict={}, appendList=[]):
        """
        Instantiation method.
        
        Required Arguments:
        name:   str        -- Name of test.
        logger: TestOutput -- Instance of TestOuput object.   
        
        Keyword Arguments:
        recurrence:  int  -- Amount of times you wish to run self.recurringTest method in test classes,
                             used by TestObject
        appendDict:  dict -- Used by test class writers when executing tests and writing self.startTest methods.
                             Currently not needed unless you run test classes in threaded stress testing env.
        appendList:  list -- List used for appends by test class writers.
        appendVar:   str  -- String used for conveinient test class appends.
        printAppend: str  -- Used by TestObject.printOut method for appending to print. Useful when appending
                             thread number in stress testing framework.
        
        """
        
        self.results = []
        self.resultNames = []
        self.resultComments = []
        self.recurrence = recurrence
        self.appendVar = str(appendVar)
        self.printAppend = printAppend
        self.appendDict = appendDict
        self.appendList = appendList
        self.logger = logger
        self.name = name
        self.scripting = scripting
        self.app_ns = scripting.app_ns()
        
    def runTest(self):
        """
        Method to execute all test functions in order.
        """
        self.logger.startTest(name=self.name)
        self.startTest()
        self.logger.endTest()
