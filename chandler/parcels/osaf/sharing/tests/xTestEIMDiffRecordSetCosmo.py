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
from osaf.sharing.tests.round_trip import RoundTripTestCase

from osaf.sharing import recordset_conduit, translator, eimml, cosmo

from repository.item.Item import Item
from util import testcase
from PyICU import ICUtzinfo
from application import schema

import osaf.sharing.tests.round_trip
osaf.sharing.tests.round_trip.checkStatistics = False

logger = logging.getLogger(__name__)

class EIMDiffRecordSetCosmoTestCase(RoundTripTestCase):

    def runTest(self):
        self.RoundTripRun()

    def PrepareShares(self):

        view0 = self.views[0]
        coll0 = self.coll
        self.assert_(not pim.has_stamp(coll0, sharing.SharedItem))
        account = cosmo.CosmoAccount(itsView=view0,
            host="bcm.osafoundation.org",
            port=8080,
            path="/cosmo",
            username="test",
            password="test1",
            useSSL=False
        )
        conduit = cosmo.CosmoConduit(itsView=view0,
            account=account,
            shareName=coll0.itsUUID.str16(),
            translator=translator.PIMTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share0 = sharing.Share("share", itsView=view0,
            contents=coll0, conduit=conduit)
        self.assert_(pim.has_stamp(coll0, sharing.SharedItem))


        view1 = self.views[1]
        account = cosmo.CosmoAccount(itsView=view1,
            host="bcm.osafoundation.org",
            port=8080,
            path="/cosmo",
            username="test",
            password="test1",
            useSSL=False
        )
        conduit = cosmo.CosmoConduit(itsView=view1,
            account=account,
            shareName=coll0.itsUUID.str16(),
            translator=translator.PIMTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share1 = sharing.Share("share", itsView=view1,
            conduit=conduit)


if __name__ == "__main__":
    unittest.main()
