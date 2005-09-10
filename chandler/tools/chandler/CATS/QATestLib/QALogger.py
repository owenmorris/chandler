from datetime import datetime, timedelta
import time
import string


def QALogger(filepath=None,description="No description"):
    ''' Factory method for QALogger '''
    try:
        TestLogger.logger
    except AttributeError:
        return TestLogger(filepath=filepath,description=description)
    else:
        if TestLogger.logger == None: # TestLogger has been destructed by the Close() method
            return TestLogger(filepath=filepath,description=description)
        else:
            TestLogger.logger.toClose = False
            TestLogger.logger.testcaseStartDate = datetime.now()
            TestLogger.logger.Print("")
            TestLogger.logger.Print("----- Testcase %s = %s -----" %(len(TestLogger.logger.testcaseList)+1, description))
            TestLogger.logger.subTestcaseDesc = description
            return TestLogger.logger

class TestLogger:        
    def __init__(self,filepath=None,description="No description"):
        if filepath:
            self.inTerminal = False
            try:
                self.File = open(filepath, 'a')
            except IOError:
                print "Unable to open file %s" % filepath
                print "log report in default_test.log"
                self.File = open("default_test.log", 'a')
        else:
            self.inTerminal = True
        # new testcase inits
        self.Reset()
        # logger inits
        self.startDate = datetime.now()
        self.testcaseList = []
        self.checked = False
        self.mainDescription = description
        # action inits
        self.actionDescription = "No action description"
        self.actionStartDate = self.actionEndDate = None
        # some printing
        self.Print("")
        self.Print("******* Test Script : %s (date : %s) *******" %(self.mainDescription, self.startDate))
        # TestLogger.logger init
        TestLogger.logger = self

    def Reset(self):
        ''' Reset all the attributes relative to a testcase '''
        self.subTestcaseDesc = None
        self.toClose = True
        self.nbPass = 0
        self.nbFail = 0
        self.nbUnchecked = 0
        self.nbAction = 0
        self.nbVerif = 0
        self.failureList = []
        self.passedList = []
            
    def Print(self,string):
        ''' Printing method '''
        if self.inTerminal:
            print "%s" %string
        else:
            self.File.write(string+'\n')

    def PrintTBOX(self, elapsed, level=None):
        description = string.join(string.split(self.mainDescription, " "), "_")
        if level == "Testcase":
            testcaseDesc = string.join(string.split(self.subTestcaseDesc, " "), "_")
            description = "%s.%s" %(description, testcaseDesc)
        elif level == "Action":
            actionDesc = string.join(string.split(self.actionDescription, " "), "_")
            if self.subTestcaseDesc:
                testcaseDesc = string.join(string.split(self.subTestcaseDesc, " "), "_")
                description = "%s.%s" %(description, testcaseDesc)
            description = "%s.%s" %(description, actionDesc)
        elapsed_min = (elapsed.seconds / 60.0) + (elapsed.microseconds / 60000000.0)
        self.Print("OSAF_QA: %s | %s | %s | %s" %(description, 1, elapsed_min, elapsed_min)) 
    
    def Start(self,string):
        ''' Start the action timer  '''
        # usefull inits
        self.failureList = []
        self.passedList = []
        self.checked = False
        self.nbAction = self.nbAction + 1
        self.actionDescription = string
        self.actionStartDate = self.actionEndDate = datetime.now()
        #some init printing
        self.Print("")
        self.Print("-------------------------------------------------------------------------------------------------")

    def Stop(self):
        ''' Stop the action timer  '''
        self.actionEndDate = datetime.now()
        #report the timing information
        elapsed = self.actionEndDate - self.actionStartDate
        self.Print("Action = "+self.actionDescription)
        if self.actionStartDate == None: # Start method has not been called
            self.Print("!!! No time informations available !!!")
        else:
            self.Print("Start date (before %s) = %s" %(self.actionDescription, self.actionStartDate))
            self.Print("End date (after %s) = %s" %(self.actionDescription, self.actionEndDate))
            self.Print("Time Elapsed = %s.%s seconds" %(elapsed.seconds, elapsed.microseconds))
            self.PrintTBOX(elapsed, "Action")
        #reset timing infos
        self.actionStartDate = self.actionEndDate = None
        
    def Report(self,description="Unknown"):
        ''' Report the current action states'''
        self.nbVerif = self.nbVerif + 1
        self.Print("")
        self.Print("%s checking report : " %description)
        for failure in self.failureList:
            self.Print("        - Error : %s" % failure)
        for passed in self.passedList:
            self.Print("        - Ok : %s" % passed)
        if len(self.failureList) == 0 and self.checked:
            status = "Pass"
            self.nbPass = self.nbPass + 1
        elif len(self.failureList) == 0 and not self.checked:
            status = "Uncheck"
            self.nbUnchecked = self.nbUnchecked + 1
        else:
            status = "Fail"
            self.nbFail = self.nbFail + 1
        self.Print("Verification = %s" % status)
        self.Print("")

        #reset
        self.failureList = []
        self.passedList = []
        self.checked = False
        
    def InitFailureList(self):
        self.failureList = []
    
    def ReportFailure(self, string):
        self.failureList.append(string)

    def ReportPass(self, string):
        self.passedList.append(string)

    def SetChecked(self, bool):
        self.checked = bool
    
    def Close(self):
        if self.toClose: # The file must close (time to report a summary)
            TestLogger.logger = None
            now = datetime.now()
            elapsed = now - self.startDate
            self.Print("")
            self.Print("++++++++++++++++++++++++SUMMARY++++++++++++++++++++++++")
            self.Print("Start date (before %s test script) = %s" %(self.mainDescription, self.startDate))
            self.Print("End date (after %s test script) = %s" %(self.mainDescription, now))
            self.Print("Time Elapsed = %s.%s seconds" %(elapsed.seconds, elapsed.microseconds))
            self.Print("")
            #display the TestSuite status summary
            if not len(self.testcaseList) == 0:
                self.Print("TestSuite Summary :")
                nbTCFailed = 0
                nbTCPassed = 0
                nbTCUnchecked = 0
                for tc in self.testcaseList:
                    if tc[1] == "FAIL":
                        nbTCFailed = nbTCFailed + 1
                    elif tc[1] == "PASS":
                        nbTCPassed = nbTCPassed + 1
                    else:
                        nbTCUnchecked = nbTCUnchecked + 1
                    self.Print("-  %s  =  %s" %(tc[0],tc[1]))
                self.Print("")
                self.Print("Total number of Testcases RUN : %s" %len(self.testcaseList))
                self.Print("Total number of Testcases PASSED : %s" %nbTCPassed)
                self.Print("Total number of Testcases FAILED : %s" %nbTCFailed)
                self.Print("")
                # compute the status of the Testscript if is composed by sub-testcases
                if nbTCFailed == 0:
                    status = "PASSED"
                else:
                    status = "FAILED"
                # Test suite status
                self.Print("Status : %s test suite %s" %(self.mainDescription, status))
            # compute the status of the main testcase if is composed by actions
            else:
                if self.nbUnchecked == self.nbVerif:
                    status = "UNCHECKED"
                elif self.nbPass == self.nbVerif:
                    status = "PASSED"
                else:
                    status = "FAILED"
                self.Print("")
                #Test case status
                self.Print("Status : %s testcase %s" %(self.mainDescription, status))

            # Tindebox printing
            # convert the elapsed time in minutes
            elapsed_min = (elapsed.seconds / 60.0) + (elapsed.microseconds / 60000000.0)
            self.Print("")
            self.Print("#TINDERBOX# Testname = %s" %self.mainDescription)    
            self.Print("#TINDERBOX# Status = %s" %status)
            self.Print("#TINDERBOX# Time elapsed = %s (minutes)" %elapsed_min)
            self.PrintTBOX(elapsed)
            self.Print("")
            self.Print("*******               End of Report               *******")
            print("#TINDERBOX# Testname = %s" %self.mainDescription)    
            print("#TINDERBOX# Status = %s" %status)
            print("#TINDERBOX# Time elapsed = %s (minutes)" %elapsed_min)
            if not self.inTerminal:
                # close the file
                self.File.close()
        else: # Just the end of a testcase
            if self.subTestcaseDesc:
                if self.nbUnchecked == self.nbVerif:
                    status = "UNCHECKED"
                elif self.nbPass == self.nbVerif:
                    status = "PASS"
                else:
                    status = "FAIL"
                self.testcaseList.append((self.subTestcaseDesc,status))
            # Test case status
            now = datetime.now()
            elapsed = now - self.testcaseStartDate
            self.Print("-----  %s summary  -----" %self.subTestcaseDesc)
            self.Print("Start date (before %s testcase) = %s" %(self.subTestcaseDesc, self.testcaseStartDate))
            self.Print("End date (after %s testcase) = %s" %(self.subTestcaseDesc, now))
            self.Print("Time Elapsed = %s.%s seconds" %(elapsed.seconds, elapsed.microseconds))
            self.Print("Testcase Name= %s" %self.subTestcaseDesc)
            self.Print("Testcase Status = %s" %status)
            self.PrintTBOX(elapsed, "Testcase")
            # new testcase inits
            self.Reset()
            
