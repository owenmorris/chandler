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


""" Unit test for Reply, Reply All, Forward """

import MailTestCase as MailTestCase
import osaf.mail.message as message
import osaf.mail.utils as utils
from osaf.pim.mail import *
import unittest as unittest

class TestReplyReplyAllForward(MailTestCase.MailTestCase):
    M1 = """\
To: test@test.com, John Johnson <john@home.com>
Message-Id: <E1Bu9Jy-0007u1-9d@test.com>
From: bill@home.net
Cc: jake@now.com
Date: Mon, 9 Aug 2004 13:55:15 -0700
Content-Length: 75
Content-Transfer-Encoding: 8bit
Mime-Version: 1.0
Received: from [192.168.101.37] (w002.z065106067.sjc-ca.dsl.cnc.net [65.106.67.2]) by kahuna.osafoundation.org (8.12.8/8.12.8) with ESMTP id i7GKWWpo017020; Mon, 16 Aug 2004 13:32:32 -0700
References: <9CF0AF12-ED6F-11D8-B611-000A95B076C2@osafoundation.org> <7542F892-EF9F-11D8-8048-000A95CA1ECC@osafoundation.org> <07A5D499-EFA1-11D8-9F44-000A95D9289E@osafoundation.org> <2EE66978-EFB1-11D8-8048-000A95CA1ECC@osafoundation.org>
In-Reply-To: <9CF0AF12-ED6F-11D8-B611-000A95B076C2@osafoundation.org>
Subject: test mail
Content-Type: text/plain; charset=utf-8; format=flowed

This is the body"""

    M2 = """\
Return-Path: <design-bounces@osafoundation.org>
X-Original-To: bkirsch@osafoundation.org
Delivered-To: bkirsch@osafoundation.org
Received: from leilani.osafoundation.org (leilani.osafoundation.org [127.0.0.1])
	by leilani.osafoundation.org (Postfix) with ESMTP id D92DA7FAAA;
	Fri,  8 Sep 2006 12:55:40 -0700 (PDT)
X-Original-To: design@osafoundation.org
Delivered-To: design@osafoundation.org
Received: from laweleka.osafoundation.org (laweleka.osafoundation.org
	[204.152.186.98])
	by leilani.osafoundation.org (Postfix) with ESMTP id 44B337FA58;
	Fri,  8 Sep 2006 12:55:39 -0700 (PDT)
Received: from localhost (localhost [127.0.0.1])
	by laweleka.osafoundation.org (Postfix) with ESMTP id 33717142286;
	Fri,  8 Sep 2006 12:55:39 -0700 (PDT)
Received: from laweleka.osafoundation.org ([127.0.0.1])
	by localhost (laweleka.osafoundation.org [127.0.0.1]) (amavisd-new,
	port 10024)
	with ESMTP id 24824-05; Fri, 8 Sep 2006 12:55:36 -0700 (PDT)
Received: from linode.visnes.com (li11-18.members.linode.com [70.85.31.18])
	(using TLSv1 with cipher DHE-RSA-AES256-SHA (256/256 bits))
	(No client certificate requested)
	by laweleka.osafoundation.org (Postfix) with ESMTP id 6023F142285;
	Fri,  8 Sep 2006 12:55:36 -0700 (PDT)
Received: from localhost ([127.0.0.1] helo=[192.168.0.2])
	by linode.visnes.com with esmtpa (Exim 4.42)
	id 1GLmRn-0005jC-Ss; Fri, 08 Sep 2006 15:55:32 -0400
Message-ID: <4501CA88.5010303@osafoundation.org>
Date: Fri, 08 Sep 2006 12:54:48 -0700
From: John Anderson <john@osafoundation.org>
User-Agent: Thunderbird 1.5.0.5 (Windows/20060719)
MIME-Version: 1.0
To: Mimi Yin <mimi@osafoundation.org>
Subject: Re: [Design] Dashboard confusing, don't know how to get calendar view
References: <44FF5B63.2040307@osafoundation.org>
	<44FF7ADA.9050201@osafoundation.org>
	<0D486597-2462-4F3D-B27D-8084E1B02726@osafoundation.org>
In-Reply-To: <0D486597-2462-4F3D-B27D-8084E1B02726@osafoundation.org>
X-Virus-Scanned: by amavisd-new and clamav at osafoundation.org
X-Spam-Status: No, hits=-0.3 tagged_above=-50.0 required=4.0 tests=AWL,
	HTML_30_40, HTML_MESSAGE, HTML_TITLE_EMPTY
X-Spam-Level: 
Cc: Heikki Toivonen <heikki@osafoundation.org>,
	Chandler Design list <design@osafoundation.org>
X-BeenThere: design@osafoundation.org
X-Mailman-Version: 2.1.5
Precedence: list
List-Id: Design Discussions <design.osafoundation.org>
List-Unsubscribe: <http://lists.osafoundation.org/mailman/listinfo/design>,
	<mailto:design-request@osafoundation.org?subject=unsubscribe>
List-Archive: <http://lists.osafoundation.org/pipermail/design>
List-Post: <mailto:design@osafoundation.org>
List-Help: <mailto:design-request@osafoundation.org?subject=help>
List-Subscribe: <http://lists.osafoundation.org/mailman/listinfo/design>,
	<mailto:design-request@osafoundation.org?subject=subscribe>
Content-Type: multipart/mixed; boundary="===============0673688943=="
Mime-version: 1.0
Sender: design-bounces@osafoundation.org
Errors-To: design-bounces@osafoundation.org

This is a multi-part message in MIME format.
--===============0673688943==
Content-Type: multipart/alternative;
	boundary="------------000003000304040804010603"

This is a multi-part message in MIME format.
--------------000003000304040804010603
Content-Type: text/plain; charset=ISO-8859-1; format=flowed
Content-Transfer-Encoding: 7bit

One possibility that's easy to implement (at least easier than the 
sidebar work we're doing for 0.7) is to put a "view selector" in the 
summary view, perhaps at the top using a toolbar like we do for stamping 
in the detail view. Each summary view would have it's own selector so 
whenever you went to a particular summary view you'd get the last view 
you chose.

John

Mimi Yin wrote:
> +1
>
> I heartily agree that this is the right design. After discussing it 
> briefly with Philippe, I think this would address some of his concerns 
> as well. The design we have today is a compromise in the face of 
> limited resources and limited time. As a result, a view selector that 
> is independent of the App Area has been relegated to our long list of 
> 'right designs that we can't do for Beta'.
>
> Some of the things we would need to make the view selector design work 
> include:
>
> + Custom toolbar across the top of the sidebar, summary and detail 
> view panes. 
> + Split pane view (a la iCal) with the ability to display a summary 
> table view and a calendar view at the same time.
>
> Mimi
>
> On Sep 6, 2006, at 6:50 PM, John Anderson wrote:
>
>> Hi Heikki:
>>
>> The latest design spec says that Calendar View is only shown for user 
>> collections.
>>
>> Personally, my preference would be to be able to see any collection 
>> (or combination of collections) through any view, i.e. let the user 
>> choose the view.
>>
>> John
>>
>> Heikki Toivonen wrote:
>>> I am somewhat confused about the new dashboard and default view. I look
>>> at the toolbar and see that calendar is selected, and I see (and can
>>> create) more events, yet I don't see the calendar view. I look at View
>>> menu, which has the Calendar entry selected. Looking through the other
>>> menus I have no idea how to get a calendar view.
>>>
>>> The only reason why I actually know calendar view works and how to get
>>> to it was by reading John's checkins comments where he mentioned that
>>> you need to create a collection. And that still does not show the
>>> dashboard items in the calendar view.
>>>
>>> And now that I have a collection of my own and the dashboard, clicking
>>> between them switches between table view and calendar view even though
>>> both show events.
>>>
>>> I am not sure what would be the best way to change this, but the current
>>> situation feels like a wrong approach.
>>>
>>> I think I would expect a PIM to start with a calendar view.
>>>
>>> I also think that Dashboard acts so differently from all the other
>>> collections in the sidebar that I don't think it should be in the
>>> sidebar at all. I think it should be a new button on the toolbar.
>>>
>>>   
>>> ------------------------------------------------------------------------
>>> _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
>>>
>>> Open Source Applications Foundation "Design" mailing list
>>> http://lists.osafoundation.org/mailman/listinfo/design
>>>   
>> _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
>>
>> Open Source Applications Foundation "Design" mailing list
>> http://lists.osafoundation.org/mailman/listinfo/design
>
    """
    M3 = """\
To: test@test.com, John Johnson <john@home.com>
Message-Id: <E1Bu9Jy-0007u1-9d@test.com>
From: bill@home.net
Cc: jake@now.com
Date: Mon, 9 Aug 2004 13:55:15 -0700
Content-Length: 75
Content-Transfer-Encoding: 8bit
Mime-Version: 1.0
Received: from [192.168.101.37] (w002.z065106067.sjc-ca.dsl.cnc.net [65.106.67.2]) by kahuna.osafoundation.org (8.12.8/8.12.8) with ESMTP id i7GKWWpo017020; Mon, 16 Aug 2004 13:32:32 -0700
References: <9CF0AF12-ED6F-11D8-B611-000A95B076C2@osafoundation.org> <7542F892-EF9F-11D8-8048-000A95CA1ECC@osafoundation.org> <07A5D499-EFA1-11D8-9F44-000A95D9289E@osafoundation.org> <2EE66978-EFB1-11D8-8048-000A95CA1ECC@osafoundation.org>
In-Reply-To: <9CF0AF12-ED6F-11D8-B611-000A95B076C2@osafoundation.org>
Subject: [Fwd: test mail]
Content-Type: text/plain; charset=utf-8; format=flowed

This is the body"""

    def setUp(self):
        super(TestReplyReplyAllForward, self).setUp()

        self.messageOne = message.messageTextToKind(self.rep.view, self.M1)
        self.messageTwo = message.messageTextToKind(self.rep.view, self.M2)
        self.messageThree = message.messageTextToKind(self.rep.view, self.M3)

        self.assertTrue(isinstance(self.messageOne, MailMessage))
        self.assertTrue(isinstance(self.messageTwo, MailMessage))
        self.assertTrue(isinstance(self.messageThree, MailMessage))

    def _createMeAddress(self):
        from application import schema
        account = IMAPAccount(itsView=self.rep.view)
        me = EmailAddress(itsView=self.rep.view)
        me.fullName = "Test User"
        me.emailAddress = "test@test.com"
        account.replyToAddress = me
        schema.ns('osaf.pim', self.rep.view).currentMailAccount.item = account

    def testMeLogic(self):
        newMessage = replyToMessage(self.rep.view, self.messageOne)

        self.assertEquals(getattr(newMessage, "fromAddress", None), None)

        self._createMeAddress()

        newMessage = replyToMessage(self.rep.view, self.messageOne)
        self.assertEquals(newMessage.fromAddress.emailAddress, "test@test.com")

    def testReLogic(self):
        newMessage = replyToMessage(self.rep.view, self.messageTwo)

        #Since the original message already started with "Re: " in subject
        #they should be an exact match
        self.assertEquals(newMessage.subject, self.messageTwo.subject)

        newMessage = replyToMessage(self.rep.view, self.messageOne)

        #Tests that an Re: was added to subject
        self.assertEquals(newMessage.subject, "Re: test mail")

    def testFwdLogic(self):
        newMessage = forwardMessage(self.rep.view, self.messageThree)

        #Since the original message already started with "[Fwd: " in subject
        #they should be an exact match
        self.assertEquals(newMessage.subject, self.messageThree.subject)

        newMessage = forwardMessage(self.rep.view, self.messageOne)

        #Tests that an Fwd: was added to subject
        self.assertEquals(newMessage.subject, "Fwd: test mail")

    def testReplyBody(self):
        newMessage = replyToMessage(self.rep.view, self.messageOne)

        self.assertTrue(newMessage.body == \
                 u"\n\non Aug 9, 2004, bill@home.net wrote:\n\n> This is the body""")

    def testInReplyTo(self):
        newMessage = replyToMessage(self.rep.view, self.messageOne)

        self.assertEquals(getattr(newMessage, "inReplyTo", None), u"<E1Bu9Jy-0007u1-9d@test.com>")

    def testReferences(self):
        newMessage = replyToMessage(self.rep.view, self.messageOne)

        ref = [
                u"<9CF0AF12-ED6F-11D8-B611-000A95B076C2@osafoundation.org>",
                u"<7542F892-EF9F-11D8-8048-000A95CA1ECC@osafoundation.org>",
                u"<07A5D499-EFA1-11D8-9F44-000A95D9289E@osafoundation.org>",
                u"<2EE66978-EFB1-11D8-8048-000A95CA1ECC@osafoundation.org>",
                u"<E1Bu9Jy-0007u1-9d@test.com>",
              ]

        self.assertEquals(newMessage.referencesMID, ref)

    def testToAddress(self):
        newMessage = replyToMessage(self.rep.view, self.messageOne)

        #Did the from address of original mail become the to address
        self.assertEquals(len(newMessage.toAddress), 1)

        for addr in newMessage.toAddress:
            self.assertEquals(addr.emailAddress, u"bill@home.net")

    def testCCAddress(self):
        newMessage = replyAllToMessage(self.rep.view, self.messageOne)
        #print message.kindToMessageText(newMessage)

        #The from 'me' address has not been assigned so "test@test.com"
        #should show up in CC list
        addresses = []

        for addr in newMessage.ccAddress:
            addresses.append(EmailAddress.format(addr))

        self.assertTrue(u"test@test.com" in addresses)
        self.assertTrue(u"John Johnson <john@home.com>" in addresses)
        self.assertTrue(u"jake@now.com" in addresses)

        #Set the me address so test@test.com should no longer show up in
        #CC list
        self._createMeAddress()

        newMessage = replyAllToMessage(self.rep.view, self.messageOne)
        addresses = []

        for addr in newMessage.ccAddress:
            addresses.append(EmailAddress.format(addr))

        self.assertFalse(u"test@test.com" in addresses)

    def testForward(self):
        #rfc2882 in attachment
        #body empty
        #no to field
        #for from is set with current me

        self._createMeAddress()
        newMessage = forwardMessage(self.rep.view, self.messageTwo)

        attachments = newMessage.getAttachments()

        for attachment in attachments:
            self.assertTrue(isinstance(attachment, MailMessage))
            rfc2822 = utils.binaryToData(attachment.rfc2822Message)
            self.assertEquals(self.M2, rfc2822)
            break

        self.assertEquals(newMessage.fromAddress.emailAddress, u"test@test.com")
        self.assertEquals(newMessage.body.strip(), u"")
        self.assertEquals(len(newMessage.toAddress), 0)
        self.assertEquals(len(newMessage.ccAddress), 0)
        self.assertEquals(len(newMessage.bccAddress), 0)

        newMessage = forwardMessage(self.rep.view, self.messageOne)
        txt = message.kindToMessageText(newMessage)

        self.assertTrue("Content-Type: multipart/mixed; boundary=" in txt)
        self.assertTrue("Content-Type: message/rfc822" in txt)
        self.assertTrue("This is the body" in txt)


if __name__ == "__main__":
    unittest.main()
