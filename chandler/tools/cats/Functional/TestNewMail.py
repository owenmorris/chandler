import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase

class TestNewMail(ChandlerTestCase):

    def startTest(self):
        
        # creation
        mail = QAUITestAppLib.UITestItem("MailMessage", self.logger)
        
        # action
        mail.SetAttr(displayName="Invitation Mail", toAddress="demo2@osafoundation.org", body="This is an email to invite you")
        mail.SendMail()
        
        # verification
        mail.Check_DetailView({"displayName":"Invitation Mail","body":"This is an email to invite you"})

