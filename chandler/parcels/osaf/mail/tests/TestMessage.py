__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Unit test for message parsing """

import MailTestCase as MailTestCase
import osaf.mail.message as message
import osaf.contentmodel.mail.Mail as Mail
import email as email
import email.Message as Message
import email.Utils as Utils
import unittest as unittest
from repository.item.RefCollections import RefList

import mx.DateTime as MXDateTime


class MessageTest(MailTestCase.MailTestCase):

    __mail = """To: test@testuser.com, John Johnson <john@home.com>
Message-Id: <E1Bu9Jy-0007u1-9d@test.com>
From: bill@home.net
Cc: jake@now.com
Bcc: don@we.com
Date: Mon, 9 Aug 2004 13:55:15 -0700
Content-Length: 75
Content-Transfer-Encoding: us-ascii
Mime-Version: 1.0
Received: from [192.168.101.37] (w002.z065106067.sjc-ca.dsl.cnc.net [65.106.67.2]) by kahuna.osafoundation.org (8.12.8/8.12.8) with ESMTP id i7GKWWpo017020; Mon, 16 Aug 2004 13:32:32 -0700
In-Reply-To: <2EE66978-EFB1-11D8-8048-000A95CA1ECC@osafoundation.org>
References: <9CF0AF12-ED6F-11D8-B611-000A95B076C2@osafoundation.org> <7542F892-EF9F-11D8-8048-000A95CA1ECC@osafoundation.org> <07A5D499-EFA1-11D8-9F44-000A95D9289E@osafoundation.org> <2EE66978-EFB1-11D8-8048-000A95CA1ECC@osafoundation.org>
Subject: test mail
Content-Type: text/plain

This is the body"""

    __addresses = [None, "    ", "john", "sd$%dsd@dsd-fffd!.com", "bill.jones@tc.unernet.com"]

    def __getMessageObject(self):
        if self.__messageObject is None:
           self.__messageObject = email.message_from_string(self.__mail)

        return self.__messageObject

    def __getMessageText(self):
        return self.__mail

    def __getMailMessage(self):
        if self.__mailMessage is not None:
            return self.__mailMessage

        m = Mail.MailMessage()
        m.fromAddress = Mail.EmailAddress()
        m.fromAddress.emailAddress = "bill@home.net"

        toOne = Mail.EmailAddress()
        toOne.emailAddress = "test@testuser.com"

        toTwo = Mail.EmailAddress()
        toTwo.emailAddress = "john@home.com"
        toTwo.fullName = "John Johnson"

        m.toAddress = []
        m.toAddress.append(toOne)
        m.toAddress.append(toTwo)

        ccOne = Mail.EmailAddress()
        ccOne.emailAddress = "jake@now.com"

        m.ccAddress = []
        m.ccAddress.append(ccOne)

        bccOne = Mail.EmailAddress()
        bccOne.emailAddress = "don@we.com"

        m.bccAddress = []
        m.bccAddress.append(bccOne)

        m.subject = "test mail"
        dateString = "Mon, 9 Aug 2004 13:55:15 -0700"
        m.contentLength = "75"
        m.contentType = "text/plain"
        m.contentTransferEncoding = "us-ascii"
        m.mimeVersion = "1.0"
        m.inReplyTo = "<2EE66978-EFB1-11D8-8048-000A95CA1ECC@osafoundation.org>"

        #XXX: This will need to be updated to handle multiple received headers
        m.received.append("from [192.168.101.37] (w002.z065106067.sjc-ca.dsl.cnc.net [65.106.67.2]) by kahuna.osafoundation.org (8.12.8/8.12.8) with ESMTP id i7GKWWpo017020; Mon, 16 Aug 2004 13:32:32 -0700")

        #XXX: This will need to be updated laterQ
        m.references.append("<9CF0AF12-ED6F-11D8-B611-000A95B076C2@osafoundation.org> <7542F892-EF9F-11D8-8048-000A95CA1ECC@osafoundation.org> <07A5D499-EFA1-11D8-9F44-000A95D9289E@osafoundation.org> <2EE66978-EFB1-11D8-8048-000A95CA1ECC@osafoundation.org>")

        m.dateSent = MXDateTime.mktime(Utils.parsedate(dateString))
        m.dateSentString = dateString
        m.dateReceived = MXDateTime.now()
        m.body = message.strToText(m, "body", "This is the body")
        m.rfc2822Message = message.strToText(m, "rfc2822Message", self.__mail)

        self.__mailMessage = m

        return self.__mailMessage

    def __compareEmailAddressLists(self, adOne, adTwo):

        self.assertNotEqual(adOne, RefList)
        self.assertNotEqual(adTwo, RefList)

        self.assertEquals(len(adOne), len(adTwo))

        tempDict = {}
        tempList = []

        for address in adOne:
            tempDict[address.emailAddress] = ""

        for address in adTwo:
            try:
                dummy = tempDict[address.emailAddress]

            except KeyError:
                tempList.append(address.emailAddress)

        if len(tempList) > 0:
            print "Email Addresses do not match:", ", ".join(tempList)
            self.fail(str)

    def __compareDateTimes(self, dOne, dTwo):
        ### XXX: Figure out what DateTime object is in Repository
        self.assertNotEqual(dOne, None)
        self.assertNotEqual(dTwo, None)

        self.assertEquals(dOne.strftime(), dTwo.strftime())

    def __compareMailMessages(self, mOne, mTwo):
        self.assertNotEqual(mOne, None)
        self.assertNotEqual(mTwo, None)

        self.__compareEmailAddressLists(mOne.toAddress, mTwo.toAddress)
        self.__compareEmailAddressLists(mOne.ccAddress, mTwo.ccAddress)
        self.__compareEmailAddressLists(mOne.bccAddress, mTwo.bccAddress)

        self.__compareDateTimes(mOne.dateSent, mTwo.dateSent)

        self.assertEquals(mOne.fromAddress.emailAddress, mTwo.fromAddress.emailAddress)

        self.assertEquals(mOne.subject, mTwo.subject)
        self.assertEquals(mOne.contentLength, mTwo.contentLength)
        self.assertEquals(mOne.contentType, mTwo.contentType)
        self.assertEquals(mOne.contentTransferEncoding, mTwo.contentTransferEncoding)
        self.assertEquals(mOne.mimeVersion, mTwo.mimeVersion)
        self.assertEquals(mOne.inReplyTo, mTwo.inReplyTo)
        self.assertEquals(message.textToStr(mOne.body), message.textToStr(mTwo.body))
        self.assertEquals(message.textToStr(mOne.rfc2822Message), message.textToStr(mTwo.rfc2822Message))


    def __compareMessageObjects(self, mOne, mTwo):
        self.assertNotEqual(mOne, None)
        self.assertNotEqual(mTwo, None)

        self.assertEquals(mOne['From'], mTwo['From'])
        self.assertEquals(mOne['To'], mTwo['To'])
        self.assertEquals(mOne['Cc'], mTwo['Cc'])
        self.assertEquals(mOne['Bcc'], mTwo['Bcc'])
        self.assertEquals(mOne['Content-Length'], mTwo['Content-Length'])
        self.assertEquals(mOne['Content-Type'], mTwo['Content-Type'])
        self.assertEquals(mOne['Content-Transfer-Encoding'], mTwo['Content-Transfer-Encoding'])
        self.assertEquals(mOne['Mime-Version'], mTwo['Mime-Version'])
        self.assertEquals(mOne['In-Reply-To'], mTwo['In-Reply-To'])
        self.assertEquals(mOne['Subject'], mTwo['Subject'])


        dOne = Utils.parsedate(mOne['Date'])
        dTwo = Utils.parsedate(mTwo['Date'])

        for i in range(6):
            if dOne[i] != dTwo[i]:
               self.fail("Dates do not match %s != %s" % (mOne['Date'], mTwo['Date']))

        self.assertEquals(mOne.get_payload(), mTwo.get_payload())

    #XXX: This needs work
    def assertListEquals(self, list1, list2):
         self.assertEquals(len(list1), len(list2))

         size = len(list1)

         for i in range(size):
             self.assertEquals(list1[i], list2[i])

    #XXX:needs woek
    def assertDictEquals(dict1, dict2):
         self.assertEquals(dict1, dict)
         self.assertEquals(dict2, dict)

         self.assertEquals(len(dict1), len(dict2))

         l1 = dict1.keys()
         l2 = dict2.keys()

         size = len(l1)

         for i in range(size):
             self.assertEquals(l1[i], l2[i])
             self.assertEquals(dict1[l1[i]], dict2[l2[i]])

    def testMessageTextToKind(self):
        mailKind = message.messageTextToKind(self.__getMessageText())

        self.assertNotEqual(mailKind, None)

        self.__compareMailMessages(mailKind, self.__getMailMessage())

    def testMessageObjectToKind(self):
        mailKind = message.messageObjectToKind(self.__getMessageObject(), self.__mail)

        self.assertNotEqual(mailKind, None)

        self.__compareMailMessages(mailKind, self.__getMailMessage())

    def testKindToMessageText(self):
        mailText = message.kindToMessageText(self.__getMailMessage())
        mailObject = email.message_from_string(mailText)

        self.__compareMessageObjects(mailObject, self.__getMessageObject())

    def testKindToMessageObject(self):
        messageObject = message.kindToMessageObject(self.__getMailMessage())

        self.__compareMessageObjects(messageObject, self.__getMessageObject())

    def testEmailValidation(self):
         self.assertEquals(Mail.EmailAddress.isValidEmailAddress(self.__addresses[1]), False)
         self.assertEquals(Mail.EmailAddress.isValidEmailAddress(self.__addresses[2]), False)
         self.assertEquals(Mail.EmailAddress.isValidEmailAddress(self.__addresses[3]), False)
         self.assertEquals(Mail.EmailAddress.isValidEmailAddress(self.__addresses[4]), True)

    def setUp(self):
        super(MessageTest, self).setUp()
        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/mail")
        self.__messageObject = None
        self.__mailMessage = None

if __name__ == "__main__":
   unittest.main()
