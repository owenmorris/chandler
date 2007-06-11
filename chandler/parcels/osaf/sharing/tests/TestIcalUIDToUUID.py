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


import unittest, os, sys
from osaf import pim, sharing
from util import testcase

class IcalUIDToUUIDTestCase(testcase.SingleRepositoryTestCase):

    def testImport(self):
        sharePath = os.path.join(os.getenv('CHANDLERHOME') or '.',
                            'parcels', 'osaf', 'sharing', 'tests')

        #sharePath is stored as schema.Text so convert to unicode
        sharePath = unicode(sharePath, sys.getfilesystemencoding())

        sharing.importFile(self.view, os.path.join(sharePath, u"icaluid.ics"))

        # This item had a UUID-friendly icalUID
        self.assert_(self.view.findUUID('bed962e5-6042-11d9-be74-000a95bb2738'))

        # This item did not have a UUID-friendly icalUID, so we hashed it
        self.assert_(self.view.findUUID('92a2a53e-497e-9e95-4fc7-20840927796e'))

if __name__ == "__main__":
    unittest.main()
