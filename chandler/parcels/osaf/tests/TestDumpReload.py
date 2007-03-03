#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


import unittest, sys, os, logging
from osaf import pim, dumpreload
from util import testcase
from PyICU import ICUtzinfo
import datetime

logger = logging.getLogger(__name__)


class DumpReloadTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
        self.PrepareTestData()
        self.RoundTrip()

    def PrepareTestData(self):

        view = self.views[0]

        self.coll = pim.ListCollection("testCollection", itsView=view,
            displayName="Test Collection")

        titles = [
            u"dunder",
            u"mifflin",
        ]

        self.uuids = { }

        tzinfo = ICUtzinfo.floating
        createdOn = datetime.datetime(2007, 3, 1, 10, 0, 0, 0, tzinfo)
        lastModified = datetime.datetime(2007, 3, 1, 12, 0, 0, 0, tzinfo)
        email = "test@example.com"
        emailAddress = pim.EmailAddress.getEmailAddress(view, email)

        count = len(titles)
        for i in xrange(count):
            n = pim.Note(itsView=view)
            n.createdOn = createdOn
            n.displayName = titles[i % count]
            self.uuids[n.itsUUID] = n.displayName
            n.body = u"Here is the body"
            n.lastModifiedBy = emailAddress
            n.lastModified = lastModified
            self.coll.add(n)


    def RoundTrip(self):

        view0 = self.views[0]
        view1 = self.views[1]

        # Ensure the items aren't in view1
        for uuid, displayName in self.uuids.iteritems():
            item = view1.findUUID(uuid)
            self.assert_(item is None)

        filename = "tmp_dump_file"

        try:
            dumpreload.dump(view0, filename, [i.itsUUID for i in self.coll])
            dumpreload.reload(view1, filename)

            # Ensure the items are now in view1
            for uuid, displayName in self.uuids.iteritems():
                item = view1.findUUID(uuid)
                self.assert_(item is not None)
                self.assertEqual(item.displayName, displayName)
                self.assertEqual(item.lastModifiedBy.emailAddress,
                    "test@example.com")

        finally:
            os.remove(filename)


if __name__ == "__main__":
    unittest.main()
