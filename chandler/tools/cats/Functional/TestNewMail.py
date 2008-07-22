#   Copyright (c) 2003-2008 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
from i18n.tests import uw

class TestNewMail(ChandlerTestCase):

    def startTest(self):
        ap = QAUITestAppLib.UITestAccounts(self.logger)

        pSMTP   = uw("Personal SMTP")
        pIMAP   = uw("Personal IMAP")
        pPOP    = uw("Personal POP")
        pEMAIL  = "demo1@osafoundation.org"
        pNAME   = uw("Demo One")

        # action
        ap.Open() # first, open the accounts dialog window

        ap.GetDefaultAccount("OUTGOING")
        ap.TypeValue("displayName", pSMTP) # type the following values into their apporpriate fields
        ap.TypeValue("host","smtp.osafoundation.org")
        ap.SelectValue("security",  'TLS') # select the TLS radio button
        ap.ToggleValue("authentication", True) # turn on the authentication checkbox
        ap.TypeValue("port", '587')
        ap.TypeValue("email", pEMAIL)
        ap.TypeValue("name", pNAME)
        ap.TypeValue('username', 'demo1')
        ap.TypeValue('password', 'ad3leib5')

        ap.GetDefaultAccount("INCOMING")
        ap.TypeValue("displayName", pIMAP)
        ap.TypeValue("email", pEMAIL)
        ap.TypeValue("name", pNAME)
        ap.TypeValue("host", "imap.osafoundation.org")
        ap.TypeValue("username", "demo1")
        ap.TypeValue("password", "ad3leib5")
        ap.SelectValue("security", "SSL")
        ap.SelectValue("protocol", "IMAP")

        ap.CreateAccount("INCOMING")
        ap.TypeValue("displayName", pPOP)
        ap.TypeValue("email", pEMAIL)
        ap.TypeValue("name", pNAME)
        ap.TypeValue("host", "pop.osafoundation.org")
        ap.TypeValue("username", "demo1")
        ap.TypeValue("password", "ad3leib5")
        ap.SelectValue("security", "SSL")
        ap.SelectValue("protocol", "POP")

        ap.Ok()

        # verification
        self.logger.startAction("Verifying Account Values")
        ap.VerifyValues("SMTP", pSMTP, host= "smtp.osafoundation.org", connectionSecurity = "TLS", useAuth = True, port = 587, username = 'demo1', password = 'ad3leib5' )
        ap.VerifyValues("IMAP", pIMAP, host = "imap.osafoundation.org", connectionSecurity = "SSL", username = "demo1", password = "ad3leib5")
        ap.VerifyValues("POP", pPOP, host = "pop.osafoundation.org", connectionSecurity = "SSL", username = "demo1", password = "ad3leib5")
        self.logger.endAction(True, "Verifying Account Values")
        
        # creation
        mail = QAUITestAppLib.UITestItem("MailMessage", self.logger)
        
        # action
        mail.SetAttr(displayName=uw("Invitation Mail"), toAddress="demo2@osafoundation.org", body=uw("This is an email to invite you"))
        mail.SendMail()
        
        # verification
        mail.Check_DetailView({"displayName":uw("Invitation Mail"),"toAddress":"demo2@osafoundation.org","body":uw("This is an email to invite you")})
