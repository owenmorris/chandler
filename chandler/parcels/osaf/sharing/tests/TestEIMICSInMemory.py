#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

# This will move to TestEIMICSInMemory.py once ICSSerializer is operational

import unittest, sys, os, logging, time
from datetime import datetime, timedelta
from osaf import pim, sharing

from osaf.sharing import recordset_conduit, translator, ics

from repository.item.Item import Item
from util import testcase
from application import schema

logger = logging.getLogger(__name__)

printStatistics = False

def printStats(view, stats):
    if printStatistics:
        for opStats in stats:
            share = view.findUUID(opStats['share'])
            print "'%s' %-25s Add: %3d, Mod: %3d, Rm: %3d" % \
                (opStats['op'], share.conduit.shareName.encode('utf8'),
                 len(opStats['added']),
                 len(opStats['modified']),
                 len(opStats['removed'])
                )
        print

def checkStats(stats, expecting):
    for seen, expected in zip(stats, expecting):
        for event in ('added', 'modified', 'removed'):
            if len(seen[event]) != expected[event]:
                return False
    return True


class EIMICSInMemoryTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
        self.PrepareTestData()
        self.PrepareShares()
        self.RoundTrip()

    def PrepareTestData(self):

        view = self.views[0]

        self.coll = pim.ListCollection("testCollection", itsView=view,
            displayName="Test Collection")


        pacific = view.tzinfo.getInstance('America/Los_Angeles')
        floating = view.tzinfo.floating

        titles = [(u"breakfast", datetime(2007, 3, 1, 10, 30, 0, 0, floating)),
                  (u"dinner", datetime(2007, 3, 1, 18, 30, 0, 0, pacific))
                 ]

        self.uuids = { }

        createdOn = datetime(2007, 3, 1, 10, 0, 0, 0, floating)
        for title, dt in titles:
            event = pim.CalendarEvent(itsView=view)
            n = event.itsItem
            n.createdOn = createdOn
            n.displayName = title
            self.uuids[n.itsUUID] = n.displayName
            n.body = u"Here is the body"
            event.startTime = dt
            event.duration  = timedelta(hours=1)
            event.anyTime   = False
            self.coll.add(n)



    def PrepareShares(self):

        view0 = self.views[0]
        coll0 = self.coll
        conduit = recordset_conduit.InMemoryResourceRecordSetConduit(
            "conduit", itsView=view0,
            shareName="exportedCollection",
            translator=translator.SharingTranslator,
            serializer=ics.ICSSerializer
        )
        self.share0 = sharing.Share("share", itsView=view0,
            contents=coll0, conduit=conduit)


        view1 = self.views[1]
        conduit = recordset_conduit.InMemoryResourceRecordSetConduit(
            "conduit", itsView=view1,
            shareName="exportedCollection",
            translator=translator.SharingTranslator,
            serializer=ics.ICSSerializer
        )
        self.share1 = sharing.Share("share", itsView=view1,
            conduit=conduit)





    def RoundTrip(self):

        view0 = self.views[0]
        view1 = self.views[1]
        coll0 = self.coll

        item = self.share0.contents.first()
        testUuid = item.itsUUID.str16()
        item.icalUID = testUuid

        self.assert_(not pim.has_stamp(item, sharing.SharedItem))

        # Initial publish
        self.share0.create()
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 2, 'modified' : 0, 'removed' : 0},)),
            "Sync operation mismatch")
        self.assert_(pim.has_stamp(coll0, sharing.SharedItem))
        self.assert_(pim.has_stamp(item, sharing.SharedItem))
        self.assert_(self.share0 in sharing.SharedItem(item).sharedIn)

        # Local modification only
        item.body = u"CHANGED"
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")

        ## Initial subscribe
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 2, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")

        # Verify items are imported
        for uuid in self.uuids:
            n = view1.findUUID(uuid)
            self.assertEqual(self.uuids[uuid], n.displayName)
        item1 = view1.findUUID(testUuid)
        self.assert_(item1 in self.share1.contents)
        self.assert_(item1.body == u"CHANGED")
        self.assert_(pim.has_stamp(item1, sharing.SharedItem))
        self.assert_(pim.has_stamp(self.share1.contents, sharing.SharedItem))
        # XXX This fails, why?
        #self.assertEqual(self.share0.contents.itsUUID,
            #self.share1.contents.itsUUID)



        # Local and Remote modification, non-overlapping changes - all changes
        # apply
        item.body = u"body changed in 0"
        item1.displayName = u"displayName changed in 1"
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(item.displayName == "displayName changed in 1")
        self.assert_(item.body == "body changed in 0")
        self.assert_(item1.displayName == "displayName changed in 1")
        self.assert_(item1.body == "body changed in 0")


        self.share0.destroy() # clean up
        #self.share1.destroy() # this doesn't work; why?

if __name__ == "__main__":
    unittest.main()
