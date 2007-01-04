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
from i18n.tests import uw

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
            displayName=uw("Test Collection"))

        titles = [
            u"breakfast",
            u"lunch",
            u"dinner",
            u"meeting",
            u"movie",
        ]

        self.uuids = { }

        for i in xrange(6):
            n = pim.Note(itsParent=sandbox)
            n.displayName = titles[i % 5]
            self.uuids[n.itsUUID] = n.displayName
            n.body = u"Here is the body"
            coll.add(n)

    def PrepareShares(self):

        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")
        conduit = recordset_conduit.InMemoryRecordSetConduit(
            "conduit", itsView=view0,
            shareName=uw("exportedCollection"),
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
            shareName=uw("exportedCollection"),
            translator=translator.PIMTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share1 = sharing.Share("share", itsView=view1,
            conduit=conduit)

    def RoundTrip(self):

        # Export
        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")
        # view0.commit()
        self.share0.create()
        self.share0.sync()
        # view0.commit()

        # Import
        view1 = self.views[1]
        self.share1.sync()
        # view1.commit()

        for uuid in self.uuids:
            n = view1.findUUID(uuid)
            self.assertEqual(self.uuids[uuid], n.displayName)


if __name__ == "__main__":
    unittest.main()
