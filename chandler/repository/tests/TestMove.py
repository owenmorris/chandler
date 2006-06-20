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

"""
Test moving of items
"""

import unittest, os

from repository.tests.RepositoryTestCase import RepositoryTestCase


class TestMove(RepositoryTestCase):
    """ Test item moving """

    def setUp(self):

        super(TestMove, self).setUp()
        view = self.rep.view

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        view.loadPack(cineguidePack)
        
    def move(self, withCommit):

        view = self.rep.view
        if withCommit:
            view.commit()
            
        c = view['CineGuide']
        k = c['KHepburn']
        m = k.movies.first()

        m.move(view)
        self.assert_(m._parent is view)
        self.assert_(m._root is m)
        self.assert_(c.hasChild(m._name) is False)

        if withCommit:
            view.commit()
        
        m.move(c)
        self.assert_(m._parent is c)
        self.assert_(m._root is c)
        self.assert_(view.hasRoot(m._name) is False)

        if withCommit:
            view.commit()
        
    def testMoveCommit(self):
        self.move(True)

    def testMove(self):
        self.move(False)

    def testReopenCommit(self):
        self._reopenRepository()
        self.move(True)

    def testReopen(self):
        self._reopenRepository()
        self.move(False)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
