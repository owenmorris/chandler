"""
Unit tests for mail
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import OSAF.contentmodel.tests.TestContentModel as TestContentModel
import OSAF.contentmodel.mail.Mail as Mail

import mx.DateTime as DateTime

class MailTest(TestContentModel.ContentModelTestCase):
    """ Test Mail Content Model """

    def testMail(self):
        """ Simple test for creating instances of email related kinds """

        self.loadParcel("OSAF/contentmodel/mail")

        def _verifyMailMessage(message):
            pass

        # Test the globals
        mailPath = '//parcels/OSAF/contentmodel/mail/%s'

        self.assertEqual(Mail.MailParcel.getAttachmentKind(),
                         self.rep.find(mailPath % 'Attachment'))
        self.assertEqual(Mail.MailParcel.getEmailAccountKind(),
                         self.rep.find(mailPath % 'EmailAccount'))
        self.assertEqual(Mail.MailParcel.getEmailAddressKind(),
                         self.rep.find(mailPath % 'EmailAddress'))
        self.assertEqual(Mail.MailParcel.getMailMessageKind(),
                         self.rep.find(mailPath % 'MailMessage'))

        # Construct sample items
        attachmentItem = Mail.Attachment("attachmentItem")
        emailAccountItem = Mail.EmailAccount("emailAccountItem")
        emailAddressItem = Mail.EmailAddress("emailAddressItem")
        mailMessageItem = Mail.MailMessage("mailMessageItem")

        # Double check kinds
        self.assertEqual(attachmentItem.kind,
                         Mail.MailParcel.getAttachmentKind())
        self.assertEqual(emailAccountItem.kind,
                         Mail.MailParcel.getEmailAccountKind())
        self.assertEqual(emailAddressItem.kind,
                         Mail.MailParcel.getEmailAddressKind())
        self.assertEqual(mailMessageItem.kind,
                         Mail.MailParcel.getMailMessageKind())

        # Literal properties
        mailMessageItem.subject = "Hello"
        mailMessageItem.spamScore = 5

        _verifyMailMessage(mailMessageItem)

        self._reopenRepository()

        contentItemParent = self.rep.find("//userdata/contentitems")
        
        mailMessageItem = contentItemParent.find("mailMessageItem")
        _verifyMailMessage(mailMessageItem)
        

if __name__ == "__main__":
    unittest.main()
