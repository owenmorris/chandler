import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import osaf.framework.scripting as scripting

class TestDeleteCollection(ChandlerTestCase):
    
    def startTest(self):
    
        # creation
        col = QAUITestAppLib.UITestItem("Collection", self.logger)
        col.SetDisplayName("ToBeDeleted")
    
        # action
        sb = self.app_ns.sidebar
        # move focus from collection name text to collection
        scripting.User.emulate_sidebarClick(sb, 'ToBeDeleted')
        col.DeleteCollection()
    
        # verification
        col.Check_CollectionExistence(expectedResult=False)
    

