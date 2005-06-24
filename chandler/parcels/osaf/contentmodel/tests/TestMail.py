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

from datetime import datetime
from repository.util.Path import Path


class MailTest(TestContentModel.ContentModelTestCase):
    """ Test Mail Content Model """

    def testMail(self):
        """ Simple test for creating instances of email related kinds """

        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/mail")


        # Test the globals
        mailPath = Path('//parcels/osaf/contentmodel/mail')
        view = self.rep.view
        
        self.assertEqual(Mail.AccountBase.getKind(view),
                         view.find(Path(mailPath, 'AccountBase')))

        self.assertEqual(Mail.IMAPAccount.getKind(view),
                         view.find(Path(mailPath, 'IMAPAccount')))

        self.assertEqual(Mail.SMTPAccount.getKind(view),
                         view.find(Path(mailPath, 'SMTPAccount')))

        self.assertEqual(Mail.MailDeliveryError.getKind(view),
                         view.find(Path(mailPath, 'MailDeliveryError')))

        self.assertEqual(Mail.MailDeliveryBase.getKind(view),
                         view.find(Path(mailPath, 'MailDeliveryBase')))

        self.assertEqual(Mail.SMTPDelivery.getKind(view),
                         view.find(Path(mailPath, 'SMTPDelivery')))

        self.assertEqual(Mail.IMAPDelivery.getKind(view),
                         view.find(Path(mailPath, 'IMAPDelivery')))

        self.assertEqual(Mail.MIMEBase.getKind(view),
                         view.find(Path(mailPath, 'MIMEBase')))

        self.assertEqual(Mail.MIMENote.getKind(view),
                         view.find(Path(mailPath, 'MIMENote')))

        self.assertEqual(Mail.MailMessage.getKind(view),
                         view.find(Path(mailPath, 'MailMessage')))

        self.assertEqual(Mail.MailMessageMixin.getKind(view),
                         view.find(Path(mailPath, 'MailMessageMixin')))

        self.assertEqual(Mail.MIMEBinary.getKind(view),
                         view.find(Path(mailPath, 'MIMEBinary')))

        self.assertEqual(Mail.MIMEText.getKind(view),
                         view.find(Path(mailPath, 'MIMEText')))

        self.assertEqual(Mail.MIMEContainer.getKind(view),
                         view.find(Path(mailPath, 'MIMEContainer')))

        self.assertEqual(Mail.MIMESecurity.getKind(view),
                         view.find(Path(mailPath, 'MIMESecurity')))

        self.assertEqual(Mail.EmailAddress.getKind(view),
                         view.find(Path(mailPath, 'EmailAddress')))


        # Construct sample items
        accountBaseItem = Mail.AccountBase("accountBaseItem", view=view)
        imapAccountItem = Mail.IMAPAccount("imapAccountItem", view=view)
        smtpAccountItem = Mail.SMTPAccount("smtpAccountItem", view=view)
        mailDeliveryErrorItem = Mail.MailDeliveryError("mailDeliveryErrorItem",
                                                       view=view)
        mailDeliveryBaseItem = Mail.MailDeliveryBase("mailDeliveryBaseItem",
                                                     view=view)
        smtpDeliveryItem = Mail.SMTPDelivery("smtpDeliveryItem", view=view)
        imapDeliveryItem = Mail.IMAPDelivery("imapDeliveryItem", view=view)
        mimeBaseItem = Mail.MIMEBase("mimeBaseItem", view=view)
        mimeNoteItem = Mail.MIMENote("mimeNoteItem", view=view)
        mailMessageItem = Mail.MailMessage("mailMessageItem", view=view)
        mailMessageMixinItem = Mail.MailMessageMixin("mailMessageMixinItem",
                                                     view=view)
        mimeBinaryItem = Mail.MIMEBinary("mimeBinaryItem", view=view)
        mimeTextItem = Mail.MIMEText("mimeTextItem", view=view)
        mimeContainerItem = Mail.MIMEContainer("mimeContainerItem", view=view)
        mimeSecurityItem = Mail.MIMESecurity("mimeSecurityItem", view=view)
        emailAddressItem = Mail.EmailAddress("emailAddressItem", view=view)

        # Double check kinds
        self.assertEqual(accountBaseItem.itsKind,
                         Mail.AccountBase.getKind(view))

        self.assertEqual(imapAccountItem.itsKind,
                         Mail.IMAPAccount.getKind(view))

        self.assertEqual(smtpAccountItem.itsKind,
                         Mail.SMTPAccount.getKind(view))

        self.assertEqual(mailDeliveryErrorItem.itsKind,
                         Mail.MailDeliveryError.getKind(view))

        self.assertEqual(mailDeliveryBaseItem.itsKind,
                         Mail.MailDeliveryBase.getKind(view))

        self.assertEqual(smtpDeliveryItem.itsKind,
                         Mail.SMTPDelivery.getKind(view))

        self.assertEqual(imapDeliveryItem.itsKind,
                         Mail.IMAPDelivery.getKind(view))

        self.assertEqual(mimeBaseItem.itsKind,
                         Mail.MIMEBase.getKind(view))

        self.assertEqual(mimeNoteItem.itsKind,
                         Mail.MIMENote.getKind(view))

        self.assertEqual(mailMessageItem.itsKind,
                         Mail.MailMessage.getKind(view))

        self.assertEqual(mailMessageMixinItem.itsKind,
                         Mail.MailMessageMixin.getKind(view))

        self.assertEqual(mimeBinaryItem.itsKind,
                         Mail.MIMEBinary.getKind(view))

        self.assertEqual(mimeTextItem.itsKind,
                         Mail.MIMEText.getKind(view))

        self.assertEqual(mimeContainerItem.itsKind,
                         Mail.MIMEContainer.getKind(view))

        self.assertEqual(mimeSecurityItem.itsKind,
                         Mail.MIMESecurity.getKind(view))

        self.assertEqual(emailAddressItem.itsKind,
                         Mail.EmailAddress.getKind(view))

        accountBaseItem = self.__populateAccount(accountBaseItem)
        smtpAccountItem = self.__populateAccount(smtpAccountItem)
        imapAccountItem = self.__populateAccount(imapAccountItem)

        mailDeliveryErrorItem.errorCode = 25
        mailDeliveryErrorItem.errorString = "Test String"
        mailDeliveryErrorItem.errorDate = datetime.now()

        smtpDeliveryItem.state = "DRAFT"
        smtpDeliveryItem.deliveryError = mailDeliveryErrorItem
        imapDeliveryItem.uid = 0
        mimeBaseItem.mimeType = "SGML"
        mimeBinaryItem.mimeType = "APPLICATION"
        mimeTextItem.mimeType = "PLAIN"
        mimeContainerItem.mimeType = "ALTERNATIVE"
        mimeSecurityItem.mimeType = "SIGNED"

        # Literal properties
        mailMessageItem.dateSent = datetime.now()
        mailMessageItem.dateReceived = datetime.now()
        mailMessageItem.subject = "Hello"
        mailMessageItem.spamScore = 5

        # Item Properties
        emailAddressItem.emailAddress = "test@test.com"
        mailMessageItem.replyAddress = emailAddressItem

        self._reopenRepository()
        view = self.rep.view
        
        contentItemParent = view.findPath("//userdata")
        outbound = contentItemParent.getItemChild("mailItems")

        mailMessageItem = outbound.getItemChild("mailMessageItem")

        #Test cloud membership

        items = mailMessageItem.getItemCloud('default')
        self.assertEqual(len(items), 1)

    def __populateAccount(self, account):

        account.username = "test"
        account.password = "test"
        account.host = "test"

        if type(account) == Mail.AccountBase:
            account.port = 1
            account.connectionSecurity = "NONE"

        if type(account) == Mail.SMTPAccount:
            account.fullName = "test"
            account.replyToAddress = Mail.EmailAddress(view=account.itsView)
            account.replyToAddress.emailAddress = "test@test.com"

if __name__ == "__main__":
    unittest.main()
