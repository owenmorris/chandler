import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
from i18n.tests import uw

class TestNewTask(ChandlerTestCase):

    def startTest(self):

        # creation
        task = QAUITestAppLib.UITestItem("Task", self.logger)
        
        # action
        task.SetAttr(displayName=uw("Task of sending birthday invites"), body=uw("Send birthday invitations"))
     
        # verification
        task.Check_DetailView({"displayName":uw("Task of sending birthday invites"),"body":uw("Send birthday invitations")})
 

