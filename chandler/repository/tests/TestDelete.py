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
Test deletion of items
"""

import unittest, os

from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.util.Path import Path
import util.timing


class TestDelete(RepositoryTestCase):
    """ Test item deletion """

    def setUp(self):

        super(TestDelete, self).setUp()

        view = self.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        view.loadPack(cineguidePack)
        view.commit()

    def testDeleteItemsInCollection(self):

        util.timing.reset()

        self._reopenRepository()
        view = self.view
        k = view.findPath('//CineGuide/KHepburn')
        util.timing.reset()
        for m in k.movies:
            util.timing.begin("repository.tests.TestDelete.testDeleteItemsInCollection")
            m.delete()
            util.timing.end("repository.tests.TestDelete.testDeleteItemsInCollection")

        self.assert_(len(k.movies) == 0)
        self.assert_(view.check())

        self._reopenRepository()
        self.assert_(self.view.check())

        util.timing.results(verbose=False)

    def testCloudDelete(self):

        util.timing.reset()
        view = self.view
        k = view.findPath('//CineGuide/KHepburn')
        util.timing.begin("repository.tests.TestDelete.testCloudDelete")
        k.delete(cloudAlias='remote')
        util.timing.end("repository.tests.TestDelete.testCloudDelete")
        view.commit()
        view.check()
        self._reopenRepository()
        self.view.check()

        util.timing.results(verbose=False)
        

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
