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
from repository.item.Item import Item
from util import testcase
from PyICU import ICUtzinfo
from application import schema
from i18n.tests import uw

logger = logging.getLogger(__name__)

class InMemoryTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
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
        coll = pim.SmartCollection("testCollection", sandbox,
            displayName=uw("Test Collection"))

        names = [
            (uw("unicode test"), uw("unicode test"), u"unicodetest@example.com"),
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
            u'\u8fd1\u85e4\u6df3\u4e5f\u306e\u65b0\u30cd\u30c3\u30c8\u30b3\u30df\u30e5\u30cb\u30c6\u30a3\u8ad6',
        ]

        self.uuids = {}

        tzinfo = ICUtzinfo.getDefault()
        for i in xrange(6):
            c = pim.CalendarEvent(itsParent=sandbox)
            c.summary = events[i % 6]
            c.organizer = contacts[0]
            c.participants = [contacts[1], contacts[2]]
            c.startTime=datetime.datetime(2005, 10, 31, 12, 0, 0, 0, tzinfo)
            c.duration=datetime.timedelta(minutes=60)
            c.anyTime=False
            c.itsItem.body = u"Here is the body"
            self.uuids[c.itsItem.itsUUID] = c.summary
            coll.add(c.itsItem)

    def PrepareShares(self):

        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")
        conduit = sharing.InMemoryConduit("conduit", itsView=view0,
            shareName=uw("exportedCollection"))
        format = sharing.CloudXMLFormat("format", itsView=view0)
        self.share0 = sharing.Share("share", itsView=view0,
            contents=coll0, conduit=conduit, format=format)

        if self.share0.exists():
            self.share0.destroy()

        view1 = self.views[1]
        conduit = sharing.InMemoryConduit("conduit", itsView=view1,
            shareName=uw("exportedCollection"))
        format = sharing.CloudXMLFormat("format", itsView=view1)
        self.share1 = sharing.Share("share", itsView=view1,
            conduit=conduit, format=format)

    def RoundTrip(self):

        # Export
        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")
        self.share0.create()
        self.share0.sync()

        # Import
        self.share1.sync()
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
        # change one of the items in both shares

        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")

        view1 = self.views[1]
        coll1 = view1.findUUID(coll0.itsUUID)

        for item in coll0:
            if item.displayName == u"meeting":
                uuid = item.itsUUID
                break

        item0 = view0.findUUID(uuid)
        event0 = pim.EventStamp(item0)
        item0.displayName = uw("meeting rescheduled")
        oldStart = event0.startTime

        tzinfo = ICUtzinfo.getDefault()
        newStart = datetime.datetime(2005, 11, 1, 12, 0, 0, 0, tzinfo)
        item1 = view1.findUUID(uuid)
        event1 = pim.EventStamp(item1)
        event1.startTime = newStart
        newBody = "I changed the body"
        item1.body = newBody

        view0.commit()
        sharing.sync(coll0)
        view0.refresh()

        view1.commit()
        sharing.sync(coll1)
        view1.refresh()

        view0.commit()
        sharing.sync(coll0)
        view0.refresh()

        self.assertEqual(item0.displayName, uw("meeting rescheduled"),
         u"displayName is %s" % (item0.displayName))
        self.assertEqual(item1.displayName, uw("meeting rescheduled"),
         u"displayName is %s" % (item1.displayName))

        self.assertEqual(event0.startTime, newStart,
         u"startTime is %s" % (event0.startTime))
        self.assertEqual(event1.startTime, newStart,
         u"startTime is %s" % (event1.startTime))
        self.assertEqual(item1.body, newBody,
         u"body is %s" % (item1.body))

    def Remove(self):

        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")

        view1 = self.views[1]
        coll1 = view1.findUUID(coll0.itsUUID)

        for item in coll0:
            if item.displayName == uw("meeting rescheduled"):
                uuid = item.itsUUID
                break

        item0 = view0.findUUID(uuid)
        item1 = view1.findUUID(uuid)

        coll0.remove(item0)

        view0.commit()
        sharing.sync(coll0)
        view0.refresh()
        time.sleep(1)

        self.assert_(item1 in coll1)
        view1.commit()
        sharing.sync(coll1)
        view1.refresh()
        self.assert_(item1 not in coll1)

if __name__ == "__main__":
    unittest.main()
