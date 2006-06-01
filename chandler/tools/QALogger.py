from datetime import datetime, timedelta
import os, sys, traceback
import time
import string
import version
import application.Globals as Globals
import osaf.framework.scripting as scripting
import hotshot
            
class FileWatcher:       
    """masquerades as a file so stderr can be directed to it
         sets a flag if writen to, then passes str to stdout via print"""
    def __init__(self):
        self.text = ''
        self.hadError = False
    def write(self, str):
        self.text = self.text + str
        self.hadError = True 
        print str #send to stdout
    def clear(self):
        self.text = ''
        self.hadError = False

def QALogger(fileName=None, description="No description"):
    ''' Factory method for QALogger '''
    qaLogger = getattr(TestLogger, 'logger', None)
    if qaLogger is None:
        # never created, or already destructed by Close()
        filePath = os.getenv('CATSREPORTDIR')
        if not filePath:
            filePath = os.getcwd()
        filePath = os.path.join(filePath, fileName)
        return TestLogger(filepath=filePath, description=description)
    else:
        # reinitialize existing logger
        qaLogger.toClose = False
        qaLogger.Print("")
        qaLogger.Print("----- Testcase %s = %s -----" %(len(qaLogger.testcaseList)+1, description))
        qaLogger.subTestcaseDesc = description
        qaLogger.testcaseStartDate = datetime.now()
        return qaLogger

class TestLogger:
    def __init__(self,filepath=None,description="No description"):
        self.startDate = datetime.now()
        #capture stderr
        self.old_stderr = sys.stderr #need this so we can go back to it in close()
        self.standardErr = FileWatcher()
        sys.stderr = self.standardErr      
            
        if filepath:
            self.inTerminal = False
    
            # Rename the last log file to timestamped version
            try:
                # getatime returns last mod on Unix, and creation time on Win
                atime = os.path.getatime(filepath)
                time_stamp = time.strftime('%Y%m%d%H%M%S',
                                           time.localtime(atime))
                os.rename(filepath, '%s.%s' % (filepath, time_stamp))
            except OSError:
                # Most likely the file didn't exist, just ignore
                pass
                
            try:
                self.File = open(filepath, 'w')
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
        # By default, enable profiling
        self.enableProfiling = True

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

        if isinstance(string, unicode):
            string = string.encode('utf8')

        if self.inTerminal:
            print "%s" % string
        else:
            self.File.write(string+'\n')
            self.File.flush()

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
        self.Print("OSAF_QA: %s | %s | %s" %(description, version.revision, elapsed_secs)) 
        print("OSAF_QA: %s | %s | %s" %(description, version.revision, elapsed_secs))

    def SuspendProfiling(self):
        """
        Suspend profiling of code between Start()/Stop() calls
        (profiling is usually enabled via the --catsProfile
        command-line option).
        """
        self.enableProfiling = False
        
    def ResumeProfiling(self):
        """
        Resume profiling of code between Start()/Stop() calls.
        (profiling is usually enabled via the --catsProfile
        command-line option)
        """
        self.enableProfiling = True
        
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
        if self.enableProfiling and self.profiler is not None:
            self.profiler.start()
        self.actionStartDate = self.actionEndDate = datetime.now()

    def Stop(self):
        ''' Stop the action timer  '''
        self.actionEndDate = datetime.now()
        if self.enableProfiling and self.profiler is not None:
            self.profiler.stop()
        #report the timing information
        self.Print("Action = "+self.actionDescription)
        if self.actionStartDate == None: # Start method has not been called
            self.Print("!!! No timing information available !!!")
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
        #reset timing info
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
            status = "PASSED"
            self.nbPass = self.nbPass + 1
        elif len(self.failureList) == 0 and not self.checked:
            status = "Uncheck"
            self.nbUnchecked = self.nbUnchecked + 1
        else:
            status = "FAILED"
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

    def ReportException(self, string):
        self.ReportFailure("%s, exception raised:\n%s" %(string, ''.join(traceback.format_exception(*sys.exc_info()))))

    def ReportPass(self, string):
        self.passedList.append(string)

    def SetChecked(self, bool):
        self.checked = bool
        
    def PrintBoth(self, str):
        """use both self.Print and print"""
        self.Print(str)
        print str
                
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
                    if tc[1] == "FAILED":
                        nbTCFailed = nbTCFailed + 1
                    elif tc[1] == "PASSED":
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
                if nbTCPassed == len(self.testcaseList):
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
            #change to fail if output detected on stderr
            if self.standardErr.hadError:
                status = "FAILED"
                self.Print(self.standardErr.text)
            # Tinderbox printing
            # compute the elapsed time in seconds
            elapsed_secs = elapsed.seconds + elapsed.microseconds / 1000000.0
            description = string.join(string.split(self.mainDescription, " "), "_")
            self.Print("")
            self.Print("#TINDERBOX# Testname = %s" %description)    
            self.Print("#TINDERBOX# Status = %s" %status)
            self.Print("#TINDERBOX# Time elapsed = %s (seconds)" %elapsed_secs)
            if status == "PASSED":
                self.PrintTBOX(elapsed)
            self.Print("")
            self.Print("*******               End of Report               *******")
            print("#TINDERBOX# Testname = %s" %description)    
            print("#TINDERBOX# Status = %s" %status)
            print("#TINDERBOX# Time elapsed = %s (seconds)" %elapsed_secs)
            #print names of failed tests and stderr output if there was any
            if status == "FAILED":
                for tc in self.testcaseList:
                    if tc[1] == "FAILED":
                        self.PrintBoth( tc[0] + ' failed')
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
                    status = "PASSED"
                else:
                    status = "FAILED"
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
            if status == "PASSED":
                self.PrintTBOX(elapsed, "Testcase")
            # new testcase inits
            self.Reset()
