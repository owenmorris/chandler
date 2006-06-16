import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
from i18n.tests import uw

class TestNewMail(ChandlerTestCase):

    def startTest(self):
        
        # creation
        mail = QAUITestAppLib.UITestItem("MailMessage", self.logger)
        
        # action
        mail.SetAttr(displayName=uw("Invitation Mail"), toAddress="demo2@osafoundation.org", body=uw("This is an email to invite you"))
        mail.SendMail()
        
        # verification
        mail.Check_DetailView({"displayName":uw("Invitation Mail"),"toAddress":"demo2@osafoundation.org","body":uw("This is an email to invite you")})
