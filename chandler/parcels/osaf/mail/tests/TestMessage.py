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
import repository.persistence.XMLRefDict as XMLRefDict

import mx.DateTime as MXDateTime


class MessageTest(MailTestCase.MailTestCase):

    __mail = """To:test@testuser.com, John Johnson <john@home.com>
Message-Id: <E1Bu9Jy-0007u1-9d@test.com>
From: bill@home.net
Cc: jake@now.com
Bcc: don@we.com
Date: Mon, 9 Aug 2004 13:55:15 -0700
Subject: test mail

This is the body"""

    __addresses = [None, "    ", "john", "sd$%dsd@dsd-fffd!.com", "bill.jones@tc.unernet.com"]


    def __getMessageObject(self):
        if self.__messageObject is None:
           self.__messageObject = email.message_from_string(self.__mail)

        return self.__messageObject

    def __getMessageText(self):
        return self.__mail

    ###Add in Body read
    def __getMailMessage(self):
        if self.__mailMessage is not None:
            return self.__mailMessage

        m = Mail.MailMessage()
        m.replyAddress = Mail.EmailAddress()
        m.replyAddress.emailAddress = message.format_addr(Utils.parseaddr("bill@home.net"))

        toOne = Mail.EmailAddress()
        toOne.emailAddress = message.format_addr(Utils.parseaddr("test@testuser.com"))

        toTwo = Mail.EmailAddress()
        toTwo.emailAddress = message.format_addr(Utils.parseaddr("John Johnson <john@home.com>"))

        m.toAddress = []
        m.toAddress.append(toOne)
        m.toAddress.append(toTwo)

        ccOne = Mail.EmailAddress()
        ccOne.emailAddress = message.format_addr(Utils.parseaddr("jake@now.com"))

        m.ccAddress = []
        m.ccAddress.append(ccOne)

        bccOne = Mail.EmailAddress()
        bccOne.emailAddress = message.format_addr(Utils.parseaddr("don@we.com"))

        m.bccAddress = []
        m.bccAddress.append(bccOne)

        m.subject = "test mail"

        date = Utils.parsedate("Mon, 9 Aug 2004 13:55:15 -0700")

        m.dateSent = MXDateTime.mktime(date)
        m.dateReceived = MXDateTime.now()

        self.__mailMessage = m

        return self.__mailMessage

    def __compareEmailAddressLists(self, adOne, adTwo):
        self.assertNotEqual(adOne, XMLRefDict.XMLRefDict)
        self.assertNotEqual(adTwo, XMLRefDict.XMLRefDict)
        self.assertEqual(len(adOne), len(adTwo))

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
            str = "Email Addresses do not match: ", ", ".join(tempList)
            self.fail(str)

    def __compareDateTimes(self, dOne, dTwo):
        ### XXX: Figure out what DateTime object is in Repository
        self.assertNotEqual(dOne, None)
        self.assertNotEqual(dTwo, None)

        self.assertEqual(dOne.strftime(), dTwo.strftime())

    def __compareMailMessages(self, mOne, mTwo):
        self.assertNotEqual(mOne, None)
        self.assertNotEqual(mTwo, None)

        self.__compareEmailAddressLists(mOne.toAddress, mTwo.toAddress)
        self.__compareEmailAddressLists(mOne.ccAddress, mTwo.ccAddress)
        self.__compareEmailAddressLists(mOne.bccAddress, mTwo.bccAddress)
        self.__compareDateTimes(mOne.dateSent, mTwo.dateSent)

        self.assertEquals(mOne.subject, mTwo.subject)

        ###Add in body test

    def __compareMessageObjects(self, mOne, mTwo):
        self.assertNotEqual(mOne, None)
        self.assertNotEqual(mTwo, None)

        self.assertEquals(mOne['From'], mTwo['From'])
        self.assertEquals(mOne['To'], mTwo['To'])
        self.assertEquals(mOne['Cc'], mTwo['Cc'])
        self.assertEquals(mOne['Bcc'], mTwo['Bcc'])


        dOne = Utils.parsedate(mOne['Date'])
        dTwo = Utils.parsedate(mTwo['Date'])

        for i in range(6):
            if dOne[i] != dTwo[i]:
               self.fail("Dates do not match %s != %s" % (mOne['Date'], mTwo['Date']))

        self.assertEquals(mOne['Subject'], mTwo['Subject'])


    def testEmailValidation(self):
         self.assertEquals(message.isValidEmailAddress(self.__addresses[0]), False)
         self.assertEquals(message.isValidEmailAddress(self.__addresses[1]), False)
         self.assertEquals(message.isValidEmailAddress(self.__addresses[2]), False)
         self.assertEquals(message.isValidEmailAddress(self.__addresses[3]), False)
         self.assertEquals(message.isValidEmailAddress(self.__addresses[4]), True)

    def testMessageTextToKind(self):
        """Conditions:
           1. Only strings can be passed to messageTextToKind
           2. Should return a Mail.MailMessage object containing the
              values passed
        """

        self.assertRaises(TypeError, message.messageTextToKind, None)

        mailKind = message.messageTextToKind(self.__getMessageText())

        self.assertNotEqual(mailKind, None)

        self.__compareMailMessages(mailKind, self.__getMailMessage())


    def testMessageObjectToKind(self):
        """Conditions:
           1. Only email.Message objects can be passed to messageObjectToKind
           2. Should return a Mail.MailMessage object containing the    values passed
        """

        self.assertRaises(TypeError, message.messageObjectToKind, "Error")

        mailKind = message.messageObjectToKind(self.__getMessageObject())

        self.assertNotEqual(mailKind, None)

        self.__compareMailMessages(mailKind, self.__getMailMessage())


    def testKindToMessageText(self):
        """Conditions:
           1. Only Mail.MailMessage objects  can be passed to kindToMessageText
           2. Should return a string object containing the
              values passed
        """
        self.assertRaises(TypeError, message.kindToMessageText, "Error")

        mailText = message.kindToMessageText(self.__getMailMessage())
        mailObject = email.message_from_string(mailText)

        self.__compareMessageObjects(mailObject, self.__getMessageObject())


    def testKindToMessageObject(self):
        """Conditions:
           1. Only Mail.MailMessage objects  can be passed to kindToMessageObject
           2. Should return a email.Message object containing the
              values passed
        """

        self.assertRaises(TypeError, message.kindToMessageObject, "Error")

        messageObject = message.kindToMessageObject(self.__getMailMessage())

        self.__compareMessageObjects(messageObject, self.__getMessageObject())

    def setUp(self):
        super(MessageTest, self).setUp()
        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel/mail")
        self.__messageObject = None
        self.__mailMessage = None

if __name__ == "__main__":
   unittest.main()
