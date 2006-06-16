from datetime import datetime as dtime
import copy

class datetime(dtime):
    
    def __str__(self):
        
        return '%s:%s:%s:%s' % (self.hour, self.minute, self.second, self.microsecond)

class TestOutput:
    
    def __init__(self, logname=None, debug=0, mask=0, stdout=None):
        
        print 'logger starting'
        self.debug = debug
        self.mask = mask
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
        self.passedTests = 0
        self.failedTests = 0
        self.passedActions = 0
        self.failedActions = 0
        self.passedReports = 0
        self.failedReports = 0
        
        if stdout is True:
           import sys
     #      self.stdout = sys.__stdout__
           self.stdout = sys.__stdout__
        else:
           self.stdout = None
        
        if logname is not None:
            self.f = file(logname, 'w')
        else:
            self.f = None
            
    def startSuite(self, name, comment=None):
        
        self.currentSuite = {}
        self.testList = []
        self.currentSuite = {'name':name, 'comment':comment, 'starttime':datetime.now()}
        self.printOut('Starting Suite %s :: StartTime %s' % (name, self.currentSuite['starttime']), level=3) 
        self.inSuite = True
        
    def endSuite(self):
            
        self.currentSuite['endtime'] = datetime.now()
        self.currentSuite['totaltime'] = self.currentSuite['endtime'] - self.currentSuite['starttime']
  
  #    This code is for if we implement this where there may be multiple suites.
  #      if self.calculateSuite(self.suiteList) == True:
  #         self.passedTests = self.passedSuites + 1
  #      else:
  #          self.failedTests = self.failedSuites + 1
        self.displaySummary()
        self.printOut('Ending Suite ""%s"" :: EndTime %s :: Total Time %s' % (self.currentSuite['name'], self.currentSuite['endtime'], self.currentSuite['totaltime']), level=3)
        self.currentSuite['testlist'] = copy.copy(self.testList)
        self.suiteList.append(copy.copy(self.currentSuite))
        self.inSuite = False
        
    def startTest(self, name, comment=None):
        
        self.currentTest = {}
        self.actionList = []
        self.currentTest = {'name':name, 'comment':comment, 'starttime':datetime.now()}
        self.printOut('Starting Test ""%s"" :: StartTime %s' % (name, self.currentTest['starttime']), level=2)
        self.inTest = True
        
    def endTest(self, comment=None):
        
        self.currentTest['endtime'] = datetime.now()
        self.currentTest['totaltime'] = self.currentTest['endtime'] - self.currentTest['starttime']
        self.currentTest['comment'] = '%s\n%s' % (self.currentTest['comment'], comment)
        
#        if self.calculateTest(self.testList) == True:
#            self.passedTests = self.passedTests + 1
#        else:
#            self.failedTests = self.failedTests + 1
            
        self.printOut('Ending Test ""%s"" :: EndTime %s :: Total Time %s' % (self.currentTest['name'], self.currentTest['endtime'], self.currentTest['totaltime']), level=2)
        self.currentTest['actionlist'] = copy.copy(self.actionList)
        self.testList.append(copy.copy(self.currentTest))
        self.inTest = False
        
    def startAction(self, name, comment=None):
        
        self.currentAction = {}
        self.currentResultList = []
        self.currentAction = {'name':name, 'comment':comment, 'starttime':datetime.now()}
        self.printOut('Starting Action ""%s"" :: StartTime %s' % (name, self.currentAction['starttime']), level=1)
        self.inAction = True
                       
    def endAction(self, result=True, comment=None):
        
        if self.inAction is False:
            self.printOut("ENDACTION HAS BEEN CALLED OUTSIDE OF ACTION", level=1, result=False)
            return False
        self.currentAction['endtime'] = datetime.now()
        self.currentAction['totaltime'] = self.currentAction['endtime'] - self.currentAction['starttime']
        self.report(result, comment)
        
#        for result in self.currentResultList:
#            if result[0] is False:
#                reportResult = False
#                break
#            else:
#                reportResult = True
#        if reportResult is True:
#            self.passedActions = self.passedActions + 1
#            self.printOut('Ending Action ""%s"" :: EndTime %s :: Total Time %s' % (self.currentAction['name'], self.currentAction['endtime'], self.currentAction['totaltime']), level=1)
#        if reportResult is False:
#            self.failedActions = self.failedActions + 1
#            self.printOut('Ending Action FAILED ""%s"" :: EndTime %s :: Total Time %s' % (self.currentAction['name'], self.currentAction['endtime'], self.currentAction['totaltime']), level=1, result=False)
        
        self.currentAction['resultList'] = copy.copy(self.currentResultList)
        self.actionList.append(copy.copy(self.currentAction))
        self.inAction = False
        
    def startPerformanceAction(self, name, comment=None):
        
        self.currentPerformanceAction = {}
        self.currentPerformanceAction = {'name':name, 'comment':comment, 'starttime':datetime.now()}
        self.printOut('Performance Starting Action ""%s"" :: StartTime %s' % (name, self.currentPerformanceAction['starttime']), level=1)

    def endPerformanceAction(self):
        
        self.currentPerformanceAction['endtime'] = datetime.now()
        self.currentPerformanceAction['totaltime'] = self.currentPerformanceAction['endtime'] - self.currentPerformanceAction['starttime']
        self.performanceActionList.append(copy.copy(self.currentPerformanceAction))
        
    def addComment(self, string):
        
        string = '[%s] %s' % (datetime.now(), string)
        
        if self.inAction is True:
            self.currentAction['comment'] = '%s :: %s' % (self.currentAction['comment'], string)
            self.printOut('CommentAdd :: %s' % string, level=0, result=True)
        elif self.inAction is False:
            self.currentTest['comment'] = '%s :: %s' % (self.currentTest['comment'], string)
            self.printOut('CommentAdd :: %s' % string, level=1, result=True)
    
    def report(self, result, name=None, comment=None):
        
        # check state
        if self.inAction is True:
            self.currentResultList.append([result, comment])
        elif self.inAction is False:
            if name is None:
                x = datetime.now()
                self.printOut('UNNAMED REPORT CANNOT BE CALLED OUTSIDE OF ACTION %s:%s:%s:%s' % (x.hour, x.minute, x.second, x.microsecond), level=0, result=False)
                return
            elif name is not None:
                if comment is None: comment = 'Action created by framework for report call'
                self.startAction(name=name, comment=comment)
                self.endAction(result, comment=comment)
                return
        
        if name is not None: comment = '%s :: %s' % (name, comment)
        
        if result is True:
            self.passedReports = self.passedReports + 1
            if self.debug > 0:
                self.printOut('Success in action.%s.report:: %s' % (self.currentAction['name'], comment), level=0)
        else:
            self.failedReports = self.failedReports + 1
            self.printOut('Failure in action.%s.report :: %s' % (self.currentAction['name'], comment), level=0)
        

    def write(self, string):
        if self.f is not None:
            self.f.write(string)
            self.f.flush()
        
        if self.stdout is not None:
            self.stdout.write(string)
            self.stdout.flush()
 
    def printOut(self, string, level=0, result=True):
        
        if result is True:
            leadchar = '+'
        else:
            leadchar = '-'
            
        string = '%s%s\n' % (leadchar * (4 - level), string)
        if self.debug > 2:
            self.write(string)
            return
        if self.debug > 1:
            if level >= self.mask:
                self.write(string)
                return
        if self.debug > 0:
            if result is False:
                self.write(string)
                return
        if self.debug == 0:
            if result is False:
                if level >= self.mask:
                    self.write(string)
                    return

    def displaySummary(self):
        for test in self.testList:
            if test['comment'] == 'None\nNone':
                self.printOut( "%s %s %s" % ( test['name'] , 'PASS',  test['totaltime'] ), 4)
            else:
                self.printOut ("%s %s %s" % ( test['name'] , 'FAIL',  test['totaltime'] ), 4) 
                self.printOut (test['comment'].replace('\n','') )
        self.printOut('\n--Suite Summary-- There were %s passed tests and %s failed with a combined %s passed actions and %s failed actions, with %s passed reports and %s failed reports.' % (self.passedTests, self.failedTests, self.passedActions, self.failedActions, self.passedReports,self.failedReports))
        

    def traceback(self):
        
        import sys, traceback
        type, value, stack = sys.exc_info()
        
        #Print the exception
        if self.f is not None:
            traceback.print_exception(type, value, stack, None, self.f)
        if self.stdout is not None:
            traceback.print_exception(type, value, stack, None, self.stdout)
        if self.stdout is None and self.f is None:
            traceback.print_exception(type, value, stack, None, self.stderr)
        
        #Clean up logger state
        if self.inAction is True:
            self.endAction(result=False, comment='Action Failure due to traceback')
        if self.inTest is True:
            self.endTest(comment='Test Failure due to traceback')
        

   
    def Start(self, string):
        
        self.printOut('DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def Stop(self):
        
        self.printOut('DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def Print(self, string):
        
        self.printOut('DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def Report(self, string):
        
        self.printOut('DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def ReportPass(self, string):
        
        self.printOut('DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def ReportFailure(self, string):
        
        self.printOut('DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def SetChecked(self, string):
        
        self.printOut('DEPRICATED LOGGER FUNCTION', level=0, result=False)   
        
    def Close(self):
        
        self.printOut('DEPRICATED LOGGER FUNCTION', level=0, result=False)
        
    def calculateReport(self, reportList):
        
        result = True #keeping track of pass/fail
        
        for report in reportList:
            if report[0] is False:
                result = False
       #     self.printOut(report[1], level = 0, result = report[0])
        return result
        
    def calculateAction(self, actionList):
        result = True
        
        iterations = len(actionList)
        i = 0
       
        while i < iterations:
            
            reportResult = self.calculateReport(actionList[i+1])
            if reportResult is False:
                result = False
            
           # printString = 'Name:: %s Comments:: %s Starttime:: %s Endtime:: %s TotalTime:: %s Passed:: %s' % (actionList[i]['name'], actionList[i]['comment'], actionList[i]['starttime'], actionList[i]['endtime'], actionList[i]['totaltime'], reportResult)
           # self.printOut(printString, level=1, result=reportResult)
            
            i = i+2
        return result
    
    def calculateTest(self, testList):
        result = True
        
        iterations = len(testList)
        i = 0
       
        while i < iterations:
            
            reportResult = self.calculateAction(testList[i+1])
            if reportResult is False:
                result = False
            
          #  printString = 'Name:: %s Comments:: %s Starttime:: %s Endtime:: %s TotalTime:: %s Passed:: %s' % (testList[i]['name'], testList[i]['comment'], testList[i]['starttime'], testList[i]['endtime'], testList[i]['totaltime'], reportResult)
            #self.printOut(printString, level = 2, result=reportResult)
            
            i = i+2
        return result
        
        
    def calculateSuite(self, suiteList):
        result = True
        
        iterations = len(suiteList)
        i = 0
       
        while i < iterations:
            
            reportResult = self.calculateTest(suiteList[i+1])
            if reportResult is False:
                result = False
            
         #   printString = 'Name:: %s Comments:: %s Starttime:: %s Endtime:: %s TotalTime:: %s Passed:: %s' % (suiteList[i]['name'], suiteList[i]['comment'], suiteList[i]['starttime'], suiteList[i]['endtime'], suiteList[i]['totaltime'], reportResult)
           # self.printOut(printString, level = 3, result = reportResult)
            
            i = i+2
        return result    
        
        
        
if __name__ == "__main__":
    
    logger = TestOutput(logname='testlog')
   # logger.debug = 1
    logger.startSuite('1st suite', 'comment')
    logger.startTest('1st test')
    logger.startAction('1st action in 1st test will pass')
    logger.endAction(True)
    logger.startAction('2nd action in 1st test will fail')
    logger.endAction(False)
    logger.startAction('3nd action in 1st test will fail')
    logger.endAction(False)
    logger.startAction('4nd action in 1st test will fail')
    logger.endAction(False)
    logger.startAction('5nd action in 1st test will fail')
    logger.endAction(False)
    logger.startAction('6nd action in 1st test will fail')
    logger.endAction(False)
    logger.startAction('7nd action in 1st test will fail')
    logger.endAction(False)
    logger.startAction('8nd action in 1st test will fail')
    logger.endAction(False)
    logger.startAction('9nd action in 1st test will fail')
    logger.endAction(False)
    logger.endTest()
    logger.startTest('2nd test')
    logger.startAction('1st action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('2nd action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('3rd action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('4nd action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('5nd action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('6nd action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('7nd action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('8nd action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('9nd action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('10nd action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('11nd action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('12nd action in 2nd test will pass')
    logger.endAction(True)
    logger.startAction('13nd action in 2nd test will pass')
    logger.endAction(True)
    logger.endTest()
    logger.endSuite()
    
   # logger.mask = 1
    logger.calculateSuite(logger.suiteList)
    logger.displaySummary()