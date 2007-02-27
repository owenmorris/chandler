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

from osaf.sharing import recordset_conduit, translator, eimml

from repository.item.Item import Item
from util import testcase
from PyICU import ICUtzinfo
from application import schema

logger = logging.getLogger(__name__)

class MultipleSharesTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
        self.PrepareTestData()
        self.PrepareShares()
        self.RoundTrip()

    def PrepareTestData(self):

        view0 = self.views[0]

        item0 = pim.Note(itsView=view0)
        item0.displayName = "test displayName"
        item0.body = "test body"
        self.itemuuid = item0.itsUUID.str16()

        coll = pim.ListCollection(itsView=view0, displayName="Collection a")
        coll.add(item0)
        self.coluuida = coll.itsUUID.str16()

        coll = pim.ListCollection(itsView=view0, displayName="Collection b")
        coll.add(item0)
        self.coluuidb = coll.itsUUID.str16()


    def PrepareShares(self):

        view0 = self.views[0]
        view1 = self.views[1]
        coll0a = view0.findUUID(self.coluuida)
        coll0b = view0.findUUID(self.coluuidb)

        self.assert_(not pim.has_stamp(coll0a, sharing.SharedItem))

        # First share in first repo
        conduit = recordset_conduit.InMemoryDiffRecordSetConduit(itsView=view0,
            shareName="foo",
            translator=translator.PIMTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share0a = sharing.Share(itsView=view0,
            contents=coll0a, conduit=conduit)
        self.assert_(pim.has_stamp(coll0a, sharing.SharedItem))

        if self.share0a.exists():
            self.share0a.destroy()


        # Second share in first repo
        conduit = recordset_conduit.InMemoryDiffRecordSetConduit(itsView=view0,
            shareName="bar",
            translator=translator.PIMTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share0b = sharing.Share(itsView=view0,
            contents=coll0b, conduit=conduit)
        self.assert_(pim.has_stamp(coll0b, sharing.SharedItem))

        if self.share0b.exists():
            self.share0b.destroy()



        # First share in second repo
        conduit = recordset_conduit.InMemoryDiffRecordSetConduit(itsView=view1,
            shareName="foo",
            translator=translator.PIMTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share1a = sharing.Share(itsView=view1, conduit=conduit)


        # Second share in second repo
        conduit = recordset_conduit.InMemoryDiffRecordSetConduit(itsView=view1,
            shareName="bar",
            translator=translator.PIMTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share1b = sharing.Share(itsView=view1, conduit=conduit)




    def RoundTrip(self):

        view0 = self.views[0]
        view1 = self.views[1]
        coll0a = view0.findUUID(self.coluuida)
        coll0b = view0.findUUID(self.coluuidb)
        item0 = view0.findUUID(self.itemuuid)



        # Initial publish
        view0.commit()
        self.share0a.create()
        self.share0a.sync()
        self.share0b.create()
        self.share0b.sync()
        view0.commit()

        # Initial subscribe
        view1.commit()
        self.share1a.sync()
        self.share1b.sync()
        view1.commit()

        coll1a = self.share1a.contents
        coll1b = self.share1b.contents
        item1 = view1.findUUID(self.itemuuid)
        self.assert_(item1 in coll1a)
        self.assert_(item1 in coll1b)


        # Create two conflicts on displayName

        item1.displayName = "changed by 1A"
        view1.commit(); self.share1a.sync(); view1.commit()

        item1.displayName = "changed by 1B"
        view1.commit(); self.share1b.sync(); view1.commit()

        item0.displayName = "changed by 0"
        view0.commit()
        self.share0a.sync()
        self.share0b.sync()
        view0.commit()

        shared = sharing.SharedItem(item0)
        conflicts = shared.getConflicts()
        self.assert_(conflicts)
        # TODO: when conflicts API develops, make sure there are two
        # conflicts here



if __name__ == "__main__":
    unittest.main()
