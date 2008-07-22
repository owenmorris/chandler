#   Copyright (c) 2008 Open Source Applications Foundation
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

import unittest
import util.testcase as testcase

import osaf.sharing as sharing
import osaf.pim as pim
 
class ParseCosmoXMLTestCase(testcase.SharedSandboxTestCase):
    def setUp(self):
        super(ParseCosmoXMLTestCase, self).setUp()
        self.cosmoConduit = sharing.CosmoConduit(itsParent=self.sandbox)

    def testBogus(self):
        self.failUnless(
            self.cosmoConduit.raiseCosmoError("woo-woo! This is not XML") is None
        )

    def testDuplicateUids(self):
        try:
            self.cosmoConduit.raiseCosmoError(
"""<?xml version="1.0" encoding="utf-8" ?>
<error xmlns="http://osafoundation.org/mc/">
  <no-uid-conflict>
    <existing-uuid>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</existing-uuid>
    <conflicting-uuid>ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj</conflicting-uuid>
  </no-uid-conflict>
</error>
""")
        except sharing.errors.DuplicateIcalUids, e:
            self.failUnlessEqual(
                e.annotations,
                [(u'Duplicate ical UIDs detected: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee, ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj', '')]
            )
            self.failUnlessEqual(
                e.uuids,
                ['aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
                 'ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj']
             )
        else:
            self.fail("raiseCosmoError() failed to raise")

    def testUnknownXml(self):
        element = self.cosmoConduit.raiseCosmoError(
"""<?xml version="1.0" encoding="utf-8" ?>
<tasty-snack xmlns="http://osafoundation.org/mc/">
  <no-uid-conflict>
    <existing-uuid>aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee</existing-uuid>
    <conflicting-uuid>ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj</conflicting-uuid>
  </no-uid-conflict>
</tasty-snack>
""")
        self.failIf(element is None)


    def testInsufficientPrivileges(self):
        item = pim.Note(itsParent=self.sandbox, displayName=u"Hi, mom!")
        try:
            self.cosmoConduit.raiseCosmoError(
"""<?xml version='1.0' encoding='UTF-8'?>
<mc:error xmlns:mc="http://osafoundation.org/mc/">
<mc:insufficient-privileges>
<mc:target-uuid>%s</mc:target-uuid>
<mc:required-privilege>READ</mc:required-privilege>
</mc:insufficient-privileges>
</mc:error>
""" % (item.itsUUID.str16()))
        except sharing.errors.ForbiddenItem, e:
            self.failUnless(unicode(e).find(item.displayName) != -1)
            self.failUnlessEqual(e.uuid, item.itsUUID.str16())

        else:
            self.fail("raiseCosmoError() failed to raise")

    def testInsufficientPrivileges(self):
        item = pim.Note(itsParent=self.sandbox, displayName=u"Hi, mom!")
        try:
            self.cosmoConduit.raiseCosmoError(
"""<?xml version='1.0' encoding='UTF-8'?>
<mc:error xmlns:mc="http://osafoundation.org/mc/">
<mc:insufficient-privileges>
<mc:target-uuid>%s</mc:target-uuid>
<mc:required-privilege>READ</mc:required-privilege>
</mc:insufficient-privileges>
</mc:error>
""" % (item.itsUUID.str16()))
        except sharing.errors.ForbiddenItem, e:
            self.failUnless(unicode(e).find(item.displayName) != -1)
            self.failUnlessEqual(e.uuid, item.itsUUID.str16())

        else:
            self.fail("raiseCosmoError() failed to raise")

    def testInsufficientPrivilegesNoItem(self):
        try:
            self.cosmoConduit.raiseCosmoError(
"""<?xml version='1.0' encoding='UTF-8'?>
<mc:error xmlns:mc="http://osafoundation.org/mc/">
<mc:insufficient-privileges>
<mc:target-uuid>qqq-wwwwwwwww-lksldk22</mc:target-uuid>
<mc:required-privilege>READ</mc:required-privilege>
</mc:insufficient-privileges>
</mc:error>
""")
        except sharing.errors.ForbiddenItem, e:
            self.failUnless(unicode(e).find('qqq-wwwwwwwww-lksldk22') != -1)
            self.failUnlessEqual(e.uuid, 'qqq-wwwwwwwww-lksldk22')

        else:
            self.fail("raiseCosmoError() failed to raise")

    def testInsufficientPrivilegesNoTarget(self):
        if __debug__:
            self.failUnlessRaises(
                AssertionError,
                self.cosmoConduit.raiseCosmoError,
                """<?xml version='1.0' encoding='UTF-8'?>
                <mc:error xmlns:mc="http://osafoundation.org/mc/">
                <mc:insufficient-privileges>
                <mc:required-privilege>READ</mc:required-privilege>
                </mc:insufficient-privileges>
                </mc:error>
                """
            )

if __name__ == "__main__":
    unittest.main()
