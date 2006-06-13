import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class TestNewTask(ChandlerTestCase):

    def startTest(self):

        # creation
        task = QAUITestAppLib.UITestItem("Task", self.logger)
        
        # action
        task.SetAttr(displayName="Task of sending birthday invites", body="Send birthday invitations")
        
        # verification
        task.Check_DetailView({"displayName":"Task of sending birthday invites","body":"Send birthday invitations"})


