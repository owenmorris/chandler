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

        pje = schema.Item(itsView=view0, itsName="pje")
        morgen = schema.Item(itsView=view1, itsName="morgen")

        # morgen sends to pje
        self.assert_(not pim.has_stamp(item0, sharing.SharedItem))
        view0.commit()
        text = itemcentric.outbound(pje, item0)
        view0.commit()
        self.assert_(pim.has_stamp(item0, sharing.SharedItem))

        # pje receives from morgen
        self.assert_(view1.findUUID(self.uuid) is None)
        view1.commit()
        item1 = itemcentric.inbound(morgen, text)
        view1.commit()
        self.assert_(pim.has_stamp(item1, sharing.SharedItem))
        self.assertEqual(item1.displayName, "test displayName")
        self.assertEqual(item1.body, "test body")

        shared0 = sharing.SharedItem(item0)
        shared1 = sharing.SharedItem(item1)

        self.assert_(not shared0.getConflicts())

        # conflict
        item0.displayName = "changed by morgen"
        item1.displayName = "changed by pje"
        view0.commit()
        text = itemcentric.outbound(pje, item0)
        view0.commit()
        view1.commit()
        itemcentric.inbound(morgen, text)
        view1.commit()
        self.assert_(shared1.getConflicts())


        # try sending when there are pending conflicts
        try:
            itemcentric.outbound(morgen, item1)
        except sharing.ConflictsPending:
            pass # This is what we're expecting
        else:
            raise Exception("We were expecting an ConflictsPending exception")



        # removal
        view0.commit()
        text = itemcentric.outboundDeletion(pje, self.uuid)
        view0.commit()
        # allowDeletion flag False
        view1.commit()
        itemcentric.inbound(morgen, text, allowDeletion=False)
        view1.commit() # to give a chance for a deleted item to go away
        self.assert_(view1.findUUID(self.uuid) is not None)
        # allowDeletion flag True
        itemcentric.inbound(morgen, text, allowDeletion=True)
        view1.commit() # to give a chance for a deleted item to go away
        self.assert_(view1.findUUID(self.uuid) is None)

        # adding item back
        text = itemcentric.outbound(pje, item0)
        itemcentric.inbound(morgen, text)
        self.assert_(view1.findUUID(self.uuid) is not None)

        # overlapping but identical modifications results in no conflicts
        item0.displayName = "changed"
        item1.displayName = "changed"
        view0.commit()
        text = itemcentric.outbound(pje, item0)
        view0.commit()
        view1.commit()
        itemcentric.inbound(morgen, text)
        view1.commit()
        self.assert_(not shared1.getConflicts())


        # Verify that an out of sequence update is rejected
        view0.itsVersion = 2
        text = itemcentric.outbound(pje, item0)
        try:
            itemcentric.inbound(morgen, text)
        except sharing.OutOfSequence:
            pass # This is what we're expecting
        else:
            raise Exception("We were expecting an OutOfSequence exception")

if __name__ == "__main__":
    unittest.main()
