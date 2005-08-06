import osaf.framework.scripting.QATestAppLib as QATestAppLib
import os
import string

login = os.getlogin()
plateform = os.uname()[0]
if not string.find(plateform,"Linux") == -1:
    filePath = "/home/%s" %login
elif not string.find(plateform,"Darwin") == -1:
    filePath = "/Users/%s" %login
elif not string.find(plateform,"Windows") == -1:
    filePath = "C:\temp"
else:
    filePath = os.getcwd()
    
#initialization
fileName = "TestNewMail.log"
logger = QATestAppLib.TestLogger(os.path.join(filePath, fileName),"TestNewMail")
mail = QATestAppLib.BaseByUI(__view__, "MailMessage", logger)

#action
mail.logger.Start("Setting attributes of message")
mail.SetAttr(displayName="bar", fromAddress="from@bar.com", toAddress="to@foo.org", body="a message")
mail.logger.Stop()

#verification
mail.Check_DetailView({"displayName":"bar","fromAddress":"from@bar.com","toAddress":"to@foo.org","body":"a message"})
mail.logger.Report()

#cleaning
logger.Close()
