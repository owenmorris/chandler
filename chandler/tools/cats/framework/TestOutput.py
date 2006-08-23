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

"""TestOutput class for cats 0.2

This is a module contains a major class, TestOutput,
which is used for string output, timeing, and report->action->test->suite
encapsulation.
"""
__author__ =  'Mikeal Rogers <mikeal@osafoundation.org>'
__version__=  '0.2'

from datetime import datetime as dtime
import copy
import sys
import os.path
import time 

class datetime(dtime):
    """Class for overriding datetime's normal string method"""
    def __str__(self):
        """Method to return more parsable datetime string"""
        return '%s:%s:%s:%s' % (self.hour, self.minute, self.second, self.microsecond)

class TestOutput:
    """
    Test output and timing class.
    """
    def __init__(self, logName=None, debug=1, mask=2, stdout=None):
        """Instantiation method
        
        Keyword Arguments:
        logName: str  -- Name of the logfile
        debug:   int  -- Debug level: 
                0 = show only failures
                1 = show pass and fail
                2 = show pass and fail and check repository after each test
        mask:    int  -- Masking level
                0 = show everything
                1 = don't show report 
                2 = don't show report, action
                3 = don't show report, action, test
        stdout   bool -- Switch to turn on stdout output
        """
        self.debug = int(debug)
        self.mask = int(mask)
        self.logName = logName
        self.suiteList = []
        self.testList = []
        self.actionList = []
        self.performanceActionList = []
        self.currentSuite = {}
        self.currentTest = {}
        self.currentAction = {}
        self.currentPerformanceAction = {}
        self.inAction = False
        self.inTest = False
        self.inSuite = False
        #print 'logName = %s:: debug level = %d :: mask level = %d ::  stdout = %s' % (logName, debug, mask, stdout)
        
        if stdout is True:
           import sys
           self.stdout = sys.__stdout__
        else:
           self.stdout = None
           
        if self.logName is not None:
            self.LogName = os.path.abspath(self.logName)
            # Rename the last log file to timestamped version
            try:
                # getatime returns last mod on Unix, and creation time on Win
                atime = os.path.getatime(self.LogName)
                time_stamp = time.strftime('%Y%m%d%H%M%S',
                                           time.localtime(atime))
                os.rename(self.LogName, '%s.%s' % (self.LogName, time_stamp))
            except OSError:
                # Most likely the file didn't exist, just ignore
                pass            
            
            self.f = file(self.logName, 'w')
        else:
            self.f = None

    def startSuite(self, name, comment=None):
        """Method to begin test Suite.
        
        Required Argument:
        name: str -- Name of Suite
        
        Keyword Argument:
        comment: str -- Comment string
        """
        
        self.currentSuite = {}
        self.testList = []
        self.currentSuite = {'name':name, 'comment':comment, 'starttime':datetime.now(), 'result':None}
        self.printOut(u'Starting Suite %s :: StartTime %s' % (name, self.currentSuite['starttime']), level=3) 
        self.inSuite = True
        
    def endSuite(self):
        """Method to end current running suite.
        
        Encapsulates test list."""
            
        self.currentSuite['endtime'] = datetime.now()
        self.currentSuite['totaltime'] = self.currentSuite['endtime'] - self.currentSuite['starttime']
        self.printOut(u'Ending Suite ""%s"" :: EndTime %s :: Total Time %s' % (self.currentSuite['name'], self.currentSuite['endtime'], self.currentSuite['totaltime']), level=3)
        self.currentSuite['testlist'] = copy.copy(self.testList)
        self.suiteList.append(copy.copy(self.currentSuite))
        self.inSuite = False
        
    def startTest(self, name, comment=None):
        """Method to begin individual test class run.
        
        Required Argument:
        name: str -- Name of Test
        
        Keyword Argument:
        comment: -- Comment string"""
        
        self.currentTest = {}
        self.actionList = []
        self.currentTest = {'name':name, 'comment':comment, 'starttime':datetime.now(), 'result':None}
        self.printOut(u'Starting Test ""%s"" :: StartTime %s' % (name, self.currentTest['starttime']), level=2)
        self.inTest = True
        
    def endTest(self, comment=None):
        """Method to end individual test class run.
        
        Encapsulates action list."""
        self.currentTest['endtime'] = datetime.now()
        self.currentTest['totaltime'] = self.currentTest['endtime'] - self.currentTest['starttime']
        self.currentTest['comment'] = '%s\n%s' % (self.currentTest['comment'], comment)
        self.printOut(u'Ending Test ""%s"" :: EndTime %s :: Total Time %s' % (self.currentTest['name'], self.currentTest['endtime'], self.currentTest['totaltime']), level=2)
        self.currentTest['actionlist'] = copy.copy(self.actionList)
        self.testList.append(copy.copy(self.currentTest))
        self.inTest = False
        
    def startAction(self, name, comment=None):
        """Method to being action inside of test class run.
        
        Required Argument:
        name: str -- Name of action
        
        Keyword Argument:
        comment: str -- Comment string"""
        self.currentAction = {}
        self.currentReportList = []
        self.currentAction = {'name':name, 'comment':comment, 'starttime':datetime.now(), 'result':None}
        self.printOut(u'Starting Action ""%s"" :: StartTime %s' % (name, self.currentAction['starttime']), level=1)
        self.inAction = True
                       
    def endAction(self, result=True, comment=None):
        """Method to end current action.
        
        Keyword Arguments:
        result:  bool -- User signalled result of action. Shortcut to call report() at end of action.
        comment: str  -- Comment string
        """
        if self.inAction is False:
            self.printOut("ENDACTION HAS BEEN CALLED OUTSIDE OF ACTION", level=1, result=False)
            return False
        self.currentAction['endtime'] = datetime.now()
        self.currentAction['totaltime'] = self.currentAction['endtime'] - self.currentAction['starttime']
        self.report(result, comment)
        self.currentAction['reportlist'] = copy.copy(self.currentReportList)
        self.actionList.append(copy.copy(self.currentAction))
        self.inAction = False
        
    def startPerformanceAction(self, name, comment=None):
        """Method to being performance action timer.
        
        This starts and stops it's own timer and isn't encapsulated in the normal output datastructure.
        
        Required Argument:
        name: str -- Name of action you wish to time.
        
        Keyword Argument:
        comment: str -- Comment string.
        """
        self.currentPerformanceAction = {}
        self.currentPerformanceAction = {'name':name, 'comment':comment, 'starttime':datetime.now()}
        self.printOut(u'Performance Starting Action ""%s"" :: StartTime %s' % (name, self.currentPerformanceAction['starttime']), level=1)

    def endPerformanceAction(self):
        """Method to end preformance action timer."""
        self.currentPerformanceAction['endtime'] = datetime.now()
        self.currentPerformanceAction['totaltime'] = self.currentPerformanceAction['endtime'] - self.currentPerformanceAction['starttime']
        self.performanceActionList.append(copy.copy(self.currentPerformanceAction))
        
    def addComment(self, string):
        """Method to insert comment in to current action or test.
        
        Required Argument:
        string: str -- Comment string."""
        string = '[%s] %s' % (datetime.now(), string)
        
        if self.inAction is True:
            self.currentAction['comment'] = '%s :: %s' % (self.currentAction['comment'], string)
            self.printOut(u'CommentAdd :: %s' % string, level=0, result=True)
        elif self.inAction is False:
            self.currentTest['comment'] = '%s :: %s' % (self.currentTest['comment'], string)
            self.printOut(u'CommentAdd :: %s' % string, level=1, result=True)
    
    def report(self, result, name=None, comment=None):
        """Method to report PASS/FAIL within test or action.
        
        Required Argument:
        result: bool -- PASS=True, FAIL=False
        
        Keyword Arguments:
        name:    str -- Name of report being called. If not inside action name is REQUIRED.
        comment: str -- Comment string.
        """
        # check state
        if self.inAction is True:
            self.currentReportList.append((result, name, comment))
        elif self.inAction is False:
            if name is None:
                x = datetime.now()
                self.printOut(u'UNNAMED REPORT CANNOT BE CALLED OUTSIDE OF ACTION %s:%s:%s:%s' % (x.hour, x.minute, x.second, x.microsecond), level=0, result=False)
                return
            elif name is not None:
                if comment is None: comment = 'Action created by framework for report call'
                self.startAction(name=name, comment=comment)
                self.endAction(result, comment=comment)
                return
        
        if name is not None: comment = '%s :: %s' % (name, comment)
        
        if result is True:
            self.printOut(u'Success in action.%s.report:: %s' % (self.currentAction['name'], comment), level=0, result=True)
        else:
            self.printOut(u'Failure in action.%s.report :: %s' % (self.currentAction['name'], comment), level=0, result=False)
        
    def write(self, string):
        """Method to allow TestOutput to be used like a file object.
        
        Required Argument:
        string: str -- String you wish to write."""
        self._write(string)    

    def _write(self, string):
        """Internal method for writing to log/stdout when enabled.
        
        Required Argument:
        string: str -- String you wish to write."""
        if self.f is not None:
            self.f.write(string.encode('raw_unicode_escape'))
            self.f.flush()
        
        if self.stdout is not None:
            self.stdout.write(string.encode('raw_unicode_escape'))
            self.stdout.flush()
 
    def printOut(self, string, level=0, result=True):
        """Method to print using self._write but observe debug and mask settings.
        
        Required Argument:
        string: str -- String you wish to print.
        
        level:  int  -- Level at which the output came; report=0, action=1, test=2, suite=3.
        result: bool -- Result for output. Necessary for masking passes.
        debug:   int  -- Debug level: 
                0 = show only failures
                1 = show pass and fail
                2 = show pass and fail and check repository after each test
        mask:    int  -- Masking level
                0 = show everything
                1 = don't show report 
                2 = don't show report, action
                3 = don't show report, action, test
        level:     int -- indentation level
                0 = report
                1 = action
                2 = test
                3 = suite
        """
        
        def sendTo_write(string, result):
            """prepend lead characters and send to _write 
                prepend + for true and - for false to the beginning of each string 
                repeat leadchar level number of time to show encapsulation
            """
            leadchar = '-'
            if result: leadchar = '+'
            self._write( u'%s%s\n' % (leadchar * (4 - level) * 3, string))
            
        if self.debug == 0 and result == True:
            return #don't print passes when debug = 0
        if level >= self.mask:
            sendTo_write(string, result)
            
    def easyReadSummary(self):
        """Failures displayed to be easily readable by humans """
        def stripStuff(s):
            if s == None:
                return ''
            if 'Traceback' not in s:
                s.replace('None', '')
                s.replace('\n', '')
            return s 
        self._parse_results()
        for suite_dict in self.suiteList:
            if suite_dict['result'] == False:
                self._write('\nSUITE %s FAILED\n' % suite_dict['name'])
                for test_dict in suite_dict['testlist']:
                    if test_dict['result'] == False:
                        self._write('\tTEST %s failed\n ' % stripStuff(test_dict['name']))
                        for action_dict in test_dict['actionlist']:
                            if action_dict['result'] == False:
                                self._write('\t\tACTION %s %s\n' % (stripStuff(action_dict['name']),stripStuff(action_dict['comment'])))
                                for report_tuple in action_dict['reportlist']:
                                    if report_tuple[0] is False:
                                        self._write('\t\t\tREPORT %s %s\n' % (stripStuff(report_tuple[1]), stripStuff(report_tuple[2])))
                                        


    def traceback(self):
        """Method to handle python traceback exception."""
        import sys, traceback
        type, value, stack = sys.exc_info()
        
        #Print the exception
        if self.f is not None:
            traceback.print_exception(type, value, stack, None, self.f)
        if self.stdout is not None:
            traceback.print_exception(type, value, stack, None, self.stdout)
        if self.stdout is None and self.f is None:
            traceback.print_exception(type, value, stack, None, self.stderr)
        
        #report the action
        self.report(False, 'Traceback detected')
        
        #Clean up logger state
        if self.inAction is True:
            self.endAction(result=False, comment='Action failed due to traceback')
        if self.inTest is True:
            self.endTest(comment='Test failed due to traceback\n' + traceback.format_exc())
            
    def _parse_results(self):
        """Method to parse through the result output datastructure to bubble up encapsulated failures"""
        for suite_dict in self.suiteList:
            for test_dict in suite_dict['testlist']:
                for action_dict in test_dict['actionlist']:
                    for report_tuple in action_dict['reportlist']:
                        if report_tuple[0] is False:
                            action_dict['result'] = False
                    if action_dict['result'] is False:
                        test_dict['result'] = False
                if test_dict['result'] is False:
                    suite_dict['result'] = False
            
    def summary(self):
        """Method to calculate and print summary and report"""
        suites_ran = 0
        suites_failed = 0
        tests_ran = 0
        tests_failed = 0
        actions_ran = 0
        actions_failed = 0
        reports_ran = 0
        reports_failed = 0
        
        self._parse_results()
        #Parse through finalized suiteList for failures
        
        self._write('\n*** Test Report ***\n\n')
        for suite_dict in self.suiteList:
            if suite_dict['result'] is False:
                self._write('Suite ""%s"" Failed :: Total Time ""%s"" :: Comment ""%s""\n' % (suite_dict['name'], suite_dict['totaltime'], suite_dict['comment']))
                suites_failed = suites_failed + 1
                for test_dict in suite_dict['testlist']:
                    if test_dict['result'] is False:
                        self._write('    Test ""%s"" Failed :: Total Time ""%s"" :: Comment ""%s""\n' % (test_dict['name'], test_dict['totaltime'], test_dict['comment']))
                        tests_failed = tests_failed + 1
                        for action_dict in test_dict['actionlist']:
                            if action_dict['result'] is False:
                                self._write('        Action ""%s"" Failed :: Total Time ""%s"" :: Comment ""%s""\n' % (action_dict['name'], action_dict['totaltime'], action_dict['comment']))
                                actions_failed = actions_failed + 1
                                for report_tuple in action_dict['reportlist']:
                                    if report_tuple[0] is False:
                                        self._write('            Report ""%s"" Failed :: Comment ""%s""\n' % (report_tuple[1], report_tuple[2]))
                                        reports_failed = reports_failed + 1

        #Calculate number ran
        for suite in self.suiteList:
            suites_ran = suites_ran + 1
            for test in suite['testlist']:
                tests_ran = tests_ran + 1
                for action in test['actionlist']:
                    actions_ran = actions_ran + 1
                    for report in action['reportlist']:
                        reports_ran = reports_ran + 1
        
        self._write('$Suites run=%s, pass=%s, fail=%s :: Tests run=%s, pass=%s, fail=%s :: Actions run=%s, pass=%s, fail=%s :: Reports run=%s, pass=%s, fail=%s \n' % 
                    (suites_ran, suites_ran - suites_failed, suites_failed, tests_ran, tests_ran - tests_failed, tests_failed, actions_ran, 
                     actions_ran - actions_failed, actions_failed, reports_ran, reports_ran - reports_failed, reports_failed))                                
    
    def simpleSummary(self):
        #write simple summary
        self._write("\n*********** TEST RESULTS ************\n*************************************\n")
        for suite_dict in self.suiteList:
                for test_dict in suite_dict['testlist']:
                    if test_dict['result'] == False:
                        self._write('%s*FAILED*\n' % test_dict['name'].ljust(30,'_'))
                    else:
                        self._write('%s passed \n' % test_dict['name'].ljust(30,'_'))
        self._write("*************************************\n")

    def tinderOutput(self):
        #write out stuff for tinderbox
        for suite_dict in self.suiteList:
            self._write('#TINDERBOX# Testname = %s\n' % suite_dict['name'])
            self._write('#TINDERBOX# Time elapsed = %s (seconds)\n' % suite_dict['totaltime'])
            if suite_dict['result'] is None:
                self._write('#TINDERBOX# Status = PASSED\n')
            else:
                self._write('#TINDERBOX# Status = FAILED\n')
        
        
    ### All the methods below will be removed pre 0.2-cats-release. They are only there for reverse compatability in old test so that those tests don't fail in Python.    
        
    def Start(self, string):
        
        self.printOut(u'DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def Stop(self):
        
        self.printOut(u'DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def Print(self, string):
        
        self.printOut(u'DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def Report(self, string):
        
        self.printOut(u'DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def ReportPass(self, string):
        
        self.printOut(u'DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def ReportFailure(self, string):
        
        self.printOut(u'DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def SetChecked(self, string):
        
        self.printOut(u'DEPRICATED LOGGER FUNCTION', level=0, result=False)   
        
    def Close(self):
        
        self.printOut(u'DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def calculateReport(self, reportList):
        
        result = True #keeping track of pass/fail
        
        for report in reportList:
            if report[0] is False:
                result = False
       #     self.printOut(report[1], level = 0, result = report[0])
        return result
                
        
if __name__ == "__main__":
    
    #test masking
    levels = ['report', 'action', 'test', 'suite']
    for self.debug in [0, 1, 2]:
        for self.mask in [0, 1, 2, 3]:
            for result in [True, False]:
                print '########## debug = %d :: mask = %d :: result = %s' % (debug, mask, result)
                logger = TestOutput(debug=debug, mask=mask, stdout=True)
                for level in [0, 1, 2, 3]:
                    output = 'At  level %d, %s' % (level, levels[level])
                    logger.printOut(output, level=level, result=result)
                    
            
    #logger = TestOutput(logName='testlog')
   ## logger.debug = 1
    #logger.startSuite('1st suite', 'comment')
    #logger.startTest('1st test')
    #logger.startAction('1st action in 1st test will pass')
    #logger.endAction(True)
    #logger.startAction('2nd action in 1st test will fail')
    #logger.endAction(False)
    #logger.startAction('3nd action in 1st test will fail')
    #logger.endAction(False)
    #logger.startAction('4nd action in 1st test will fail')
    #logger.endAction(False)
    #logger.startAction('5nd action in 1st test will fail')
    #logger.endAction(False)
    #logger.startAction('6nd action in 1st test will fail')
    #logger.endAction(False)
    #logger.startAction('7nd action in 1st test will fail')
    #logger.endAction(False)
    #logger.startAction('8nd action in 1st test will fail')
    #logger.endAction(False)
    #logger.startAction('9nd action in 1st test will fail')
    #logger.endAction(False)
    #logger.endTest()
    #logger.startTest('2nd test')
    #logger.startAction('1st action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('2nd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('3rd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('4nd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('5nd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('6nd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('7nd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('8nd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('9nd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('10nd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('11nd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('12nd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.startAction('13nd action in 2nd test will pass')
    #logger.endAction(True)
    #logger.endTest()
    #logger.endSuite()
    
   ## logger.mask = 1
    #logger.calculateSuite(logger.suiteList)
