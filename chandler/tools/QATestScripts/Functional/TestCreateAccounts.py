import tools.QAUITestAppLib as QAUITestAppLib
from i18n.tests import uw

# initialization
fileName = "TestCreateAccounts.log"
logger = QAUITestAppLib.QALogger(fileName, "TestCreateAccounts")

try:
    # creation
    logger.Start("Account Preferences Dialog")
    ap = QAUITestAppLib.UITestAccounts(logger)

    pSMTP   = uw("Personal SMTP")
    pIMAP   = uw("Personal IMAP")
    pPOP    = uw("Personal POP")
    pWEBDAV = uw("Personal WEBDAV")
    pEMAIL  = "demo1@osafoundation.org"
    pNAME   = uw("Demo One")

    # action
    ap.Open() # first, open the accounts dialog window

    ap.CreateAccount("SMTP") # create a new SMTP account
    ap.TypeValue("displayName", pSMTP)
    ap.TypeValue("host","smtp.osafoundation.org")
    ap.SelectValue("security",  'TLS') # select the TLS radio button
    ap.ToggleValue("authentication", True) # turn on the authentication checkbox
    ap.TypeValue("port", '587')
    ap.TypeValue("email",pEMAIL)
    ap.TypeValue('username', 'demo1')
    ap.TypeValue('password', 'ad3leib5')

    ap.CreateAccount("IMAP")
    ap.TypeValue("displayName", pIMAP)
    ap.TypeValue("email", pEMAIL)
    ap.TypeValue("name", pNAME)
    ap.TypeValue("host", "imap.osafoundation.org")
    ap.TypeValue("username", "demo1")
    ap.TypeValue("password", "ad3leib5")
    ap.SelectValue("security", "SSL")
    ap.ToggleValue("default", True)
    ap.SelectValue("server", pSMTP)

    ap.CreateAccount("POP")
    ap.TypeValue("displayName", pPOP)
    ap.TypeValue("email", pEMAIL)
    ap.TypeValue("name", pNAME)
    ap.TypeValue("host", "pop.osafoundation.org")
    ap.TypeValue("username", "demo1")
    ap.TypeValue("password", "ad3leib5")
    ap.SelectValue("security", "SSL")
    ap.TypeValue("port", "143")
    ap.ToggleValue("leave", True)
    ap.ToggleValue("default", True)
    ap.SelectValue("server", pSMTP)

    ap.CreateAccount("WebDAV")
    ap.TypeValue("displayName", pWEBDAV)
    ap.TypeValue("host", "qacosmo.osafoundation.org")
    ap.TypeValue("path", "home/demo1")
    ap.TypeValue("username", "demo1")
    ap.TypeValue("password", "ad3leib5")
    ap.TypeValue("port", "8080")
    ap.ToggleValue("ssl", False)
    ap.ToggleValue("default", True)

    ap.Ok()
    logger.Stop()

    # verification
    ap.VerifyValues("SMTP", pSMTP, displayName = pSMTP, host= "smtp.osafoundation.org", connectionSecurity = "TLS", useAuth = True, port = 587, username = 'demo1', password = 'ad3leib5' )
    ap.VerifyValues("IMAP", pIMAP, displayName = pIMAP, host = "imap.osafoundation.org", connectionSecurity = "SSL", username = "demo1", password = "ad3leib5")
    ap.VerifyValues("POP", pPOP, displayName = pPOP, host = "pop.osafoundation.org", connectionSecurity = "SSL", username = "demo1", password = "ad3leib5")
    ap.VerifyValues("WebDAV", pWEBDAV, displayName = pWEBDAV, host = "qacosmo.osafoundation.org", username = "demo1", password="ad3leib5", port=8080)

finally:
    # cleaning
    logger.Close()
