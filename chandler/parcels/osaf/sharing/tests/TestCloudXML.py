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


import unittest, sys, os, logging, datetime, time, os.path
from osaf import pim, sharing
from repository.item.Item import Item
from chandlerdb.util.c import UUID
from util import testcase
from application import schema
from i18n.tests import uw

logger = logging.getLogger(__name__)

class CloudXMLTestCase(testcase.DualRepositoryTestCase):

    def runTest(self):

        self.setUp()

        self.dir = os.path.join(os.getenv('CHANDLERHOME') or '.',
            'parcels', 'osaf', 'sharing', 'tests')

        self.GoodData()
        self.BadData()

    def GoodData(self):

        view = self.views[0]
        share = sharing.Share(itsView=view)
        share.format = sharing.CloudXMLFormat(itsView=view)
        fileName = "good.xml"
        filePath = os.path.join(self.dir, fileName)
        goodDataFile = file(filePath, "r")
        goodData = goodDataFile.read()
        goodDataFile.close()
        stats = { 'added' : [], 'modified' : [], 'removed' : [] }
        item = share.format.importProcess(view, goodData, stats=stats)
        self.assertEquals(len(stats['added']), 1)
        self.assertEquals(stats['added'][0],
            UUID('a54d7ff0-23e2-11db-9020-ae744e613304'))

    def BadData(self):

        view = self.views[0]
        share = sharing.Share(itsView=view)
        share.format = sharing.CloudXMLFormat(itsView=view)
        fileName = "bad.xml"
        filePath = os.path.join(self.dir, fileName)
        badDataFile = file(filePath, "r")
        badData = badDataFile.read()
        badDataFile.close()
        stats = { 'added' : [], 'modified' : [], 'removed' : [] }
        try:
            item = share.format.importProcess(view, badData, stats=stats)
        except sharing.MalformedData:
            pass # This is what we're expecting
        else:
            raise Exception("We were expecting a MalformedData exception")

if __name__ == "__main__":
    unittest.main()
