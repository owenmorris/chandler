import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
    
class TestMulti(ChandlerTestCase):    
    
    def startTest(self):
        
        # action -- Setup mail accounts
        #execfile(os.path.join(functional_dir,"TestCreateAccounts.py"))
        
        ## Create Accounts for Mail 
        
        ap = QAUITestAppLib.UITestAccounts(self.logger)
        
        # action
        self.logger.startAction("Setup email account")
        ap.Open() # first, open the accounts dialog window
        ap.CreateAccount("SMTP") # create a new SMTP account
        ap.TypeValue("displayName", "Personal SMTP") # type the following values into their apporpriate fields
        ap.TypeValue("host","smtp.osafoundation.org")
        ap.SelectValue("security",  'TLS') # select the TLS radio button
        ap.ToggleValue("authentication", True) # turn on the authentication checkbox
        ap.TypeValue("port", '587')
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
        
        ap.Ok()
        self.logger.endAction(True)
        
        # verification
        ap.VerifyValues("SMTP", "Personal SMTP", displayName = "Personal SMTP", host= "smtp.osafoundation.org", connectionSecurity = "TLS", useAuth = True, port = 587, username = 'demo1', password = 'ad3leib5' )
        ap.VerifyValues("IMAP", "Personal IMAP", displayName = "Personal IMAP", host = "imap.osafoundation.org", connectionSecurity = "SSL", username = "demo1", password = "ad3leib5")
         
        ## End Create accounts for Mail
        
        # action -- Create new Collection
        col = QAUITestAppLib.UITestItem("Collection", self.logger)
        # action -- Set the Display name for new Collection
        col.SetDisplayName("TestCollection")
        # verification -- Initial Existense of Collection
        col.Check_CollectionExistence("TestCollection")
        
        # creation
        note = QAUITestAppLib.UITestItem("Note", self.logger)
        # action -- Add to TestCollection
        note.AddCollection("TestCollection")
        # action -- Set Note attributes
        note.SetAttr(displayName="Test Note in TestCollection", body="This is the body, can i give it \n for new line.")
        # action -- Stamp as Mail message
        note.StampAsMailMessage(True)
        # action -- Set attributes for mail sending
        note.SetAttr(toAddress="demo2@osafoundation.org")
        # action -- Send the Mail message
        note.SendMail()
        # action -- Stamp as Calendar message
        note.StampAsCalendarEvent(True)
        # action -- Set Event attributes
        note.SetAttr(startDate="09/12/2004", startTime="6:00 PM", location="Club101", status="FYI",timeZone="US/Central", recurrence="Daily", recurrenceEnd="9/14/2005")
        
        # verification -- Collection Display
        col.Check_CollectionExistence("TestCollection")
        # verification -- note object in TestCollection
        note.Check_ItemInCollection("TestCollection")
        # verification -- Note Attributes
        note.Check_DetailView({"displayName":"Test Note in TestCollection","body":"This is the body, can i give it \n for new line."})
        # verification -- Test Stamps
        note.Check_DetailView({"stampMail":True,"stampEvent":True})
        # verification -- Test Mail Attributes
        note.Check_DetailView({"toAddress":"demo2@osafoundation.org"})
        # verification -- Test Calendar Event Attributes ## Notice that Chandler takes recurrenceEnd="9/14/2005" but the viewer fixes this to display as "9/14/05"
        note.Check_DetailView({"startDate":"9/12/04","startTime":"6:00 PM","location":"Club101","status":"FYI","timeZone":"US/Central","recurrence":"Daily","recurrenceEnd":"9/14/05"})
    

