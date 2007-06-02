#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
from osaf.pim import has_stamp, Modification, Note, ContentItem
from application import schema
from osaf.framework import password
from osaf.framework.twisted import waitForDeferred

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
        view = self.view

        self.assertEqual(Mail.AccountBase.getKind(view),
                         view.find(Path(mailPath, 'AccountBase')))

        self.assertEqual(Mail.IMAPAccount.getKind(view),
                         view.find(Path(mailPath, 'IMAPAccount')))

        self.assertEqual(Mail.SMTPAccount.getKind(view),
                         view.find(Path(mailPath, 'SMTPAccount')))

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

        mimeBaseObject = Mail.MIMEBase("mimeBaseItem", itsView=view)
        mimeNoteObject = Mail.MIMENote("mimeNoteItem", itsView=view)
        mailMessageObject = Mail.MailMessage("mailMessageItem", itsView=view)
        mimeBinaryObject = Mail.MIMEBinary("mimeBinaryItem", itsView=view)
        mimeTextObject = Mail.MIMEText("mimeTextItem", itsView=view)
        mimeContainerObject = Mail.MIMEContainer("mimeContainerItem", itsView=view)
        mimeSecurityObject = Mail.MIMESecurity("mimeSecurityItem", itsView=view)
        emailAddressItem = Mail.EmailAddress("emailAddressItem", itsView=view)

        # Double check kinds
        self.assertEqual(accountBaseItem.itsKind,
                         Mail.AccountBase.getKind(view))

        self.assertEqual(imapAccountItem.itsKind,
                         Mail.IMAPAccount.getKind(view))

        self.assertEqual(smtpAccountItem.itsKind,
                         Mail.SMTPAccount.getKind(view))

        self.failUnless(isinstance(mimeBaseObject, Mail.MIMEBase))
        self.failUnless(isinstance(mimeNoteObject, Mail.MIMENote))

        self.failUnless(isinstance(mailMessageObject, Mail.MailStamp))
        self.failUnless(isinstance(mailMessageObject.itsItem, Note))
        self.failUnless(has_stamp(mailMessageObject, Mail.MailStamp))

        self.failUnless(isinstance(mimeBinaryObject, Mail.MIMEBinary))

        self.failUnless(isinstance(mimeTextObject, Mail.MIMEText))

        self.failUnless(isinstance(mimeContainerObject, Mail.MIMEContainer))

        self.failUnless(isinstance(mimeSecurityObject, Mail.MIMESecurity))

        self.assertEqual(emailAddressItem.itsKind, Mail.EmailAddress.getKind(view))

        accountBaseItem = self.__populateAccount(accountBaseItem)
        smtpAccountItem = self.__populateAccount(smtpAccountItem)
        imapAccountItem = self.__populateAccount(imapAccountItem)

        mimeBaseObject.mimeType = "SGML"
        mimeBinaryObject.mimeType = "APPLICATION"
        mimeTextObject.mimeType = "PLAIN"
        mimeContainerObject.mimeType = "ALTERNATIVE"
        mimeSecurityObject.mimeType = "SIGNED"

        # Literal properties
        mailMessageObject.dateSent = datetime.now(ICUtzinfo.default)
        mailMessageObject.subject = uw("Hello")
        self.assertEqual(mailMessageObject.subject,
                         mailMessageObject.itsItem.displayName)
        #mailMessageObject.spamScore = 5

        # Item Properties
        emailAddressItem.emailAddress = u"test@test.com"
        mailMessageObject.replyToAddress = emailAddressItem

        self._reopenRepository()
        view = self.view

        contentItemParent = view.findPath("//userdata")
        mailMessageItem = contentItemParent.getItemChild("mailMessageItem")

        #Test cloud membership

        items = mailMessageItem.getItemCloud('copying')
        self.assertEqual(len(items), 3) # item & reply-to address, mimeContent

    def __populateAccount(self, account):

        #XXX: i18n usernames and passwords can be non-ascii.
        # Need to investigate how best to deal with this as 
        # there is no standard. It is server implementation dependent.
        account.username = uw("test")
        account.password = password.Password(itsView=account.itsView,
                                             itsParent=account)
        waitForDeferred(account.password.encryptPassword(uw("test")))
        account.host = uw("test")

        if type(account) == Mail.AccountBase:
            account.port = 1
            account.connectionSecurity = "NONE"

        if type(account) == Mail.SMTPAccount:
            account.fullName = uw("test")
            account.replyToAddress = Mail.EmailAddress(itsView=account.itsView)
            account.replyToAddress.emailAddress = "test@test.com"

    def testAddresses(self):
        allAddressCollection = schema.ns('osaf.pim', self.view).emailAddressCollection
        meAddressCollection = schema.ns('osaf.pim', self.view).meEmailAddressCollection

        def factory(addr, name=u''): 
            return Mail.EmailAddress.getEmailAddress(self.view, addr, name)
        
        normal = factory("bob@mailtest.example.com", "Bob")

        self.failUnless(normal is factory("bob@mailtest.example.com", "Bob"), 
                        "same address parameters should the existing EmailAddress item")
        
        self.failUnless(normal is factory("Bob <bob@mailtest.example.com>"), 
                        "name/address parsing should be consistent")
        
        normalWithoutFullname = factory("bob@mailtest.example.com")
        self.failUnless(normal is not normalWithoutFullname,
                        "fullname absence should be significant")
        
        normalWithDifferentFullname = factory("bob@mailtest.example.com", "Robert")
        self.failUnless(normal is not normalWithDifferentFullname,
                        "fullname difference should be significant")
        
        fullnameOnly = factory("Bob")
        self.failUnless(normal is not fullnameOnly,
                        "emailAddress absence should be significant")
        
        uppercaseAddress = factory("BOB@mailtest.example.com", "Bob")
        self.failUnless(normal is not uppercaseAddress,
                        "comparison is case sensitive on emailAddress")
        uppercaseFullname = factory("bob@mailtest.example.com", "BOB")
        self.failUnless(normal is not uppercaseFullname,
                        "comparison is case sensitive on fullName")
        
        addresses = (normal, normalWithoutFullname, normalWithDifferentFullname,
                     fullnameOnly, uppercaseAddress, uppercaseFullname)
        self.failUnless([ea for ea in addresses if ea not in allAddressCollection] == [],
                        "addresses should show up in the address collection automatically")
        self.failUnless([ea for ea in addresses if ea in meAddressCollection] == [],
                        "addresses should not show up in the 'Me' address collection if they don't belong")
        
        # Make one a "me" address
        outgoingAccount = Mail.getCurrentOutgoingAccount(self.view)
        oldFromAddress = outgoingAccount.fromAddress
        outgoingAccount.fromAddress = normalWithoutFullname
        
        self.failUnless([ea for ea in addresses if ea not in meAddressCollection] == [fullnameOnly],
                        "Addresses matching a 'me' address should become 'me' addresses too")        
        self.failUnless(fullnameOnly not in meAddressCollection,
                        "Addresses not matching a 'me' address should not become 'me' addresses too")
        
        # Put the old account's address back, and remove the addresses we 
        # created from the "me" collection
        outgoingAccount.fromAddress = oldFromAddress
        for ea in addresses:
            if ea in meAddressCollection:
                meAddressCollection.remove(ea)
        
        # Make sure a new address like those doesn't become "me"
        anotherMeLikeAddress = factory("bob@mailtest.example.com", "Bobby")
        self.failUnless(anotherMeLikeAddress not in meAddressCollection,
                        "Once removed, other similar addresses shouldn't appear in 'me'")


class MailWhoTestCase(TestDomainModel.DomainModelTestCase):
    def setUp(self):
        super(MailWhoTestCase, self).setUp()
        self.loadParcel("osaf.pim.mail")
        self.address = Mail.EmailAddress(
                        itsView=self.view,
                        fullName=u"Grant Baillie",
                        emailAddress=u"grant@example.com")

    def testWho(self):
        msg = Mail.MailMessage(itsView=self.view, subject=u"Hi!")
        msg.toAddress=[self.address]

        # Make sure the 'displayWho' field was set correctly
        self.failUnlessEqual(msg.itsItem.displayWho,
                             u"Grant Baillie <grant@example.com>")

         # Now, remove the stamp...
        msg.remove()

        # ... and check the who field is gone
        self.failUnless (not hasattr (msg.itsItem, 'displayWho'))

    def testNoStamp(self):
        # Make sure that, even if we create a Note with a toAddress,
        # that doesn't show up in the who field
        note = Note(itsView=self.view)
        notStampedMsg = Mail.MailStamp(note)
        notStampedMsg.toAddress=[self.address]
        self.failUnless (not hasattr (notStampedMsg.itsItem, 'displayWho'))

class CommunicationStatusTestCase(TestDomainModel.DomainModelTestCase):
    def setUp(self):
        super(CommunicationStatusTestCase, self).setUp()
        self.address = Mail.EmailAddress(
                        itsView=self.view,
                        fullName=u"Mr. President",
                        emailAddress=u"kemal@aturk.tr")
        #account = Mail.IMAPAccount(itsView=self.view,
        #                           replyToAddress=self.address)
        schema.ns('osaf.pim', self.view).meEmailAddressCollection.add(self.address)
        self.note = Note(itsView=self.view)


    def testOrder(self):
        self.failUnless(Mail.CommunicationStatus.UPDATE      <
                        Mail.CommunicationStatus.OUT         <
                        Mail.CommunicationStatus.IN          <
                        Mail.CommunicationStatus.NEITHER     <
                        Mail.CommunicationStatus.EDITED      <
                        Mail.CommunicationStatus.SENT        <
                        Mail.CommunicationStatus.ERROR       <
                        Mail.CommunicationStatus.QUEUED      <
                        Mail.CommunicationStatus.DRAFT       <
                        Mail.CommunicationStatus.NEEDS_REPLY <
                        Mail.CommunicationStatus.READ)

    def checkStatus(self, startStatus, *flagNames):
        expectedStatus = startStatus
        for name in flagNames:
            expectedStatus |= getattr(Mail.CommunicationStatus, name)
        status = Mail.CommunicationStatus(self.note).status
        self.failUnlessEqual(status, expectedStatus, 
            "Unexpected communication status: got %s, expected %s" % 
            (Mail.CommunicationStatus.dump(status), 
             Mail.CommunicationStatus.dump(expectedStatus)))

    def testNote(self):
        self.checkStatus(0)
        self.note.changeEditState(Modification.edited)
        self.checkStatus(0) # edited has no effect till created
        self.note.changeEditState(Modification.created)
        self.checkStatus(0)
        self.note.changeEditState(Modification.edited)
        self.checkStatus(0, 'EDITED')

    def testMail(self):
        self.note = Note(itsView=self.view)
        Mail.MailStamp(self.note).add()
        self.checkStatus(0, 'DRAFT', 'NEITHER')

        # Remove the MailStamp; that should make it no longer a Draft
        Mail.MailStamp(self.note).remove()
        self.checkStatus(0)


    def runMailTest(self, incoming=False, outgoing=False):

        self.note = Note(itsView=self.view)

        mail = Mail.MailStamp(self.note)
        mail.add()
        self.checkStatus(0, 'DRAFT', 'NEITHER')

        inoutFlags = 0
        if incoming:
            inoutFlags |= Mail.CommunicationStatus.IN
            mail.toAddress = self.address
        if outgoing:
            inoutFlags |= Mail.CommunicationStatus.OUT
            mail.fromAddress = self.address
        elif not incoming:
            inoutFlags |= Mail.CommunicationStatus.NEITHER

        self.checkStatus(inoutFlags, 'DRAFT')        

        self.note.changeEditState(Modification.queued)
        self.checkStatus(inoutFlags, 'QUEUED')        

        self.note.changeEditState(Modification.sent)
        self.checkStatus(inoutFlags, 'SENT')

        self.note.changeEditState(Modification.edited)
        self.checkStatus(inoutFlags, 'UPDATE', 'DRAFT')

        # Remove the MailStamp; that should make it no longer a Draft
        mail.remove()
        self.checkStatus(0, 'EDITED')

        # Re-add the stamp
        mail.add()
        self.checkStatus(inoutFlags, 'UPDATE', 'DRAFT')

        # and finally, re-send it
        self.note.changeEditState(Modification.updated)
        self.checkStatus(inoutFlags, 'UPDATE', 'SENT')


    def testOutgoingMail(self):
        self.runMailTest(outgoing=True)

    def testIncomingMail(self):
        self.runMailTest(incoming=True)

    def testInOutMail(self):
        self.runMailTest(incoming=True, outgoing=True)

if __name__ == "__main__":
    unittest.main()
