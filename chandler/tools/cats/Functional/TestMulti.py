#   Copyright (c) 2003-2006 Open Source Applications Foundation
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
from osaf import pim

class TestMulti(ChandlerTestCase):    
    
    def startTest(self):
        
        # action -- Setup mail accounts
        #execfile(os.path.join(functional_dir,"TestCreateAccounts.py"))
        
        ## Create Accounts for Mail 
        
        ap = QAUITestAppLib.UITestAccounts(self.logger)
        
        # action
        self.logger.startAction("Setup email account")
        ap.Open() # first, open the accounts dialog window
        ap.GetDefaultAccount("OUTGOING") # get the default SMTP account
        ap.TypeValue("displayName", uw("Personal SMTP")) # type the following values into their apporpriate fields
        ap.TypeValue("host","smtp.osafoundation.org")
        ap.SelectValue("security",  'TLS') # select the TLS radio button
        ap.ToggleValue("authentication", True) # turn on the authentication checkbox
        ap.TypeValue("port", '587')
        ap.TypeValue('username', 'demo1')
        ap.TypeValue('password', 'ad3leib5')

        ap.GetDefaultAccount("INCOMING")
        ap.TypeValue("displayName", uw("Personal IMAP"))
        ap.TypeValue("email", "demo1@osafoundation.org")
        ap.TypeValue("name", uw("Demo One"))
        ap.TypeValue("host", "imap.osafoundation.org")
        ap.TypeValue("username", "demo1")
        ap.TypeValue("password", "ad3leib5")
        ap.SelectValue("security", "SSL")
        ap.SelectValue("protocol", "IMAP")
        
        ap.Ok()
        self.logger.endAction(True)
        
        # verification
        ap.VerifyValues("SMTP", uw("Personal SMTP"), host= "smtp.osafoundation.org", connectionSecurity = "TLS", useAuth = True, port = 587, username = 'demo1', password = 'ad3leib5' )
        ap.VerifyValues("IMAP", uw("Personal IMAP"), host = "imap.osafoundation.org", connectionSecurity = "SSL", username = "demo1", password = "ad3leib5")
 
        ## End Create accounts for Mail
        
        # action -- Create new Collection
        col = QAUITestAppLib.UITestItem("Collection", self.logger)
        # action -- Set the Display name for new Collection
        col.SetDisplayName(uw("TestCollection"))
        # verification -- Initial Existense of Collection
        col.Check_CollectionExistence(uw("TestCollection"))
        
        # creation
        note = QAUITestAppLib.UITestItem("Note", self.logger)
        # action -- Add to TestCollection
        note.AddCollection(uw("TestCollection"))
        # action -- Stamp as Mail message
        note.StampAsMailMessage(True)

        # action -- Set Note attributes
        #XXX Moving the attribute setting after stamping
        #    fixes an issue where the displayName was not getting set.
        #    I am not sure of the reasoning of why this was
        #    failing but believe it has to do
        #    with either the CATS or CPIA layers
        note.SetAttr(displayName= uw("Test Note in TestCollection"), body=uw("This is the body, can i give it \n for new line."))

        # action -- Set attributes for mail sending
        note.SetAttr(toAddress="demo2@osafoundation.org")
        # action -- Send the Mail message
        note.SendMail()
        # action -- Stamp as Calendar message
        note.StampAsCalendarEvent(True)
        # action -- Set Event attributes
        note.SetAttr(startDate="09/12/2006", startTime="6:00 PM", location=uw("Club101"), status="FYI",timeZone="America/Chicago", recurrence="Daily", recurrenceEnd="10/14/2006")

        # adding recurrence will have caused UITestItem to have the master
        # as its item.  That doesn't work very well for selection, since the
        # last occurrence is the only row that will be displayed in the
        # Dashboard, so set note's item to the (single) modification
        #note.item = pim.EventStamp(note.item).modifications.first()
        
        # verification -- Collection Display
        col.Check_CollectionExistence(uw("TestCollection"))
        # verification -- note object in TestCollection
        note.Check_ItemInCollection(uw("TestCollection"))
        ## verification -- Note Attributes
        #note.Check_DetailView({"displayName":uw("Test Note in TestCollection"), "body":uw("This is the body, can i give it \n for new line.")})
        ## verification -- Test Stamps
        #note.Check_DetailView({"stampMail":True,"stampEvent":True})
        ## verification -- Test Mail Attributes
        #note.Check_DetailView({"toAddress":"demo2@osafoundation.org"})
        ## verification -- Test Calendar Event Attributes ## Notice that Chandler takes recurrenceEnd="9/14/2005" but the viewer fixes this to display as "9/14/05"
        #note.Check_DetailView({"displayName":uw("Test Note in TestCollection"), "body":uw("This is the body, can i give it \n for new line.")})
