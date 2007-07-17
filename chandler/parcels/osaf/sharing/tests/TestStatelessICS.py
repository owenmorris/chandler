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


from util import testcase
import unittest, sys, os.path, logging, datetime
from osaf import pim, sharing


logger = logging.getLogger(__name__)

items = {
    'bff59a42-1647-11dc-be0a-ab106e3ae5d1' : ('FYI', 'fyi', None),
    'b858eadc-1647-11dc-be0a-ab106e3ae5d1' : ('Confirmed', 'confirmed', None),
    'bbccb70c-1647-11dc-be0a-ab106e3ae5d1' : ('Tentative', 'tentative', None),
    '95bd184a-1647-11dc-be0a-ab106e3ae5d1' : ('With Reminder', 'confirmed',
        datetime.timedelta(-1, 85500))
}


class StatelessICS(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.setUp()
        dir = os.path.join(os.getenv('CHANDLERHOME') or '.',
            'parcels', 'osaf', 'sharing', 'tests')

        inFile = os.path.join(dir, 'stateless.ics')
        outFile = os.path.join(dir, 'tmp_stateless.ics')



        # Both status and reminders filters active

        filters = [
            'cid:event-status-filter@osaf.us',
            'cid:reminders-filter@osaf.us',
        ]

        coll = sharing.importFile(self.views[0], inFile, filters=filters)

        for item in coll:
            uuidStr = item.icalUID
            self.assertEquals(item.displayName, items[uuidStr][0])
            self.assert_(not item.reminders)
            event = pim.EventStamp(item)
            self.assertEquals(event.transparency, 'confirmed')


        # reminders filters active

        filters = [
            'cid:reminders-filter@osaf.us',
        ]

        coll = sharing.importFile(self.views[0], inFile, filters=filters)

        for item in coll:
            uuidStr = item.icalUID
            self.assertEquals(item.displayName, items[uuidStr][0])
            self.assert_(not item.reminders)
            event = pim.EventStamp(item)
            self.assertEquals(event.transparency, items[uuidStr][1])


        # No filters active

        coll = sharing.importFile(self.views[0], inFile)

        for item in coll:
            uuidStr = item.icalUID
            self.assertEquals(item.displayName, items[uuidStr][0])
            if items[uuidStr][2] is None:
                self.assert_(not item.reminders)
            else:
                self.assertEquals(list(item.reminders)[0].delta,
                    items[uuidStr][2])

            event = pim.EventStamp(item)
            self.assertEquals(event.transparency, items[uuidStr][1])


        if os.path.exists(outFile):
            os.remove(outFile)

        try:
            # Export using reminders filter
            filters = ['cid:reminders-filter@osaf.us']
            sharing.exportFile(self.views[0], outFile, coll, filters=filters)

            # Import using no filters; verify reminders not set on items
            coll = sharing.importFile(self.views[1], outFile)

            for item in coll:
                uuidStr = item.icalUID
                self.assertEquals(item.displayName, items[uuidStr][0])
                self.assert_(not item.reminders)
                event = pim.EventStamp(item)
                self.assertEquals(event.transparency, items[uuidStr][1])

        finally:
            if os.path.exists(outFile):
                os.remove(outFile)


if __name__ == "__main__":
    unittest.main()
