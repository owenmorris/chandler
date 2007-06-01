#   Copyright (c) 2005-2007 Open Source Applications Foundation
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


import os, unittest
import repository.tests.RepositoryTestCase as RepositoryTestCase
import util.timing

class TestParcelPerf(RepositoryTestCase.RepositoryTestCase):

    def testLoadAllParcelItems(self):
        """ Load the entire domain model into the repository and then commit it"""
        def load(parent):
            count = 0
            for child in parent.iterChildren():
                count += 1 + load(child)
            return count

        self.loadParcels(['osaf.pim'])
        view = self.view
        view.commit()

        ##TODO SHOULD NOT RUN IN RAMDB
        self._reopenRepository()
        util.timing.reset()
        util.timing.begin("repository.tests.TestLoadAll")
        count = load(self.view)
        util.timing.end("repository.tests.TestLoadAll")
        util.timing.results(verbose=False)

if __name__ == "__main__":
    unittest.main()
