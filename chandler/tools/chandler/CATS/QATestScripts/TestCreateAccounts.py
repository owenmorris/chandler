import osaf.framework.scripting.QAUITestAppLib as QAUITestAppLib
import os

filePath = os.path.expandvars('$CATSREPORTDIR')
if not os.path.exists(filePath):
    filePath = os.getcwd()


# initialization
fileName = "TestCreateAccounts.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestCreateAccounts")
logger.Start("Account Preferences Dialog")
ap = QAUITestAppLib.UITestAccounts(app_ns().itsView, logger)

# action
ap.Open() # first, open the accounts dialog window

ap.CreateAccount("SMTP") # create a new SMTP account
ap.TypeValue("displayName", "Personal SMTP") # type the following values into their apporpriate fields
ap.TypeValue("host","smtp.osafoundation.org")
ap.SelectValue("security",  'TLS') # select the TLS radio button
ap.ToggleValue("authentication", True) # turn on the authentication checkbox
ap.TypeValue("port", '25')
ap.TypeValue('username', 'demo1')
ap.TypeValue('password', 'ad3leib5')

ap.CreateAccount("IMAP")
ap.TypeValue("displayName", "Personal IMAP")
ap.TypeValue("email", "demo1@osaofundation.org")
ap.TypeValue("name","Demo One")
ap.TypeValue("host", "imap.osafoundation.org")
ap.TypeValue("username", "demo1")
ap.TypeValue("password", "ad3leib5")
ap.SelectValue("security", "SSL")
ap.ToggleValue("default", True)
ap.SelectValue("server", "Personal SMTP")

ap.CreateAccount("POP")
ap.TypeValue("displayName", "Personal POP")
ap.TypeValue("email", "demo1@osafoundation.org")
ap.TypeValue("name", "Demo One")
ap.TypeValue("host", "pop.osafoundation.org")
ap.TypeValue("username", "demo1")
ap.TypeValue("password", "ad3leib5")
ap.SelectValue("security", "SSL")
ap.TypeValue("port", "143")
ap.ToggleValue("leave", True)
ap.ToggleValue("default", True)
ap.SelectValue("server", "Personal SMTP")

ap.CreateAccount("WebDAV")
ap.TypeValue("displayName", "Personal WebDAV")
ap.TypeValue("host", "qacosmo.osafoundation.org")
ap.TypeValue("path", "home/demo1")
ap.TypeValue("username", "demo1")
ap.TypeValue("password", "ad3leib5")
ap.TypeValue("port", "8080")
ap.ToggleValue("ssl", False)
ap.ToggleValue("default", True)

ap.Ok()
logger.Stop()

#verification
ap.VerifyValues("SMTP", "Personal SMTP", displayName = "Personal SMTP", host= "smtp.osafoundation.org", connectionSecurity = "TLS", useAuth = True, port = 25, username = 'demo1', password = 'ad3leib5' )
ap.VerifyValues("IMAP", "Personal IMAP", displayName = "Personal IMAP", host = "imap.osafoundation.org", connectionSecurity = "SSL", username = "demo1", password = "ad3leib5")
ap.VerifyValues("POP", "Personal POP", displayName = "Personal POP", host = "pop.osafoundation.org", connectionSecurity = "SSL", username = "demo1", password = "ad3leib5")
ap.VerifyValues("WebDAV", "Perosnal WebDAV", displayName = "Personal WebDAV", host = "qacosmo.osafoundation.org", username = "demo1", password="ad3leib5", port=8080)


#cleaning
logger.Close()
