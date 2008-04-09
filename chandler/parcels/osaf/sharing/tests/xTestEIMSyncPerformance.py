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

import unittest, sys, os, logging, datetime, time
from osaf import pim, sharing, dumpreload
from osaf.sharing import recordset_conduit, translator, eimml
from util import testcase
import hotshot, hotshot.stats

logger = logging.getLogger(__name__)


class EIMSyncPerformanceTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):
        self.PrepareData()
        self.PrepareShares()

        # Set to True any method you want to profile:

        self.Publish(profile=False)
        self.Subscribe(profile=False)
        self.Sync(profile=False)

    def PrepareData(self):

        inFile = self.getTestResourcePath('office.dump')
        collUUID = "5e4092b2-e79d-11db-9ba9-a51a3cf1b340"
        dumpreload.reload(self.views[0], path, testmode=True)
        self.coll0 = self.views[0].findUUID(collUUID)
        self.views[0].commit()

    def PrepareShares(self):

        conduit = recordset_conduit.InMemoryDiffRecordSetConduit(
            "conduit", itsView=self.views[0],
            shareName="OfficeCal",
            translator=translator.SharingTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share0 = sharing.Share("share", itsView=self.views[0],
            contents=self.coll0, conduit=conduit)

        conduit = recordset_conduit.InMemoryDiffRecordSetConduit(
            "conduit", itsView=self.views[1],
            shareName="OfficeCal",
            translator=translator.SharingTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share1 = sharing.Share("share", itsView=self.views[1],
            conduit=conduit)

    def Publish(self, profile=False):
        if profile:
            profileLog = 'publish_perf.log'
            prof = hotshot.Profile(profileLog)
            prof.runcall(self.share0.put)
            prof.close()
        else:
            self.share0.put()

    def Subscribe(self, profile=False):
        if profile:
            profileLog = 'subscribe_perf.log'
            prof = hotshot.Profile(profileLog)
            prof.runcall(self.share1.sync)
            prof.close()
        else:
            self.share1.sync()

    def Sync(self, profile=False):
        count = 20
        for item in self.coll0:
            item.displayName = "changed"
            if count == 0:
                break
            count -= 1

        self.views[0].commit()
        if profile:
            profileLog = 'sync_perf.log'
            prof = hotshot.Profile(profileLog)
            prof.runcall(self.share0.sync)
            prof.close()
        else:
            self.share0.sync()

if __name__ == "__main__":
    unittest.main()
