import osaf.framework.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewMail.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewMail")
mail = QAUITestAppLib.UITestItem("MailMessage", logger)

#action
mail.logger.Start("Setting attributes of message")
mail.SetAttr(displayName="Invitation Mail", toAddress="olivier@osafoundation.org", body="This is an email to invite you")
mail.logger.Stop()
mail.SendMail()
#verification
mail.Check_DetailView({"displayName":"Invitation Mail","toAddress":"olivier@osafoundation.org","body":"This is an email to invite you"})

#cleaning
logger.Close()
