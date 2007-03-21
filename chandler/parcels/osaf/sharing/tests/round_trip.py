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

cosmo = False

def checkStats(stats, expecting):
    for seen, expected in zip(stats, expecting):
        for event in ('added', 'modified', 'removed'):
            count = len(seen[event])
            expect = expected[event]
            if isinstance(expect, tuple):
                if count != expect[1 if cosmo else 0]:
                    return False
            else:
                if count != expect:
                    return False
    return True


class RoundTripTestCase(testcase.DualRepositoryTestCase):

    def RoundTripRun(self):
        self.setUp()
        self.PrepareTestData()
        self.PrepareShares()
        self.RoundTrip()

    def PrepareTestData(self):

        view = self.views[0]

        self.coll = pim.ListCollection("testCollection", itsView=view,
            displayName="Test Collection")

        titles = [
            u"breakfast",
        ]

        self.uuids = { }

        tzinfo = ICUtzinfo.floating
        createdOn = datetime.datetime(2007, 3, 1, 10, 0, 0, 0, tzinfo)
        count = len(titles)
        for i in xrange(count):
            n = pim.Note(itsView=view)
            n.createdOn = createdOn
            n.displayName = titles[i % count]
            self.uuids[n.itsUUID] = n.displayName
            n.body = u"Here is the body"
            self.coll.add(n)


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
            ({'added' : 1, 'modified' : 0, 'removed' : 0},)),
            "Sync operation mismatch")
        self.assert_(pim.has_stamp(coll0, sharing.SharedItem))
        self.assert_(pim.has_stamp(item, sharing.SharedItem))
        self.assert_(self.share0 in sharing.SharedItem(item).sharedIn)

        # Local modification only
        item.body = u"CHANGED"
        item.read = True
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(item.read == True)

        # Initial subscribe
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 1, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")

        # Verify items are imported
        for uuid in self.uuids:
            n = view1.findUUID(uuid)
            self.assertEqual(self.uuids[uuid], n.displayName)
        item1 = view1.findUUID(testUuid)
        self.assert_(item1 in self.share1.contents)
        self.assert_(item1.body == u"CHANGED")
        self.assert_(item1.read == False)
        self.assert_(pim.has_stamp(item1, sharing.SharedItem))
        self.assert_(pim.has_stamp(self.share1.contents, sharing.SharedItem))
        self.assertEqual(self.share0.contents.itsUUID,
            self.share1.contents.itsUUID)



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
        self.assert_(item.read == False)
        self.assert_(item1.displayName == "displayName changed in 1")
        self.assert_(item1.body == "body changed in 0")
        self.assert_(item1.read == False)




        # Ensure last-modified is transmitted properly

        # 1) Simple case, only one way:
        email = "test@example.com"
        emailAddress = pim.EmailAddress.getEmailAddress(view0, email)
        tzinfo = ICUtzinfo.floating
        lastModified = datetime.datetime(2030, 3, 1, 12, 0, 0, 0, tzinfo)
        item.lastModifiedBy = emailAddress
        item.lastModified = lastModified
        item.lastModification = pim.Modification.edited
        item.read = True
        item1.read = True
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(item1.lastModifiedBy.emailAddress == email)
        self.assert_(item1.lastModified == lastModified)
        self.assert_(item1.lastModification == pim.Modification.edited)
        self.assert_(item.read == True)
        self.assert_(item1.read == False)

        # 2) receiving more recent modification:
        email0 = "test0@example.com"
        emailAddress0 = pim.EmailAddress.getEmailAddress(view0, email0)
        lastModified0 = datetime.datetime(2030, 3, 1, 13, 0, 0, 0, tzinfo)
        item.lastModifiedBy = emailAddress0
        item.lastModified = lastModified0
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        email1 = "test1@example.com"
        emailAddress1 = pim.EmailAddress.getEmailAddress(view1, email1)
        lastModified1 = datetime.datetime(2030, 3, 1, 11, 0, 0, 0, tzinfo)
        item1.lastModifiedBy = emailAddress1
        item1.lastModified = lastModified1
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        # In this case, the mod from view0 is more recent, so applied
        self.assert_(item1.lastModifiedBy.emailAddress == email0)
        self.assert_(item1.lastModified == lastModified0)

        # (Cosmo won't send older modifications, so that is why the stats
        # are the way they are)
        # 3) receiving an older modification:
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : (1,0), 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        # In this case, the mod from view1 is out of date, so ignored,
        # and both clients have email0 and lastModified0
        self.assert_(item.lastModifiedBy.emailAddress == email0)
        self.assert_(item.lastModified == lastModified0)




        # Local and Remote modification, overlapping and non-overlapping
        # changes - non-overlapping changes apply, overlapping changes
        # become pending for the second syncer
        item.body = u"body changed again in 0"
        item.displayName = u"displayName changed in 0"
        item.setTriageStatus(pim.TriageEnum.later)
        item1.displayName = u"displayName changed again in 1"
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        view1.commit(); stats = self.share1.sync(); view1.commit()
        # In Cosmo mode, we end up sending a deletion of an old last modified
        # by record, because of the manner in which Cosmo ignores deletions.
        # That is why the stats are different between non-Cosmo and Cosmo mode:
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : (0,1), 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(item1.displayName == "displayName changed again in 1")
        self.assert_(item1.triageStatus == pim.TriageEnum.later)
        self.assert_(item1.body == "body changed again in 0")
        # TODO: Verify the pending here
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(item.displayName == "displayName changed in 0")
        self.assert_(item.body == "body changed again in 0")

        self.assert_(sharing.hasConflicts(item1))
        self.assert_(self.share1.hasConflicts())
        for conflict in sharing.SharedItem(item1).getConflicts():
            conflict.discard()
        # Verify that conflicts are removed when discarded
        self.assertEqual(len(list(sharing.SharedItem(item1).getConflicts())), 0)
        self.assert_(not sharing.hasConflicts(item1))
        self.assert_(not self.share1.hasConflicts())


        # Remote stamping - stamp applied locally
        self.assert_(not pim.has_stamp(item, pim.EventStamp))
        pim.EventStamp(item).add()
        self.assert_(pim.has_stamp(item, pim.EventStamp))
        time0 = datetime.datetime(2007, 1, 26, 12, 0, 0, 0, tzinfo)
        pim.EventStamp(item).startTime = time0
        pim.EventStamp(item).duration = datetime.timedelta(minutes=60)
        pim.EventStamp(item).anyTime = False
        pim.EventStamp(item).transparency = 'tentative'
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(not pim.has_stamp(item1, pim.EventStamp))
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(pim.has_stamp(item1, pim.EventStamp))
        self.assertEqual(pim.EventStamp(item1).transparency, 'tentative')




        # Remote unstamping - item unstamped locally
        pim.EventStamp(item).remove()
        self.assert_(not pim.has_stamp(item, pim.EventStamp))
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(pim.has_stamp(item1, pim.EventStamp))
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(not pim.has_stamp(item1, pim.EventStamp))




        # Remote unstamping, local modification - item does not get unstamped
        # locally, the unstamping becomes a pending conflict
        # First, put the stamp back
        pim.EventStamp(item).add()
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(pim.has_stamp(item1, pim.EventStamp))
        pim.EventStamp(item).remove()
        self.assert_(not pim.has_stamp(item, pim.EventStamp))
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        pim.EventStamp(item1).transparency = 'fyi'
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(pim.has_stamp(item1, pim.EventStamp))
        self.assertEqual(pim.EventStamp(item1).transparency, 'fyi')
        # TODO: Verify pending is correct
        # print self.share1.conduit.getState(testUuid)[1]

        # Clear the conflict by removing the stamp from item1
        pim.EventStamp(item1).remove()
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")



        # Non-overlapping stamping - stamps get applied on both ends
        pim.EventStamp(item).add()
        pim.TaskStamp(item1).add()
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
        self.assert_(pim.has_stamp(item, pim.EventStamp))
        self.assert_(pim.has_stamp(item, pim.TaskStamp))
        self.assert_(pim.has_stamp(item1, pim.EventStamp))
        self.assert_(pim.has_stamp(item1, pim.TaskStamp))




        # Both sides unstamp - no conflict
        pim.EventStamp(item).remove()
        pim.EventStamp(item1).remove()
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(not pim.has_stamp(item, pim.EventStamp))
        self.assert_(pim.has_stamp(item, pim.TaskStamp))
        self.assert_(not pim.has_stamp(item1, pim.EventStamp))
        self.assert_(pim.has_stamp(item1, pim.TaskStamp))
        # TODO: Verify no pending



        # Local unstamping, remote modification - item does not change locally;
        # the remote modification becomes a pending conflict

        # First, put the event stamp back
        pim.EventStamp(item).add()
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(pim.has_stamp(item, pim.EventStamp))
        self.assert_(pim.has_stamp(item1, pim.EventStamp))
        pim.EventStamp(item).transparency = 'confirmed'
        pim.EventStamp(item1).remove()
        self.assert_(not pim.has_stamp(item1, pim.EventStamp))
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(not pim.has_stamp(item1, pim.EventStamp))
        self.assertEqual(pim.EventStamp(item1).transparency, 'tentative')
        # TODO: Verify pending is correct
        # print self.share1.conduit.getState(testUuid)[1]



        # Local removal -  sends removal recordset
        self.share0.contents.remove(item)
        self.assert_(pim.has_stamp(item, sharing.SharedItem))
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 1})),
            "Sync operation mismatch")
        self.assert_(not pim.has_stamp(item, sharing.SharedItem))




        # Remote removal - results in local removal
        self.assert_(pim.has_stamp(item1, sharing.SharedItem))
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 1},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(item1 not in self.share1.contents)
        self.assert_(not pim.has_stamp(item1, sharing.SharedItem))




        # Local addition of once-shared item - sends item
        self.share0.contents.add(item)
        item.body = "back from removal"
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 1, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")




        # Remote modification of existing item *not* in the local collection
        # - adds item to local collection
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        item1 = view1.findUUID(testUuid)
        self.assert_(item1 in self.share1.contents)
        # Note, we have pending changes because we already had this item
        # in our repository (and it wasn't deleted). Our body is as we had
        # it before the sync:
        self.assertEqual(item1.body, "body changed again in 0")
        # print self.share1.conduit.getState(testUuid)
        # TODO: When there is an API for examining pending changes, test that
        # here to verify they include "back from removal"




        # Remote modification of locally *deleted* item - reconstitutes the
        # item based on last agreed state and adds to local collection
        item.body = "back from the dead"
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        # Completely delete item in view 1, ensure it comes back
        item1.delete(True)
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 1, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
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
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 1})),
            "Sync operation mismatch")
        item1.body = "modification trumps removal"
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 1, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(item in self.share0.contents)
        # item retains any local differences from what's on server:
        self.assertEqual(item.body, "back from the dead")
        # We have pending changes ("modification trumps removal"), so clear
        # them out:
        for conflict in sharing.SharedItem(item).getConflicts():
            conflict.discard()



        # Remotely modified, locally removed - item gets put back into local
        # collection with remote state.
        item.body = "I win!"
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        self.share1.contents.remove(item1)
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(item1 in self.share1.contents)



        # Remote *and* Local item removal
        self.share0.contents.remove(item)
        self.share1.contents.remove(item1)
        view0.commit(); stats = self.share0.sync(); view0.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 1})),
            "Sync operation mismatch")
        view1.commit(); stats = self.share1.sync(); view1.commit()
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(item not in self.share0.contents)
        self.assert_(item1 not in self.share1.contents)


        # TODO: verify that master items are synced when a modification
        # changes

        # self.share0.conduit.dump("at the end")

        self.share0.destroy() # clean up
