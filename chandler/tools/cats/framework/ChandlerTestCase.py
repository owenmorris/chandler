import osaf.pim as pim
from datetime import date
import osaf.framework.scripting as scripting

class ChandlerTestCase:
    
    def __init__(self, name, logger, recurrence=1, appendVar='', printAppend='', appendDict={}, appendList=[], threadNum=None):
        
        self.results = []
        self.resultNames = []
        self.resultComments = []
        self.recurrence = recurrence
        self.appendVar = str(appendVar)
        self.printAppend = printAppend
        self.threadNum = threadNum
        self.appendDict = appendDict
        self.appendList = appendList
        self.logger = logger
        self.name = name
        self.scripting = scripting
        self.app_ns = scripting.app_ns()
        
    def runTest(self):
        
        self.logger.startTest(name=self.name)
        self.startTest()
        self.logger.endTest()