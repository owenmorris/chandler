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

class DuplicateIcalUIDTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
        self.PrepareTestData()
        self.PrepareShares()
        self.Subscribe()

    def PrepareTestData(self):

        view = self.views[0]
        # create a sandbox root
        Item("sandbox", view, None)

        sandbox = view.findPath("//sandbox")
        coll = pim.ListCollection("testCollection", sandbox,
            displayName=uw("Test Collection"))

        tzinfo = ICUtzinfo.getDefault()
        c = pim.CalendarEvent(itsParent=sandbox)
        c.summary = "Test event"
        c.startTime = datetime.datetime(2005, 10, 31, 12, 0, 0, 0, tzinfo)
        c.duration = datetime.timedelta(minutes=60)
        c.anyTime = False
        c.itsItem.icalUID = "dc969288-7029-11db-df82-93e0418c9857"
        coll.add(c.itsItem)

    def PrepareShares(self):

        view0 = self.views[0]
        sandbox0 = view0.findPath("//sandbox")
        coll0 = sandbox0.findPath("testCollection")

        self.share0 = sharing.Share(itsView=view0,
            contents=coll0,
            conduit=sharing.InMemoryConduit(itsView=view0,
                                            shareName=uw("duplicates")),
            format=sharing.CalDAVFormat(itsView=view0)
        )

        subShare = sharing.Share(itsView=view0,
            contents=coll0,
            conduit=sharing.InMemoryConduit(itsView=view0,
                                            shareName=uw("duplicates/.chandler")),
            format=sharing.CloudXMLFormat(itsView=view0)
        )
        self.share0.follows = subShare

        for attr in sharing.CALDAVFILTER:
            subShare.filterAttributes.append(attr)

        if self.share0.exists():
            self.share0.destroy()
        self.share0.create()
        subShare.create()

        xml = """<?xml version="1.0" encoding="UTF-8"?>

<CalendarEvent version='2' class='osaf.pim.calendar.Calendar.CalendarEvent' uuid='dc969288-7029-11db-df82-93e0418c9857'>
<icalUID>dc969288-7029-11db-df82-93e0418c9857</icalUID>
<displayName>Event</displayName>
<body mimetype='text/plain' encoding='utf-8'></body>
<createdOn>2006-11-03 12:23:45.688922 US/Pacific</createdOn>
</CalendarEvent>
"""
        subShare.conduit.inject("dc969288-7029-11db-df82-93e0418c9857.xml",
                                xml)


    def Subscribe(self):

        view = self.views[0]
        try:
            stats = self.share0.sync()
        except sharing.SharingError:
            pass # This is what we're expecting
        else:
            raise Exception("We were expecting a SharingError")

if __name__ == "__main__":
    unittest.main()
