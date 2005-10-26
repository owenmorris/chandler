import tools.QAUITestAppLib as QAUITestAppLib

# initialization
fileName = "TestNewMail.log"
logger = QAUITestAppLib.QALogger(fileName, "TestNewMail")

try:
    # creation
    mail = QAUITestAppLib.UITestItem("MailMessage", logger)
    
    # action
    mail.SetAttr(displayName="Invitation Mail", toAddress="demo2@osafoundation.org", body="This is an email to invite you")
    mail.SendMail()
    
    # verification
    mail.Check_DetailView({"displayName":"Invitation Mail","toAddress":"demo2@osafoundation.org","body":"This is an email to invite you"})
    
finally:
    #cleaning
    logger.Close()
