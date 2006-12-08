import unittest
from application import schema
import TestCollections
from osaf.pim.mail import MailStamp, MailMessage, EmailAddress, IMAPAccount, SMTPAccount
from i18n.tests import uw

"""Tests to confirm In and Out collection Email Address obbservers function properly"""

class InOutCollectionTests(TestCollections.CollectionTestCase):
    def setUp(self):
        super(InOutCollectionTests, self).setUp()

        self.inCol  = schema.ns('osaf.pim', self.view).inCollection
        self.outCol = schema.ns('osaf.pim', self.view).outCollection
        self.meCol  = schema.ns("osaf.pim", self.view).meAddressCollection

        self.m1 = MailMessage(itsView=self.view)
        self.m2 = MailMessage(itsView=self.view)
        self.m3 = MailMessage(itsView=self.view)
        self.m4 = MailMessage(itsView=self.view)
        self.m5 = MailMessage(itsView=self.view)
        self.m6 = MailMessage(itsView=self.view)

        self.e1 = EmailAddress(itsView=self.view)
        self.e1.fullName = uw("Test User1")
        self.e1.emailAddress = u"test1@test.com"

        self.e2 = EmailAddress(itsView=self.view)
        self.e2.fullName = uw("Test User2")
        self.e2.emailAddress = u"test2@test.com"

        self.e3 = EmailAddress(itsView=self.view)
        self.e3.fullName = uw("Test User3")
        self.e3.emailAddress = u"tes3t@test.com"

        self.imapAcct = IMAPAccount(itsView=self.view)
        self.smtpAcct = SMTPAccount(itsView=self.view)


    def testCollectionLogic(self):
        self.m1.toAddress = self.e1
        self.m2.fromAddress = self.e1

        #No me addresses set up yet so m1 and m2
        #should not be in the collections
        self.assertFalse(self.m1.itsItem in self.inCol)
        self.assertFalse(self.m2.itsItem in self.outCol)

        #Set up me address
        self.imapAcct.replyToAddress = self.e1

        #The mail messages should now be in the In and Out collections
        self.assertTrue(self.m1.itsItem in self.inCol)
        self.assertTrue(self.m2.itsItem in self.outCol)

        self.m3.ccAddress = self.e2
        self.m4.replyToAddress =self.e2

        #Make sure m3 and m4 not yet in the collections
        self.assertFalse(self.m3.itsItem in self.inCol)
        self.assertFalse(self.m4.itsItem in self.outCol)

        #Now change the current me address
        self.imapAcct.replyToAddress = self.e2

        #Make sure messages with either the old me
        #address e1 or the new me address e2
        #are in the collections
        self.assertTrue(self.m1.itsItem in self.inCol)
        self.assertTrue(self.m2.itsItem in self.outCol)
        self.assertTrue(self.m3.itsItem in self.inCol)
        self.assertTrue(self.m4.itsItem in self.outCol)

        self.m5.toAddress = self.e3
        self.m6.fromAddress = self.e3

        #Make sure m5 and m6 not yet in the collections
        self.assertFalse(self.m5.itsItem in self.inCol)
        self.assertFalse(self.m6.itsItem in self.outCol)

        #Now add another me address
        self.smtpAcct.fromAddress = self.e3

        #All six messages should now be in the collections
        self.assertTrue(self.m1.itsItem in self.inCol)
        self.assertTrue(self.m2.itsItem in self.outCol)
        self.assertTrue(self.m3.itsItem in self.inCol)
        self.assertTrue(self.m4.itsItem in self.outCol)
        self.assertTrue(self.m5.itsItem in self.inCol)
        self.assertTrue(self.m6.itsItem in self.outCol)

        #confirm that e1, e2, and e2 in meAddressCollection
        self.assertTrue(self.e1 in self.meCol)
        self.assertTrue(self.e2 in self.meCol)
        self.assertTrue(self.e3 in self.meCol)

if __name__ == "__main__":
    unittest.main()
