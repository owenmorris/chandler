"""
Unit tests for mail
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
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

        self.assertEqual(Mail.AccountBase.getKind(),
                         self.rep.find(Path(mailPath, 'AccountBase')))

        self.assertEqual(Mail.IMAPAccount.getKind(),
                         self.rep.find(Path(mailPath, 'IMAPAccount')))

        self.assertEqual(Mail.SMTPAccount.getKind(),
                         self.rep.find(Path(mailPath, 'SMTPAccount')))

        self.assertEqual(Mail.MailDeliveryError.getKind(),
                         self.rep.find(Path(mailPath, 'MailDeliveryError')))

        self.assertEqual(Mail.MailDeliveryBase.getKind(),
                         self.rep.find(Path(mailPath, 'MailDeliveryBase')))

        self.assertEqual(Mail.SMTPDelivery.getKind(),
                         self.rep.find(Path(mailPath, 'SMTPDelivery')))

        self.assertEqual(Mail.IMAPDelivery.getKind(),
                         self.rep.find(Path(mailPath, 'IMAPDelivery')))

        self.assertEqual(Mail.MIMEBase.getKind(),
                         self.rep.find(Path(mailPath, 'MIMEBase')))

        self.assertEqual(Mail.MIMENote.getKind(),
                         self.rep.find(Path(mailPath, 'MIMENote')))

        self.assertEqual(Mail.MailMessage.getKind(),
                         self.rep.find(Path(mailPath, 'MailMessage')))

        self.assertEqual(Mail.MailMessageMixin.getKind(),
                         self.rep.find(Path(mailPath, 'MailMessageMixin')))

        self.assertEqual(Mail.MIMEBinary.getKind(),
                         self.rep.find(Path(mailPath, 'MIMEBinary')))

        self.assertEqual(Mail.MIMEText.getKind(),
                         self.rep.find(Path(mailPath, 'MIMEText')))

        self.assertEqual(Mail.MIMEContainer.getKind(),
                         self.rep.find(Path(mailPath, 'MIMEContainer')))

        self.assertEqual(Mail.MIMESecurity.getKind(),
                         self.rep.find(Path(mailPath, 'MIMESecurity')))

        self.assertEqual(Mail.EmailAddress.getKind(),
                         self.rep.find(Path(mailPath, 'EmailAddress')))


        # Construct sample items
        accountBaseItem = Mail.AccountBase("accountBaseItem")
        imapAccountItem = Mail.IMAPAccount("imapAccountItem")
        smtpAccountItem = Mail.SMTPAccount("smtpAccountItem")
        mailDeliveryErrorItem = Mail.MailDeliveryError("mailDeliveryErrorItem")
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
                         Mail.AccountBase.getKind())

        self.assertEqual(imapAccountItem.itsKind,
                         Mail.IMAPAccount.getKind())

        self.assertEqual(smtpAccountItem.itsKind,
                         Mail.SMTPAccount.getKind())

        self.assertEqual(mailDeliveryErrorItem.itsKind,
                         Mail.MailDeliveryError.getKind())

        self.assertEqual(mailDeliveryBaseItem.itsKind,
                         Mail.MailDeliveryBase.getKind())

        self.assertEqual(smtpDeliveryItem.itsKind,
                         Mail.SMTPDelivery.getKind())

        self.assertEqual(imapDeliveryItem.itsKind,
                         Mail.IMAPDelivery.getKind())

        self.assertEqual(mimeBaseItem.itsKind,
                         Mail.MIMEBase.getKind())

        self.assertEqual(mimeNoteItem.itsKind,
                         Mail.MIMENote.getKind())

        self.assertEqual(mailMessageItem.itsKind,
                         Mail.MailMessage.getKind())

        self.assertEqual(mailMessageMixinItem.itsKind,
                         Mail.MailMessageMixin.getKind())

        self.assertEqual(mimeBinaryItem.itsKind,
                         Mail.MIMEBinary.getKind())

        self.assertEqual(mimeTextItem.itsKind,
                         Mail.MIMEText.getKind())

        self.assertEqual(mimeContainerItem.itsKind,
                         Mail.MIMEContainer.getKind())

        self.assertEqual(mimeSecurityItem.itsKind,
                         Mail.MIMESecurity.getKind())

        self.assertEqual(emailAddressItem.itsKind,
                         Mail.EmailAddress.getKind())

        accountBaseItem = self.__populateAccount(accountBaseItem)
        smtpAccountItem = self.__populateAccount(smtpAccountItem)
        imapAccountItem = self.__populateAccount(imapAccountItem)

        mailDeliveryErrorItem.errorCode = 25
        mailDeliveryErrorItem.errorString = "Test String"
        mailDeliveryErrorItem.errorDate = DateTime.now()

        mailDeliveryBaseItem.deliveryType = "POP"
        smtpDeliveryItem.deliveryType = "SMTP"
        smtpDeliveryItem.state = "DRAFT"
        smtpDeliveryItem.deliveryError = mailDeliveryErrorItem
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
        outbound = contentItemParent.getItemChild("outboundMailItems")

        mailMessageItem = outbound.getItemChild("mailMessageItem")

        #Test cloud membership

        # the code below is wrong. It should be:
        #     items = mailMessageItem.getItemCloud('default')
        #     self.assertEqual(len(items), 1)

        cloud = self.manager.lookup("http://osafoundation.org/parcels/osaf/contentmodel/mail",
           "MailMessageMixin/Cloud")

        items = cloud.getItems(mailMessageItem, 'default')
        self.assertEqual(len(items), 1)

    def __populateAccount(self, account):

        account.username = "test"
        account.password = "test"
        account.host = "test"

        if type(account) == Mail.AccountBase:
            account.port = 1
            account.useSSL = False

        if type(account) == Mail.SMTPAccount:
            account.fullName = "test"
            account.replyToAddress = Mail.EmailAddress()
            account.replyToAddress.emailAddress = "test@test.com"

if __name__ == "__main__":
    unittest.main()
