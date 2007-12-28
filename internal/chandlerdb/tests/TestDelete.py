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

from chandlerdb.util.RepositoryTestCase import RepositoryTestCase
from chandlerdb.util.Path import Path


class TestDelete(RepositoryTestCase):
    """ Test item deletion """

    def setUp(self):

        super(TestDelete, self).setUp()
        self.loadCineguide(self.view)

    def testDeleteItemsInCollection(self):

        self._reopenRepository()
        view = self.view
        k = view.findPath('//CineGuide/KHepburn')
        for m in k.movies:
            m.delete()

        self.assert_(len(k.movies) == 0)
        self.assert_(view.check())

        self._reopenRepository()
        self.assert_(self.view.check())

    def testCloudDelete(self):

        view = self.view
        k = view.findPath('//CineGuide/KHepburn')
        k.delete(cloudAlias='remote')
        view.commit()
        view.check()
        self._reopenRepository()
        self.view.check()


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
