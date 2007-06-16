#   Copyright (c) 2004-2007 Open Source Applications Foundation
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


""" Unit test for i18n message parsing """

import pkg_resources, email

import osaf.mail.tests.MailTestCase as MailTestCase
import osaf.mail.message as message
import unittest


class MessageI18nTest(MailTestCase.MailTestCase):
    def testI18nMessage(self):
        """
           Basic unit test which loads a mail message
           in the utf-8 charset encoding off the filesystem
           and converts the bytes to a Chandler
           C{Mail.MailMessage}.

           This Chandler c{Mail.MailMessage} is then 
           converted back to bytes for sending.
           The bytes contained in the To, From, Subject,
           and Body payload are compared with the original.

           This test confirms that encoded headers
           are decoded to Unicode, The Body is converted
           from bytes to Unicode, and that the headers and
           Body are properly encoded back to bytes.

           A header in a non-ascii charset
           should be encoded for sending. For example:

           To: =?utf-8?b?IsSFxI3EmcSXxK/FocWzxavFviDEhMSMxJjElsSuxaDFssWqxb0i?= <testreceive@test.com>
        """

        msgText = self.__loadTestMessage()

        mOne = email.message_from_string(msgText)
        messageKind = message.messageObjectToKind(self.view, mOne, msgText)
        mTwo  = message.kindToMessageObject(messageKind)

        self.assertEquals(mOne['To'], mTwo['To'])
        self.assertEquals(mOne['From'], mTwo['From'])
        self.assertEquals(mOne['Subject'], mTwo['Subject'])
        o = mOne.get_payload(decode=True)
        self.assertEquals(o, mTwo.get_payload()[0].get_payload()[1].get_payload(decode=True))

    def __loadTestMessage(self):

        fp = pkg_resources.resource_stream('debug', 'i18n_tests/test_i18n_utf8')
        messageText = fp.read()
        fp.close()

        return message.addCarriageReturn(messageText)

    def setUp(self):
        super(MessageI18nTest, self).setUp()
        self.loadParcel("osaf.pim.mail")


if __name__ == "__main__":
   unittest.main()
