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


import unittest, sys, os, logging, datetime, time
from osaf import pim, sharing

# @@@MOR: clean this up
from osaf.sharing import recordset_conduit, translator, eimml

from repository.item.Item import Item
from util import testcase
from PyICU import ICUtzinfo
from application import schema

logger = logging.getLogger(__name__)

class EIMInMemoryTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
        self.PrepareTestData()
        self.PrepareShares()
        self.RoundTrip()

    def PrepareTestData(self):

        view = self.views[0]
        # create a sandbox root
        Item("sandbox", view, None)

        sandbox = view.findPath("//sandbox")
        coll = pim.ListCollection("testCollection", sandbox,
            displayName="Test Collection")

        titles = [
            u"breakfast",
        ]

        self.uuids = { }

        count = len(titles)
        for i in xrange(count):
            n = pim.Note(itsParent=sandbox)
            n.displayName = titles[i % count]
            self.uuids[n.itsUUID] = n.displayName
            n.body = u"Here is the body"
            coll.add(n)

    def PrepareShares(self):

        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")
        conduit = recordset_conduit.InMemoryRecordSetConduit(
            "conduit", itsView=view0,
            shareName="exportedCollection",
            translator=translator.PIMTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share0 = sharing.Share("share", itsView=view0,
            contents=coll0, conduit=conduit)

        if self.share0.exists():
            self.share0.destroy()

        view1 = self.views[1]
        conduit = recordset_conduit.InMemoryRecordSetConduit(
            "conduit", itsView=view1,
            shareName="exportedCollection",
            translator=translator.PIMTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share1 = sharing.Share("share", itsView=view1,
            conduit=conduit)

    def RoundTrip(self):

        view0 = self.views[0]
        view1 = self.views[1]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")

        item = self.share0.contents.first()
        testUuid = item.itsUUID.str16()

        # Initial publish
        self.share0.create()
        view0.commit(); self.share0.sync(); view0.commit()

        # Local modification only
        item.body = u"CHANGED"
        view0.commit(); self.share0.sync(); view0.commit()

        # Initial subscribe
        view1.commit(); self.share1.sync(); view1.commit()

        # Verify items are imported
        for uuid in self.uuids:
            n = view1.findUUID(uuid)
            self.assertEqual(self.uuids[uuid], n.displayName)
        item1 = view1.findUUID(testUuid)
        self.assert_(item1 in self.share1.contents)
        self.assert_(item1.body == u"CHANGED")


        # TODO: stamping/unstamping
        # TODO: non-overlapping changes
        # TODO: overlapping changes


        # Local removal -  sends removal recordset
        self.share0.contents.remove(item)
        view0.commit(); self.share0.sync(); view0.commit()

        # Remote removal - results in local removal
        view1.commit(); self.share1.sync(); view1.commit()
        item1 = view1.findUUID(testUuid)
        self.assert_(item1 not in self.share1.contents)




        # Local addition of once-shared item - sends item
        self.share0.contents.add(item)
        item.body = "back from removal"
        view0.commit(); self.share0.sync(); view0.commit()




        # Remote modification of existing item *not* in the local collection
        # - adds item to local collection
        view1.commit(); self.share1.sync(); view1.commit()
        item1 = view1.findUUID(testUuid)
        self.assert_(item1 in self.share1.contents)
        # Note, we have pending changes because we already had this item
        # in our repository (and it wasn't deleted). Our body is as we had
        # it before the sync:
        self.assertEqual(item1.body, "CHANGED")
        # print self.share1.conduit.getState(testUuid)
        # TODO: When there is an API for examining pending changes, test that
        # here to verify they include "back from removal"




        # Remote modification of locally *deleted* item - reconstitutes the
        # item based on last agreed state and adds to local collection
        item.body = "back from the dead"
        view0.commit(); self.share0.sync(); view0.commit()
        # Completely delete item in view 1, ensure it comes back
        item1.delete(True)
        view1.commit(); self.share1.sync(); view1.commit()
        item1 = view1.findUUID(testUuid)
        self.assert_(item1 in self.share1.contents)
        # Note, since we completely deleted the item, and we reconstituted
        # it back from the agreed state, there are no pending changes
        # print self.share1.conduit.getState(testUuid)
        self.assertEqual(item1.body, "back from the dead")



        # Remotely removed, locally modified - item gets put back to server
        # including local mods
        self.share0.contents.remove(item)
        self.assert_(item not in self.share0.contents)
        view0.commit(); self.share0.sync(); view0.commit()
        item1.body = "modification trumps removal"
        view1.commit(); self.share1.sync(); view1.commit()
        view0.commit(); self.share0.sync(); view0.commit()
        self.assert_(item in self.share0.contents)
        self.assertEqual(item.body, "back from the dead")
        # We have pending changes ("modification trumps removal"), so clear
        # them out:
        # agreed, pending = self.share0.conduit.getState(testUuid)
        # print pending
        self.share0.conduit.discardPending(testUuid)



        # Remotely modified, locally removed - item gets put back into local
        # collection with remote state.
        item.body = "I win!"
        view0.commit(); self.share0.sync(); view0.commit()
        self.share1.contents.remove(item1)
        view1.commit(); self.share1.sync(); view1.commit()
        self.assert_(item1 in self.share1.contents)



        # Remote *and* Local item removal
        self.share0.contents.remove(item)
        self.share1.contents.remove(item1)
        view0.commit(); self.share0.sync(); view0.commit()
        view1.commit(); self.share1.sync(); view1.commit()
        self.assert_(item not in self.share0.contents)
        self.assert_(item1 not in self.share1.contents)

        # self.share0.conduit.dump("at the end")

if __name__ == "__main__":
    unittest.main()
