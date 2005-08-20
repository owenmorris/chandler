from datetime import datetime, timedelta
import time

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
            TestLogger.logger.Print("")
            TestLogger.logger.Print("----- Testcase = %s -----" %description)
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
        self.actionStartTime = self.actionEndTime = self.actionStartDate = self.actionEndDate = None
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
        self.failureList = []
        self.passedList = []
            
    def Print(self,string):
        ''' Printing method '''
        if self.inTerminal:
            print "%s" %string
        else:
            self.File.write(string+'\n')

    def Start(self,string):
        ''' Start the action timer  '''
        # usefull inits
        self.failureList = []
        self.passedList = []
        self.checked = False
        self.actionDescription = string
        self.actionStartTime = self.actionEndTime = time.time()
        self.actionStartDate = datetime.now()
        #some init printing
        self.Print("")
        self.Print("-------------------------------------------------------------------------------------------------")

    def Stop(self):
        ''' Stop the action timer  '''
        self.actionEndTime = time.time()
        self.actionEndDate = datetime.now()
        #report the timing information
        elapsed = self.actionEndTime - self.actionStartTime
        self.Print("Action = "+self.actionDescription)
        if self.actionStartTime == None: # Start method has not been called
            self.Print("!!! No time informations available !!!")
        else:
            self.Print("Start date (before %s) = %s" %(self.actionDescription, self.actionStartDate))
            self.Print("End date (after %s) = %s" %(self.actionDescription, self.actionEndDate))
            self.Print("Time Elapsed = %.3f seconds" %elapsed)
        #reset timing infos
        self.actionStartTime = self.actionEndTime = self.actionStartDate = self.actionEndDate = None
        
    def Report(self,description="Unknown"):
        ''' Report the current action states'''
        self.nbAction = self.nbAction + 1
        self.Print("")
        self.Print("%s checking report : " %description)
        for failure in self.failureList:
            self.Print("        - Error : %s" % failure)
        for passed in self.passedList:
            self.Print("        - Ok : %s" % passed)
        if len(self.failureList) == 0 and self.checked:
            status = "PASS"
            self.nbPass = self.nbPass + 1
        elif len(self.failureList) == 0 and not self.checked:
            status = "UNCHECK"
            self.nbUnchecked = self.nbUnchecked + 1
        else:
            status = "FAIL"
            self.nbFail = self.nbFail + 1
        self.Print("ACTION STATUS = %s" % status)

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
            #display the sub-testcase status summary
            if not len(self.testcaseList) == 0:
                self.Print("Sub-Testcase Status summary :")
                nbTCFailed = 0
                nbTCPassed = 0
                for tc in self.testcaseList:
                    if tc[1] == "FAIL":
                        nbTCFailed = nbTCFailed + 1
                    else:
                        nbTCPassed = nbTCPassed + 1
                    self.Print("-  %s  =  %s" %(tc[0],tc[1]))
                self.Print("")
                self.Print("Total number of Sub-Testcase : %s" %len(self.testcaseList))
                self.Print("Total number of Sub-Testcase PASSED : %s" %nbTCPassed)
                self.Print("Total number of Sub-Testcase FAILED : %s" %nbTCFailed)
                self.Print("")
                # compute the status of the main testcase if is composed by sub-testcase
                if nbTCFailed == 0:
                    status = "PASS"
                else:
                    status = "FAIL"
            # compute the status of the main testcase if is composed by actions
            else:
                if self.nbPass == self.nbAction:
                    status = "PASS"
                elif self.nbUnchecked == self.nbAction:
                    status = "UNCHECK"
                else:
                    status = "FAIL"
            # Tindebox printing
            # convert the elapsed tme in minutes
            elapsed_min = (elapsed.seconds / 60.0) + (elapsed.microseconds / 60000000.0)
            self.Print("#TINDERBOX# Testname = %s" %self.mainDescription)    
            self.Print("#TINDERBOX# Status = %s" %status)
            self.Print("#TINDERBOX# Time elapsed = %s" %elapsed_min)
            self.Print("OSAF_QA: %s | %s | %s | %s" %(self.mainDescription, 1, elapsed_min, elapsed_min)) 
            self.Print("")
            self.Print("*******               End of Report               *******")
            print("#TINDERBOX# Testname = %s" %self.mainDescription)    
            print("#TINDERBOX# Status = %s" %status)
            print("#TINDERBOX# Time elapsed = %s" %elapsed_min)
            print("OSAF_QA: %s | %s | %s | %s" %(self.mainDescription, 1, elapsed_min, elapsed_min)) 
            if not self.inTerminal:
                # close the file
                self.File.close()
        else: # Just the end of a testcase
            if self.subTestcaseDesc:
                if self.nbPass == self.nbAction:
                    status = "PASS"
                else:
                    status = "FAIL"
                self.testcaseList.append((self.subTestcaseDesc,status))
            # new testcase inits
            self.Reset()
           
