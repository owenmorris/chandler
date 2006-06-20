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

"""
Unit tests for mail
"""

import unittest, os

import osaf.pim.tests.TestDomainModel as TestDomainModel
import osaf.pim.mail as Mail

from datetime import datetime
from repository.util.Path import Path
from PyICU import ICUtzinfo
from i18n.tests import uw

class MailTest(TestDomainModel.DomainModelTestCase):
    """ Test Mail Domain Model """

    def testMail(self):
        """ Simple test for creating instances of email related kinds """

        self.loadParcel("osaf.pim.mail")


        # Test the globals
        mailPath = Path('//parcels/osaf/pim/mail')
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
        accountBaseItem = Mail.AccountBase("accountBaseItem", itsView=view)
        imapAccountItem = Mail.IMAPAccount("imapAccountItem", itsView=view)
        smtpAccountItem = Mail.SMTPAccount("smtpAccountItem", itsView=view)
        mailDeliveryErrorItem = Mail.MailDeliveryError("mailDeliveryErrorItem",
                                                       itsView=view)
        mailDeliveryBaseItem = Mail.MailDeliveryBase("mailDeliveryBaseItem",
                                                     itsView=view)
        smtpDeliveryItem = Mail.SMTPDelivery("smtpDeliveryItem", itsView=view)
        imapDeliveryItem = Mail.IMAPDelivery("imapDeliveryItem", itsView=view)
        mimeBaseItem = Mail.MIMEBase("mimeBaseItem", itsView=view)
        mimeNoteItem = Mail.MIMENote("mimeNoteItem", itsView=view)
        mailMessageItem = Mail.MailMessage("mailMessageItem", itsView=view)
        mailMessageMixinItem = Mail.MailMessageMixin("mailMessageMixinItem",
                                                     itsView=view)
        mimeBinaryItem = Mail.MIMEBinary("mimeBinaryItem", itsView=view)
        mimeTextItem = Mail.MIMEText("mimeTextItem", itsView=view)
        mimeContainerItem = Mail.MIMEContainer("mimeContainerItem", itsView=view)
        mimeSecurityItem = Mail.MIMESecurity("mimeSecurityItem", itsView=view)
        emailAddressItem = Mail.EmailAddress("emailAddressItem", itsView=view)

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
        mailDeliveryErrorItem.errorString = uw("Test String")
        mailDeliveryErrorItem.errorDate = datetime.now(ICUtzinfo.default)

        smtpDeliveryItem.state = "DRAFT"
        smtpDeliveryItem.deliveryError = mailDeliveryErrorItem
        imapDeliveryItem.uid = 0
        mimeBaseItem.mimeType = "SGML"
        mimeBinaryItem.mimeType = "APPLICATION"
        mimeTextItem.mimeType = "PLAIN"
        mimeContainerItem.mimeType = "ALTERNATIVE"
        mimeSecurityItem.mimeType = "SIGNED"

        # Literal properties
        mailMessageItem.dateSent = datetime.now(ICUtzinfo.default)
        mailMessageItem.dateReceived = datetime.now(ICUtzinfo.default)
        mailMessageItem.subject = uw("Hello")
        mailMessageItem.spamScore = 5

        # Item Properties
        emailAddressItem.emailAddress = u"test@test.com"
        mailMessageItem.replyAddress = emailAddressItem

        self._reopenRepository()
        view = self.rep.view

        contentItemParent = view.findPath("//userdata")
        mailMessageItem = contentItemParent.getItemChild("mailMessageItem")

        #Test cloud membership

        items = mailMessageItem.getItemCloud('copying')
        self.assertEqual(len(items), 1)

    def __populateAccount(self, account):

        #XXX: i18n usernames and passwords can be non-ascii.
        # Need to investigate how best to deal with this as 
        # there is no standard. It is server implementation dependent.
        account.username = uw("test")
        account.password = uw("test")
        account.host = uw("test")

        if type(account) == Mail.AccountBase:
            account.port = 1
            account.connectionSecurity = "NONE"

        if type(account) == Mail.SMTPAccount:
            account.fullName = uw("test")
            account.replyToAddress = Mail.EmailAddress(itsView=account.itsView)
            account.replyToAddress.emailAddress = "test@test.com"

if __name__ == "__main__":
    unittest.main()
