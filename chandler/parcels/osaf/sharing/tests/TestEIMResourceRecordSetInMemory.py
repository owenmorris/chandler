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
from osaf import pim, sharing
from round_trip import RoundTripTestCase

from osaf.sharing import recordset_conduit, translator, eimml

from repository.item.Item import Item
from util import testcase
from application import schema

logger = logging.getLogger(__name__)


class EIMResourceRecordSetInMemoryTestCase(RoundTripTestCase):

    def runTest(self):
        self.RoundTripRun()

    def PrepareShares(self):

        view0 = self.views[0]
        coll0 = self.coll
        conduit = recordset_conduit.InMemoryResourceRecordSetConduit(
            "conduit", itsView=view0,
            shareName="exportedCollection",
            translator=translator.SharingTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share0 = sharing.Share("share", itsView=view0,
            contents=coll0, conduit=conduit)


        view1 = self.views[1]
        conduit = recordset_conduit.InMemoryResourceRecordSetConduit(
            "conduit", itsView=view1,
            shareName="exportedCollection",
            translator=translator.SharingTranslator,
            serializer=eimml.EIMMLSerializer
        )
        self.share1 = sharing.Share("share", itsView=view1,
            conduit=conduit)


if __name__ == "__main__":
    unittest.main()
