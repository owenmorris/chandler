import tools.QAUITestAppLib as QAUITestAppLib
from i18n.tests import uw

# initialization
fileName = "TestNewMail.log"
logger = QAUITestAppLib.QALogger(fileName, "TestNewMail")

try:
    # creation
    mail = QAUITestAppLib.UITestItem("MailMessage", logger)

    # action
    mail.SetAttr(displayName=uw("Invitation Mail"), toAddress="demo2@osafoundation.org", body=uw("This is an email to invite you"))
    mail.SendMail()

    # verification
    mail.Check_DetailView({"displayName":uw("Invitation Mail"),"toAddress":"demo2@osafoundation.org","body":uw("This is an email to invite you")})
    
finally:
    #cleaning
    logger.Close()
