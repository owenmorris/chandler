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


""" Unit test for html only message parsing """

import MailTestCase as MailTestCase
import osaf.mail.message as message
import unittest as unittest

class HTMLMessageTest(MailTestCase.MailTestCase):
    M = """\
Return-Path: <testuser@test.com>
X-Original-To: testuser@test.com
Delivered-To: testuser@test.com
Received: from laweleka.test.com (laweleka.test.com [204.152.186.98])
	by leilani.test.com (Postfix) with ESMTP id 721858021C
	for <testuser@test.com>; Wed,  4 Oct 2006 15:40:20 -0700 (PDT)
Received: from [192.168.1.100] (cpe-66-91-57-35.hawaii.res.rr.com [66.91.57.35])
	(using TLSv1 with cipher DHE-RSA-AES256-SHA (256/256 bits))
	(No client certificate requested)
	by laweleka.test.com (Postfix) with ESMTP id 41A9914227D
	for <testuser@test.com>; Wed,  4 Oct 2006 15:40:20 -0700 (PDT)
Message-ID: <45243860.7040709@test.com>
Date: Wed, 04 Oct 2006 12:40:32 -1000
From: Test User <testuser@test.com>
User-Agent: Thunderbird 1.5.0.7 (Macintosh/20060909)
MIME-Version: 1.0
To: Test User <testuser@test.com>
Subject: HTML BODY TEST
Content-Type: text/html; charset=ISO-8859-1
Content-Transfer-Encoding: 7bit

<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
  <meta content="text/html;charset=ISO-8859-1" http-equiv="Content-Type">
</head>
<body bgcolor="#ffffff" text="#000000">
<blockquote>
  <h2><b>Start of Body</b></h2>
  <p><font color="#cc0000"><big>More text in red</big></font><br>
  </p>
  <br>
</blockquote>
</body>
</html>
"""
    def testHTMLMessage(self):
        mailStamp = message.messageTextToKind(self.rep.view, self.M)
        self.assertEquals(mailStamp.body.strip(), \
                        u"Start of Body\n  \nMore text in red")

if __name__ == "__main__":
   unittest.main()
