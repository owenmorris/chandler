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
from osaf.pim import has_stamp, Note, ContentItem
from application import schema

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

        self.assertEqual(schema.itemFor(Mail.MIMEBase, view),
                         view.find(Path(mailPath, 'MIMEBase')))

        self.assertEqual(schema.itemFor(Mail.MIMENote, view),
                         view.find(Path(mailPath, 'MIMENote')))

        self.assertEqual(schema.itemFor(Mail.MailStamp, view),
                         view.find(Path(mailPath, 'MailStamp')))

        self.assertEqual(schema.itemFor(Mail.MIMEBinary, view),
                         view.find(Path(mailPath, 'MIMEBinary')))

        self.assertEqual(schema.itemFor(Mail.MIMEText, view),
                         view.find(Path(mailPath, 'MIMEText')))

        self.assertEqual(schema.itemFor(Mail.MIMEContainer, view),
                         view.find(Path(mailPath, 'MIMEContainer')))

        self.assertEqual(schema.itemFor(Mail.MIMESecurity, view),
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
        
        def makeAnnotationItem(cls, name):
            kind = cls.targetType()
            item = kind(name, itsView=view)
            return cls(item) # return the annotation
        
        mimeBaseObject = makeAnnotationItem(Mail.MIMEBase, "mimeBaseItem")
        mimeNoteObject = makeAnnotationItem(Mail.MIMENote, "mimeNoteItem")
        mailMessageObject = Mail.MailMessage("mailMessageItem", itsView=view)
        mimeBinaryObject = makeAnnotationItem(Mail.MIMEBinary, "mimeBinaryItem")
        mimeTextObject = makeAnnotationItem(Mail.MIMEText, "mimeTextItem")
        mimeContainerObject = makeAnnotationItem(Mail.MIMEContainer, "mimeContainerItem")
        mimeSecurityObject = makeAnnotationItem(Mail.MIMESecurity, "mimeSecurityItem")
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

        def checkAnnotation(object, annotationClass, kindClass):
            self.failUnless(isinstance(object, annotationClass))
            self.assertEqual(object.itsItem.itsKind,
                             kindClass.getKind(view))
 
        checkAnnotation(mimeBaseObject, Mail.MIMEBase, ContentItem),
        checkAnnotation(mimeNoteObject, Mail.MIMENote, ContentItem),

        checkAnnotation(mailMessageObject, Mail.MailStamp, Note)
        self.failUnless(has_stamp(mailMessageObject, Mail.MailStamp))

        checkAnnotation(mimeBinaryObject, Mail.MIMEBinary, ContentItem)

        checkAnnotation(mimeTextObject, Mail.MIMEText, ContentItem)

        checkAnnotation(mimeContainerObject, Mail.MIMEContainer, ContentItem)

        checkAnnotation(mimeSecurityObject, Mail.MIMESecurity, ContentItem)

        self.assertEqual(emailAddressItem.itsKind, Mail.EmailAddress.getKind(view))

        accountBaseItem = self.__populateAccount(accountBaseItem)
        smtpAccountItem = self.__populateAccount(smtpAccountItem)
        imapAccountItem = self.__populateAccount(imapAccountItem)

        mailDeliveryErrorItem.errorCode = 25
        mailDeliveryErrorItem.errorString = uw("Test String")
        mailDeliveryErrorItem.errorDate = datetime.now(ICUtzinfo.default)

        smtpDeliveryItem.state = "DRAFT"
        smtpDeliveryItem.deliveryError = mailDeliveryErrorItem
        imapDeliveryItem.uid = 0
        mimeBaseObject.itsItem.mimeType = "SGML"
        mimeBinaryObject.itsItem.mimeType = "APPLICATION"
        mimeTextObject.itsItem.mimeType = "PLAIN"
        mimeContainerObject.itsItem.mimeType = "ALTERNATIVE"
        mimeSecurityObject.itsItem.mimeType = "SIGNED"

        # Literal properties
        mailMessageObject.dateSent = datetime.now(ICUtzinfo.default)
        mailMessageObject.subject = uw("Hello")
        self.assertEqual(mailMessageObject.subject, 
                         mailMessageObject.itsItem.displayName)
        mailMessageObject.spamScore = 5

        # Item Properties
        emailAddressItem.emailAddress = u"test@test.com"
        mailMessageObject.replyToAddress = emailAddressItem

        self._reopenRepository()
        view = self.rep.view

        contentItemParent = view.findPath("//userdata")
        mailMessageItem = contentItemParent.getItemChild("mailMessageItem")

        #Test cloud membership

        items = mailMessageItem.getItemCloud('copying')
        self.assertEqual(len(items), 2) # item & reply-to address

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
            
class MailWhoTestCase(TestDomainModel.DomainModelTestCase):
    def setUp(self):
        super(MailWhoTestCase, self).setUp()
        self.loadParcel("osaf.pim.mail")
        self.address = Mail.EmailAddress(
                        itsView=self.rep.view,
                        fullName=u"Grant Baillie",
                        emailAddress=u"grant@example.com")

    def testWho(self):
        msg = Mail.MailMessage(itsView=self.rep.view, subject=u"Hi!")
        msg.toAddress=[self.address]
        
        # Make sure the 'displayWho' field was set correctly
        self.failUnlessEqual(msg.itsItem.displayWho,
                             u"Grant Baillie <grant@example.com>")
       
         # Now, remove the stamp...
        msg.remove()
        
        # ... and check the who field is blank
        self.failUnlessEqual(msg.itsItem.displayWho, u"")
                             
    def testNoStamp(self):
        # Make sure that, even if we create a Note with a toAddress,
        # that doesn't show up in the who field
        note = Note(itsView=self.rep.view)
        notStampedMsg = Mail.MailStamp(note)
        notStampedMsg.toAddress=[self.address]
        self.failUnlessEqual(notStampedMsg.itsItem.displayWho, u"")
                             
    
if __name__ == "__main__":
    unittest.main()
