import osaf.framework.scripting.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATS_REPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewMail.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestNewMail")
mail = QAUITestAppLib.UITestItem(__view__, "MailMessage", logger)

#action
mail.logger.Start("Setting attributes of message")
mail.SetAttr(displayName="bar", toAddress="to@foo.org", body="a message")
mail.logger.Stop()

#verification
mail.Check_DetailView({"displayName":"bar","toAddress":"to@foo.org","body":"a message"})

#cleaning
logger.Close()
