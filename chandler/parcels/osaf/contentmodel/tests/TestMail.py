"""
Unit tests for mail
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.mail.Mail as Mail

import mx.DateTime as DateTime

from repository.util.Path import Path


class MailTest(TestContentModel.ContentModelTestCase):
    """ Test Mail Content Model """

    def testMail(self):
        """ Simple test for creating instances of email related kinds """

        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/mail")


        # Test the globals
        mailPath = Path('//parcels/osaf/contentmodel/mail')

        self.assertEqual(Mail.MailParcel.getAccountBaseKind(),
                         self.rep.find(Path(mailPath, 'AccountBase')))

        self.assertEqual(Mail.MailParcel.getIMAPAccountKind(),
                         self.rep.find(Path(mailPath, 'IMAPAccount')))

        self.assertEqual(Mail.MailParcel.getSMTPAccountKind(),
                         self.rep.find(Path(mailPath, 'SMTPAccount')))

        self.assertEqual(Mail.MailParcel.getMailDeliveryBaseKind(),
                         self.rep.find(Path(mailPath, 'MailDeliveryBase')))

        self.assertEqual(Mail.MailParcel.getSMTPDeliveryKind(),
                         self.rep.find(Path(mailPath, 'SMTPDelivery')))

        self.assertEqual(Mail.MailParcel.getIMAPDeliveryKind(),
                         self.rep.find(Path(mailPath, 'IMAPDelivery')))

        self.assertEqual(Mail.MailParcel.getMIMEBaseKind(),
                         self.rep.find(Path(mailPath, 'MIMEBase')))

        self.assertEqual(Mail.MailParcel.getMIMENoteKind(),
                         self.rep.find(Path(mailPath, 'MIMENote')))

        self.assertEqual(Mail.MailParcel.getMailMessageKind(),
                         self.rep.find(Path(mailPath, 'MailMessage')))

        self.assertEqual(Mail.MailParcel.getMailMessageMixinKind(),
                         self.rep.find(Path(mailPath, 'MailMessageMixin')))

        self.assertEqual(Mail.MailParcel.getMIMEBinaryKind(),
                         self.rep.find(Path(mailPath, 'MIMEBinary')))

        self.assertEqual(Mail.MailParcel.getMIMETextKind(),
                         self.rep.find(Path(mailPath, 'MIMEText')))

        self.assertEqual(Mail.MailParcel.getMIMEContainerKind(),
                         self.rep.find(Path(mailPath, 'MIMEContainer')))

        self.assertEqual(Mail.MailParcel.getMIMESecurityKind(),
                         self.rep.find(Path(mailPath, 'MIMESecurity')))

        self.assertEqual(Mail.MailParcel.getEmailAddressKind(),
                         self.rep.find(Path(mailPath, 'EmailAddress')))


        # Construct sample items
        accountBaseItem = Mail.AccountBase("accountBaseItem")
        imapAccountItem = Mail.IMAPAccount("imapAccountItem")
        smtpAccountItem = Mail.SMTPAccount("smtpAccountItem")
        mailDeliveryBaseItem = Mail.MailDeliveryBase("mailDeliveryBaseItem")
        smtpDeliveryItem = Mail.SMTPDelivery("smtpDeliveryItem")
        imapDeliveryItem = Mail.IMAPDelivery("imapDeliveryItem")
        mimeBaseItem = Mail.MIMEBase("mimeBaseItem")
        mimeNoteItem = Mail.MIMENote("mimeNoteItem")
        mailMessageItem = Mail.MailMessage("mailMessageItem")
        mailMessageMixinItem = Mail.MailMessageMixin("mailMessageMixinItem")
        mimeBinaryItem = Mail.MIMEBinary("mimeBinaryItem")
        mimeTextItem = Mail.MIMEText("mimeTextItem")
        mimeContainerItem = Mail.MIMEContainer("mimeContainerItem")
        mimeSecurityItem = Mail.MIMESecurity("mimeSecurityItem")
        emailAddressItem = Mail.EmailAddress("emailAddressItem")

        # Double check kinds
        self.assertEqual(accountBaseItem.itsKind,
                         Mail.MailParcel.getAccountBaseKind())

        self.assertEqual(imapAccountItem.itsKind,
                         Mail.MailParcel.getIMAPAccountKind())

        self.assertEqual(smtpAccountItem.itsKind,
                         Mail.MailParcel.getSMTPAccountKind())

        self.assertEqual(mailDeliveryBaseItem.itsKind,
                         Mail.MailParcel.getMailDeliveryBaseKind())

        self.assertEqual(smtpDeliveryItem.itsKind,
                         Mail.MailParcel.getSMTPDeliveryKind())

        self.assertEqual(imapDeliveryItem.itsKind,
                         Mail.MailParcel.getIMAPDeliveryKind())

        self.assertEqual(mimeBaseItem.itsKind,
                         Mail.MailParcel.getMIMEBaseKind())

        self.assertEqual(mimeNoteItem.itsKind,
                         Mail.MailParcel.getMIMENoteKind())

        self.assertEqual(mailMessageItem.itsKind,
                         Mail.MailParcel.getMailMessageKind())

        self.assertEqual(mailMessageMixinItem.itsKind,
                         Mail.MailParcel.getMailMessageMixinKind())

        self.assertEqual(mimeBinaryItem.itsKind,
                         Mail.MailParcel.getMIMEBinaryKind())

        self.assertEqual(mimeTextItem.itsKind,
                         Mail.MailParcel.getMIMETextKind())

        self.assertEqual(mimeContainerItem.itsKind,
                         Mail.MailParcel.getMIMEContainerKind())

        self.assertEqual(mimeSecurityItem.itsKind,
                         Mail.MailParcel.getMIMESecurityKind())

        self.assertEqual(emailAddressItem.itsKind,
                         Mail.MailParcel.getEmailAddressKind())

        accountBaseItem = self.__populateAccount(accountBaseItem)
        smtpAccountItem = self.__populateAccount(smtpAccountItem)
        imapAccountItem = self.__populateAccount(imapAccountItem)

        mailDeliveryBaseItem.deliveryType = "POP"
        smtpDeliveryItem.deliveryType = "SMTP"
        smtpDeliveryItem.state = "DRAFT"
        imapDeliveryItem.deliveryType = "IMAP"
        imapDeliveryItem.uid = 0
        mimeBaseItem.mimeType = "SGML"
        mimeBinaryItem.mimeType = "APPLICATION"
        mimeTextItem.mimeType = "PLAIN"
        mimeContainerItem.mimeType = "ALTERNATIVE"
        mimeSecurityItem.mimeType = "SIGNED"

        # Literal properties
        mailMessageItem.dateSent = DateTime.now()
        mailMessageItem.dateReceived = DateTime.now()
        mailMessageItem.subject = "Hello"
        mailMessageItem.spamScore = 5

        # Item Properties
        emailAddressItem.emailAddress = "test@test.com"
        mailMessageItem.replyAddress = emailAddressItem

        self._reopenRepository()

        contentItemParent = self.rep.findPath("//userdata/contentitems")

        mailMessageItem = contentItemParent.getItemChild("mailMessageItem")

        #Test cloud membership
        cloud = self.manager.lookup("http://osafoundation.org/parcels/osaf/contentmodel/mail",
           "MailMessageMixin/Cloud")

        items = cloud.getItems(mailMessageItem)
        self.assertEqual(len(items), 1)

    def __populateAccount(self, account):

        account.username = "test"
        account.password = "test"
        account.host = "test"

        if type(account) == Mail.AccountBase:
            account.port = 1
            account.portSSL = 1
            account.useSSL = 'NoSSL'

        if type(account) == Mail.SMTPAccount:
            account.fullName = "test"
            account.replyToAddress = Mail.EmailAddress()
            account.replyToAddress.emailAddress = "test@test.com"

if __name__ == "__main__":
    unittest.main()
