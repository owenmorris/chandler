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

import unittest, os, logging
from osaf import dumpreload
from util import testcase
logger = logging.getLogger(__name__)

profile = True
printStats = False
profileLog = 'reload_perf.log'

class ReloadTestCase(testcase.NRVTestCase):

    def testReload(self):
        path = os.path.join(os.getenv('CHANDLERHOME') or '.',
            'parcels', 'osaf', 'tests', 'office.dump')

        if profile:
            import hotshot, hotshot.stats
            prof = hotshot.Profile(profileLog)
            prof.runcall(dumpreload.reload, self.view, path, testmode=True)
            prof.close()
            if printStats:
                stats = hotshot.stats.load(profileLog)
                stats.sort_stats("cumulative")
                stats.print_stats(30)
                stats.sort_stats("time")
                stats.print_stats(30)
                stats.sort_stats("calls")
                stats.print_stats(30)
        else:
            dumpreload.reload(self.view, path, testmode=True)

if __name__ == "__main__":
    unittest.main()
