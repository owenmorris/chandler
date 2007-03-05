#   Copyright (c) 2007-2007 Open Source Applications Foundation
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

from __future__ import with_statement

import unittest, os

from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.util.Path import Path


class TestAfterChange(RepositoryTestCase):
    """
    afterChange methods (also known as observers)
    """

    def setUp(self):

        super(TestAfterChange, self).setUp()

        view = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.kh = Path('//CineGuide/KHepburn')
        view.loadPack(cineguidePack)
        movies = view.find(self.kh).movies
        movies.addIndex('n', 'numeric')
        movies.first().itsKind.getAttribute('title').afterChange = ['titleChanged']

    def testInvoke(self):
        
        view = self.rep.view
        m1 = view.find(self.kh).movies.first()
        m1._titleChanged = 0

        m1.title = 'Foo'
        self.assert_(getattr(m1, '_titleChanged', 0) == 1)

    def testDeferredInvoke(self):
        
        view = self.rep.view
        m1 = view.find(self.kh).movies.first()
        m1._titleChanged = 0

        with view.observersDeferred():
            m1.title = 'Foo'
            self.assert_(view.areObserversDeferred())
            self.assert_(getattr(m1, '_titleChanged', 0) == 0)
            m1.title = 'Bar'

        self.assert_(not view.areObserversDeferred())
        self.assert_(getattr(m1, '_titleChanged', 0) == 1)

    def testDeferredInvokeNoDiscard(self):
        
        view = self.rep.view
        m1 = view.find(self.kh).movies.first()
        m1._titleChanged = 0

        with view.observersDeferred(False):
            m1.title = 'Foo'
            self.assert_(view.areObserversDeferred())
            self.assert_(getattr(m1, '_titleChanged', 0) == 0)
            m1.title = 'Bar'
            with view.observersDeferred(False):
                m1.title = 'Baz'
                self.assert_(getattr(m1, '_titleChanged', 0) == 0)
            self.assert_(view.areObserversDeferred())
            self.assert_(getattr(m1, '_titleChanged', 0) == 0)

        self.assert_(not view.areObserversDeferred())
        self.assert_(getattr(m1, '_titleChanged', 0) == 3)


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
