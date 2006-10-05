#   Copyright (c) 2004-2006 Open Source Applications Foundation
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


""" Unit test for message parsing """

import MailTestCase as MailTestCase
import osaf.mail.message as message
import osaf.mail.utils as utils
import osaf.pim.mail as Mail
import email as email
import email.Message as Message
import email.Utils as emailUtils
import unittest as unittest
from repository.item.RefCollections import RefList
from osaf.pim.stamping import has_stamp
from osaf.pim.mail import MailStamp
from osaf.pim.calendar import EventStamp

from PyICU import ICUtzinfo
from datetime import datetime


class MessageTest(MailTestCase.MailTestCase):

    __mail = """To: test@testuser.com, John Johnson <john@home.com>
Message-Id: <E1Bu9Jy-0007u1-9d@test.com>
From: bill@home.net
Cc: jake@now.com
Date: Mon, 9 Aug 2004 13:55:15 -0700
Content-Length: 75
Content-Transfer-Encoding: 8bit
Mime-Version: 1.0
Received: from [192.168.101.37] (w002.z065106067.sjc-ca.dsl.cnc.net [65.106.67.2]) by kahuna.test.com (8.12.8/8.12.8) with ESMTP id i7GKWWpo017020; Mon, 16 Aug 2004 13:32:32 -0700
References: <9CF0AF12-ED6F-11D8-B611-000A95B076C2@test.com> <7542F892-EF9F-11D8-8048-000A95CA1ECC@test.com> <07A5D499-EFA1-11D8-9F44-000A95D9289E@test.com> <2EE66978-EFB1-11D8-8048-000A95CA1ECC@test.com>
Subject: test mail
Content-Type: text/plain; charset=utf-8; format=flowed

This is the body"""

    __mailWithEvent = """Return-Path: <sir.strawberry@gmail.com>
X-Original-To: capt.crunch@yahoo.com
Delivered-To: capt.crunch@yahoo.com
Received: from laweleka.test.com (laweleka.test.com [204.152.186.98])
	by leilani.test.com (Postfix) with ESMTP id 1D5607FAFA
	for <capt.crunch@yahoo.com>; Fri,  8 Sep 2006 09:16:44 -0700 (PDT)
Received: from localhost (localhost [127.0.0.1])
	by laweleka.test.com (Postfix) with ESMTP id 07A71142276
	for <capt.crunch@yahoo.com>; Fri,  8 Sep 2006 09:16:44 -0700 (PDT)
Received: from laweleka.test.com ([127.0.0.1])
	by localhost (laweleka.test.com [127.0.0.1]) (amavisd-new, port 10024)
	with ESMTP id 10491-10 for <capt.crunch@yahoo.com>;
	Fri, 8 Sep 2006 09:16:42 -0700 (PDT)
Received: from wx-out-0506.google.com (wx-out-0506.google.com [66.249.82.226])
	by laweleka.test.com (Postfix) with ESMTP id 9AC1614228B
	for <capt.crunch@yahoo.com>; Fri,  8 Sep 2006 09:16:42 -0700 (PDT)
Received: by wx-out-0506.google.com with SMTP id i30so925749wxd
        for <capt.crunch@yahoo.com>; Fri, 08 Sep 2006 09:16:42 -0700 (PDT)
Received: by 10.70.47.19 with SMTP id u19mr428339wxu;
        Fri, 08 Sep 2006 09:16:41 -0700 (PDT)
Received: from localhost ( [71.198.128.206])
        by mx.gmail.com with ESMTP id 35sm421990wra.2006.09.08.09.16.40;
        Fri, 08 Sep 2006 09:16:41 -0700 (PDT)
Message-ID: <20060908161637.13058.91624@localhost>
Date: Fri, 08 Sep 2006 09:16:37 -0700
From: sir.strawberry@gmail.com
To: capt.crunch@yahoo.com
User-Agent: Chandler (0.7alpha3)
Content-Transfer-Encoding: 8bit
Subject: Interview w/ Count Chocula
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="===============0937948688=="
X-Chandler-EventDescriptionLength: 54

--===============0937948688==
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: base64

V2hlbjogVHVlc2RheSwgU2VwIDUsIDIwMDYgMzowMCBQTSAtIDQ6MDAgUE0KV2hlcmU6IE96CgoK

--===============0937948688==
Content-Type: text/calendar; charset="utf-8"; method="REQUEST"
MIME-Version: 1.0
Content-Disposition: attachment; filename="event.ics"

BEGIN:VCALENDAR
VERSION:2.0
METHOD:REQUEST
PRODID:-//PYVOBJECT//NONSGML Version 1//EN
BEGIN:VEVENT
UID:bdf62c0c-39e8-11db-e3ed-8cdcc2c2c3d9
DTSTART:20060905T150000
DTEND:20060905T160000
DESCRIPTION:
LOCATION:Oz
STATUS:CONFIRMED
SUMMARY:Interview w/ Count Chocula
END:VEVENT
END:VCALENDAR

--===============0937948688==--
"""

    __addresses = [None, "    ", "john", "sd$%dsd@dsd-fffd!.com", "bill.jones@tc.unernet.com"]

    def __getMessageObject(self):
        if self.__messageObject is None:
           self.__messageObject = email.message_from_string(self.__mail)

        return self.__messageObject

    def __getMessageText(self):
        return self.__mail

    def __getMultipartMessageText(self):
        return self.__mailWithEvent

    def __getMailMessage(self):
        if self.__mailMessage is not None:
            return self.__mailMessage

        view = self.rep.view
        m = Mail.MailMessage(itsView=view)
        m.fromAddress = Mail.EmailAddress(itsView=view)
        m.fromAddress.emailAddress = "bill@home.net"

        toOne = Mail.EmailAddress(itsView=view)
        toOne.emailAddress = "test@testuser.com"

        toTwo = Mail.EmailAddress(itsView=view)
        toTwo.emailAddress = "john@home.com"
        toTwo.fullName = "John Johnson"

        m.toAddress = []
        m.toAddress.append(toOne)
        m.toAddress.append(toTwo)

        ccOne = Mail.EmailAddress(itsView=view)
        ccOne.emailAddress = "jake@now.com"

        m.ccAddress = []
        m.ccAddress.append(ccOne)

        m.subject = "test mail"
        m.headers['Content-Length'] = "75"
        m.headers['Content-Type'] = "text/plain; charset=utf-8; format=flowed"
        m.headers['Content-Transfer-Encoding'] = "8bit"
        m.headers['Mime-Version'] = "1.0"

        m.headers['Received'] = "from [192.168.101.37] (w002.z065106067.sjc-ca.dsl.cnc.net [65.106.67.2]) by kahuna.test.com (8.12.8/8.12.8) with ESMTP id i7GKWWpo017020; Mon, 16 Aug 2004 13:32:32 -0700"

        m.headers['References'] = "<9CF0AF12-ED6F-11D8-B611-000A95B076C2@test.com> <7542F892-EF9F-11D8-8048-000A95CA1ECC@test.com> <07A5D499-EFA1-11D8-9F44-000A95D9289E@test.com> <2EE66978-EFB1-11D8-8048-000A95CA1ECC@test.com>"

        dateString = "Mon, 9 Aug 2004 13:55:15 -0700"
        m.dateSent = datetime.fromtimestamp(emailUtils.mktime_tz(emailUtils.parsedate_tz(dateString)), ICUtzinfo.getInstance("Etc/GMT-7"))
        m.dateSentString = dateString

        m.itsItem.body = u"This is the body"
        m.rfc2822Message = utils.dataToBinary(m, "rfc2822Message", self.__mail)

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
        self.assertNotEqual(dOne, None)
        self.assertNotEqual(dTwo, None)

        self.assertEquals(dOne, dTwo)

    def __compareMailMessages(self, mOne, mTwo):
        self.assertNotEqual(mOne, None)
        self.assertNotEqual(mTwo, None)

        self.__compareEmailAddressLists(mOne.toAddress, mTwo.toAddress)
        self.__compareEmailAddressLists(mOne.ccAddress, mTwo.ccAddress)

        self.__compareDateTimes(mOne.dateSent, mTwo.dateSent)

        self.assertEquals(mOne.fromAddress.emailAddress, mTwo.fromAddress.emailAddress)

        self.assertEquals(mOne.subject, mTwo.subject)
        self.assertEquals(mOne.headers['Content-Length'], mTwo.headers['Content-Length'])
        self.assertEquals(mOne.headers['Content-Type'], mTwo.headers['Content-Type'])
        self.assertEquals(mOne.headers['Content-Transfer-Encoding'], mTwo.headers['Content-Transfer-Encoding'])
        self.assertEquals(mOne.headers['Mime-Version'], mTwo.headers['Mime-Version'])
        self.assertEquals(mOne.itsItem.body, mTwo.itsItem.body)
        self.assertEquals(utils.binaryToData(mOne.rfc2822Message), utils.binaryToData(mTwo.rfc2822Message))


    def __compareMessageObjects(self, mOne, mTwo):
        self.assertNotEqual(mOne, None)
        self.assertNotEqual(mTwo, None)

        self.assertEquals(mOne['From'], mTwo['From'])
        self.assertEquals(mOne['To'], mTwo['To'])
        self.assertEquals(mOne['Cc'], mTwo['Cc'])
        self.assertEquals(mOne['Content-Length'], mTwo['Content-Length'])
        self.assertEquals(mOne['Content-Transfer-Encoding'], mTwo['Content-Transfer-Encoding'])
        self.assertEquals(mOne['Mime-Version'], mTwo['Mime-Version'])
        self.assertEquals(mOne['Subject'], mTwo['Subject'])


        dOne = emailUtils.parsedate(mOne['Date'])
        dTwo = emailUtils.parsedate(mTwo['Date'])

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
        mailKind = message.messageTextToKind(self.rep.view, self.__getMessageText())

        self.assertNotEqual(mailKind, None)

        self.__compareMailMessages(mailKind, self.__getMailMessage())

    def testMessageWithEvent(self):
        eventMessage = message.messageTextToKind(self.rep.view, self.__getMultipartMessageText())
        self.assertTrue(has_stamp(eventMessage, MailStamp))
        self.assertTrue(has_stamp(eventMessage, EventStamp))

    def testMessageObjectToKind(self):
        mailKind = message.messageObjectToKind(self.rep.view, self.__getMessageObject(), self.__mail)

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
        self.loadParcel("osaf.pim.mail")
        self.__messageObject = None
        self.__mailMessage = None

if __name__ == "__main__":
   unittest.main()
