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
from osaf import pim, dumpreload, sharing
from osaf.framework.password import Password
from util import testcase
from PyICU import ICUtzinfo
import datetime

logger = logging.getLogger(__name__)


class DumpReloadTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
        self.RoundTrip()

    def RoundTrip(self):

        filename = "tmp_dump_file"

        view0 = self.views[0]
        view1 = self.views[1]

        # uuids to dump; add your items to this:
        uuids = set()

        # Prepare test data

        coll0 = pim.SmartCollection("testCollection", itsView=view0,
            displayName="Test Collection")
        uuids.add(coll0.itsUUID)

        titles = [
            u"dunder",
            u"mifflin",
        ]

        tzinfo = ICUtzinfo.floating
        createdOn = datetime.datetime(2007, 3, 1, 10, 0, 0, 0, tzinfo)
        lastModified = datetime.datetime(2007, 3, 1, 12, 0, 0, 0, tzinfo)
        email = "test@example.com"
        emailAddress = pim.EmailAddress.getEmailAddress(view0, email)

        count = len(titles)
        for i in xrange(count):
            n = pim.Note(itsView=view0)
            n.createdOn = createdOn
            n.displayName = titles[i % count]
            n.body = u"Here is the body"
            n.lastModifiedBy = emailAddress
            n.lastModified = lastModified
            coll0.add(n)
            uuids.add(n.itsUUID)


        # Sharing related items
        account0 = sharing.CosmoAccount(itsView=view0,
            host="chandler.o11n.org",
            port=1888,
            path="/cosmo",
            username="test",
            password=Password(itsView=view0),
            userSSL=True
        )
        uuids.add(account0.itsUUID)
        cosmo_conduit0 = sharing.CosmoConduit(itsView=view0,
            account=account0,
            shareName=coll0.itsUUID.str16(),
            translator=sharing.SharingTranslator,
            serializer=sharing.EIMMLSerializer
        )
        uuids.add(cosmo_conduit0.itsUUID)
        cosmo_share0 = sharing.Share(itsView=view0,
            contents=coll0,
            conduit=cosmo_conduit0
        )
        uuids.add(cosmo_share0.itsUUID)


        inmemory_conduit0 = sharing.InMemoryDiffRecordSetConduit(itsView=view0,
            shareName="in_memory",
            translator=sharing.SharingTranslator,
            serializer=sharing.EIMMLSerializer
        )
        uuids.add(inmemory_conduit0.itsUUID)

        inmemory_share0 = sharing.Share(itsView=view0,
            conduit=inmemory_conduit0,
            contents=coll0
        )
        uuids.add(inmemory_share0.itsUUID)

        # Create some State objects
        inmemory_share0.create()
        view0.commit()
        inmemory_share0.sync()
        for state in inmemory_share0.states:
            uuids.add(state.itsUUID)





        try:

            dumpreload.dump(view0, filename, uuids)
            dumpreload.reload(view1, filename)

            # Ensure the items are now in view1
            for uuid in uuids:
                item0 = view0.findUUID(uuid)
                item1 = view1.findUUID(uuid)

                self.assert_(item1 is not None)
                if hasattr(item0, 'displayName'):
                    self.assertEqual(item0.displayName, item1.displayName)
                if hasattr(item0, 'body'):
                    self.assertEqual(item0.body, item1.body)

            # Verify collection membership:
            coll1 = view1.findUUID(coll0.itsUUID)
            for item0 in coll0:
                item1 = view1.findUUID(item0.itsUUID)
                self.assert_(item1 in coll1)

            # Verify sharing
            inmemory_share1 = view1.findUUID(inmemory_share0.itsUUID)
            self.assert_(inmemory_share1 is not None)
            self.assertEqual(inmemory_share0.contents.itsUUID,
                inmemory_share1.contents.itsUUID)
            for state0 in inmemory_share0.states:
                state1 = view1.findUUID(state0.itsUUID)
                self.assert_(state1 in inmemory_share1.states)


        finally:
            os.remove(filename)


if __name__ == "__main__":
    unittest.main()
