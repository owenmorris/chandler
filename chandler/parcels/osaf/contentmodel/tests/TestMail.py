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

        def _verifyMailMessage(message):
            pass

        # Test the globals
        mailPath = Path('//parcels/osaf/contentmodel/mail')

        self.assertEqual(Mail.MailParcel.getAttachmentKind(),
                         self.rep.find(Path(mailPath, 'Attachment')))
        self.assertEqual(Mail.MailParcel.getEmailAccountKind(),
                         self.rep.find(Path(mailPath, 'EmailAccount')))
        self.assertEqual(Mail.MailParcel.getEmailAddressKind(),
                         self.rep.find(Path(mailPath, 'EmailAddress')))
        self.assertEqual(Mail.MailParcel.getMailMessageKind(),
                         self.rep.find(Path(mailPath, 'MailMessage')))


        # Construct sample items
        attachmentItem = Mail.Attachment("attachmentItem")
        emailAccountItem = Mail.EmailAccount("emailAccountItem")
        emailAddressItem = Mail.EmailAddress("emailAddressItem")
        mailMessageItem = Mail.MailMessage("mailMessageItem")

        # Double check kinds
        self.assertEqual(attachmentItem.itsKind,
                         Mail.MailParcel.getAttachmentKind())
        self.assertEqual(emailAccountItem.itsKind,
                         Mail.MailParcel.getEmailAccountKind())
        self.assertEqual(emailAddressItem.itsKind,
                         Mail.MailParcel.getEmailAddressKind())
        self.assertEqual(mailMessageItem.itsKind,
                         Mail.MailParcel.getMailMessageKind())

        # Literal properties
        mailMessageItem.subject = "Hello"
        mailMessageItem.spamScore = 5
        # Item Properties
        mailMessageItem.replyAddress = emailAddressItem

        _verifyMailMessage(mailMessageItem)

        self._reopenRepository()

        contentItemParent = self.rep.findPath("//userdata/contentitems")
        
        mailMessageItem = contentItemParent.getItemChild("mailMessageItem")
        _verifyMailMessage(mailMessageItem)

        cloud = self.manager.lookup("http://osafoundation.org/parcels/osaf/contentmodel/mail",
           "MailMessageMixin/Cloud")

#        items = cloud.getItems(mailMessageItem)
#        self.assertEqual(len(items), 1)


if __name__ == "__main__":
    unittest.main()
