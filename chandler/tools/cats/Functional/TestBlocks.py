import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

# These tests help find problems with widget creation and destruction
# that occurs when the user interface is exercised. If a problem occurs
# you should see a traceback.

class TestBlocks(ChandlerTestCase):
    
    def startTest(self):
    
        self.logger.startAction('TestBlocks')
        self.app_ns.root.ChooseCPIATestMainView()
        self.logger.addComment('CPIATestMainView ')
        self.app_ns.root.ChooseChandlerMainView()
        self.logger.addComment( 'ChandlerMainView')
        self.app_ns.root.ReloadParcels()
        self.logger.addComment('ReloadParcels')
        self.logger.endAction(True, 'TestBlocks complete')


