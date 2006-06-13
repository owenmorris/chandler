import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

# These tests help find problems with widget creation and destruction
# that occurs when the user interface is exercised. If a problem occurs
# you should see a traceback.

class TestAdditionalViews(ChandlerTestCase):

    def startTest(self):
        
        self.app_ns.root.AddRepositoryView()
        self.logger.report(True, name='AddRepositoryView')
        self.app_ns.root.AddCPIAView()
        self.logger.report(True, name='AddCPIAView')