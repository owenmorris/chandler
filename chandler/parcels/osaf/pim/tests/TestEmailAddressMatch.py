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
#   WITHIN WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


""" Unit test for case insensitive EmailAddress.emailAddress compare"""

from osaf.pim.mail import *
import osaf.pim.mail as mail
from application import schema
import unittest as unittest
import TestDomainModel

class TestEmailAddressMatch(TestDomainModel.DomainModelTestCase):

    def testFindMatches(self):
        eaddr = "test@test.com"

        addrs = [
            EmailAddress(itsView=self.view, fullName="Test", emailAddress=eaddr),
            EmailAddress(itsView=self.view, fullName="Test1", emailAddress=eaddr),
            EmailAddress(itsView=self.view, fullName="Test2", emailAddress=eaddr),
            EmailAddress(itsView=self.view, fullName="Test3", emailAddress=eaddr),
        ]

        results = []

        for ret in mail.addressMatchGenerator(addrs[3]):
           results.append(ret)

        self.assertTrue(len(results) == 4)

        for addr in addrs:
            self.assertTrue(addr in results)


if __name__ == "__main__":
    unittest.main()
