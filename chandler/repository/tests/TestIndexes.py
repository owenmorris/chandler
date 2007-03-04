#   Copyright (c) 2004-2006 Open Source Applications Foundation
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

import unittest, os, random

from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.util.Path import Path


class TestIndexes(RepositoryTestCase):
    """
    Indexes
    """

    def setUp(self):

        super(TestIndexes, self).setUp()

        view = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.kh = Path('//CineGuide/KHepburn')
        view.loadPack(cineguidePack)
        view.find(self.kh).movies.addIndex('n', 'numeric')
        view.commit()

    def testNumeric(self):

        view = self.rep.view
        movies = view.find(self.kh).movies
        keys = movies.keys()
        i = random.randint(0, len(keys) - 1)
        print 'random i:', i
        self.assert_(movies.getByIndex('n', i) is movies[keys[i]])

        self._reopenRepository()
        view = self.rep.view

        movies = view.find(self.kh).movies
        keys = movies.keys()
        i = random.randint(0, len(keys) - 1)
        print 'random i:', i
        self.assert_(movies.getByIndex('n', i) is movies[keys[i]])

    def testPlace(self):

        view = self.rep.view
        movies = view.find(self.kh).movies

        i = random.randint(0, len(movies) - 1)
        print 'random i:', i
        j = i

        while j == i:
            j = random.randint(0, len(movies) - 1)
        print 'random j:', j

        mi = movies.getByIndex('n', i)
        mj = movies.getByIndex('n', j)
        movies.placeItem(mj, mi, 'n')

        if j > i:
            self.assert_(movies.getByIndex('n', i) is mi)
            self.assert_(movies.getByIndex('n', i + 1) is mj)
        else:
            self.assert_(movies.getByIndex('n', i - 1) is mi)
            self.assert_(movies.getByIndex('n', i) is mj)

        self._reopenRepository()
        view = self.rep.view

        movies = view.find(self.kh).movies
        if j > i:
            self.assert_(movies.getByIndex('n', i).itsUUID == mi.itsUUID)
            self.assert_(movies.getByIndex('n', i + 1).itsUUID == mj.itsUUID)
        else:
            self.assert_(movies.getByIndex('n', i - 1).itsUUID == mi.itsUUID)
            self.assert_(movies.getByIndex('n', i).itsUUID == mj.itsUUID)
        
    def _remove(self):

        view = self.rep.view
        movies = view.find(self.kh).movies

        keys = movies.keys()
        values = movies.values()
        n = len(keys)

        for m in xrange(0, n / 2):
            i = random.randint(0, n - 1)
            print 'random remove:', i

            movie = movies.getByIndex('n', i)
            movies.remove(movie)
            del values[i]
        
            for i in xrange(0, n - 1):
                self.assert_(values[i] is movies.getByIndex('n', i))
            n -= 1

    def _add(self):

        view = self.rep.view
        movies = view.find(self.kh).movies

        keys = movies.keys()
        values = movies.values()
        n = len(keys)

        kind = values[0].itsKind
        parent = values[0].itsParent
        count = random.randint(0, n / 2)

        for m in xrange(0, count):
            title = "movie%d" %(n+m)
            movie = kind.newItem(title, parent)
            movies.append(movie)
        
            for i in xrange(0, n - 1):
                self.assert_(values[i] is movies.getByIndex('n', i))
            for i in xrange(n, n + m):
                self.assert_(movies.getByIndex('n', i)._name == "movie%d" %(i),
                             movies.getByIndex('n', i)._name)

    def testAdd(self):

        self._add()

    def testRemove(self):

        self._add()

    def testAddRemove(self):

        self._add()
        self._remove()

    def testRemoveAdd(self):

        self._remove()
        self._add()

    def testDeferredReindexing(self):

        view = self.rep.view
        movies = view.find(self.kh).movies
        movies.addIndex('t', 'value', attribute='title', ranges=[(0, 1)])
        movies.addIndex('f', 'string', attributes=('frenchTitle', 'title'),
                        locale='fr_FR')
        view.commit()

        m1 = movies.first()
        m2 = movies.next(m1)
        with view.reindexingDeferred():
            m1.title = 'Foo'
            self.assert_(view.isReindexingDeferred())
            m2.title = 'Baz'
            with view.reindexingDeferred() as depth:
                self.assert_(view.isReindexingDeferred())
                self.assert_(depth == 2, "depth is %d" %(depth))
                m1.title = 'Bar'
                m2.title = 'Baz'
            self.assert_(view.isReindexingDeferred())
            try:
                movies.getIndex('t').getLastKey()
            except LookupError, e:
                self.assert_('skiplist' in e.args[0], e.args)
            m1.frenchTitle = 'Alfred'

        self.assert_(not view.isReindexingDeferred())
        self.assert_(view.check(), "view does not check out")


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
