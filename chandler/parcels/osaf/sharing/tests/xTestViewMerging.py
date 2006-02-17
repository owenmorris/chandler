__revision__  = "$Revision: 9354 $"
__date__      = "$Date: 2006-02-06 08:17:55 -0800 (Mon, 06 Feb 2006) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, sys, os, logging, datetime, time
from osaf import pim, sharing
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
                (opStats['op'], share.conduit.shareName,
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

class ViewMergingTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
        sharing.Sharing.USE_VIEW_MERGING = True
        self.PrepareTestData()
        self.PrepareShares()
        self.RoundTrip()
        self.Modify()
        self.Remove()
        self.Unpublish()

    def PrepareTestData(self):

        view = self.views[0]
        # create a sandbox root
        Item("sandbox", view, None)

        sandbox = view.findPath("//sandbox")
        coll = pim.ListCollection("testCollection", sandbox,
            displayName="Test Collection")

        names = [
            (u"Morgen", u"Sagen", u"morgen@example.com"),
            (u"Ted", u"Leung", u"ted@example.com"),
            (u"Andi", u"Vajda", u"andi@example.com"),
        ]

        contacts = []

        for name in names:
            c = pim.Contact(itsParent=sandbox)
            c.contactName = pim.ContactName(itsParent=sandbox)
            c.contactName.firstName = name[0]
            c.contactName.lastName = name[1]
            c.emailAddress = name[2]
            c.displayName = u"%s %s" % (name[0], name[1])
            contacts.append(c)

        events = [
            u"breakfast",
            u"lunch",
            u"dinner",
            u"meeting",
            u"movie",
        ]

        self.uuids = {}

        tzinfo = ICUtzinfo.getDefault()
        lob = view.findPath("//Schema/Core/Lob")
        for i in xrange(5):
            c = pim.CalendarEvent(itsParent=sandbox)
            c.displayName = events[i % 5]
            c.organizer = contacts[0]
            c.participants = [contacts[1], contacts[2]]
            c.startTime=datetime.datetime(2005, 10, 31, 12, 0, 0, 0, tzinfo)
            c.duration=datetime.timedelta(minutes=60)
            c.anyTime=False
            c.body = lob.makeValue("test", mimetype="plain/text")
            self.uuids[c.itsUUID] = c.displayName
            coll.add(c)

    def PrepareShares(self):

        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")

        self.share0 = sharing.Share(itsView=view0,
            contents=coll0,
            conduit=sharing.InMemoryConduit(itsView=view0,
                                            shareName="viewmerging"),
            format=sharing.CalDAVFormat(itsView=view0)
        )

        subShare = sharing.Share(itsView=view0,
            contents=coll0,
            conduit=sharing.InMemoryConduit(itsView=view0,
                                            shareName="viewmerging/.chandler"),
            format=sharing.CloudXMLFormat(itsView=view0)
        )
        self.share0.follows = subShare

        for attr in sharing.CALDAVFILTER:
            subShare.filterAttributes.append(attr)

        if self.share0.exists():
            self.share0.destroy()
        self.share0.create()
        subShare.create()

        view1 = self.views[1]

        self.share1 = sharing.Share(itsView=view1,
            conduit=sharing.InMemoryConduit(itsView=view1,
                                            shareName="viewmerging"),
            format=sharing.CalDAVFormat(itsView=view1)
        )

        subShare = sharing.Share(itsView=view1,
            conduit=sharing.InMemoryConduit(itsView=view1,
                                            shareName="viewmerging/.chandler"),
            format=sharing.CloudXMLFormat(itsView=view1)
        )
        self.share1.follows = subShare

        for attr in sharing.CALDAVFILTER:
            subShare.filterAttributes.append(attr)


    def RoundTrip(self):

        # Export
        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")
        stats = self.share0.sync()
        printStats(view0, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 6, 'modified' : 0, 'removed' : 0},
             {'added' : 5, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")


        # Import
        stats = self.share1.sync()
        printStats(self.share1.itsView, stats)
        self.assert_(checkStats(stats,
            ({'added' : 6, 'modified' : 0, 'removed' : 0},
             {'added' : 5, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")

        coll1 = self.share1.contents

        self.assertEqual(coll0.itsUUID, coll1.itsUUID, "Collection UUIDs "
            "don't match")

        # Make sure that the items we imported have the same displayNames
        # as the ones we exported (and no fewer, no more), and UUIDs match
        names = {}
        for item in coll0:
            names[item.displayName] = 1
        for item in coll1:
            self.assert_(item.displayName in names, "Imported item that wasn't "
             "exported")
            del names[item.displayName]
            self.assertEqual(item.displayName, self.uuids[item.itsUUID],
                "UUID of imported item doesn't match original")
        self.assert_(len(names) == 0, "Import is missing some items that were "
         "exported")

    def Unpublish(self):
        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")
        sharing.unpublish(coll0)


    def Modify(self):

        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")

        view1 = self.views[1]
        coll1 = view1.findUUID(coll0.itsUUID)

        for item in coll0:
            if item.displayName == u"meeting":
                uuid = item.itsUUID
                break


        # Make non-overlapping changes to the item

        item0 = view0.findUUID(uuid)
        item0.displayName = u"meeting rescheduled"
        oldStart = item0.startTime

        tzinfo = ICUtzinfo.getDefault()
        newStart = datetime.datetime(2005, 11, 1, 12, 0, 0, 0, tzinfo)
        item1 = view1.findUUID(uuid)
        item1.startTime = newStart

        stats = sharing.sync(coll0)
        printStats(view0, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        stats = sharing.sync(coll1)
        printStats(view1, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        stats = sharing.sync(coll0)
        printStats(view0, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")

        self.assertEqual(item0.displayName, u"meeting rescheduled",
         u"displayName is %s" % (item0.displayName))
        self.assertEqual(item1.displayName, u"meeting rescheduled",
         u"displayName is %s" % (item1.displayName))

        self.assertEqual(item0.startTime, newStart,
         u"startTime is %s" % (item0.startTime))
        self.assertEqual(item1.startTime, newStart,
         u"startTime is %s" % (item1.startTime))



        # Make overlapping changes to the item

        newStart0 = datetime.datetime(2006, 1, 1, 12, 0, 0, 0, tzinfo)
        item0.startTime = newStart0
        newStart1 = datetime.datetime(2006, 1, 2, 12, 0, 0, 0, tzinfo)
        item1.startTime = newStart1

        stats = sharing.sync(coll0)
        printStats(view0, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        stats = sharing.sync(coll1)
        printStats(view1, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        stats = sharing.sync(coll0)
        printStats(view0, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")

        # Since we sync'd coll0 first, its change wins out over coll1
        self.assertEqual(item0.startTime, newStart0,
         u"startTime is %s" % (item0.startTime))
        self.assertEqual(item1.startTime, newStart0,
         u"startTime is %s" % (item1.startTime))



        # Make an overlapping change on a Lob attribute

        # (Not sure if I need view-specific lob items for makeValue( ), but
        # just to be safe...)
        lob0 = view0.findPath("//Schema/Core/Lob")
        lob1 = view1.findPath("//Schema/Core/Lob")

        item0.body = lob0.makeValue("view0 change", mimetype="plain/text")
        item1.body = lob1.makeValue("view1 change", mimetype="plain/text")

        stats = sharing.sync(coll0)
        printStats(view0, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        stats = sharing.sync(coll1)
        printStats(view1, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0})),
            "Sync operation mismatch")
        stats = sharing.sync(coll0)
        printStats(view0, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 1, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")

        # Since we sync'd coll0 first, its change wins out over coll1
        item0body = item0.body.getInputStream().read()
        self.assertEqual(item0body, "view0 change",
         u"item0 body is %s" % item0body)
        item1body = item1.body.getInputStream().read()
        self.assertEqual(item1body, "view0 change",
         u"item1 body is %s" % item1body)



    def Remove(self):

        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")

        view1 = self.views[1]
        coll1 = view1.findUUID(coll0.itsUUID)

        for item in coll0:
            if item.displayName == u"meeting rescheduled":
                uuid = item.itsUUID
                break

        item0 = view0.findUUID(uuid)
        item1 = view1.findUUID(uuid)

        coll0.remove(item0)

        stats = sharing.sync(coll0)
        printStats(view0, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 1},
             {'added' : 0, 'modified' : 0, 'removed' : 1})),
            "Sync operation mismatch")

        self.assert_(item1 in coll1)
        stats = sharing.sync(coll1)
        printStats(view1, stats)
        self.assert_(checkStats(stats,
            ({'added' : 0, 'modified' : 0, 'removed' : 1},
             {'added' : 0, 'modified' : 0, 'removed' : 1},
             {'added' : 0, 'modified' : 0, 'removed' : 0},
             {'added' : 0, 'modified' : 0, 'removed' : 0})),
            "Sync operation mismatch")
        self.assert_(item1 not in coll1)

if __name__ == "__main__":
    unittest.main()
