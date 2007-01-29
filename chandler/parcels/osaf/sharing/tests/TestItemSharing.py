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

from osaf.sharing import itemcentric

from repository.item.Item import Item
from util import testcase
from PyICU import ICUtzinfo
from application import schema

logger = logging.getLogger(__name__)

class ItemSharingTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
        self.PrepareTestData()
        self.RoundTrip()

    def PrepareTestData(self):

        item0 = pim.Note(itsView=self.views[0])
        item0.displayName = "test displayName"
        item0.body = "test body"
        self.uuid = item0.itsUUID.str16()

    def RoundTrip(self):

        view0 = self.views[0]
        view1 = self.views[1]

        item0 = view0.findUUID(self.uuid)

        # morgen sends to pje
        self.assert_(not pim.has_stamp(item0, sharing.SharedItem))
        text = itemcentric.outbound(view0, "pje", item0)
        self.assert_(pim.has_stamp(item0, sharing.SharedItem))

        # pje receives from morgen
        self.assert_(view1.findUUID(self.uuid) is None)
        item1 = itemcentric.inbound(view1, "morgen", text)
        self.assert_(pim.has_stamp(item1, sharing.SharedItem))
        self.assertEqual(item1.displayName, "test displayName")
        self.assertEqual(item1.body, "test body")

        shared0 = sharing.SharedItem(item0)
        shared1 = sharing.SharedItem(item1)

        self.assert_(not shared0.getConflicts())

        # conflict
        item0.displayName = "changed by morgen"
        item1.displayName = "changed by pje"
        text = itemcentric.outbound(view0, "pje", item0)
        itemcentric.inbound(view1, "morgen", text)
        self.assert_(shared1.getConflicts().has_key('morgen'))

        # removal
        text = itemcentric.outboundDeletion(view0, "pje", self.uuid)
        # allowDeletion flag False
        itemcentric.inbound(view1, "morgen", text, allowDeletion=False)
        view1.commit() # to give a chance for a deleted item to go away
        self.assert_(view1.findUUID(self.uuid) is not None)
        # allowDeletion flag True
        itemcentric.inbound(view1, "morgen", text, allowDeletion=True)
        view1.commit() # to give a chance for a deleted item to go away
        self.assert_(view1.findUUID(self.uuid) is None)

        # adding item back
        text = itemcentric.outbound(view0, "pje", item0)
        itemcentric.inbound(view1, "morgen", text)
        self.assert_(view1.findUUID(self.uuid) is not None)

        # overlapping but identical modifications results in no conflicts
        item0.displayName = "changed"
        item1.displayName = "changed"
        text = itemcentric.outbound(view0, "pje", item0)
        itemcentric.inbound(view1, "morgen", text)
        self.assert_(not shared1.getConflicts().has_key('morgen'))

if __name__ == "__main__":
    unittest.main()
