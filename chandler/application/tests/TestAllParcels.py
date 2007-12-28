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

"""
Loads all parcels
"""

import os, sys, unittest

from ParcelLoaderTestCase import ParcelLoaderTestCase
from application import Utility, Globals
import util.timing

class AllParcelsTestCase(ParcelLoaderTestCase):

    def testAllParcels(self):
        """
        Test to ensure all parcels load
        """
        util.timing.begin("application.TestAllParcels")

        self.loadParcels()
        
        util.timing.end("application.TestAllParcels")
        util.timing.results(verbose=False)

        self.assert_(self.view.check(),
                     "Repository check failed -- see chandler.log" )

if __name__ == "__main__":
    unittest.main()
