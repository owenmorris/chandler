import tools.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()

#initialization
fileName = "TestNewMail.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewMail")
mail = QAUITestAppLib.UITestItem("MailMessage", logger)

#action
mail.SetAttr(displayName="Invitation Mail", toAddress="demo2@osafoundation.org", body="This is an email to invite you")
mail.SendMail()

#verification
mail.Check_DetailView({"displayName":"Invitation Mail","toAddress":"demo2@osafoundation.org","body":"This is an email to invite you"})

#cleaning
logger.Close()
