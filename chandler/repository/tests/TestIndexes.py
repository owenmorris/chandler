
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os, random

from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.util.Path import Path


class TestIndexes(RepositoryTestCase):
    """
    Indexes
    """

    def setUp(self):

        super(TestIndexes, self).setUp()

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        self.kh = Path('//CineGuide/KHepburn')
        self.rep.loadPack(cineguidePack)
        self.rep.find(self.kh).movies.addIndex('n', 'numeric')
        self.rep.commit()

    def testNumeric(self):

        movies = self.rep.find(self.kh).movies
        keys = movies.keys()
        i = random.randint(0, len(keys) - 1)
        print 'random i:', i
        self.assert_(movies.getByIndex('n', i) is movies[keys[i]])

        self._reopenRepository()

        movies = self.rep.find(self.kh).movies
        keys = movies.keys()
        i = random.randint(0, len(keys) - 1)
        print 'random i:', i
        self.assert_(movies.getByIndex('n', i) is movies[keys[i]])

    def testPlace(self):

        movies = self.rep.find(self.kh).movies

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

        movies = self.rep.find(self.kh).movies
        if j > i:
            self.assert_(movies.getByIndex('n', i).itsUUID == mi.itsUUID)
            self.assert_(movies.getByIndex('n', i + 1).itsUUID == mj.itsUUID)
        else:
            self.assert_(movies.getByIndex('n', i - 1).itsUUID == mi.itsUUID)
            self.assert_(movies.getByIndex('n', i).itsUUID == mj.itsUUID)
        
    def _remove(self):

        movies = self.rep.find(self.kh).movies

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

        movies = self.rep.find(self.kh).movies

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


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
