# The fastest way to cleanly quit Chandler
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import os
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib

class quit(ChandlerTestCase):

    def startTest(self):
        filePath = os.getenv('CATSREPORTDIR')
        if not filePath:
            filePath = os.getcwd()
        fileName = "quit.log"
        self.logger.Start("quit")
        self.logger.SetChecked(True)
        self.logger.Report("quit")
        self.logger.Close()

