from datetime import datetime, timedelta
import time
import string
import version
import application.Globals as Globals
import osaf.framework.scripting as scripting
import hotshot

def QALogger(filepath=None,description="No description"):
    ''' Factory method for QALogger '''
    qaLogger = getattr(TestLogger, 'logger', None)
    if qaLogger is None:
        # never created, or already destructed by Close()
        return TestLogger(filepath=filepath,description=description)
    else:
        qaLogger.toClose = False
        qaLogger.Print("")
        qaLogger.Print("----- Testcase %s = %s -----" %(len(qaLogger.testcaseList)+1, description))
        qaLogger.subTestcaseDesc = description
        qaLogger.testcaseStartDate = datetime.now()
        return qaLogger

class TestLogger:
    def __init__(self,filepath=None,description="No description"):
        self.startDate = datetime.now()
        if filepath:
            self.inTerminal = False
            time_stamp = "%4s%2s%2s%2s%2s%2s" %(self.startDate.year, self.startDate.month, self.startDate.day,
                                          self.startDate.hour, self.startDate.minute, self.startDate.second)
            time_stamp = string.replace(time_stamp, ' ', '0')
            # add a time stamp at the end of the filename
            filepath = filepath+'.'+time_stamp
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
        # Check if we're profiling
        self.profiler = scripting.cats_profiler()

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
        elapsed_secs = elapsed.seconds + elapsed.microseconds / 1000000.0
        self.Print("OSAF_QA: %s | %s | %s" %(description, version.buildRevision, elapsed_secs)) 
        print("OSAF_QA: %s | %s | %s" %(description, version.buildRevision, elapsed_secs))
        
    def Start(self,string):
        ''' Start the action timer  '''
        # usefull inits
        self.failureList = []
        self.passedList = []
        self.checked = False
        self.nbAction = self.nbAction + 1
        self.actionDescription = string
        #some init printing
        self.Print("")
        self.Print("-------------------------------------------------------------------------------------------------")
        if self.profiler is not None:
            self.profiler.start()
        self.actionStartDate = self.actionEndDate = datetime.now()

    def Stop(self):
        ''' Stop the action timer  '''
        self.actionEndDate = datetime.now()
        if self.profiler is not None:
            self.profiler.stop()
        #report the timing information
        self.Print("Action = "+self.actionDescription)
        if self.actionStartDate == None: # Start method has not been called
            self.Print("!!! No time information available !!!")
        else:
            elapsed = self.actionEndDate - self.actionStartDate
            elapsed_secs = elapsed.seconds + elapsed.microseconds / 1000000.0
            self.Print("Start date (before %s) = %s" %(self.actionDescription, self.actionStartDate))
            self.Print("End date (after %s) = %s" %(self.actionDescription, self.actionEndDate))
            self.Print("Time Elapsed = %s seconds" % elapsed_secs)
            self.PrintTBOX(elapsed, "Action")
            # Open the cats log if that was requested
            if Globals.options.catsPerfLog:
                catsPerfLog = open(Globals.options.catsPerfLog, 'wt')
                try:
                    catsPerfLog.write("%s\n" % elapsed_secs)
                finally:
                    catsPerfLog.close()
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
    
    def Close(self, quit=True):
        now = datetime.now()
        if self.toClose: # The file must close (time to report a summary)
            TestLogger.logger = None
            elapsed = now - self.startDate
            elapsed_secs = elapsed.seconds + elapsed.microseconds / 1000000.0
            self.Print("")
            self.Print("++++++++++++++++++++++++SUMMARY++++++++++++++++++++++++")
            self.Print("Start date (before %s test script) = %s" %(self.mainDescription, self.startDate))
            self.Print("End date (after %s test script) = %s" %(self.mainDescription, now))
            self.Print("Time Elapsed = %s seconds" % elapsed_secs)
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
            # compute the elapsed time in seconds
            elapsed_secs = elapsed.seconds + elapsed.microseconds / 1000000.0
            description = string.join(string.split(self.mainDescription, " "), "_")
            self.Print("")
            self.Print("#TINDERBOX# Testname = %s" %description)    
            self.Print("#TINDERBOX# Status = %s" %status)
            self.Print("#TINDERBOX# Time elapsed = %s (seconds)" %elapsed_secs)
            self.PrintTBOX(elapsed)
            self.Print("")
            self.Print("*******               End of Report               *******")
            print("#TINDERBOX# Testname = %s" %description)    
            print("#TINDERBOX# Status = %s" %status)
            print("#TINDERBOX# Time elapsed = %s (seconds)" %elapsed_secs)
            if not self.inTerminal:
                # close the file
                self.File.close()
            # quit Chandler
            if quit:
                import osaf.framework.scripting as scripting
                scripting.app_ns().root.Quit()
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
            elapsed = now - self.testcaseStartDate
            elapsed_secs = elapsed.seconds + elapsed.microseconds / 1000000.0
            self.Print("-----  %s summary  -----" %self.subTestcaseDesc)
            self.Print("Start date (before %s testcase) = %s" %(self.subTestcaseDesc, self.testcaseStartDate))
            self.Print("End date (after %s testcase) = %s" %(self.subTestcaseDesc, now))
            self.Print("Time Elapsed = %s seconds" % elapsed_secs)
            self.Print("Testcase Name= %s" %self.subTestcaseDesc)
            self.Print("Testcase Status = %s" %status)
            self.PrintTBOX(elapsed, "Testcase")
            # new testcase inits
            self.Reset()
            
