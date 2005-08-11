import osaf.framework.scripting.QATestAppLib as QATestAppLib
import os

filePath = os.path.expandvars('$QAPROFILEDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewMail.log"
logger = QATestAppLib.Logger(os.path.join(filePath, fileName),"TestNewMail")
mail = QATestAppLib.BaseByUI(__view__, "MailMessage", logger)

#action
mail.logger.Start("Setting attributes of message")
mail.SetAttr(displayName="bar", toAddress="to@foo.org", body="a message")
mail.logger.Stop()

#verification
mail.Check_DetailView({"displayName":"bar","fromAddress":"from@bar.com","toAddress":"to@foo.org","body":"a message"})
mail.logger.Report()

#cleaning
logger.Close()
