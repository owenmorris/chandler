
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os, random

from repository.persistence.XMLRepository import XMLRepository
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
        

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
